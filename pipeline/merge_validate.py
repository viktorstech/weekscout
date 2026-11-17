#!/usr/bin/env python3
"""Deterministické sloučení, deduplikace, rozdělení na dávky a validace dat (0 kreditů).

Používá jen standardní knihovnu Pythonu 3.
Pravidla odpovídají schématu v GEMINI.md.

Příklady:
  python pipeline/merge_validate.py validate data.json
  python pipeline/merge_validate.py merge --include-pilot
  python pipeline/merge_validate.py batches --size 20
  python pipeline/merge_validate.py apply --out data/curated.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
CANDIDATES_PATH = REPO_ROOT / "data" / "candidates.json"
BATCHES_DIR = REPO_ROOT / "data" / "verify_batches"
VERIFIED_DIR = REPO_ROOT / "data" / "verified"
PILOT_PATH = REPO_ROOT / "data.json"

DATE_MIN = "2026-12-01"
DATE_MAX = "2027-08-31"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# EU-27 + EHP (IS, LI, NO) + RS, MK, TR
ALLOWED_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    "IS", "LI", "NO",
    "RS", "MK", "TR",
}

VALID_MOBILITY = ("teaching", "training", "studying")
VALID_FIELDS = {"zdravi", "pedag", "design", "human", "tech", "it", "ekon", "prir", "intl"}
VALID_SOURCE_TYPES = {"official", "imotion", "partner"}
VALID_VERIFY_STATUS = {"ověřeno", "částečně", "neověřeno"}
SOURCE_PRIORITY = {"official": 3, "imotion": 2, "partner": 1}

COMMERCIAL_BLACKLIST = (
    "pulse of mind",
    "eiapd",
    "european academy of innovation",
    "ebmx",
    "erasmus nostrum",
)

EVENT_SCHEMA_FIELDS = {
    "id", "uni", "uni_short", "country_iso", "country", "city", "lat", "lng",
    "erasmus_code", "event_name", "start", "end", "start2", "end2",
    "deadline", "deadline_note", "mobility", "fields", "topic",
    "audience", "program", "language", "fee_eur", "fee_text", "capacity",
    "registration_url", "registration_url2", "event_url", "source_urls",
    "source_type", "contacts", "notes", "verify",
}


def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def _norm_text(text: str | None) -> str:
    if not text:
        return ""
    s = _strip_accents(text).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def _norm_uni(uni: str | None) -> str:
    s = _norm_text(uni)
    for stop in ("university of applied sciences", "university of", "university", "hochschule", "universite", "universidad de"):
        s = re.sub(rf"\b{re.escape(stop)}\b", " ", s)
    return re.sub(r"\s+", " ", s).strip() or _norm_text(uni)


def _slugify(text: str) -> str:
    s = _strip_accents(text).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "event"


def _is_valid_date(val: Any) -> bool:
    if not isinstance(val, str) or not DATE_RE.match(val):
        return False
    try:
        dt.date.fromisoformat(val)
        return True
    except ValueError:
        return False


def _is_valid_url(val: Any) -> bool:
    return isinstance(val, str) and (val.startswith("http://") or val.startswith("https://"))


def _matches_blacklist(ev: dict[str, Any]) -> str | None:
    haystack = " ".join(
        str(x or "")
        for x in [
            ev.get("uni"),
            ev.get("uni_short"),
            ev.get("event_name"),
            ev.get("event_url"),
            ev.get("registration_url"),
            " ".join(ev.get("source_urls") or []),
        ]
    ).lower()
    for banned in COMMERCIAL_BLACKLIST:
        if banned in haystack:
            return banned
    return None


def _canonical_mobility(items: list[str] | None) -> list[str]:
    if not items:
        return []
    seen = set(items)
    return [m for m in VALID_MOBILITY if m in seen]


def _load_events_file(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict) and isinstance(data.get("events"), list):
        return [x for x in data["events"] if isinstance(x, dict)]
    raise ValueError(f"Neznámá struktura JSON v {path}")


def _merge_two(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    """Sloučí duplicitní akce se zachováním hodnotnějšího zdroje."""
    p_rank = SOURCE_PRIORITY.get(str(primary.get("source_type") or ""), 0)
    s_rank = SOURCE_PRIORITY.get(str(secondary.get("source_type") or ""), 0)
    base, extra = (dict(primary), secondary) if p_rank >= s_rank else (dict(secondary), primary)

    # Sloučit source_urls bez duplicit
    urls: list[str] = []
    for src in (base.get("source_urls") or []) + (extra.get("source_urls") or []):
        if isinstance(src, str) and src not in urls:
            urls.append(src)
    base["source_urls"] = urls

    # Sloučit mobility v kanonickém pořadí
    base["mobility"] = _canonical_mobility((base.get("mobility") or []) + (extra.get("mobility") or []))

    # Sloučit fields (max 3)
    fields: list[str] = []
    for f in (base.get("fields") or []) + (extra.get("fields") or []):
        if f in VALID_FIELDS and f not in fields and len(fields) < 3:
            fields.append(f)
    if fields:
        base["fields"] = fields

    # Doplnit chybějící skalární pole z druhého záznamu
    fill_fields = (
        "uni_short", "erasmus_code", "end", "start2", "end2", "deadline",
        "deadline_note", "language", "fee_eur", "fee_text", "capacity",
        "registration_url", "registration_url2", "event_url", "notes",
        "lat", "lng", "audience", "program", "contacts",
    )
    for k in fill_fields:
        if base.get(k) in (None, "", []):
            if extra.get(k) not in (None, "", []):
                base[k] = extra[k]

    return base


def _dedup_key(ev: dict[str, Any]) -> tuple[str, str, str]:
    iso = str(ev.get("country_iso") or "").upper()
    uni_k = _norm_uni(ev.get("uni"))
    start = str(ev.get("start") or "")[:7]  # YYYY-MM
    return (iso, uni_k, start)


def cmd_merge(args: argparse.Namespace) -> int:
    raw_files = sorted(RAW_DIR.glob("*.json"))
    all_raw: list[dict[str, Any]] = []
    sources_used: list[str] = []

    if args.include_pilot and PILOT_PATH.is_file():
        pilot_events = _load_events_file(PILOT_PATH)
        all_raw.extend(pilot_events)
        sources_used.append("data.json")

    for rf in raw_files:
        evs = _load_events_file(rf)
        all_raw.extend(evs)
        sources_used.append(str(rf.relative_to(REPO_ROOT)))

    if not all_raw:
        print(f"V {RAW_DIR} nejsou žádné JSON soubory ke sloučení.", file=sys.stderr)
        return 1

    filtered_commercial = 0
    filtered_date = 0
    filtered_country = 0
    merged_dups = 0

    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    url_to_key: dict[str, tuple[str, str, str]] = {}

    for ev in all_raw:
        ev = {k: v for k, v in ev.items() if k in EVENT_SCHEMA_FIELDS}

        if _matches_blacklist(ev):
            filtered_commercial += 1
            continue

        iso = str(ev.get("country_iso") or "").upper()
        if iso == "EL":
            iso = "GR"
            ev["country_iso"] = "GR"
            print(f"[oprava] {ev.get('uni')}: country_iso EL -> GR", file=sys.stderr)
        if iso and iso not in ALLOWED_COUNTRIES:
            filtered_country += 1
            continue

        start = ev.get("start")
        if not _is_valid_date(start) or not (DATE_MIN <= start <= DATE_MAX):
            filtered_date += 1
            continue

        end = ev.get("end")
        if end and _is_valid_date(end) and end < start:
            filtered_date += 1
            continue

        ev["mobility"] = _canonical_mobility(ev.get("mobility"))

        dk = _dedup_key(ev)
        ev_url = (ev.get("event_url") or "").strip().rstrip("/")
        if dk in by_key:
            by_key[dk] = _merge_two(by_key[dk], ev)
            merged_dups += 1
        elif ev_url and ev_url in url_to_key:
            existing_k = url_to_key[ev_url]
            by_key[existing_k] = _merge_two(by_key[existing_k], ev)
            merged_dups += 1
        else:
            by_key[dk] = ev
            if ev_url:
                url_to_key[ev_url] = dk

    # Unikátní slugy pro id
    used_ids: set[str] = set()
    final_events: list[dict[str, Any]] = []
    for ev in sorted(by_key.values(), key=lambda x: (str(x.get("start") or ""), str(x.get("uni") or ""))):
        raw_id = ev.get("id") or f"{_slugify(str(ev.get('uni_short') or ev.get('uni') or 'event'))}-{str(ev.get('start') or '')[:7]}"
        slug = _slugify(str(raw_id))
        cand = slug
        n = 2
        while cand in used_ids:
            cand = f"{slug}-{n}"
            n += 1
        used_ids.add(cand)
        ev["id"] = cand
        final_events.append(ev)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "updated": dt.date.today().isoformat(),
            "count": len(final_events),
            "sources": sources_used,
        },
        "events": final_events,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Souhrn
    by_src = Counter(ev.get("source_type") or "neuvedeno" for ev in final_events)
    by_country = Counter(ev.get("country_iso") or "??" for ev in final_events)
    no_end = sum(1 for ev in final_events if not ev.get("end"))
    no_dl = sum(1 for ev in final_events if not ev.get("deadline"))

    print(f"Uloženo do: {out_path}")
    print(f"Načteno raw záznamů: {len(all_raw)}")
    print(f"Vyřazeno komerčních: {filtered_commercial} | mimo termín: {filtered_date} | mimo země: {filtered_country}")
    print(f"Sloučeno duplicit:   {merged_dups}")
    print(f"Výsledný počet:      {len(final_events)} akcí z {len(by_country)} zemí")
    print(f"Podle source_type:   {dict(by_src)}")
    print(f"Chybí end: {no_end} | Chybí deadline: {no_dl}")
    return 0


def cmd_batches(args: argparse.Namespace) -> int:
    in_path = Path(args.input)
    if not in_path.is_file():
        print(f"Soubor neexistuje: {in_path}", file=sys.stderr)
        return 1

    events = _load_events_file(in_path)
    BATCHES_DIR.mkdir(parents=True, exist_ok=True)
    for old in BATCHES_DIR.glob("batch_*.json"):
        old.unlink()

    size = max(1, args.size)
    blind_fields = (
        "id", "uni", "uni_short", "country_iso", "country", "city",
        "event_name", "start", "end", "start2", "end2",
        "deadline", "deadline_note", "mobility", "fee_eur", "fee_text",
        "capacity", "language", "erasmus_code",
        "registration_url", "registration_url2", "event_url", "source_urls",
        "source_type", "contacts",
    )

    total_batches = 0
    for idx in range(0, len(events), size):
        total_batches += 1
        chunk = [{k: ev.get(k) for k in blind_fields if k in ev} for ev in events[idx : idx + size]]
        bpath = BATCHES_DIR / f"batch_{total_batches:02d}.json"
        bpath.write_text(json.dumps(chunk, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Vytvořeno {total_batches} nezávislých dávek po max {size} akcích v {BATCHES_DIR}")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    cand_path = Path(args.candidates)
    if not cand_path.is_file():
        print(f"Soubor s kandidáty neexistuje: {cand_path}", file=sys.stderr)
        return 1

    events = _load_events_file(cand_path)
    ver_files = sorted(VERIFIED_DIR.glob("*.json"))
    reports: dict[str, dict[str, Any]] = {}

    for vf in ver_files:
        data = json.loads(vf.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("results", [])
        for rep in items:
            if isinstance(rep, dict) and rep.get("id"):
                reports[str(rep["id"])] = rep

    today = dt.date.today().isoformat()
    kept: list[dict[str, Any]] = []
    removed = 0
    unmatched = 0

    for ev in events:
        eid = str(ev.get("id"))
        rep = reports.get(eid)
        if rep is None:
            unmatched += 1
            if args.only_verified:
                continue
            kept.append(ev)
            continue

        if rep.get("remove") is True:
            removed += 1
            continue

        ev = dict(ev)
        fixes = rep.get("fixes") or {}
        if isinstance(fixes, dict):
            for fk, fv in fixes.items():
                if fk in EVENT_SCHEMA_FIELDS and fk != "id":
                    ev[fk] = fv

        status = rep.get("status")
        if status not in VALID_VERIFY_STATUS:
            status = "neověřeno"
        ev["verify"] = {
            "status": status,
            "note": rep.get("note") or "",
            "checked": rep.get("checked") or today,
        }

        if args.only_verified and status == "neověřeno":
            continue
        kept.append(ev)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "updated": today,
            "count": len(kept),
        },
        "events": kept,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Aplikováno {len(reports)} záznamů ověření -> {out_path}")
    print(f"Ponecháno: {len(kept)} | Vyřazeno (remove=true): {removed} | Bez reportu: {unmatched}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.is_file():
        print(f"Soubor neexistuje: {path}", file=sys.stderr)
        return 1

    raw = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    if isinstance(raw, dict):
        meta = raw.get("meta")
        events = raw.get("events")
        if not isinstance(events, list):
            errors.append("Chybí pole 'events' (musí být seznam).")
            events = []
        if isinstance(meta, dict):
            if meta.get("count") != len(events):
                errors.append(f"meta.count ({meta.get('count')}) neodpovídá počtu akcí ({len(events)}).")
            if not _is_valid_date(meta.get("updated")):
                warnings.append("meta.updated chybí nebo není ve formátu YYYY-MM-DD.")
        else:
            warnings.append("Chybí objekt 'meta'.")
    elif isinstance(raw, list):
        events = raw
        if not args.candidates:
            warnings.append("Kořenový prvek je pole místo objektu {meta, events}.")
    else:
        print("CHYBA: Neplatný kořenový JSON typ.", file=sys.stderr)
        return 1

    seen_ids: set[str] = set()
    for idx, ev in enumerate(events):
        prefix = f"[{idx}:{ev.get('id', '?')}]"
        if not isinstance(ev, dict):
            errors.append(f"{prefix} Položka není JSON objekt.")
            continue

        eid = ev.get("id")
        if not isinstance(eid, str) or not eid:
            errors.append(f"{prefix} Chybí id.")
        else:
            if eid in seen_ids:
                errors.append(f"{prefix} Duplicitní id '{eid}'.")
            seen_ids.add(eid)
            if not SLUG_RE.match(eid):
                warnings.append(f"{prefix} id '{eid}' není čistý lowercase slug.")

        for req in ("uni", "country", "city", "event_name", "topic"):
            if not isinstance(ev.get(req), str) or not ev[req].strip():
                errors.append(f"{prefix} Chybí povinné textové pole '{req}'.")

        iso = ev.get("country_iso")
        if iso == "EL":
            errors.append(f"{prefix} country_iso je 'EL', musí být 'GR'.")
        elif iso not in ALLOWED_COUNTRIES:
            errors.append(f"{prefix} Neplatné nebo nepovolené country_iso: {iso!r}.")

        for coord in ("lat", "lng"):
            if not isinstance(ev.get(coord), (int, float)):
                if args.candidates:
                    warnings.append(f"{prefix} Chybí souřadnice '{coord}'.")
                else:
                    errors.append(f"{prefix} Chybí číselná souřadnice '{coord}'.")

        start = ev.get("start")
        end = ev.get("end")
        if not _is_valid_date(start):
            errors.append(f"{prefix} Neplatné start: {start!r}.")
        elif not (DATE_MIN <= start <= DATE_MAX):
            errors.append(f"{prefix} start ({start}) je mimo rozsah {DATE_MIN}..{DATE_MAX}.")

        if end is None and args.candidates:
            warnings.append(f"{prefix} Chybí 'end'.")
        elif not _is_valid_date(end):
            errors.append(f"{prefix} Neplatné end: {end!r}.")
        elif _is_valid_date(start) and end < start:
            errors.append(f"{prefix} end ({end}) je dříve než start ({start}).")

        for opt_date in ("start2", "end2", "deadline"):
            val = ev.get(opt_date)
            if val is not None and not _is_valid_date(val):
                errors.append(f"{prefix} Neplatné datum {opt_date}: {val!r}.")

        mob = ev.get("mobility")
        if not isinstance(mob, list) or not mob or any(m not in VALID_MOBILITY for m in mob):
            errors.append(f"{prefix} Neplatné mobility: {mob!r}.")
        elif mob != _canonical_mobility(mob):
            warnings.append(f"{prefix} mobility {mob} není v kanonickém pořadí {list(VALID_MOBILITY)}.")

        flds = ev.get("fields")
        if not isinstance(flds, list) or not (1 <= len(flds) <= 3) or any(f not in VALID_FIELDS for f in flds):
            errors.append(f"{prefix} fields musí mít 1–3 povolené kódy, je: {flds!r}.")

        surls = ev.get("source_urls")
        if not isinstance(surls, list) or not surls or any(not _is_valid_url(u) for u in surls):
            errors.append(f"{prefix} source_urls musí být neprázdný seznam http(s) URL.")

        for opt_url in ("registration_url", "registration_url2", "event_url"):
            val = ev.get(opt_url)
            if val is not None and not _is_valid_url(val):
                errors.append(f"{prefix} Neplatná URL v {opt_url}: {val!r}.")

        if ev.get("source_type") not in VALID_SOURCE_TYPES:
            errors.append(f"{prefix} Neplatné source_type: {ev.get('source_type')!r}.")

        ver = ev.get("verify")
        if ver is None and args.candidates:
            pass
        elif not isinstance(ver, dict):
            errors.append(f"{prefix} Chybí objekt 'verify'.")
        else:
            if ver.get("status") not in VALID_VERIFY_STATUS:
                errors.append(f"{prefix} Neplatný verify.status: {ver.get('status')!r}.")
            if not _is_valid_date(ver.get("checked")):
                warnings.append(f"{prefix} verify.checked není YYYY-MM-DD.")

        banned = _matches_blacklist(ev)
        if banned:
            errors.append(f"{prefix} Komerční subjekt na blacklistu ('{banned}').")

        if "obor_note" in ev:
            warnings.append(f"{prefix} Obsahuje nepoužívané pole 'obor_note'.")

    print(f"Validace: {path} ({len(events)} akcí)")
    print(f"Chyb: {len(errors)} | Varování: {len(warnings)}")
    for e in errors[:50]:
        print(f"  CHYBA: {e}")
    for w in warnings[:30]:
        print(f"  VAROVÁNÍ: {w}")
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Sloučení, dávkování a validace dat Erasmus International Weeks.")
    sub = p.add_subparsers(dest="cmd", required=True)

    mg = sub.add_parser("merge", help="Sloučí data/raw/*.json do data/candidates.json.")
    mg.add_argument("--include-pilot", action="store_true", help="Zahrnout i stávající pilotní data.json.")
    mg.add_argument("--out", default=str(CANDIDATES_PATH), help="Výstupní soubor.")
    mg.set_defaults(func=cmd_merge)

    bt = sub.add_parser("batches", help="Rozdělí data/candidates.json do nezávislých dávek pro Agenta 4.")
    bt.add_argument("--input", default=str(CANDIDATES_PATH), help="Vstupní soubor s kandidáty.")
    bt.add_argument("--size", type=int, default=20, help="Počet akcí na dávku (výchozí 20).")
    bt.set_defaults(func=cmd_batches)

    ap = sub.add_parser("apply", help="Aplikuje reporty z data/verified/*.json na data/candidates.json.")
    ap.add_argument("--candidates", default=str(CANDIDATES_PATH), help="Vstupní candidates.json.")
    ap.add_argument("--out", default=str(REPO_ROOT / "data" / "curated.json"), help="Výstupní soubor.")
    ap.add_argument("--only-verified", action="store_true", help="Vynechat akce se stavem 'neověřeno' nebo bez reportu.")
    ap.set_defaults(func=cmd_apply)

    vl = sub.add_parser("validate", help="Zvaliduje JSON soubor oproti schématu z GEMINI.md.")
    vl.add_argument("file", help="Cesta k JSON souboru.")
    vl.add_argument("--candidates", action="store_true", help="Mírnější režim pro neověřené kandidáty.")
    vl.set_defaults(func=cmd_validate)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
