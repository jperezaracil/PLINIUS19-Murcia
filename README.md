# Plinius 19 (Murcia 2026) · Mediterranean heatwave precursors (STCO-FS)

Static results site of the talk *Identifying the spatio-temporal drivers of Mediterranean heatwaves: a machine learning
feature selection framework* (19th Plinius Conference, Murcia, 7 October 2026). A Coral Reefs Optimization (CRO)
wrapper (STCO-FS) selects spatio-temporal predictors for a logistic-regression model of summer heatwave days at 12
Mediterranean sites.

The site is published with GitHub Pages from the `main` branch (root folder). Open `index.html` to browse it locally.

## Contents

- `index.html`: overview with key numbers, what the model can do, the framework, the conclusions and links to the result
  pages.
- `talk.html`: the figures used in the talk, by slide, with the key messages of the results slides.
- One page per topic, grouped in the top menu:
  - Method: `setup`;
  - Results: `skill`, `selection`, `lags`, `anomalies`, `eof`;
  - More: `versions`, `crosssite` (`.html`).
- `img/`: the figures as WebP (maximum width 1800 px).
- `data/`:
  - `figures.json`: header, caption, page and source of every figure;
  - `pages.json`, `overview.json`, `talk.json`: page texts;
  - `skill_by_site.csv`, `skill_by_run.csv`: skill tables.
- `tools/build_site.py`: rebuilds the HTML and images from `data/` and the analysis folder:

      python tools/build_site.py --src <path to sim_lag30/analisis>

The figures are produced by the analysis scripts (not included here). The path under each figure is its location
inside the analysis folder.
