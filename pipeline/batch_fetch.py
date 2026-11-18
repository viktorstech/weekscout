#!/usr/bin/env python3
"""Dávkový runner nad pipeline/exa_client.py pro sběr, nezávislé ověření a doplnění.

Spouští dotazy přes jednotlivé klíče EXA_API_KEY_1..5, využívá lokální cache
a ukládá stažené stránky do data/cache/, odkud je zpracují agenti 1–5.

Příklady:
  python pipeline/batch_fetch.py collect --mode pilot
  python pipeline/batch_fetch.py verify data/verify_batches/batch_01.json --key 4
  python pipeline/batch_fetch.py enrich data/curated.json --key 5 --limit 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import exa_client  # noqa: E402

REPO_ROOT = exa_client.REPO_ROOT
CACHE_DIR = exa_client.CACHE_DIR

PILOT_QUERIES: dict[str, tuple[int, list[dict[str, Any]]]] = {
    "01_portals": (
        1,
        [
            {
                "query": "International Staff Week 2027 Erasmus",
                "includeDomains": ["staffmobility.eu"],
                "numResults": 8,
            },
            {
                "query": '"Blended Intensive Programme" OR "BIP" 2027 Erasmus CIVIS OR ENHANCE OR EUGLOH OR "Una Europa"',
                "numResults": 8,
            },
        ],
    ),
    "02_north_west": (
        2,
        [
            {
                "query": '"International Week" OR "Staff Week" 2027 university Finland OR Sweden OR Norway OR Denmark OR Iceland',
                "numResults": 8,
            },
            {
                "query": '"International Staff Week" OR "International Week" 2027 university France OR Belgium OR Netherlands OR Germany OR Austria OR Ireland',
                "numResults": 8,
            },
        ],
    ),
    "03_south_east": (
        3,
        [
            {
                "query": '"International Week" OR "Staff Week" 2027 university Greece OR Bulgaria OR Serbia OR Romania OR Malta OR Cyprus',
                "numResults": 8,
            },
            {
                "query": '"International Staff Week" OR "International Week" 2027 university Spain OR Portugal OR Italy OR Poland OR Lithuania OR Estonia OR Czech',
                "numResults": 8,
            },
        ],
    ),
}

FULL_EXTRA_QUERIES: dict[str, list[dict[str, Any]]] = {
    "01_portals": [
        {
            "query": "Teaching Week OR Training Week 2027 March April May June",
            "includeDomains": ["staffmobility.eu"],
            "numResults": 15,
        },
        {
            "query": "Staff Week 2027 January February July August",
            "includeDomains": ["staffmobility.eu"],
            "numResults": 15,
        },
        {
            "query": '"Blended Intensive Programme" 2027 call for students OR staff university Europe',
            "numResults": 15,
        },
    ],
    "02_north_west": [
        {
            "query": '"Staff Training Week" 2027 university Germany OR Austria OR Netherlands',
            "numResults": 15,
        },
        {
            "query": '"International Teaching Week" 2027 university Finland OR Sweden OR Norway OR Denmark',
            "numResults": 15,
        },
        {
            "query": '"Semaine Internationale" OR "International Staff Week" 2027 université France OR Luxembourg',
            "numResults": 15,
        },
    ],
    "03_south_east": [
        {
            "query": '"International Staff Week" 2027 university Spain OR Portugal OR Italy',
            "numResults": 15,
        },
        {
            "query": '"International Week" 2027 university Poland OR Hungary OR Slovakia OR Slovenia OR Croatia',
            "numResults": 15,
        },
        {
            "query": '"International Staff Week" 2027 university Turkey OR Serbia OR Macedonia OR Latvia OR Lithuania',
            "numResults": 15,
        },
    ],
}


GAPS_QUERIES: dict[str, tuple[int, list[dict[str, Any]]]] = {
    "04_gaps": (
        2,
        [
            {
                "query": '"International Staff Week" OR "International Week" OR "Staff Training Week" 2027 university Sweden OR Norway OR Iceland',
                "numResults": 12,
            },
            {
                "query": '"International Staff Week" OR "International Week" OR "BIP" 2027 university Malta OR Luxembourg OR Estonia',
                "numResults": 12,
            },
            {
                "query": '"International Staff Week" OR "International Week" OR "Staff Training Week" 2027 university Serbia OR "North Macedonia" OR Belgrade OR Skopje',
                "numResults": 12,
            },
        ],
    ),
}


WAVE_A_QUERIES: dict[str, tuple[int, list[dict[str, Any]]]] = {
    "05_wave_a_czsk": (
        1,
        [
            {
                "query": '"International Week" OR "Staff Week" OR "Teaching Week" OR "Staff Training Week" 2027',
                "includeDomains": ["cvut.cz", "vut.cz", "upol.cz", "czu.cz", "vsb.cz", "tul.cz", "jcu.cz", "uhk.cz", "upce.cz", "ujep.cz", "vscht.cz"],
                "numResults": 15,
            },
            {
                "query": '"Blended Intensive Programme" OR "BIP" 2027 Erasmus',
                "includeDomains": ["cvut.cz", "vut.cz", "upol.cz", "czu.cz", "vsb.cz", "tul.cz", "jcu.cz", "uhk.cz", "upce.cz", "ujep.cz", "vscht.cz", "vse.cz", "cuni.cz", "muni.cz"],
                "numResults": 15,
            },
            {
                "query": '"International Week" OR "Staff Week" OR "Teaching Week" OR "BIP" 2027',
                "includeDomains": ["uniba.sk", "euba.sk", "tuke.sk", "uniza.sk", "upjs.sk", "umb.sk", "ukf.sk", "uniag.sk", "stuba.sk"],
                "numResults": 15,
            },
            {
                "query": '"International Staff Week" OR "International Week" OR "Staff Training Week" 2027 "Czech Republic" OR "Czechia" OR "Slovakia" university',
                "numResults": 12,
            },
        ],
    ),
}


WAVE_BC_QUERIES: dict[str, tuple[int, list[dict[str, Any]]]] = {
    "06_wave_b_bips": (
        3,
        [
            {
                "query": "Blended Intensive Programme BIP 2027 course apply deadline",
                "includeDomains": ["civis.eu"],
                "numResults": 15,
            },
            {
                "query": '"Blended Intensive Programme" OR "BIP" 2027 EUGLOH OR ENHANCE OR "Una Europa" OR Arqus OR ECIU OR EPICUR OR FORTHEM OR YUFE',
                "numResults": 15,
            },
            {
                "query": '"Blended Intensive Programme" 2027 ECTS students application deadline university Europe',
                "numResults": 15,
            },
        ],
    ),
    "07_wave_c_europe": (
        3,
        [
            {
                "query": '"International Staff Week" OR "International Week" OR "Teaching Week" 2027 university Sweden OR Norway OR Netherlands OR Luxembourg OR Iceland',
                "numResults": 15,
            },
            {
                "query": '"Semaine Internationale" OR "International Staff Week" OR "International Week" 2027 university France OR Italy OR Switzerland OR Belgium OR Austria',
                "numResults": 15,
            },
            {
                "query": '"International Week" OR "Staff Week" OR "BIP" 2027 university Estonia OR Serbia OR "North Macedonia" OR Greece OR Romania OR Bulgaria OR Hungary',
                "numResults": 15,
            },
            {
                "query": "2027 Teaching OR Library OR AI OR Sustainability OR Inclusion",
                "includeDomains": ["staffmobility.eu"],
                "numResults": 15,
            },
        ],
    ),
}


def _cost(resp: dict[str, Any]) -> float:
    cd = resp.get("costDollars")
    if isinstance(cd, dict):
        val = cd.get("total")
        if isinstance(val, (int, float)):
            return float(val)
    return 0.0


def cmd_collect(args: argparse.Namespace) -> int:
    total_cost = 0.0
    if args.mode == "gaps":
        source_map = GAPS_QUERIES
    elif args.mode == "wave_a":
        source_map = WAVE_A_QUERIES
    elif args.mode == "wave_bc":
        source_map = WAVE_BC_QUERIES
    else:
        source_map = PILOT_QUERIES
    for agent_name, (key_slot, base_queries) in source_map.items():
        queries = list(base_queries)
        if args.mode == "full":
            queries.extend(FULL_EXTRA_QUERIES.get(agent_name, []))

        seen_urls: set[str] = set()
        pages: list[dict[str, Any]] = []
        agent_cost = 0.0

        for qspec in queries:
            payload: dict[str, Any] = {
                "query": qspec["query"],
                "numResults": qspec.get("numResults", 8),
                "type": "auto",
                "contents": {"text": {"maxCharacters": args.max_chars}},
            }
            if "includeDomains" in qspec:
                payload["includeDomains"] = qspec["includeDomains"]

            try:
                resp = exa_client.exa_post(
                    exa_client.EXA_SEARCH_URL,
                    payload,
                    preferred_key=key_slot,
                    use_cache=not args.no_cache,
                )
            except RuntimeError as exc:
                print(f"[varování] {agent_name} dotaz selhal: {exc}", file=sys.stderr)
                continue

            agent_cost += _cost(resp)
            for item in resp.get("results", []):
                url = item.get("url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                pages.append(
                    {
                        "query": qspec["query"],
                        "title": item.get("title"),
                        "url": url,
                        "publishedDate": item.get("publishedDate"),
                        "text": (item.get("text") or "")[: args.max_chars],
                    }
                )

        out_path = CACHE_DIR / f"fetched_{agent_name}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(
                {
                    "agent": agent_name,
                    "mode": args.mode,
                    "key_slot": key_slot,
                    "count": len(pages),
                    "cost_dollars": round(agent_cost, 4),
                    "pages": pages,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        total_cost += agent_cost
        print(f"{agent_name} (klíč #{key_slot}): {len(pages)} unikátních stránek -> {out_path.name} (cena ~${agent_cost:.4f})")

    print(f"Celková cena sběru (včetně cache hitů): ~${total_cost:.4f}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    bpath = Path(args.batch)
    if not bpath.is_file():
        print(f"Dávka neexistuje: {bpath}", file=sys.stderr)
        return 1

    events = json.loads(bpath.read_text(encoding="utf-8"))
    evidence: list[dict[str, Any]] = []
    total_cost = 0.0

    for ev in events:
        eid = ev.get("id")
        urls: list[str] = []
        for candidate_url in [ev.get("event_url"), ev.get("registration_url"), *(ev.get("source_urls") or [])]:
            if isinstance(candidate_url, str) and candidate_url.startswith(("http://", "https://")) and candidate_url not in urls:
                urls.append(candidate_url)

        fetched_pages: list[dict[str, Any]] = []
        exa_needed: list[str] = []

        for u in urls[:3]:
            res = exa_client.direct_fetch(u, max_chars=args.max_chars, use_cache=not args.no_cache)
            if res.get("text") and len(res["text"]) >= 350:
                fetched_pages.append(res)
            else:
                exa_needed.append(u)

        if exa_needed:
            try:
                eresp = exa_client.exa_post(
                    exa_client.EXA_CONTENTS_URL,
                    {"urls": exa_needed, "text": {"maxCharacters": args.max_chars}},
                    preferred_key=args.key,
                    use_cache=not args.no_cache,
                )
                total_cost += _cost(eresp)
                for item in eresp.get("results", []):
                    fetched_pages.append(
                        {
                            "url": item.get("url"),
                            "title": item.get("title"),
                            "text": (item.get("text") or "")[: args.max_chars],
                            "_meta": {"source": "exa_contents"},
                        }
                    )
            except RuntimeError as exc:
                fetched_pages.append({"urls": exa_needed, "error": str(exc), "_meta": {"source": "exa_error"}})

        official_hits: list[dict[str, Any]] = []
        if ev.get("source_type") != "official":
            q = f'"{ev.get("uni", "")}" "{ev.get("event_name", "")}" 2027'
            try:
                sresp = exa_client.exa_post(
                    exa_client.EXA_SEARCH_URL,
                    {"query": q, "numResults": 3, "type": "auto", "contents": {"text": {"maxCharacters": 2500}}},
                    preferred_key=args.key,
                    use_cache=not args.no_cache,
                )
                total_cost += _cost(sresp)
                for item in sresp.get("results", []):
                    official_hits.append(
                        {
                            "url": item.get("url"),
                            "title": item.get("title"),
                            "text": (item.get("text") or "")[:2500],
                        }
                    )
            except RuntimeError as exc:
                official_hits.append({"error": str(exc)})

        evidence.append(
            {
                "id": eid,
                "uni": ev.get("uni"),
                "event_name": ev.get("event_name"),
                "fetched_pages": fetched_pages,
                "official_search_hits": official_hits,
            }
        )

    out_path = CACHE_DIR / f"verify_evidence_{bpath.stem}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "batch": bpath.name,
                "key_slot": args.key,
                "count": len(evidence),
                "cost_dollars": round(total_cost, 4),
                "evidence": evidence,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Důkazy pro ověření ({len(evidence)} akcí, klíč #{args.key}) -> {out_path.name} (cena ~${total_cost:.4f})")
    return 0


def cmd_verify_all(args: argparse.Namespace) -> int:
    bdir = REPO_ROOT / "data" / "verify_batches"
    batches = sorted(bdir.glob("batch_*.json"))
    if not batches:
        print(f"V {bdir} nejsou žádné dávky batch_*.json.", file=sys.stderr)
        return 1
    key_ring = [4, 5, 4, 5, 1, 2, 3]
    for i, bpath in enumerate(batches):
        sub_args = argparse.Namespace(
            batch=str(bpath),
            key=key_ring[i % len(key_ring)],
            max_chars=args.max_chars,
            no_cache=args.no_cache,
        )
        cmd_verify(sub_args)
    return 0


def cmd_enrich(args: argparse.Namespace) -> int:
    in_path = Path(args.file)
    if not in_path.is_file():
        print(f"Soubor neexistuje: {in_path}", file=sys.stderr)
        return 1

    data = json.loads(in_path.read_text(encoding="utf-8"))
    events = data.get("events", []) if isinstance(data, dict) else data
    targets = [
        ev
        for ev in events
        if (ev.get("source_type") != "official" or not ev.get("deadline") or not ev.get("end"))
        and (ev.get("verify") or {}).get("status") != "ověřeno"
    ][: args.limit]

    results: list[dict[str, Any]] = []
    total_cost = 0.0
    for ev in targets:
        q = f'"{ev.get("uni", "")}" "{ev.get("event_name", "")}" 2027 deadline registration'
        try:
            sresp = exa_client.exa_post(
                exa_client.EXA_SEARCH_URL,
                {"query": q, "numResults": 3, "type": "auto", "contents": {"text": {"maxCharacters": 2500}}},
                preferred_key=args.key,
                use_cache=not args.no_cache,
            )
            total_cost += _cost(sresp)
            hits = [
                {"url": i.get("url"), "title": i.get("title"), "text": (i.get("text") or "")[:2500]}
                for i in sresp.get("results", [])
            ]
        except RuntimeError as exc:
            hits = [{"error": str(exc)}]
        results.append({"id": ev.get("id"), "uni": ev.get("uni"), "hits": hits})

    out_path = CACHE_DIR / "enrich_evidence.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "key_slot": args.key,
                "count": len(results),
                "cost_dollars": round(total_cost, 4),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Doplňovací dotazy ({len(results)} akcí, klíč #{args.key}) -> {out_path.name} (cena ~${total_cost:.4f})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Dávkový sběr a ověřovací fetch přes 5 Exa klíčů.")
    sub = p.add_subparsers(dest="cmd", required=True)

    cl = sub.add_parser("collect", help="Stáhne vyhledávání pro Agenty 1–3 přes klíče #1, #2, #3.")
    cl.add_argument("--mode", default="pilot", choices=["pilot", "full", "gaps", "wave_a", "wave_bc"], help="pilot / full / gaps / wave_a / wave_bc.")
    cl.add_argument("--max-chars", type=int, default=4500, help="Max znaků textu na stránku.")
    cl.add_argument("--no-cache", action="store_true")
    cl.set_defaults(func=cmd_collect)

    vr = sub.add_parser("verify", help="Stáhne živé stránky a oficiální zdroje pro slepou dávku Agenta 4.")
    vr.add_argument("batch", help="Cesta k data/verify_batches/batch_XX.json.")
    vr.add_argument("--key", type=int, default=4, choices=[1, 2, 3, 4, 5])
    vr.add_argument("--max-chars", type=int, default=6000)
    vr.add_argument("--no-cache", action="store_true")
    vr.set_defaults(func=cmd_verify)

    va = sub.add_parser("verify-all", help="Stáhne důkazy pro všechny dávky batch_*.json najednou.")
    va.add_argument("--max-chars", type=int, default=6000)
    va.add_argument("--no-cache", action="store_true")
    va.set_defaults(func=cmd_verify_all)

    en = sub.add_parser("enrich", help="Dohledá chybějící oficiální údaje pro Agenta 5 přes klíč #5.")
    en.add_argument("file", help="Cesta k data/curated.json.")
    en.add_argument("--key", type=int, default=5, choices=[1, 2, 3, 4, 5])
    en.add_argument("--limit", type=int, default=3)
    en.add_argument("--no-cache", action="store_true")
    en.set_defaults(func=cmd_enrich)

    return p


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
