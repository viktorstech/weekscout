# Erasmus International Weeks 2027

Interaktivní mapa Erasmus+ International Weeks a Staff Weeks na 10 evropských univerzitách (pilot, akademický rok 2026/2027, data k 2026-11-13).

- Mapa (Leaflet) s přepínáním podkladů: Mapa, Satelit, Světlá, Tmavá (rozbalovací menu)
- Filtr: Chci učit / Chci se školit / Chci studovat
- Detail akce po kliknutí na bod nebo záznam: termín, uzávěrka, program, organizátoři, registrace, zdroje
- Časová osa listopad 2026 – červen 2027 s uzávěrkami

Data pocházejí z oficiálních stránek univerzit a databáze IMOTION (staffmobility.eu). U každé akce je uvedený stav ověření. Před přihlášením si uzávěrku ověřte u pořadatele.

Mapové podklady: © OpenStreetMap contributors, Esri World Imagery, Esri Light/Dark Gray Canvas.

Volitelně: do konstanty `CARTO_KEY` v `index.html` lze vložit bezplatný klíč z https://carto.com/basemaps/apikey (omezený na doménu webu). Světlá a Tmavá mapa pak použijí podklady CARTO Positron / Dark Matter.

## Struktura
- `index.html`: aplikace (mapa, časová osa, filtry, detail akce)
- `data.json`: data akcí (`events`), každá akce má zdroje a stav ověření

Mapa a časová osa jsou dvě obrazovky přepínané tlačítkem dole; časová osa má i vlastní adresu `#casova-osa`.
