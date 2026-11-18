# WeekScout – Erasmus International Weeks 2027

Interaktivní mapa a časová osa Erasmus+ International Weeks, Staff Weeks, Teaching Weeks a BIP (Blended Intensive Programmes) na evropských vysokých školách v akademickém roce **2026/2027** (projekt týmu 17).

- **Aktuální rozsah dat (k 2026-11-18):** **153 akcí** ze **107 institucí** ve **26 zemích** (`105 ověřeno`, `43 částečně`, `5 neověřeno`), termíny **2026-12-01 až 2027-08-31**.
- **Web bez build procesu (GitHub Pages):** čistý HTML/CSS/vanilla JS v `index.html` + `data.json` (Leaflet 1.9.4 + leaflet.markercluster 1.5.3 z CDN).

## Funkce aplikace
- **Nekonečná interaktivní mapa:** podklady *Tmavá* (výchozí), *Mapa* (OSM), *Světlá* a *Satelit* (Esri), obousměrně propojené se světlým/tmavým režimem UI (`☀/☾`).
- **Chytré štítky a výběr termínů:** štítky s názvem univerzity a datem s automatickou detekcí kolizí a výběrové okno pro překrývající se akce na jedné univerzitě.
- **Filtry a vyhledávání:** typ mobility (*Chci učit / Chci se školit / Chci studovat*), fulltextové vyhledávání bez diakritiky, obor, země, poplatek, uzávěrky, měsíc konání, jen plně ověřené, rychlé skrytí prošlých uzávěrek a sbalitelná karta filtrů.
- **Seznam, detail a časová osa:** řazení seznamu (podle termínu / nejbližší uzávěrky / ceny), detail akce se zdroji a sdílitelným odkazem (`?akce=<id>`), přepínatelná obrazovka časové osy (`#casova-osa`) s minimapou.

## 5-agentní architektura sběru a ověřování dat

Pipeline běží nezávisle na webu v `pipeline/` a `agents/` (čistý Python 3 bez externích knihoven, 5 Exa.ai API klíčů týmu v lokálním `.env` s automatickou rotací při 402/429 a lokální diskovou cache):

```text
  [Agent 1: Portály & BIP]  (klíč #1) ─┐
  [Agent 2: Sever & Západ]  (klíč #2) ─┼─▶ data/raw/*.json ─▶ merge_validate.py ─▶ data/candidates.json
  [Agent 3: Jih & Východ]   (klíč #3) ─┘       (deduplikace, filtr dat 2026/27, blacklist komerčních firem)
                                                                      │
                                                                      ▼ (slepé dávky bez historie sběru)
                                                        [Agent 4: Nezávislý ověřovatel] (klíč #4)
                                                                      │ data/verified/batch_*.json
                                                                      ▼
                                                        [Agent 5: Kurátor & Publikátor] (klíč #5)
                                                                      │ validace schématu (0 chyb)
                                                                      ▼
                                                                  data.json
```

Podrobný návod ke spuštění celé pipeline je v [agents/README.md](agents/README.md).

### Napojení na cyklus Competitive Intelligence (CI)

| Fáze CI cyklu | Realizace ve WeekScout |
|---|---|
| **1. Plánování (KIT & KIQ)** | Vymezení rozsahu (vysoké školy EU/EHP + RS, MK, TR; sezóna 2026/27; 3 typy mobility; vyřazení komerčních firem). |
| **2. Sběr (Collection)** | **Agenti 1–3** (portály IMOTION/BIP aliance, sever/západ Evropy, jih/střed-východ Evropy) přes Exa.ai API s diskovou cache. |
| **3. Zpracování & Ověření** | **Agent 4** kontroluje slepé dávky bez historie sběru proti oficiálním webům škol a odhaluje rozpory i komerční agentury. |
| **4. Analýza & Kurátorství** | **Agent 5** (`merge_validate.py`) deduplikuje, sjednocuje názvy 107 škol a validuje JSON schéma (0 chyb). |
| **5. Diseminace & Rozhodování** | Veřejná mapa a časová osa pro účastníky + **B2B Campus portál (`uni.html`)** s manažerským **CI benchmarkem** (sezónní přetlak, kolize termínů ±4 dny, cenový medián Evropy), CSV exporty a pondělním digestem. |

### Bezpečnost
- Žádné API klíče nejsou v repozitáři ani v klientském JavaScriptu (klíče Exa.ai běží výhradně lokálně v Python pipeline přes ignorovaný soubor `.env`, vzor je v `.env.example`).
- Každá akce obsahuje přímé odkazy na zdroje (`source_urls`) a stav/datum ověření (`verify`).

## Struktura repozitáře
- `index.html` – hlavní statická webová aplikace pro účastníky (mapa, filtry, seznam, časová osa, detail, modal *O projektu*)
- `uni.html` – WeekScout Campus B2B portál pro univerzity (správa akcí, Scout Credits, předplatné, CI benchmark, white-label embed, CSV export, týdenní digest)
- `logo.svg` – sjednocené vektorové logo WeekScout
- `data.json` – ověřená data akcí načítaná webem
- `pipeline/` – `exa_client.py` (Exa API + rotace klíčů + cache + HTTP fallback), `batch_fetch.py`, `merge_validate.py`
- `agents/` – specifikace všech 5 agentů (`01_portals.md` až `05_curator.md`)
- `data/` – surové sběry (`raw/`), sloučení kandidáti (`candidates.json`), nezávislé reporty (`verified/`), finální výstup (`curated.json`)

## Lokální spuštění
`data.json` se načítá přes `fetch`, proto web otevřete přes lokální HTTP server v kořeni repozitáře:

```bash
python -m http.server 8080 --bind 127.0.0.1
# otevřít http://127.0.0.1:8080/  (časová osa: http://127.0.0.1:8080/#casova-osa)
```

## Zdroje a licence podkladů
Data pocházejí z oficiálních stránek vysokých škol, databáze IMOTION (`staffmobility.eu`) a přehledů partnerských univerzit/aliancí (Una Europa, SEA-EU aj.). Komerční školicí agentury jsou vyřazovány. Ke každé akci je v detailu uveden zdroj a stav ověření — před přihlášením si uzávěrku vždy ověřte u pořadatele.

Mapové podklady: © OpenStreetMap contributors, Esri World Imagery, Esri Light/Dark Gray Canvas.
