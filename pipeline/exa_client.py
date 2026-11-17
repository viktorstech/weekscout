#!/usr/bin/env python3
"""Jednotný klient pro Exa.ai API s rotací 5 klíčů, diskovou cache a HTTP fallbackem.

Používá jen standardní knihovnu Pythonu 3 (žádné pip závislosti).
Klíče čte z lokálního souboru .env (EXA_API_KEY_1 až EXA_API_KEY_5).

Příklady:
  python pipeline/exa_client.py status
  python pipeline/exa_client.py search "Erasmus International Staff Week 2027" --key 1 --num 10 --text
  python pipeline/exa_client.py contents https://www.hamk.fi/... --key 4
  python pipeline/exa_client.py fetch https://www.hamk.fi/...
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
CACHE_DIR = REPO_ROOT / "data" / "cache"

EXA_SEARCH_URL = "https://api.exa.ai/search"
EXA_CONTENTS_URL = "https://api.exa.ai/contents"

ROTATE_STATUSES = {401, 402, 403, 429}
EXHAUSTED_STATUSES = {401, 402, 403}
RETRY_STATUSES = {500, 502, 503, 504}
_EXHAUSTED_SLOTS: set[int] = set()


class _HTMLTextExtractor(HTMLParser):
    """Jednoduchý parser HTML -> čistý text bez script/style bloků."""

    SKIP_TAGS = {"script", "style", "noscript", "svg", "iframe"}

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth += 1
        elif tag.lower() in {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def get_text(self) -> str:
        raw = "".join(self._chunks)
        lines = [re.sub(r"\s+", " ", ln).strip() for ln in raw.splitlines()]
        return "\n".join(ln for ln in lines if ln)


def load_dotenv(path: Path = ENV_PATH) -> dict[str, str]:
    """Načte KEY=VALUE páry ze souboru .env (pokud existuje)."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and v:
            values[k] = v
    return values


def get_api_keys() -> dict[int, str]:
    """Vrátí slovník {1..5: key} z proměnných prostředí a .env."""
    env_file = load_dotenv()
    keys: dict[int, str] = {}
    for i in range(1, 6):
        name = f"EXA_API_KEY_{i}"
        val = os.environ.get(name) or env_file.get(name)
        if val:
            keys[i] = val.strip()
    if not keys:
        fallback = os.environ.get("EXA_API_KEY") or env_file.get("EXA_API_KEY")
        if fallback:
            keys[1] = fallback.strip()
    return keys


def _ordered_key_slots(keys: dict[int, str], preferred: int) -> list[tuple[int, str]]:
    """Seřadí dostupné klíče tak, aby se začalo preferovaným a pak rotovalo (přeskakuje vyčerpané)."""
    slots = [s for s in sorted(keys.keys()) if s not in _EXHAUSTED_SLOTS]
    if not slots:
        slots = sorted(keys.keys())
    if preferred in slots:
        idx = slots.index(preferred)
        slots = slots[idx:] + slots[:idx]
    return [(s, keys[s]) for s in slots]


