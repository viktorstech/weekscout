# WeekScout – Erasmus International Weeks 2027

[![Status: Production](https://img.shields.io/badge/Status-Live%20on%20GitHub%20Pages-success)](https://viktorstech.github.io/weekscout/)
[![Data: 153 Events](https://img.shields.io/badge/Data-153%20akc%C3%AD%20%2F%20107%20univerzit-blue)](https://viktorstech.github.io/weekscout/)
[![Security Policy](https://img.shields.io/badge/Security-SECURITY.md-green)](SECURITY.md)
[![License: Academic](https://img.shields.io/badge/Course-4IT529%20Competitive%20Intelligence-orange)](https://github.com/viktorstech/weekscout)

Interaktivní Competitive Intelligence platforma a multiagentní systém mapující Erasmus+ International Weeks, Staff Weeks, Teaching Weeks a BIP (Blended Intensive Programmes) na evropských vysokých školách v akademickém roce **2026/2027**.

- **Předmět:** 4IT529 Competitive Intelligence (FIS VŠE v Praze, ZS 2026/2027)
- **Tým 17:** Viktor Štěch, Jiří Matějka, Jiří Jáchym, Jan Rehanzl, Barbora Beňová
- **Živá produkce (GitHub Pages):**
  - 🌍 **B2C klientská aplikace pro účastníky:** [viktorstech.github.io/weekscout/](https://viktorstech.github.io/weekscout/)
  - 🏛️ **B2B manažerský portál WeekScout Campus:** [viktorstech.github.io/weekscout/uni.html](https://viktorstech.github.io/weekscout/uni.html)
  - 📊 **Interaktivní prezentace projektu (16:9 pitch deck):** [viktorstech.github.io/weekscout/prezentace.html](https://viktorstech.github.io/weekscout/prezentace.html)

---

## 1. Rozsah dat a ověření (k 2026-11-19)

- **153 reálně ověřených akcí** ze **107 institucí** ve **26 evropských zemích**.
- **Stav ověření:** 105 plně ověřeno, 43 částečně, 5 v šetření.
- **Časový rámec:** 1. prosince 2026 až 31. srpna 2027.
- **Komerční integrita:** Komerční školicí agentury (Europass Teacher Academy, EBMX, EIAPD, ShipCon apod.) jsou striktně vyřazeny. Databáze obsahuje výhradně akreditované evropské vysokoškolské instituce.

---

## 2. Dvě propojené vrstvy aplikace

### A. Klientská vrstva pro účastníky (`index.html`)
- **Interaktivní mapa (Leaflet 1.9.4 + MarkerCluster):** 4 mapové vrstvy (*Tmavá*, *Mapa OSM*, *Světlá*, *Satelit Esri*) s automatickou dekonflikcí popisků a shlukováním.
- **Chytré persony:** Přepínání filtrů jedním kliknutím (*Chci učit* / *Chci se školit* / *Chci studovat*).
- **Vyhledávání a filtry:** Fulltextové vyhledávání odolné vůči diakritice a překlepům, filtrace podle oboru, země, poplatku (včetně filtru *Pouze zdarma*), termínů a uzávěrek.
- **9měsíční Ganttova časová osa (`#casova-osa`):** Sezónní přehled s panoramatickou minimapou a přímým proklikem na detail akce.
- **Detail a sdílení:** Přímé odkazy na oficiální weby a formuláře pořadatele, sdílitelné URL (`?akce=<id>`).

### B. Manažerská vrstva WeekScout Campus pro univerzity (`uni.html`)
- **Analýza termínových kolizí:** Detekce kolizí v okně ±4 dny se stejným oborovým či geografickým zaměřením v reálném čase.
- **Celoroční křivka vytíženosti:** Sezónní analýza přetlaku (např. dubnová špička 38 akcí vs. prázdninové minimum 7 akcí).
- **Evropský cenový benchmark:** Přehled cenové hladiny (42 % akcí zdarma, medián placených akcí 350 €).
- **Scout Credits & SaaS model:** Kreditní mechanismus pro zvýraznění univerzitních akcí na mapě a v e-mailových digestech.
- **White-label embed kód:** Generování responzivního `<iframe>` kódu pro okamžité vložení filtrované mapy partnerských mobilit do webu fakult a OZS.
- **Týdenní e-mailový digest & CSV export:** Automatizovaný reporting pro zahraniční oddělení.

---

## 3. Pětiagentní architektura v CI cyklu

Pipeline funguje jako 5-fázový multiagentní systém (čistý Python 3 standard library bez externích knihoven, multi-key rotace Exa.ai API, lokální disková cache a striktní *Fail Closed* schéma):

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
                                                                      │ validace schématu (0 chyb, 0 varování)
                                                                      ▼
                                                                  data.json
```

### Mapování na cyklus Competitive Intelligence (CI)

| Fáze CI cyklu | Role agenta / skriptu | Realizace ve WeekScout |
|---|---|---|
| **1. Plánování (KIT & KIQ)** | **Agent 1** (Architekt zadání) | Definice klíčových zpravodajských témat (KIT), geografický rozsah (EU/EHP + RS, MK, TR), typologie mobilit a vyloučení komerčních zprostředkovatelů. |
| **2. Sběr (Collection)** | **Agenti 1, 2 a 3** (Průzkumníci) | Cílený sběr z IMOTION (`staffmobility.eu`), univerzitních aliancí (Una Europa, SEA-EU, 4EU+) a webů VŠ přes Exa.ai s automatickou rotací klíčů. |
| **3. Zpracování & Ověření** | **Agent 4** (Nezávislý ověřovatel) | Nezávislá křížová kontrola slepých dávek proti primárním webům institucí, odhalování zastaralých termínů a skrytých poplatků. |
| **4. Analýza & Syntéza** | **Agent 5** (`merge_validate.py`) | Deduplikace a sjednocení 107 univerzitních entit, kalkulace termínových kolizí (±4 dny), cenový a sezónní benchmark. |
| **5. Diseminace** | **Web & Campus portál** | Distribuce výstupů koncovým uživatelům (B2C mapa a Gantt) a vysokoškolskému managementu (B2B Campus, embed kód, e-mailový digest). |

Podrobný průvodce spuštěním pipeline a specifikace agentů jsou v [agents/README.md](agents/README.md).

---

## 4. Bezpečnost a ochrana dat

Bezpečnostní architektura projektu vychází ze zásad bezpečného vývoje s AI (*Secure Vibe Coding*) a doporučení OWASP:

- **Bezpečnostní politika a kontakty:** Podrobnosti viz **[SECURITY.md](SECURITY.md)**. Hlášení zranitelností přijímají autoři na `matj36@vse.cz` a `stev29@vse.cz`.
- **Ochrana tajemství:** Žádné privátní API klíče nejsou součástí repozitáře ani klientského kódu (API klíče fungují výhradně v lokálním `.env`, k dispozici je vzor `.env.example`).
- **Nulové externí runtime závislosti:** Skripty v `pipeline/` využívají pouze standardní knihovnu Python 3 (`urllib`, `json`, `datetime`, `re`), což eliminuje riziko podvržených balíčků (*slopsquatting*) a kompromitovaných závislostí.
- **Bezpečnostní HTTP hlavičky:** Klientské stránky obsahují ochranné meta tagy:
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), camera=(), microphone=()`
- **GDPR a soukromí:** Aplikace neukládá osobní údaje uživatelů, nevyužívá sledovací cookies a pracuje výhradně s veřejnými institucionálními kontakty zahraničních oddělení.
- **Obrana proti Prompt Injection:** Sběrní i verifikační agenti striktně oddělují data od instrukcí a nemají přímý přístup k produkčnímu nasazení bez deterministické validace (*Fail Closed*).

---

## 5. Struktura repozitáře

```text
weekscout/
├── index.html              # Hlavní B2C aplikace pro účastníky (mapa, časová osa, detail)
├── uni.html                # B2B portál WeekScout Campus pro univerzity a OZS
├── prezentace.html         # Interaktivní 16:9 prezentace projektu pro obhajobu
├── SECURITY.md             # Bezpečnostní politika a Responsible Disclosure kontakty
├── README.md               # Přehled projektu, architektura a návod
├── data.json               # Validovaná databáze 153 akcí z celé Evropy
├── logo.svg                # Vektorové logo projektu
├── .nojekyll               # Konfigurace pro korektní nasazení na GitHub Pages
├── .env.example            # Bezpečná šablona pro konfiguraci API klíčů
├── pipeline/               # Výkonné Python skripty sběrné a validační pipeline
│   ├── exa_client.py       # Klient Exa API s rotací klíčů, cache a retry logikou
│   ├── batch_fetch.py      # Dávkový sběr a paralelní dotazování
│   └── merge_validate.py   # Sloučení, deduplikace a validace databáze
├── agents/                 # Specifikace a promptové šablony 5 agentů
│   ├── README.md           # Návod k obsluze multiagentní pipeline
│   └── 01_portals.md ... 05_curator.md
└── data/                   # Mezikroky sběru dat (raw, candidates, verified, curated)
```

---

## 6. Lokální spuštění a validace

Jelikož se `data.json` načítá přes asynchronní `fetch()`, spusťte v kořenovém adresáři jednoduchý HTTP server:

```bash
# 1. Klonování repozitáře
git clone https://github.com/viktorstech/weekscout.git
cd weekscout

# 2. Spuštění lokálního HTTP serveru
python -m http.server 8080 --bind 127.0.0.1
```

Otevřete ve webovém prohlížeči:
- **B2C Mapa a přehled akcí:** [http://127.0.0.1:8080/](http://127.0.0.1:8080/)
- **Ganttova časová osa:** [http://127.0.0.1:8080/#casova-osa](http://127.0.0.1:8080/#casova-osa)
- **B2B Portál Campus pro univerzity:** [http://127.0.0.1:8080/uni.html](http://127.0.0.1:8080/uni.html)
- **Pitch Deck prezentace:** [http://127.0.0.1:8080/prezentace.html](http://127.0.0.1:8080/prezentace.html)

### Kontrola integrity databáze
```bash
python pipeline/merge_validate.py validate data.json
# Očekávaný výsledek: Chyb: 0 | Varování: 0
```

---

## 7. Zdroje dat a licence

Data pocházejí z oficiálních webů evropských vysokých škol, centrální databáze IMOTION (`staffmobility.eu`) a informačních portálů univerzitních aliancí (Una Europa, SEA-EU, 4EU+ aj.). Každá akce v systému obsahuje přímý odkaz na primární zdroj a datum ověření.

- **Mapové podklady:** © OpenStreetMap contributors, Esri World Imagery, Esri Light/Dark Gray Canvas.
- **Knihovny:** Leaflet (v1.9.4), Leaflet.markercluster (v1.5.3) z CDN.
