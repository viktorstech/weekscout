# Sumarizační report pro projekt WeekScout
**Předmět:** 4IT529 Competitive Intelligence (ZS 2026/27)  
**Instituce:** Vysoká škola ekonomická v Praze, Fakulta informatiky a statistiky  
**Autoři:** Viktor Štěch, Jiří Matějka, Jiří Jáchym, Jan Rehanzl, Barbora Beňová  
**Datum odevzdání:** 19. 11. 2026  
**Odkazy na živý prototyp:**  
* Veřejná aplikace pro účastníky: https://viktorstech.github.io/weekscout/  
* B2B portál pro univerzity (OZS): https://viktorstech.github.io/weekscout/uni.html  
* Repozitář na GitHubu: https://github.com/viktorstech/weekscout  

---

## 1 Popis projektu
**WeekScout – Erasmus International Weeks 2027** je multiagentní systém a interaktivní analytická platforma mapující akce programu Erasmus+ (International Weeks, Staff Training Weeks, Teaching Weeks a Blended Intensive Programmes – BIP) na evropských vysokých školách v akademickém roce 2026/2027. K 18. 11. 2026 eviduje databáze **153 reálných akcí ze 107 institucí ve 26 evropských zemích**. Databáze prochází přísnou schématickou validací (0 chyb, 0 varování) a striktně vyřazuje komerční školicí agentury parazitující na grantových rozpočtech.

Projekt řeší dvě klíčové roviny Competitive Intelligence:
1. **B2C rovina (pro účastníky):** Odstraňuje informační asymetrii a nutnost manuálního procházení stovek roztříštěných univerzitních webů. Poskytuje interaktivní mapu s dekonflikcí popisků, 9měsíční dynamickou časovou osu (Ganttův diagram), fulltextové vyhledávání a filtrování podle typu mobility (*Chci učit / Chci se školit / Chci studovat*).
2. **B2B rovina (pro univerzity a zahraniční oddělení – OZS):** Poskytuje manažerský analytický portál **WeekScout Campus**, který pořadatelům umožňuje vyhodnocovat termínovou konkurenci v Evropě (kolize ±4 dny), identifikovat optimální termínová okna mimo celoevropské špičky a porovnávat účastnické poplatky vůči evropskému tržnímu benchmarku.

---

## 2 Key intelligence topics a key intelligence questions
KIT posuzujeme z technického i konkurenčního hlediska. Ke každému patří konkrétní KIQ:

### 2.1 Technické KIT: Data a integrita
Důvěryhodnost aplikace stojí na přesnosti termínů, uzávěrek a ověřených odkazů. Nabídky na rok 2027 se navíc průběžně vyvíjejí.
* **Q:** Jaký podíl z nově nasbíraných akcí obsahuje potvrzený termín přímo na oficiální doméně univerzity?
* **Q:** Jak rychle zachytí agentní pipeline nově vypsané termíny a změny uzávěrek pro akademický rok 2026/2027?
* **Q:** Které geografické oblasti a univerzitní aliance (např. Una Europa, SEA-EU, CIVIS) vykazují nejnižší pokrytí a vyžadují cílený re-scraping?

### 2.2 Technické KIT: Automatizace a multiagentní sběr dat
Pipeline kombinuje vyhledávací AI API (Exa.ai), dedikované HTTP fallbacky a verifikační agenty.
* **Q:** Stačí limit distribuovaných API klíčů pro kontinuální týdenní monitoring bez výpadků sběru?
* **Q:** Jak spolehlivě dokáže verifikační agent detekovat a vyřadit komerční školicí firmy, aniž by omylem zahodil legitimní univerzitní Staff Week?
* **Q:** Dokáže deduplikační agent spolehlivě sjednotit různé jazykové varianty názvů institucí na kanonické entity?

### 2.3 Technické KIT: Uživatelská zkušenost (UX)
Uživatelé (akademici, koordinátoři i studenti) vyžadují okamžitou orientaci na desktopu i mobilních zařízeních.
* **Q:** Jaké filtry a kombinace parametrů uživatelé volí nejčastěji pro nalezení relevantního výjezdu?
* **Q:** Umožňuje zobrazení mapy a časové osy přehledné rozlišení více souběžných akcí téže instituce bez překryvu vizuálních prvků?

### 2.4 Konkurenční KIT: Konkurence a kvalita zdrojů
Sledování přidané hodnoty vůči zastaralým centrálním databázím.
* **Q:** Jaké nové funkce zavádí portál staffmobility.eu a v čem si WeekScout udržuje trvalý náskok?
* **Q:** Jak účinně chráníme účastníky před skrytými poplatky komerčních zprostředkovatelů?

