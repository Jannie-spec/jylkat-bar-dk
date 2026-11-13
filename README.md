# jylkat-bar.dk

Kilden til hjemmesiden for Jylkat Bar i Gudhjem (statisk side, erstattede Aida 13. nov 2026).

- `content/*.json` – alle tekster (dansk, engelsk, tysk, svensk), menukort, åbningstider, blog.
- `site/` – design (CSS, skrifttyper, script) og serverens `.htaccess`.
- `build.py` – bygger siden: `python3 build.py` → `dist/` (det der ligger på jylkat-bar.dk).
- Billederne ligger på serveren i `/media` og er ikke med her.
- Formularerne sender via one.com's formulartjeneste til info@jylkat-bar.dk (videresendes til info@hotelklippen.dk).
- Upload: filerne i `dist/` gemmes på one.com-webhotellet for jylkat-bar.dk (File Manager).
