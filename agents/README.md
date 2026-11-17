# 5-agentní pipeline – návod ke spuštění (1 PC, 5 Exa klíčů)

Pipeline běží nezávisle na nástroji — stejně dobře v **Google Antigravity** (jako subagenti) i v **Claude Code**. Statický web (`index.html` + `data.json`) nijak neovlivňuje.

## 0. Jednorázové nastavení
1. Zkopíruj `.env.example` jako `.env` v kořeni repozitáře.
2. Do `.env` vlož 5 Exa.ai API klíčů týmu (`EXA_API_KEY_1` až `EXA_API_KEY_5`). Soubor `.env` je v `.gitignore` — **nikdy ho necommituj ani neposílej do chatu**.
3. Ověř, že klíče jsou načtené:
   ```bash
   python pipeline/exa_client.py status
   ```
4. Ověř validátor na stávajících pilotních datech:
   ```bash
   python pipeline/merge_validate.py validate data.json
   ```

## 1. Přehled 5 agentů

| # | Agent | Specifikace | Primární Exa klíč | Výstup |
|---|---|---|---|---|
| 1 | Sběrač: Portály & BIP | `agents/01_portals.md` | `--key 1` | `data/raw/01_portals.json` |
| 2 | Sběrač: Sever & Západ | `agents/02_north_west.md` | `--key 2` | `data/raw/02_north_west.json` |
| 3 | Sběrač: Jih, Střed & Východ | `agents/03_south_east.md` | `--key 3` | `data/raw/03_south_east.json` |
| 4 | Nezávislý ověřovatel | `agents/04_verifier.md` | `--key 4` | `data/verified/batch_XX.json` |
| 5 | Kurátor & Publikátor | `agents/05_curator.md` | `--key 5` | `data/curated.json` → `data.json` |

> Pokud některému klíči dojdou kredity (HTTP 402/429), `pipeline/exa_client.py` automaticky přepne na další volný klíč. Každý dotaz i stažená URL se ukládají do lokální cache `data/cache/`, takže opakovaný běh stojí 0 kreditů.

## 2. Postup spuštění krok za krokem

### Fáze 1 – Sběr kandidátů (TODO #1)
1. Spusť **Agenta 1, 2 a 3** (nejprve pilotně po ~5–10 akcích, pak ostrý běh). Každý agent ukládá průběžně do svého souboru v `data/raw/`.
2. Sluč a deduplikuj výstupy do `data/candidates.json` (0 kreditů):
   ```bash
   python pipeline/merge_validate.py merge --include-pilot
   python pipeline/merge_validate.py validate data/candidates.json --candidates
   ```

### Fáze 2 – Nezávislé ověření (TODO #2)
3. Rozděl `data/candidates.json` na slepé dávky po 20 akcích:
   ```bash
   python pipeline/merge_validate.py batches --size 20
   ```
4. Pro každou dávku `data/verify_batches/batch_XX.json` spusť **Agenta 4** v **čistém kontextu** (bez historie sběru). Výsledek ukládá do `data/verified/batch_XX.json`.

### Fáze 3 – Kurátorství a publikace
5. Spusť **Agenta 5**, který aplikuje opravy z `data/verified/`, doplní chybějící povinná pole a zvaliduje výsledek:
   ```bash
   python pipeline/merge_validate.py apply --out data/curated.json
   python pipeline/merge_validate.py validate data/curated.json
   ```
6. Teprve po kontrole a souhlasu vlastníka repa (`viktorstech`) nahraď `data.json` a přenes změny do větve `main`.