### 2.5 Konkurenční KIT: Pravidla financování a institucionální potřeby
Vývoj dotačních pravidel programu Erasmus+ a tlak na internacionalizaci vysokoškolského vzdělávání.
* **Q:** Jak se mění podíl bezplatných akcí vůči placeným a jak na to reagují rozpočty vysílajících fakult?
* **Q:** Jaké analytické podklady potřebují vedoucí zahraničních oddělení pro strategické načasování vlastních International Weeks?

---

## 3 PESTEL analýza

### 3.1 Politické faktory
* Projekt přímo reflektuje priority Evropské unie v oblasti internacionalizace vysokého školství a mobility pracovníků i studentů.
* Masivní podpora univerzitních aliancí (European Universities Initiatives) vytváří desítky nových společných akcí typu BIP, které však postrádají jednotný celoevropský vyhledávač.

### 3.2 Ekonomické faktory
* Statická serverless architektura na GitHub Pages eliminuje veškeré provozní náklady na hosting a databázové servery.
* Cestovní a grantové rozpočty fakult jsou omezené; transparentní srovnání poplatků (včetně 42% podílu akcí zcela zdarma) šetří veřejné prostředky univerzit.

### 3.3 Sociální faktory
* Rostoucí zájem akademických i administrativních pracovníků o sdílení dobré praxe a jazykový rozvoj.
* Překonání akademického žargonu: namísto matoucích administrativních zkratek (STT, STA, BIP) nabízí systém srozumitelné persony (*Chci učit / Chci se školit / Chci studovat*).

### 3.4 Technologické faktory
* Modulární 5agentní pipeline v Pythonu s validací JSON schématu zaručuje nulovou chybovost databáze.
* Rychlý klientský rendering v čistém JavaScriptu s okamžitou odezvou bez závislostí na těžkých frameworcích a kompilaci.

### 3.5 Environmentální faktory
* Podpora iniciativy *Green Erasmus*: prostorová mapa umožňuje preferovat geograficky dostupné destinace s udržitelnou vlakovou a autobusovou dopravou před leteckou.
* Energeticky nenáročný statický web bez těžkých cloudových backendů snižuje digitální uhlíkovou stopu.

### 3.6 Legislativní faktory
* Přísný soulad s licencemi mapových podkladů (OpenStreetMap, Esri) a ochranou autorských práv.
* Soulad s GDPR: platforma nesbírá osobní údaje běžných účastníků a eviduje výhradně oficiální institucionální kontakty zveřejněné pořadateli akcí.

---

## 4 Porterových pět sil

### 4.1 Rivalita stávajících konkurentů (střední až vysoká)
Trhu dominuje zavedený, avšak technologicky zastaralý portál IMOTION (staffmobility.eu). Jeho slabinou je absence mapy, nemožnost časového plánování, nepřehledný textový výpis a míchání univerzitních akcí s komerčními kurzy. WeekScout konkuruje vizuální analytikou, časovou osou a sjednocením mobilit pro zaměstnance i studenty.

### 4.2 Hrozba vstupu nových konkurentů (nízká až střední)
Vytvořit jednoduchý web dokáže kdokoli, avšak kritickou bariérou vstupu je vytvoření a provoz spolehlivé sběrné a verifikační pipeline, která dokáže z nestrukturovaných webů vytěžit validní metadata a odfiltrovat balast.

### 4.3 Vyjednávací síla dodavatelů (vysoká)
Zdrojem primárních dat jsou weby jednotlivých univerzit a databáze IMOTION. Jakákoli změna struktury stránek či zavedení bot-ochran vyžaduje adaptaci crawlerů. Riziko je zmírněno využitím lokální cache a víceúrovňových HTTP fallbacků.

### 4.4 Vyjednávací síla zákazníků (vysoká)
Účastníci i univerzity mají nulové náklady na přechod (switching costs). Pokud systém neposkytuje aktuální data a přehledné rozhraní, uživatelé se vracejí k neefektivním e-mailovým oběžníkům. Proto je kladen maximální důraz na UX a okamžitou odezvu.

### 4.5 Hrozba substitutů (vysoká)
Hlavním substitutem zůstává neformální komunikace: bilaterální e-maily koordinátorů, osobní vazby vyučujících a interní newslettery. Druhým substitutem jsou komerční školicí agentury, které systém aktivně filtruje.

---

## 5 Analýza konkurence a mezera na trhu

### 5.1 Srovnávací matice

