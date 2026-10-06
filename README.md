# PLINIUS 2026 · Mediterranean heatwave precursors (STCO-FS)

Static results site for the PLINIUS 2026 study: a Coral Reefs Optimization (CRO) wrapper (STCO-FS) selects
spatio-temporal predictors for a logistic-regression model of summer heatwave days at 12 Mediterranean sites.

The site is published with GitHub Pages from the `main` branch (root folder). Open `index.html` to browse it locally.

## Contents

- `index.html`: overview with the set-up, the main results and the caveats.
- `talk.html`: the figures used in the talk, in slide order.
- One page per topic: `setup`, `skill`, `selection`, `lags`, `anomalies`, `versions`, `crosssite` and `eof` (`.html`).
- `img/`: the figures as WebP (maximum width 1800 px).
- `data/`:
  - `figures.json`: header, caption, page and source of every figure;
  - `pages.json`, `overview.json`: page texts;
  - `skill_by_site.csv`, `skill_by_run.csv`: skill tables.
- `tools/build_site.py`: rebuilds the HTML and images from `data/` and the analysis folder:

      python tools/build_site.py --src <path to sim_lag30/analisis>

The figures themselves are produced by the analysis scripts (not included here). The path under each figure is its
location inside the analysis folder.