def _cache_path(kind: str, payload: dict[str, Any]) -> Path:
    canonical = json.dumps({"kind": kind, "payload": payload}, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return CACHE_DIR / f"{kind}_{digest}.json"


def _read_cache(path: Path) -> Any | None:
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def _write_cache(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def exa_post(
    endpoint: str,
    payload: dict[str, Any],
    preferred_key: int = 1,
    use_cache: bool = True,
    max_retries: int = 2,
    timeout: int = 30,
) -> dict[str, Any]:
    """Zavolá Exa API s diskovou cache, retry při 5xx a automatickou rotací klíčů."""
    kind = "search" if endpoint.endswith("/search") else "contents"
    cpath = _cache_path(kind, payload)
    if use_cache:
        cached = _read_cache(cpath)
        if cached is not None:
            print(f"[cache hit] {cpath.name}", file=sys.stderr)
            return cached

    keys = get_api_keys()
    if not keys:
        raise RuntimeError(
            "Nenalezen žádný EXA_API_KEY_1..5. Zkopíruj .env.example na .env a doplň klíče."
        )

    body = json.dumps(payload).encode("utf-8")
    last_error: str = "Neznámá chyba"

    for slot, api_key in _ordered_key_slots(keys, preferred_key):
        for attempt in range(max_retries + 1):
            req = urllib.request.Request(
                endpoint,
                data=body,
                method="POST",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "erasmus-iw-pipeline/1.0",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                    data = json.loads(raw)
                    data["_meta"] = {"source": "exa", "key_slot": slot}
                    if use_cache:
                        _write_cache(cpath, data)
                    print(f"[exa ok] {kind} přes klíč #{slot}", file=sys.stderr)
                    return data
            except urllib.error.HTTPError as exc:
                code = exc.code
                detail = exc.read().decode("utf-8", errors="replace")[:300]
                last_error = f"HTTP {code} (klíč #{slot}): {detail}"
                if code in ROTATE_STATUSES:
                    if code in EXHAUSTED_STATUSES:
                        _EXHAUSTED_SLOTS.add(slot)
                    print(
                        f"[rotace klíče] klíč #{slot} vrátil HTTP {code}, zkouším další klíč...",
                        file=sys.stderr,
                    )
                    break  # přejdi na další klíč
                if code in RETRY_STATUSES and attempt < max_retries:
                    wait = 2 ** (attempt + 1)
                    print(
                        f"[exa {code}] pokus {attempt + 1}/{max_retries + 1}, čekám {wait}s...",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                    continue
                if code in RETRY_STATUSES:
                    break  # po retry zkus další klíč nebo fallback
                raise RuntimeError(last_error) from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = f"Síťová chyba (klíč #{slot}): {exc}"
                if attempt < max_retries:
                    time.sleep(2 ** (attempt + 1))
                    continue
                break

    raise RuntimeError(f"Exa API selhalo na všech dostupných klíčích: {last_error}")


def direct_fetch(url: str, max_chars: int = 12000, use_cache: bool = True, timeout: int = 20) -> dict[str, Any]:
    """Přímý HTTP fetch stránky bez spotřeby Exa kreditů (s diskovou cache)."""
    cpath = _cache_path("fetch", {"url": url, "max_chars": max_chars})
    if use_cache:
        cached = _read_cache(cpath)
        if cached is not None:
            print(f"[cache hit] {cpath.name}", file=sys.stderr)
            return cached

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,cs;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = resp.headers.get("Content-Type", "")
            final_url = resp.geturl()
            raw_bytes = resp.read(2_000_000)
            if "pdf" in ctype.lower() or final_url.lower().endswith(".pdf"):
                result = {
                    "url": final_url,
                    "status": resp.status,
                    "content_type": ctype,
                    "text": "",
                    "note": "PDF dokument – pro extrakci textu použij Exa contents nebo PDF reader.",
                    "_meta": {"source": "direct_http"},
                }
            else:
                text_raw = raw_bytes.decode("utf-8", errors="replace")
                parser = _HTMLTextExtractor()
                parser.feed(text_raw)
                clean = parser.get_text()[:max_chars]
                result = {
                    "url": final_url,
                    "status": resp.status,
                    "content_type": ctype,
                    "text": clean,
                    "_meta": {"source": "direct_http"},
                }
            if use_cache:
                _write_cache(cpath, result)
            print(f"[http ok] {final_url} ({len(result['text'])} znaků)", file=sys.stderr)
            return result
    except Exception as exc:  # noqa: BLE001
        return {
            "url": url,
            "status": None,
            "error": str(exc),
            "text": "",
            "_meta": {"source": "direct_http"},
        }


def cmd_status(_args: argparse.Namespace) -> int:
    keys = get_api_keys()
    cache_count = len(list(CACHE_DIR.glob("*.json"))) if CACHE_DIR.is_dir() else 0
    print("Stav konfigurace Exa API (.env):")
    for i in range(1, 6):
        state = "nastaveno" if i in keys else "chybí"
        print(f"  EXA_API_KEY_{i}: {state}")
    print(f"Dostupných klíčů celkem: {len(keys)}/5")
    print(f"Položek v lokální cache ({CACHE_DIR.relative_to(REPO_ROOT)}): {cache_count}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "query": args.query,
        "numResults": args.num,
        "type": args.type,
    }
    if args.domains:
        payload["includeDomains"] = [d.strip() for d in args.domains.split(",") if d.strip()]
    if args.exclude_domains:
        payload["excludeDomains"] = [d.strip() for d in args.exclude_domains.split(",") if d.strip()]
    if args.start_published:
        payload["startPublishedDate"] = args.start_published
    if args.text:
        payload["contents"] = {"text": {"maxCharacters": args.max_chars}}

    data = exa_post(
        EXA_SEARCH_URL,
        payload,
        preferred_key=args.key,
        use_cache=not args.no_cache,
    )
    _emit(data, args.out)
    return 0


def cmd_contents(args: argparse.Namespace) -> int:
    payload = {
        "urls": args.urls,
        "text": {"maxCharacters": args.max_chars},
    }
    try:
        data = exa_post(
            EXA_CONTENTS_URL,
            payload,
            preferred_key=args.key,
            use_cache=not args.no_cache,
        )
    except RuntimeError as exc:
        if not args.no_fallback:
            print(f"[fallback] Exa contents selhalo ({exc}), zkouším přímý HTTP fetch...", file=sys.stderr)
            results = [
                direct_fetch(u, max_chars=args.max_chars, use_cache=not args.no_cache)
                for u in args.urls
            ]
            data = {"results": results, "_meta": {"source": "direct_http_fallback"}}
        else:
            raise
    _emit(data, args.out)
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    data = direct_fetch(args.url, max_chars=args.max_chars, use_cache=not args.no_cache)
    _emit(data, args.out)
    return 0


def _emit(data: Any, out_path: str | None) -> None:
    rendered = json.dumps(data, ensure_ascii=False, indent=2)
    if out_path:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rendered, encoding="utf-8")
        print(f"[uloženo] {p}", file=sys.stderr)
    else:
        print(rendered)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Exa.ai API klient s rotací 5 klíčů a lokální cache.")
    sub = p.add_subparsers(dest="cmd", required=True)

    st = sub.add_parser("status", help="Zkontroluje nastavené klíče v .env a velikost cache.")
    st.set_defaults(func=cmd_status)

    sr = sub.add_parser("search", help="Vyhledávání přes Exa /search.")
    sr.add_argument("query", help="Vyhledávací dotaz.")
    sr.add_argument("--key", type=int, default=1, choices=[1, 2, 3, 4, 5], help="Preferovaný klíč (1-5).")
    sr.add_argument("--num", type=int, default=10, help="Počet výsledků (výchozí 10).")
    sr.add_argument("--type", default="auto", choices=["auto", "neural", "keyword"], help="Typ hledání.")
    sr.add_argument("--domains", help="Povolené domény oddělené čárkou (např. staffmobility.eu).")
    sr.add_argument("--exclude-domains", help="Vyloučené domény oddělené čárkou.")
    sr.add_argument("--start-published", help="Od data publikace YYYY-MM-DD (např. 2026-01-01).")
    sr.add_argument("--text", action="store_true", help="Rovnou stáhnout i text stránek.")
    sr.add_argument("--max-chars", type=int, default=4000, help="Max znaků textu na stránku.")
    sr.add_argument("--no-cache", action="store_true", help="Ignorovat lokální cache.")
    sr.add_argument("--out", help="Uložit JSON výstup do souboru.")
    sr.set_defaults(func=cmd_search)

    ct = sub.add_parser("contents", help="Stažení obsahu konkrétních URL přes Exa /contents (s HTTP fallbackem).")
    ct.add_argument("urls", nargs="+", help="Jedna nebo více URL.")
    ct.add_argument("--key", type=int, default=4, choices=[1, 2, 3, 4, 5], help="Preferovaný klíč (1-5).")
    ct.add_argument("--max-chars", type=int, default=8000, help="Max znaků textu na URL.")
    ct.add_argument("--no-cache", action="store_true", help="Ignorovat lokální cache.")
    ct.add_argument("--no-fallback", action="store_true", help="Zakázat přímý HTTP fallback při výpadku Exa.")
    ct.add_argument("--out", help="Uložit JSON výstup do souboru.")
    ct.set_defaults(func=cmd_contents)

    ft = sub.add_parser("fetch", help="Přímý HTTP fetch bez spotřeby Exa kreditů.")
    ft.add_argument("url", help="URL ke stažení.")
    ft.add_argument("--max-chars", type=int, default=12000, help="Max znaků čistého textu.")
    ft.add_argument("--no-cache", action="store_true", help="Ignorovat lokální cache.")
    ft.add_argument("--out", help="Uložit JSON výstup do souboru.")
    ft.set_defaults(func=cmd_fetch)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except RuntimeError as exc:
        print(f"CHYBA: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