| Řešení | Hlavní funkce | Cena pro uživatele | Cílová skupina | Hlavní slabá místa |
| :--- | :--- | :--- | :--- | :--- |
| **1. IMOTION (staffmobility.eu)** | Textový katalog, formulář pro vkládání | Zdarma | Zaměstnanci VŠ | Bez mapy a časové osy; mísí univerzity a komerční agentury; chybí BIP pro studenty |
| **2. Erasmus+ App (EK)** | Průvodce semestrální mobilitou, OLA | Zdarma | Studenti (dlouhodobé) | Neřeší krátkodobé Staff Weeks ani zaměstnanecké výjezdy |
| **3. Portály aliancí (Una Europa aj.)** | Seznamy kurzů a společných BIP | Zdarma pro členy | Členové aliance | Uzavřené silo, chybí mezialianční srovnání |
| **4. Komerční agentury (Europass aj.)** | Komerční školení a kurzy | 400–800 € / týden | Zaměstnanci VŠ | Nejde o akademickou výměnu; poplatky odčerpávají granty |
| **5. Fakultní oběžníky a PDF tabulky** | Statické e-maily a přehledy | Zdarma | Zaměstnanci fakulty | Zastaralá data, roztříštěnost, absence vyhledávání |
| **WeekScout (náš projekt)** | **Interaktivní mapa, Ganttova osa, B2B portál Campus, CI analýza kolizí a cenový benchmark** | **Zdarma pro účastníky; prémiový B2B model pro VŠ** | **Vyučující, zaměstnanci, studenti (BIP) i vedení OZS** | **Závislost na periodickém ověřování externích webů** |

### 5.2 Mezera na trhu
WeekScout vyplňuje tři zásadní tržní mezery:
1. **Časoprostorová vizualizace:** Odstraňuje nutnost číst stovky odstavců textu – polohu i termínové překryvy uživatel vidí na první pohled.
2. **Jednotné rozhraní pro všechny typy mobilit:** Sjednocuje výuku (STA), školení (STT) i studentské programy (BIP) do jednoho konzistentního schématu.
3. **Manažerská podpora pro pořadatele (Competitive Intelligence):** Žádný existující nástroj neposkytuje univerzitám zpětnou vazbu, zda svůj termín neplánují v přetíženém týdnu nebo zda jejich poplatek není mimo tržní realitu.

---

## 6 Popis prototypu

Prototyp WeekScout byl vyvinut v souladu s principy Competitive Intelligence a sestává ze dvou propojených částí: automatizované víceagentní sběrné pipeline a webového analytického portálu.

### 6.1 Architektura multiagentního systému a provázání s CI cyklem
Sběr, čištění a publikace dat probíhá prostřednictvím modulárního systému 5 autonomních agentů, z nichž každý přímo odpovídá jedné z pěti fází klasického cyklu Competitive Intelligence:

| Fáze CI cyklu | Role agenta v pipeline | Konkrétní činnost a výstupy agenta |
| :--- | :--- | :--- |
| **1. Plánování & Řízení** | **Agent 1 – Architekt zadání** | Definuje parametr sběru (termíny 1. 12. 2026 – 31. 8. 2027), specifikaci cílových zemí (EU-27 + EHP + kandidátské země) a striktní validační schéma (povinná pole, typy mobilit, povolené oborové kódy). |
| **2. Sběr informací** | **Agent 2 – Průzkumník portálů & regionů** | Provádí masivní paralelní extrakci dat z mezinárodního portálu IMOTION (staffmobility.eu), univerzitních aliancí a webových stránek vysokých škol napříč 4 geografickými regiony Evropy. |
| **3. Zpracování & Verifikace** | **Agent 3 – Nezávislý ověřovatel** | Přebírá nalezené kandidáty a nezávisle ověřuje existenci akce na oficiální doméně instituce. Odstraňuje neexistující termíny a komerční agentury. Zajišťuje zachování oficiálních kontaktů na organizátory. |
| **4. Analýza & Syntéza** | **Agent 4 – Deduplikátor & Analytik** | Provádí normalizaci roztříštěných názvů institucí na **107 kanonických univerzit**. Počítá sezónní distribuci termínů, identifikuje časové kolize a sestavuje cenový benchmark. |
| **5. Diseminace výstupů** | **Agent 5 – Kurátor & Publikátor** | Provádí finální schématickou kontrolu (`merge_validate.py validate data.json` – **0 chyb, 0 varování**) a publikuje optimalizovaný datový soubor pro veřejnou mapu i portál Campus. |

