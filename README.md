# EPL Predictor 2026/27

EPL Predictor is a Python application for exploring Premier League match and season forecasts. It combines a Dixon–Coles low-score-adjusted Poisson model, deterministic Monte Carlo season simulation, optional machine-learning experiments, configurable data providers, a SQLAlchemy persistence layer, a Flask web dashboard, a JSON API, and downloadable reports.

The project is designed to be useful in two modes:

1. **Immediate local demo** – SQLite, seeded clubs, illustrative ratings, and the generated 2026/27 calendar work without API keys.
2. **Research/deployment workflow** – live FPL refreshes, historical FBref/soccerdata training data, optional API-Football and football-data.org cross-checks, PostgreSQL, scheduled refreshes, calibration, backtesting, and report generation.

This README documents the implementation in the repository. It is intentionally explicit about which pieces are production-shaped, which are optional, and which currently use illustrative inputs.

## Contents

- [What the application does](#what-the-application-does)
- [Reality and data-status notes](#reality-and-data-status-notes)
- [Architecture](#architecture)
- [Repository map](#repository-map)
- [Installation](#installation)
- [Running the application](#running-the-application)
- [Configuration](#configuration)
- [Prediction pipeline](#prediction-pipeline)
- [Database](#database)
- [Web dashboard](#web-dashboard)
- [JSON API](#json-api)
- [Data providers](#data-providers)
- [Reports and exports](#reports-and-exports)
- [Command-line scripts](#command-line-scripts)
- [Testing](#testing)
- [Docker and production serving](#docker-and-production-serving)
- [Extending the project](#extending-the-project)
- [Limitations and roadmap](#limitations-and-roadmap)
- [Troubleshooting](#troubleshooting)
- [License and attribution](#license-and-attribution)

## What the application does

### Match prediction

For a selected home and away club the system calculates:

- home, draw, and away probabilities;
- expected home and away goals (`xG`-style Poisson means);
- both-teams-to-score probability;
- over/under 2.5 goals probability;
- a correct-score probability matrix;
- the most likely scorelines;
- team-strength comparison data consumed by the dashboard charts.

### Season simulation

The season engine generates or consumes a 380-fixture double round-robin schedule, samples each fixture, updates a simulated table, and repeats the process. It aggregates:

- average points;
- title probability;
- top-four probability;
- relegation probability;
- final table projections.

The simulation uses a stable seed derived from a caller-supplied key, which makes local demos and tests reproducible while still allowing a different seed for a different simulation run.

### FPL companion

The FPL Lab converts match probabilities into Fantasy Premier League-oriented signals:

- captain score;
- expected goals;
- clean-sheet probability;
- opponent and venue context for a gameweek.

It is a decision aid, not ownership, price, injury-news, or transfer advice by itself.

### Research tools

The repository also contains feature engineering, Elo, fatigue, injury, lineup-risk, weather, NLP sentiment, ML-model, calibration, benchmark, and weight-optimization modules. These provide extension points and experiments; the current default live prediction path is intentionally Dixon–Coles-first.

## Reality and data-status notes

The application labels these distinctions in the UI because they matter for responsible modelling.

### Immediately usable

- Flask app and JSON API;
- SQLite database;
- seeded club metadata and colours;
- seeded illustrative ratings;
- confirmed/seeded Matchweek 1 data in the project calendar;
- generated remaining calendar rounds;
- Dixon–Coles calculations;
- season simulation;
- CSV, XLSX, and PDF generation;
- automated tests.

### Illustrative until replaced

- most default club attack, defence, form, discipline, and home-advantage values;
- the generated Matchweeks 2–38 calendar unless replaced by a provider feed;
- pre-season projections before live results are recorded;
- claims about accuracy before a real historical walk-forward evaluation is run.

### Optional or provider-dependent

- FPL live ratings and fixtures;
- API-Football cross-check data;
- football-data.org fixtures and standings;
- soccerdata/FBref historical training data;
- ScraperFC market-value enrichment;
- Transformer-based news sentiment;
- PostgreSQL deployment.

Do not present an illustrative projection as an official Premier League forecast. The project is independent and is not affiliated with, endorsed by, or licensed by the Premier League.

## Architecture

```text
                     ┌──────────────────────────┐
                     │      Browser dashboard    │
                     │  Jinja pages + CSS + JS   │
                     └────────────┬─────────────┘
                                  │ HTTP
                     ┌────────────▼─────────────┐
                     │       Flask app           │
                     │ pages / API / downloads   │
                     └──────┬─────────┬─────────┘
                            │         │
              ┌─────────────▼───┐ ┌──▼────────────────┐
              │ Prediction engine │ │ SQLAlchemy DB     │
              │ DC / MC / ML      │ │ clubs / fixtures  │
              └─────────────┬────┘ │ predictions/runs  │
                            │      └───────────────────┘
                    ┌───────▼────────┐
                    │ Data providers  │
                    │ FPL / FBref /   │
                    │ API-Football    │
                    └─────────────────┘
```

The normal request path is:

1. A browser calls a page route.
2. The page loads shared JavaScript and calls `/api/v1` for live values.
3. The API route validates IDs and query parameters.
4. `engine/predictor.py` resolves teams, weights, fixtures, and model functions.
5. The engine returns dataclasses serialized by Flask as JSON.
6. The page renders probability bars, score grids, tables, or Chart.js plots.

## Repository map

```text
EPL_PREDICTOR_2026/
├── main.py
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── README.md
├── Next_seasons_modifications_guide.md
├── EPL_homepage.html
├── epl_predictor.db
├── cache/
├── config/
├── data/
├── database/
├── engine/
├── dashboard/
├── reports/
├── scripts/
├── tests/
└── intial_project_files/
```

`__pycache__` directories and cached provider responses are runtime artifacts and are not part of the conceptual architecture.

### Root files

| File | Purpose |
|---|---|
| `main.py` | Process entry point. Configures logging, creates directories, initializes and seeds the database, optionally starts APScheduler, then serves Flask with the development server or Waitress. |
| `pyproject.toml` | Package metadata, Python version requirement, dependencies, optional extras, pytest configuration, and build backend. |
| `requirements.txt` | Flat dependency list for straightforward installation with `pip`. |
| `Dockerfile` | Container image definition for running the application in a deployment environment. |
| `README.md` | This implementation guide. |
| `Next_seasons_modifications_guide.md` | Notes for replacing the seeded season/calendar assumptions in a future season. |
| `EPL_homepage.html` | Original standalone visual prototype/reference. It is not the Flask runtime template; the live home page is `dashboard/templates/homepage.html`. |
| `epl_predictor.db` | Default local SQLite database created/used by the app. Treat it as local state, not a portable production database. |

## Installation

### Requirements

- Python 3.10 or newer;
- `pip` or another Python package installer;
- optional internet access for provider refreshes;
- optional PostgreSQL for deployment.

### Standard installation

```bash
git clone <repository-url>
cd EPL_PREDICTOR_2026
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

The project also declares optional dependency groups in `pyproject.toml`:

```bash
pip install -e ".[dev]"
pip install -e ".[nlp]"
pip install -e ".[scraping]"
```

The standard dependency set already includes the main scientific, web, reporting, and provider libraries. NLP and ScraperFC remain optional because they are not required for the default app.

## Running the application

### Development

```bash
python main.py
```

Windows also supports:

```powershell
py main.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

The first startup creates cache directories, initializes SQLAlchemy tables, seeds the local database when needed, and registers the Flask page, API, and download blueprints.

### Importing the Flask app

Tests and WSGI servers use the application factory:

```python
from dashboard.app import create_app

app = create_app()
```

`create_app()` has no server side effects. This is why it can be used by Flask’s test client, Waitress, or another WSGI host.

### Useful development commands

```bash
pytest
python scripts/migrate_db.py
python scripts/data_quality_report.py
```

## Configuration

All application settings are environment-driven with safe local defaults. The canonical definitions are in `config/settings.py`, `config/api_settings.py`, and `config/feature_weights.py`.

### Core environment variables

| Variable | Default | Meaning |
|---|---|---|
| `EPL_DEBUG` | `true` | Flask/debug behavior. Set false outside local development. |
| `EPL_SEASON` | `2026-27` | Season label used by routes, database records, and refresh jobs. |
| `EPL_SECRET_KEY` | development placeholder | Flask signing key. Replace in any real deployment. |
| `EPL_HOST` | `127.0.0.1` | Bind address. |
| `EPL_PORT` | `8000` | Listening port. |
| `EPL_WSGI_SERVER` | `dev` | `production` selects Waitress in `main.py`. |
| `EPL_DB_URL` | local SQLite path | SQLAlchemy database URL; PostgreSQL is supported by changing this value. |
| `EPL_LIVE_REFRESH_MIN` | `20` | Background live-state refresh interval. |
| `EPL_GAMEWEEK_LIVE_REFRESH_MIN` | `3` | In-gameweek score refresh interval. |
| `EPL_ENABLE_SCHEDULER` | `true` | Disable background jobs in tests/CI with `false`. |
| `EPL_LOG_LEVEL` | `INFO` | Python logging level. |
| `EPL_ENABLE_SCRAPERFC` | `false` | Enables optional ScraperFC enrichment. |

### Provider keys

| Variable | Used by | Required? |
|---|---|---|
| `API_FOOTBALL_KEY` | `data/api_football_client.py` | Only for API-Football requests. |
| `FOOTBALL_DATA_API_KEY` | `data/football_data_org_client.py` | Only for football-data.org requests. |
| `SPORTMONKS_KEY` | Reserved configuration only | Not integrated into v1. |

FPL’s public endpoints are configured in `config/api_settings.py` and do not require a key for the default flow. Providers are cached in `cache/api_responses` to reduce repeated calls.

### Model weights

`config/feature_weights.py` centralizes the default tuning values:

- `home_advantage_weight` – venue effect scale, 0–100;
- `recent_form_weight` – influence of recent form, 0–100;
- `dixon_coles_rho` – low-score correlation adjustment;
- `season_jitter` – uncertainty applied between simulated seasons;
- `ensemble_blend` – future blend percentages for Dixon–Coles, Elo, and ML;
- league-average home/away goal baselines;
- global home bonus.

`get_weights(overrides)` returns a copy, so API or script overrides do not mutate process-wide defaults.

## Prediction pipeline

### 1. Team ratings

`data/team_data.py` exposes the seeded team dictionaries. Each team includes an ID, name, short code, colour, attack, defence, home advantage, discipline, form, and metadata used by the UI and model.

### 2. League baselines

`engine/probability_model.py` computes average attack and defence values. A team’s attack is normalized against the league attack baseline; defence is normalized against the league defensive baseline.

### 3. Expected goals

`match_lambdas()` combines:

- home attack strength;
- away defensive weakness;
- away attack strength;
- home defensive weakness;
- league-average goal baselines;
- venue/home advantage;
- recent-form multiplier;
- configurable weight overrides.

The result is a pair of expected-goal means, `lambda_home` and `lambda_away`.

### 4. Dixon–Coles score matrix

For each score `(x, y)`, the engine multiplies two Poisson probability mass functions and applies `dc_tau()` to low-score outcomes. The default matrix is bounded by `MAX_GOALS` from `config/constants.py` and is normalized before downstream markets are calculated.

### 5. Market probabilities

`market_probabilities()` aggregates the matrix into:

- home win (`x > y`);
- draw (`x == y`);
- away win (`x < y`);
- BTTS yes;
- over 2.5 goals;
- top scorelines.

`engine/predictor.py` resolves IDs and returns the public `Prediction` dataclass used by the API.

### 6. Season simulation

`engine/monte_carlo.py` creates fixtures, samples Poisson goals, applies match results to points, ranks clubs, and repeats for `n_sims`. Jitter represents pre-season uncertainty. `engine/predictor.py` exposes the production-facing `get_season_projection()` function.

### 7. Supporting model modules

The following modules are available for future blending or feature enrichment:

- `elo_calculator.py` – Elo initialization, expected score, margin-of-victory adjustment, rating updates, and Elo-derived match probabilities;
- `ensemble_predictor.py` – normalized weighted combination of model probability outputs;
- `ml_models.py` – registry and training wrappers for Random Forest, XGBoost, LightGBM, CatBoost when available;
- `feature_engineering.py` – rolling form, venue form, head-to-head, and training-frame construction;
- `calibration.py` – Brier scoring, Platt calibration, isotonic calibration, and evaluation results;
- `benchmark_suite.py` – log loss, Brier score, accuracy, home-win baseline, and walk-forward reports;
- `fatigue_model.py` – rest-day and European-midweek fatigue adjustments;
- `injury_model.py` – squad availability adjustments;
- `lineup_strategy.py` – rotation-risk estimates;
- `weather_model.py` – weather classification and goal-rate adjustment;
- `huggingface_models.py` – optional team-news sentiment feature, not a pretrained match-outcome oracle.

## Database

### Connection layer

`database/connection.py` owns the SQLAlchemy engine, session factory, `init_db()`, and `session_scope()` transaction helper. The rest of the application should use this layer rather than creating engines ad hoc.

### Models

`database/models.py` defines the declarative base and these entities:

| Model | Role |
|---|---|
| `Club` | Stable club identity, name, ID, colours, and metadata. |
| `ClubSeasonRating` | Time-varying rating snapshot by club, season, and source. Supports illustrative, FPL, fitted Dixon–Coles, or ML sources. |
| `Fixture` | Home club, away club, round, date, confirmation state, and optional result. |
| `Prediction` | Per-fixture prediction output, probabilities, expected goals, model/source metadata, and timestamps. |
| `SeasonSimulation` | Stored season projection output and simulation metadata. |
| `ModelRun` | Training/evaluation/run metadata for reproducibility and auditability. |

### Initialization and seeding

`database/migrations.py` provides `run_migrations()` and `seed(force=False)`. The project uses lightweight table creation/seeding for the local application. For a production database, use a controlled migration process and back up before schema changes.

## Web dashboard

The Flask dashboard lives in `dashboard/`. It is server-rendered Jinja HTML plus vanilla JavaScript and Chart.js. The front end intentionally keeps the model/API boundary visible: pages load, then call JSON endpoints for dynamic values.

### Application and routes

- `dashboard/app.py` – `create_app()` factory; registers blueprints and configuration.
- `dashboard/page_routes.py` – HTML routes for home, dashboard, table, fixtures, H2H, FPL Lab, analytics, settings, reports, and download centre.
- `dashboard/api_routes.py` – JSON API blueprint under `/api/v1`.
- `dashboard/download_routes.py` – file responses for CSV, XLSX, and PDF exports.

### Templates

| Template | Purpose |
|---|---|
| `base.html` | Shared document shell, navigation, matchday status rail, footer, common scripts, and template blocks. |
| `homepage.html` | Editorial landing page with opening-fixture forecast, model explainer, media spaces, season preview, and calls to action. |
| `dashboard.html` | Interactive fixture picker, staged model loader, probability output, xG, BTTS, over 2.5, score grid, goal distribution, and radar comparison. |
| `table.html` | On-demand Monte Carlo simulation, projected standings, probabilities, and title-race chart. |
| `fixtures.html` | Full matchweek wall grouped by round, confirmation labels, crest rendering, and links into the match centre. |
| `h2h.html` | Home/away club selector, probability bar, scorelines, and radar comparison. |
| `fpl_lab.html` | Gameweek selector, captain watch, clean-sheet watch, and FPL interpretation notes. |
| `analytics.html` | All-club attack, defence, home-edge, form, and relative rating cards. |
| `settings.html` | Live refresh control, engine sliders, accuracy context, roadmap, methodology, and model caveats. |
| `reports.html` | CSV/XLSX export links and generated Monte Carlo PDF report. |
| `download.html` | Download-centre table for the same generated artifacts. |

### Static assets

- `styles.css` – global light visual system, responsive layout, cards, navigation, matchday rail, pitch visualizations, probability displays, media slots, and page-specific components;
- `common.js` – API helpers, percentages, team cache, crest/form renderers, probability bar, Chart.js defaults, and staged loader;
- `dashboard.js` – projected table, title-race chart, and FPL row renderers;
- `analytics.js` – team rating grid and rating bars;
- `experience.js` – homepage interaction layer;
- `dashboard-experience.js`, `fixtures-experience.js`, `table-experience.js`, `analytics-experience.js`, `h2h-experience.js`, `fpl-experience.js`, `settings-experience.js`, `reports-experience.js`, `download-experience.js` – page-specific enhancement hooks;
- `chart.min.js` – vendored Chart.js runtime;
- `epl_logo.png` – existing local visual asset retained for compatibility.

`theme.js` is retained as an unused experiment from an earlier design pass; the current dashboard is deliberately light-theme-only.

## JSON API

All API routes are mounted under `/api/v1`.

### Health and metadata

```http
GET /api/v1/health
GET /api/v1/model/metadata
```

Health returns a small service status object. Model metadata describes the active engine and roadmap exposed to the Settings page.

### Clubs

```http
GET /api/v1/teams
GET /api/v1/teams/<team_id>
```

Returns seeded/live team metadata and rating fields used by the dashboard.

### Fixtures

```http
GET /api/v1/fixtures
GET /api/v1/fixtures?matchweek=1
```

Returns serialized fixtures, including round, teams, date, confirmation flag, and result fields when available.

### Match prediction

```http
GET /api/v1/predict/<home_id>/<away_id>
```

Optional query parameters:

```text
?home_advantage_weight=55
&recent_form_weight=50
&dixon_coles_rho=-0.11
```

The response contains expected goals, 1X2 probabilities, BTTS, over 2.5, the score matrix, and top scorelines.

### Season simulation

```http
POST /api/v1/simulate-season
Content-Type: application/json

{"n_sims": 300}
```

The response contains an ordered projection with average points and title/top-four/relegation probabilities. Weight query parameters are also supported by the route implementation.

### FPL picks

```http
GET /api/v1/fpl/captain-picks?matchweek=1
```

Returns rows for club, venue, opponent, xG, captain score, and clean-sheet probability.

### Live refresh

```http
POST /api/v1/live-data/refresh?season=2026-27
```

Attempts to obtain current FPL data and persist updated ratings. The response reports success, teams updated, or the provider error.

## Data providers

### `data/api_client.py`

Shared HTTP JSON client with cache paths, TTL checks, request handling, and `ApiClientError`.

### `data/fpl_client.py`

Server-side client for the public Fantasy Premier League API. It validates expected response keys and exposes bootstrap static data, fixtures, gameweek-live data, current gameweek, and conversion into team ratings.

### `data/api_football_client.py`

Optional API-Football client. It requires `API_FOOTBALL_KEY`, tracks daily usage, self-throttles to the configured free-tier limit, and exposes fixtures and standings.

### `data/football_data_org_client.py`

Optional football-data.org client for matches and standings. It requires `FOOTBALL_DATA_API_KEY` and respects the configured rate limit.

### `data/soccerdata_integration.py`

FBref-backed historical data integration through `soccerdata`. It retrieves team season statistics and schedules, maps provider names into project IDs, and converts schedules to the engine’s history format.

### `data/scraperfc_integration.py`

Optional market-value enrichment. It is disabled unless `EPL_ENABLE_SCRAPERFC=true`.

### `data/live_updater.py`

Orchestrates live refreshes, writes rating snapshots, cross-checks API-Football when configured, and determines whether a gameweek is currently live.

### `data/calendar_2026.py` and `data/season_2026.py`

The calendar module provides round dates, fixture serialization, all fixtures, and club-specific fixture lookup. The season module records results and derives finished fixtures and recent form from the database.

### `data/team_data.py` and `data/stadium_data.py`

Static display metadata: team list, lookup helpers, promoted-team list, colours, stadium names, and venue information.

## Reports and exports

- `reports/csv_excel_report.py`:
  - `fixtures_csv()` exports the complete fixture schedule;
  - `predictions_csv(matchweek, weights)` exports prediction rows;
  - `predictions_xlsx(matchweek, weights)` creates an Excel workbook.
- `reports/pdf_generator.py`:
  - `season_report_pdf(n_sims)` runs a projection and builds a real PDF using ReportLab.
- `dashboard/download_routes.py` streams these generated artifacts with download-friendly filenames.

## Command-line scripts

All scripts are intended to be run from the repository root.

| Script | What it does |
|---|---|
| `migrate_db.py` | Initializes tables and seeds the database. |
| `data_quality_report.py` | Reports what data and records are currently present. |
| `fetch_historical_data.py` | Pulls historical schedule/statistics data through soccerdata and prepares it for training/evaluation. |
| `generate_results_template.py` | Creates a results-entry template for post-match data collection. |
| `measure_accuracy.py` | Compares model outcomes with a simple baseline on available results. |
| `post_match_evaluation.py` | Evaluates stored predictions after results become available. |
| `calibrate_probabilities.py` | Runs calibration checks and compares probability quality. |
| `optimize_weights.py` | Searches candidate engine weights and evaluates them with benchmark functions. |

Examples:

```bash
python scripts/migrate_db.py
python scripts/data_quality_report.py
python scripts/fetch_historical_data.py
python scripts/measure_accuracy.py
python scripts/calibrate_probabilities.py
python scripts/optimize_weights.py
python scripts/post_match_evaluation.py
```

Provider scripts may require network access, additional packages, API keys, and patience with rate limits.

## Testing

Run the full suite:

```bash
pytest
```

The test suite includes:

| Test file | Coverage |
|---|---|
| `tests/test_probability_model.py` | Poisson/Dixon–Coles calculations, score matrix behavior, market aggregation, and prediction shape. |
| `tests/test_monte_carlo.py` | Schedule creation, deterministic seeded simulation, and projection fields. |
| `tests/test_ml_models.py` | ML registry/training behavior using synthetic data and optional-library handling. |
| `tests/test_flask_app.py` | Flask application factory, page routes, API routes, and response contracts. |
| `tests/conftest.py` | Shared fixtures, isolated configuration, and test setup. |

For CI, set `EPL_ENABLE_SCHEDULER=false` so background jobs cannot keep a test process alive or make external requests.

## Docker and production serving

The application can run behind Waitress using:

```powershell
$env:EPL_WSGI_SERVER="production"
python main.py
```

For deployment, set at least:

```text
EPL_DEBUG=false
EPL_SECRET_KEY=<long-random-secret>
EPL_HOST=0.0.0.0
EPL_PORT=8000
EPL_DB_URL=postgresql+psycopg://user:password@host:5432/epl_predictor
EPL_ENABLE_SCHEDULER=false
```

Run scheduled refreshes as a separate worker or job in production rather than accidentally starting duplicate schedulers across multiple web replicas. Back up the database and cache provider data where reproducibility matters.

The `Dockerfile` provides the container baseline. Review its command, environment, database URL, health checks, and persistent volume strategy before production use.

## Extending the project

### Add a new model

1. Implement a pure, testable function or dataclass in `engine/`.
2. Add a focused unit test under `tests/`.
3. Add a benchmark adapter in `engine/benchmark_suite.py`.
4. Validate against a chronological walk-forward split, not a random split.
5. Add it to `ensemble_predictor.py` only after calibration and baseline comparison.
6. Record the model version and weights in `ModelRun` metadata.

### Add a new data source

1. Put provider-specific HTTP code in `data/`.
2. Reuse `data/api_client.py` for caching and error handling.
3. Add environment configuration in `config/api_settings.py`.
4. Normalize provider team names into the project’s stable IDs.
5. Store source and timestamp on rating snapshots.
6. Add an explicit fallback behavior when the provider is unavailable.

### Add a dashboard page

1. Add a route to `dashboard/page_routes.py`.
2. Add a Jinja template extending `base.html`.
3. Add JSON work to `dashboard/api_routes.py` rather than embedding database logic in templates.
4. Put shared browser helpers in `common.js` and page-only behavior in a page-specific JS file.
5. Use the shared CSS vocabulary and add responsive behavior.
6. Add a route smoke test to `tests/test_flask_app.py`.

### Replace illustrative 2026/27 data

Update `data/calendar_2026.py`, `data/team_data.py`, and the database seed path together. Do not only change the UI labels: fixture IDs, dates, club IDs, rating snapshots, and historical results must remain internally consistent.

## Limitations and roadmap

### Current limitations

- Default ratings are illustrative until a fitted/live source is loaded.
- Generated Matchweeks 2–38 should not be mistaken for an official released schedule.
- The default blend is 100% Dixon–Coles; Elo and ML blend weights are present for future validation.
- Injuries, lineups, weather, fatigue, market odds, and news sentiment are extension modules rather than fully wired production signals in the default prediction path.
- A correct-score prediction is inherently difficult; the modal score is not a guarantee.
- Accuracy claims require real, time-ordered evaluation data.

### Roadmap represented in the code

1. Fit club attack/defence parameters on historical results.
2. Add walk-forward calibration and persist model-run metrics.
3. Validate Elo and ML models against Dixon–Coles and simple baselines.
4. Blend only calibrated models with documented weights.
5. Add reliable lineup, injury, weather, and market signals.
6. Replace generated fixtures with an official schedule feed when available.
7. Move scheduled refreshes and report generation into production workers.
8. Add authentication, user prediction storage, leaderboards, and audit trails if the product becomes multi-user.

## Troubleshooting

### The app does not start

- Confirm Python is 3.10+.
- Activate the virtual environment.
- Run `pip install -r requirements.txt`.
- Check whether port 8000 is already in use; set `EPL_PORT` to another value.
- Run `python scripts/migrate_db.py` and retry.

### Provider refresh fails

- Confirm internet access.
- Check the relevant API key variable.
- Inspect cache files under `cache/api_responses`.
- Respect provider quotas and wait before retrying.
- The local seeded ratings are intentionally retained as a fallback.

### PostgreSQL cannot connect

- Verify the full SQLAlchemy URL, including the driver package.
- Confirm the database exists and accepts the application host.
- Run migrations against the target database before starting the web process.
- Use SQLite locally to isolate application issues from infrastructure issues.

### The dashboard shows stale values

- Refresh live data from Settings when a provider is configured.
- Check the cache TTL in `config/api_settings.py`.
- Check whether `EPL_ENABLE_SCHEDULER` is enabled.
- Inspect the database rating source and timestamp fields.

## License and attribution

The project is released under the MIT license as declared in `pyproject.toml`.

The application is an independent project and is not affiliated with the Premier League. Provider names and external data sources retain their own terms and licenses. Review each provider’s terms before redistributing fetched data or generated reports.
