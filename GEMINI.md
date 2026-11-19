# GEMINI.md – WeekScout: Erasmus International Weeks 2027

Kontext pro vývoj a práci v Google Antigravity. Repozitář: `viktorstech/weekscout`.
Web: https://viktorstech.github.io/weekscout/ · Stav k 2026-11-19 (Tým 17, 4IT529).

## 1. Cíl projektu, tým a stav k 19. 11. 2026

- **Předmět:** 4IT529 Competitive Intelligence (FIS VŠE v Praze, ZS 2026/27).
- **Tým 17:** Viktor Štěch, Jiří Matějka, Jiří Jáchym, Jan Rehanzl, Barbora Beňová.
- **Projekt WeekScout:** Multiagentní systém a Competitive Intelligence platforma mapující Erasmus+ International Weeks, Staff Weeks, Teaching Weeks a BIP (Blended Intensive Programmes) na evropských vysokých školách v akademickém roce 2026/2027.
- **Rozsah dat:** **153 reálně ověřených akcí** ze **107 institucí** ve **26 evropských zemích** (105 ověřeno, 43 částečně, 5 neověřeno). Termíny 2026-12-01 až 2027-08-31. Komerční školicí agentury (Europass, EBMX, EIAPD apod.) jsou striktně vyřazeny.
- **Dvě propojené vrstvy:**
  1. **B2C klientská vrstva pro účastníky (`index.html`):** Interaktivní mapa Leaflet se shlukováním a dekonflikcí popisků, 9měsíční Ganttova časová osa (`#casova-osa`) s panoramatickou minimapou, vyhledávání bez diakritiky, persony (*Chci učit / Chci se školit / Chci studovat*), filtrace podle ceny a uzávěrek.
  2. **B2B manažerská vrstva pro univerzity (`uni.html`):** Portál WeekScout Campus pro zahraniční oddělení (OZS). Competitive Intelligence analýza termínových kolizí (okno ±4 dny), celoroční křivka vytíženosti (špička duben 38 akcí vs. červenec 7 akcí), cenový benchmark (42 % akcí zdarma, medián 350 €), Scout Credits pro zvýraznění akcí, white-label embed kód pro fakulty a pondělní e-mailový digest.
  3. **Prezentace projektu (`prezentace.html`):** Interaktivní 8slajdový pitch deck v poměru 16:9 pro 10minutovou obhajobu s klávesovou navigací a živými prokliky na demo.

## 2. Architektura a pravidla kódu

- **Statický web bez build procesu (GitHub Pages):**
  - `index.html` – hlavní B2C aplikace (HTML/CSS/JS inline, Leaflet 1.9.4, leaflet.markercluster 1.5.3 z CDN).
  - `uni.html` – B2B portál Campus (statický, responzivní, modal kolizí `#col-mdl`).
  - `prezentace.html` – interaktivní prezentace bez interních časových popisků, optimalizovaná pro 16:9 a tisk do PDF.
  - `data.json` – validovaná databáze 153 akcí (validace: `pipeline/merge_validate.py validate data.json` -> 0 chyb, 0 varování).
  - `.nojekyll` – pro správné fungování GitHub Pages.
- **Multiagentní pipeline (5 agentů v 5 fázích CI cyklu):**
  - **Fáze 1 (Plánování):** Agent 1 – Architekt zadání (`agents/01_portals.md`).
  - **Fáze 2 (Sběr):** Agent 2 & 3 – Průzkumníci portálů a regionů (Exa.ai API, IMOTION, weby VŠ).
  - **Fáze 3 (Verifikace):** Agent 4 – Nezávislý ověřovatel (kontrola oficiálních webů a kontaktů).
  - **Fáze 4 (Analýza):** Deduplikace na 107 kanonických univerzit, detekce kolizí ±4 dny, cenový benchmark.
  - **Fáze 5 (Diseminace):** Agent 5 – Kurátor & Publikátor (`pipeline/merge_validate.py`).
- **Bezpečnost:** Žádné privátní API klíče v repozitáři ani v klientském kódu.

## 3. Odevzdané materiály a obhajoba (19. 11. 2026)

- **Odevzdáno do Moodle (do 9:00):**
  - Závěrečný report (PDF, cca 6,5 NS, do limitu 8 NS).
  - Prezentace (PDF, 8 slajdů 16:9).
  - Odkazy na funkční web B2C, B2B Campus a repozitář na GitHubu.
- **10minutový scénář prezentace:**
  - **Viktor Štěch (0:00 – 4:30):** B2C příběh učitele/studenta, problém roztříštěnosti, živá mapa, persony, časová osa.
  - **Jiří Matějka (4:30 – 8:30):** B2B manažerský pohled OZS, portál Campus, kolize termínů ±4 dny, sezónní graf, cenový benchmark, Scout Credits a SaaS model.
  - **Závěr (8:30 – 9:20):** 5 agentů v CI cyklu, rozdělení týmu, poděkování a otázky (cíl skončit před 10minutovým limitem).
- **Role Báry a slovenština:** V kapitolách 7 a 8 je otevřeně deklarováno, že Barbora Beňová psala podklady a koncepty v rodné slovenštině a AI byla využita k překladu a stylistickému sjednocení do akademické češtiny.
- **Argument ke 153 akcím vs 4000 škol:** Z 4000+ institucí s chartou Erasmus dělá většina jen běžné semestrální výjezdy. International Week vyžaduje velké zázemí a v celé Evropě ho ročně pořádá cca 250–300 škol. 153 akcí v listopadu pokrývá většinu včas vypsaného evropského trhu.

## 4. Lokální spuštění na jakémkoliv počítači

```bash
git clone https://github.com/viktorstech/weekscout.git
cd weekscout
python -m http.server 8080 --bind 127.0.0.1
# Otevřít v prohlížeči:
# Prezentace: http://127.0.0.1:8080/prezentace.html
# B2C Mapa:   http://127.0.0.1:8080/
# B2B Campus: http://127.0.0.1:8080/uni.html
```