### 6.2 Uživatelské rozhraní pro účastníky (B2C vrstva)
Klientská aplikace (`index.html`) funguje jako rychlý statický web bez build procesu a poskytuje:
* **Interaktivní mapu (Leaflet):** Shlukování markerů s automatickou dekonflikcí štítků, zobrazení stavu ověření a barevné odlišení akcí podle měsíce zahájení.
* **Časovou osu (Ganttův diagram):** Plynulé zobrazení 9 měsíců sezóny 2026/27. Zobrazuje délku akce, druhý termín konání, kosočtverec uzávěrky přihlášek i aktuální den. V pravém horním rohu je k dispozici panoramatická minimapa pro zachování kontextu.
* **Chytré vyhledávání a filtry:** Okamžitý fulltext bez nutnosti psát diakritiku, rozcestník typu mobility (*Chci učit / Chci se školit / Chci studovat*), filtrování podle poplatku, země, oboru i stavu uzávěrky (*Skrýt prošlé*).
* **Adaptivní detail akce:** Dialogové okno s kompletními informacemi o programu, kapacitě, kontaktech na koordinátory a inteligentním tlačítkem registrace, které po vypršení uzávěrky automaticky přepíná na archivní režim.
* **Plná podpora tmavého režimu:** Včetně dynamické výměny mapových podkladů (CartoDB Positron / Dark Matter / Esri).

### 6.3 Manažerský portál WeekScout Campus (B2B vrstva)
Pro zahraniční oddělení a pořadatele byl vytvořen dedikovaný manažerský portál (`uni.html`), který převádí nasbíraná data do strategických podkladů pro rozhodování:
1. **Analýza termínových kolizí (okno ±4 dny):** Pořadatel vidí, kolik jiných evropských škol pořádá akci ve stejném týdnu. Kliknutím na *„Zobrazit detail kolizí ↗“* se otevře detailní rozbor s kompletním seznamem soupeřících univerzit, jejich vlajkami, přímou shodou v typu mobility, poplatky a odkazy na jejich weby.
2. **Křivka sezónního vytížení Evropy:** Interaktivní sloupcový graf zobrazující distribuci všech 153 akcí v jednotlivých měsících. Upozorňuje na celoevropskou špičku (duben – 38 akcí) i optimální volná okna pro plánování (červenec – 7 akcí).
3. **Cenový a oborový benchmark:** Srovnání poplatku pořadatele vůči evropskému trhu (42 % akcí v Evropě je zdarma, medián placených akcí činí 350 €).
4. **Scout Credits a monetizační model:** Funkční ukázka zpeněžení – univerzity mohou využít kredity ke zvýraznění své akce zlatým odznakem *★ Doporučeno* přímo v mapě účastníků.
5. **Nástroje pro diseminaci:** Generátor white-label kódu pro vložení mapy do fakultního webu (iframe), export kompletní databáze do CSV a generátor týdenního pondělního e-mailového digestu otevřených uzávěrek pro katedry.

---

## 7 Rozdělení práce v týmu

Na realizaci projektu se podíleli všichni členové týmu. Rozdělení rolí odpovídalo silným stránkám jednotlivců a pokrývalo jak vývojovou, tak analytickou a textovou část:

* **Viktor Štěch:** Technická architektura multiagentního systému, implementace crawlerů a API integrace (Exa.ai), správa repozitáře a deploymentu na GitHub Pages.
* **Jiří Matějka:** Návrh a implementace B2B portálu WeekScout Campus, vývoj Competitive Intelligence analytiky (detekce kolizí, cenový benchmark), UX optimalizace a propojení klientských rozhraní.
* **Jiří Jáchym:** Nezávislá verifikace a čištění databáze akcí, testování odezvy vyhledávacího enginu, ladění kartografických podkladů Leaflet a responzivního chování na mobilních zařízeních.
* **Jan Rehanzl:** Formulace strategických cílů projektu, definice Key Intelligence Topics (KIT) a Key Intelligence Questions (KIQ), zpracování PESTEL analýzy a kompletace textu závěrečného reportu.
* **Barbora Beňová:** Zpracování analýzy pěti sil dle Portera, sestavení srovnávací matice konkurence, evaluace mezer na trhu a příprava scénáře závěrečné prezentace.

---

## 8 Deklarace využití AI

Umělá inteligence byla v projektu využita ve dvou základních rovinách:
1. **Jako součást produktu:** Modulární pipeline využívá vyhledávací AI engine Exa.ai k identifikaci nestrukturovaných univerzitních pozvánek a LLM agenty (Claude 3.5 Sonnet / Gemini 2.0 v prostředí Google Antigravity) pro extrakci strukturovaných metadat, syntézu témat a nezávislé ověřování. Všechny strojové výstupy podléhají deterministické validaci schématu (`merge_validate.py`).
2. **Při přípravě dokumentace:** AI asistenti byli využiti k revizi gramatiky, formátování markdown tabulek a logické kontrole návaznosti jednotlivých kapitol. Za věcnou správnost, interpretaci dat a dodržení etických pravidel odpovídá autorský tým.
