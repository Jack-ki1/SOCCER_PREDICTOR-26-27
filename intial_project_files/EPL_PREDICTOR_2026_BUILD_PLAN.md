# EPL_PREDICTOR_2026 — Build Plan v2
### A Flask-based, ML-powered EPL prediction system, structured like F1_PREDICTOR_2026

**This supersedes the previous FastAPI-primary plan.** You brought a cleaner
reference — a working F1 project with a proven folder structure and a
single `py main.py` entry point — and asked me to tune it for soccer rather
than force soccer into an architecture I'd already sketched. That's the
right call: FastAPI's async/WebSocket strengths matter less for a
single-operator project than having one obvious way to run the thing. Flask,
one process, one command. Here's the full adaptation.

---

## 0. What changed, and why, vs. the last plan

| Previous plan | This plan | Why |
|---|---|---|
| FastAPI primary, Flask as optional admin app | **Flask primary**, serves both the dashboard *and* the JSON API via blueprints | Matches your reference structure exactly; Flask 2.x+ supports async views if you need them later, so you're not actually giving up async — you're just not running two frameworks for no reason |
| Celery + Redis for scheduling | **In-process scheduler** (APScheduler) inside `main.py` | The reference structure has no Redis/Celery anywhere — one Dockerfile, one process. Simpler is correct until you have a concrete reason not to |
| football-data.co.uk CSVs as primary training source | **`soccerdata` (FBref-backed) as primary** | Your research surfaced it and it's a genuine upgrade — richer metrics (xG, shot maps, passing networks), actively maintained, and gives you the exact "local package that quietly handles the messy backend, hands you a DataFrame" experience FastF1 gives the F1 project. This is the single best find in your research |
| Single data source per category | **Layered, with explicit fallback order** | Mirrors how the F1 project likely treats Jolpica as primary with FastF1 as an enrichment layer — same pattern here |

Everything else — the Dixon-Coles engine, the honesty/calibration
principles, the walk-forward validation methodology, the free-API awareness
— carries forward unchanged. This document replaces the *architecture*, not
the *thinking*.

---

## 1. Folder structure

```
EPL_PREDICTOR_2026/
├── main.py                      # Single entry point — py main.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── README.md
├── pyproject.toml
│
├── cache/
│   ├── api_responses/           # Raw cached JSON from FPL / API-Football
│   └── soccerdata_cache/        # soccerdata's own local cache (its FBref/Understat pulls)
│
├── config/
│   ├── settings.py              # General settings, env-driven
│   ├── api_settings.py          # Base URLs, keys, rate limits per source
│   ├── feature_weights.py       # Dixon-Coles / Elo / ensemble blend weights
│   └── constants.py             # Season dates, club list, competition calendar
│
├── dashboard/                   # Flask application
│   ├── app.py                   # Flask app factory + blueprint registration
│   ├── api_routes.py            # JSON API blueprint (/api/v1/...) — this is where
│   │                             #   the "FastAPI-shaped" endpoints from the last
│   │                             #   plan live now, just as Flask routes
│   ├── static/
│   │   ├── styles.css
│   │   ├── dashboard.js
│   │   ├── common.js
│   │   ├── analytics.js
│   │   └── epl_logo.png
│   └── templates/
│       ├── dashboard.html
│       ├── h2h.html
│       ├── table.html           # league table + Monte Carlo projection (was constructors.html)
│       ├── fpl_lab.html         # NEW — no F1 analogue; captain/clean-sheet tooling
│       ├── analytics.html
│       ├── settings.html        # engine params + live-data connect (was Model Lab)
│       ├── reports.html         # CSV/PDF export (mirrors the JSX Reports tab)
│       ├── download.html
│       └── homepage.html
│
├── data/
│   ├── team_data.py             # Club roster + metadata (was driver_data.py)
│   ├── stadium_data.py          # Ground/venue info (was circuit_data.py)
│   ├── calendar_2026.py         # Fixture calendar, real MW1 + generated rest
│   ├── season_2026.py           # In-progress season state
│   ├── api_client.py            # Generic HTTP client: retries, timeouts, caching
│   ├── fpl_client.py            # Official FPL API wrapper (was jolpica_client.py)
│   ├── api_football_client.py   # NEW — API-Football wrapper, secondary/backup live source
│   ├── football_data_org_client.py  # NEW — secondary fixtures/standings source
│   ├── soccerdata_integration.py    # NEW — wraps `soccerdata` for historical/advanced metrics (was fastf1_integration.py)
│   ├── scraperfc_integration.py     # NEW — optional: Transfermarkt market values as a feature
│   └── live_updater.py          # Orchestrates which source feeds what, and when
│
├── engine/
│   ├── predictor.py             # Orchestrates a single-match prediction end-to-end
│   ├── feature_engineering.py   # Rolling form, rest days, H2H, market-value deltas, etc.
│   ├── ml_models.py             # The ML model zoo — see §5
│   ├── probability_model.py     # Dixon-Coles bivariate Poisson (core, port from the JS prototype)
│   ├── benchmark_suite.py       # Walk-forward backtest runner + baseline comparisons
│   ├── ensemble_predictor.py    # Blends Dixon-Coles + Elo + ML zoo output
│   ├── lineup_strategy.py       # Team-news / rotation-risk analysis (was pit_strategy.py)
│   ├── huggingface_models.py    # NLP tooling — sentiment on team news, NOT a magic predictor (see §6)
│   ├── elo_calculator.py
│   ├── monte_carlo.py           # Season simulator, jitter fix carried over from the prototype
│   ├── weather_model.py         # Kept — weather affects soccer scoring rates too
│   ├── injury_model.py          # Disruption modeling (was safety_car_model.py)
│   ├── fatigue_model.py         # Fixture-congestion/squad-fatigue degradation (was tire_model.py)
│   └── calibration.py           # Platt scaling / isotonic regression on top of raw probabilities
│
├── database/
│   ├── models.py                # SQLAlchemy models
│   ├── connection.py            # SQLite for dev, Postgres/Supabase for prod — see §7
│   └── migrations.py
│
├── reports/
│   ├── csv_excel_report.py
│   └── pdf_generator.py         # WeasyPrint or ReportLab — makes the JSX "PDF preview" real
│
├── scripts/
│   ├── migrate_db.py
│   ├── fetch_historical_data.py # NEW — one-time + seasonal soccerdata/football-data.co.uk backfill
│   ├── measure_accuracy.py
│   ├── calibrate_probabilities.py
│   ├── optimize_weights.py
│   ├── post_match_evaluation.py # was post_race_evaluation.py
│   ├── data_quality_report.py
│   └── generate_results_template.py
│
└── Next_seasons_modifications_guide.md
```

**Run it:** `py main.py`. That's the whole contract — no docker-compose
orchestration required for local dev (though the Dockerfile still exists for
deployment). `main.py`'s job, in order: load `config/settings.py`, ensure
`cache/` subfolders exist, initialize the DB connection and run pending
migrations, start the APScheduler jobs (Section 4) as background threads,
then hand off to `dashboard/app.py`'s Flask app via `app.run()` (dev) or let
a WSGI server (gunicorn/waitress) serve it in production, launched from the
same `main.py` based on an env flag.

---

## 2. Your API research, adjudicated

You did real diligence here — below is the verdict on each, with a role
assigned or a reason it's excluded, not just a restatement of your list.

| Source | Verdict | Role |
|---|---|---|
| **soccerdata** | **Adopt as primary historical/advanced-metrics source.** Free, no key, actively maintained, gives xG/shot maps/passing data that plain football-data.co.uk CSVs don't. This is the standout find. | `data/soccerdata_integration.py` — feeds `scripts/fetch_historical_data.py` and the ML feature pipeline |
| **FPL official API** | Keep as primary *live* source (from the prior research this session) — free, no key, real team-strength ratings, fixtures, gameweek state. Still has zero CORS, so it stays server-side. | `data/fpl_client.py` |
| **API-Football** | Adopt as a **secondary/backup live source**, not primary — 100 req/day free tier is tight for a season-long service polling regularly, so it's for cross-checking or filling gaps FPL's API doesn't cover (e.g., broader competition coverage, lineups). | `data/api_football_client.py` |
| **football-data.org** | Keep as a secondary fixtures/standings source, same role as the prior plan. | `data/football_data_org_client.py` |
| **penaltyblog** | Adopt — Dixon-Coles MLE fitting utility, don't reinvent that optimizer. | Used inside `engine/probability_model.py` |
| **ScraperFC** | Adopt as **optional enrichment only** — squad market value (Transfermarkt) is a genuinely useful feature signal for the ML ensemble (a team's transfer-market valuation correlates with quality independent of current form), but this is a "nice to have in Phase 4," not a Phase 1 dependency, since it's a scraper against a site that can change layout without warning. | `data/scraperfc_integration.py`, feeds `feature_engineering.py` |
| **Sportmonks** | **Not adopted for v1.** Their free-forever tier is explicitly capped to two leagues, and commercial soccer data providers almost always gate top-5-league (EPL included) data behind paid tiers — verify EPL is actually in-scope before building anything against it. Worth a 10-minute check before Phase 4, not worth planning around now. | Flagged as an open question, not integrated |
| **itscalledsoccer** | **Out of scope.** It's the American Soccer Analysis wrapper — MLS/NWSL/USL only, no EPL data. Noted because you found it, excluded because it doesn't apply here. | Not integrated |
| **sportsipy** | **Redundant with soccerdata**, skip it. Sports-Reference (which sportsipy wraps) and FBref (which soccerdata wraps) are sister sites in the same network — you'd likely be pulling overlapping data through two different clients for no benefit. If soccerdata's FBref access ever breaks, sportsipy is a reasonable fallback to keep in your back pocket, not a day-one dependency. | Documented as a fallback option only |

**Resulting layering for live data specifically** (most-trusted first): FPL
API → API-Football (cross-check/gap-fill) → football-data.org (fixtures/
standings backup). **For historical/training data**: soccerdata (primary) →
football-data.co.uk raw CSVs (fallback if soccerdata's scrape target
changes) → ScraperFC market values (enrichment, not a standalone source).

---

## 3. `config/` — what lives where

- **`settings.py`** — `DEBUG`, `SEASON = "2026-27"`, `DB_URL` (env-driven,
  defaults to local SQLite), `CACHE_DIR`, log level.
- **`api_settings.py`** — base URLs and rate-limit numbers for every client
  in `data/` (Section 2's table, encoded as config, not hardcoded in each
  client file).
- **`feature_weights.py`** — the tunable knobs: home-advantage weight,
  form weight, Dixon-Coles ρ (directly the same three sliders as the JSX
  Model Lab tab), plus the ensemble blend weights once v3 exists (how much
  the ML model vs. Dixon-Coles vs. Elo each contribute to the final
  probability).
- **`constants.py`** — the 20-club list with FPL team-id mappings, the real
  Matchweek 1 fixtures, competition calendar (which 9 clubs are in Europe
  this season, for the fatigue model).

---

## 4. `data/` and the ingestion cadence

Same three-job pattern as the prior plan, now scheduled via APScheduler
inside `main.py` instead of Celery:

1. **`refresh_live_state`** (every 15–30 min in-season) — `fpl_client.py`
   pulls bootstrap-static + fixtures, upserts into `database/models.py`
   tables.
2. **`refresh_gameweek_live`** (every 2–5 min, only while a gameweek is
   live — check `is_current` first) — fills in results as matches finish.
3. **`historical_backfill`** (one-time + yearly top-up, triggered manually
   via `scripts/fetch_historical_data.py`, not on the live scheduler) —
   `soccerdata_integration.py` pulls FBref season data, loads into a
   staging table, feeds `engine/feature_engineering.py`.

`live_updater.py` is the orchestrator: it decides, per data need, which
client to call first and what to do if it fails (fall back per the ordering
in Section 2, log the degradation, never silently serve stale data as if
fresh).

---

## 5. `engine/ml_models.py` — the model zoo

"As many as possible" is the brief, so here's the actual roster, in the
order they're worth implementing (cheap/interpretable first, expensive/
opaque last — matches the walk-forward "does it actually beat the simpler
thing" discipline from the prior plan):

| Model | Library | Role |
|---|---|---|
| Logistic Regression (multinomial) | scikit-learn | Cheapest ML baseline, good sanity check against Dixon-Coles |
| Poisson Regression | statsmodels | A more classical alternative to hand-rolled Dixon-Coles fitting |
| Random Forest | scikit-learn | Handles nonlinear feature interactions with minimal tuning |
| Gradient Boosting (XGBoost) | xgboost | The workhorse — most published soccer-prediction papers using tree ensembles lean on this or LightGBM |
| Gradient Boosting (LightGBM) | lightgbm | Faster training, often comparable accuracy to XGBoost — worth A/B-ing both |
| CatBoost | catboost | Academic literature (Greek Super League study, 2022) reports this as a top performer on similar tabular soccer data — cheap to include given how few categorical-encoding headaches it causes |
| Support Vector Machine | scikit-learn | Cited in older but still-relevant soccer-prediction literature (half-time-state prediction studies) — cheap to include as a diversity-of-errors member of the ensemble |
| Naive Bayes | scikit-learn | Same — cheap, sometimes competitive on smaller feature sets, good ensemble diversity |
| K-Nearest Neighbors | scikit-learn | Simple similarity-based baseline — "find historically similar matchups" |
| Small MLP / neural net | scikit-learn `MLPClassifier` or Keras | Academic consensus (see §6) is that deep learning has **not** clearly beaten gradient-boosted trees on this specific tabular task — include it for completeness and your own comparison, not because it's expected to win |

`ensemble_predictor.py` stacks/blends these with Dixon-Coles and Elo — start
with a simple weighted average (config-driven via `feature_weights.py`),
graduate to a proper stacking meta-learner (logistic regression on top of
the base models' outputs) once you have enough backtest history to fit one
without overfitting.

**Important discipline carried over from the last plan:** every one of these
gets walk-forward validated against the "always predict home win" and
"Dixon-Coles alone" baselines before it's allowed into the live ensemble.
More models in the zoo isn't automatically better — `benchmark_suite.py`'s
job is to prove each addition earns its place.

---

## 6. `engine/huggingface_models.py` — honest scope

I checked: there is **no authoritative, production-grade pretrained EPL
outcome-prediction model on Hugging Face** worth depending on. What exists
is scattered community models of unverified quality, and the academic
literature (arXiv surveys on ML in sports betting, 2022–2025) consistently
shows gradient-boosted trees and classical feature-engineering approaches
outperforming or matching deep-learning approaches on this specific
problem — deep learning hasn't demonstrated a clear edge here the way it has
in, say, computer vision.

So this module's real job is narrower and more honest than "download a
soccer-prediction model":

- **Sentiment/NLP on team news** — pull pre-match news/press-conference
  text (if you wire up a source for it) through a general-purpose HF
  sentiment or NER model, use the output as *one additional feature* for
  the ML ensemble (this mirrors exactly what Beal et al.'s ~63%-accuracy
  ensemble did with text signals).
- **A slot for your own fine-tuned model**, later — once you have enough
  proprietary historical + engineered-feature data, fine-tuning something
  small and pushing it to your own HF repo (`huggingface.co/Jack-ki1`) is a
  legitimate v4+ project, not a v1 shortcut.

Don't let this module's name imply more than it does — it's NLP tooling,
not the prediction engine.

---

## 7. Database

Two-tier by design, matching the F1 project's simplicity:

- **Local dev:** SQLite, zero setup, file lives in `cache/` or a top-level
  `db/` folder — `database/connection.py` should default here so `py
  main.py` works immediately after a fresh clone with no external services.
- **Production:** Postgres via **Supabase** (you already run this for other
  projects — same account, same ops muscle memory). `database/connection.py`
  reads `DB_URL` from `config/settings.py`/env and doesn't care which
  backend it's pointed at, since SQLAlchemy abstracts the dialect.

Schema is the same shape as the previous plan's Section 5.2 (`clubs`,
`club_season_ratings`, `fixtures`, `predictions`, `season_simulations`,
`model_runs`) — that part didn't need to change, only where it runs.

---

## 8. `dashboard/` — Flask, both pages and API

`app.py` is a Flask **application factory** registering two blueprints:

- A **page blueprint** serving the templates listed in Section 1 —
  server-rendered where that's simplest (settings, reports, download), or
  serving the React build as static files for the richer interactive pages
  (dashboard, analytics, h2h) if you keep the current JSX-based frontend
  rather than rewriting it in Jinja2. **Recommendation: don't rewrite the
  React dashboard in Jinja2** — serve it as a static build from
  `dashboard/static/`, and let Flask's job be the API + the simpler
  server-rendered pages (settings, reports, download, homepage can stay
  server-rendered if you want a non-JS fallback).
- An **API blueprint** (`api_routes.py`) at `/api/v1/...`, the exact
  endpoint list from the previous plan's Section 7 (`/teams`, `/fixtures`,
  `/predict/<id>`, `/simulate-season`, `/fpl/captain-picks`,
  `/model/metadata`, `/health`) — just implemented as Flask routes instead
  of FastAPI ones. Flask's request/response validation is more manual
  (no free Pydantic layer) — use `marshmallow` or hand-rolled dataclasses if
  you want that structure back.

This is exactly what the current React artifact's `fetchLiveTeams()` and the
Model Lab "Live Data" panel are already built to call — `dashboard/app.py`
running locally on port 8000 (or wherever you configure it) is a drop-in
replacement for the placeholder `backend/main.py` FastAPI proxy from the
previous session, same contract, different framework underneath.

---

## 9. `reports/` — making the JSX preview real

The current dashboard's **Reports tab** (just added) has a CSV export that
works for real (client-side) and a PDF "preview" that's explicitly labeled
as non-functional. This module is what makes the PDF real:

- **`csv_excel_report.py`** — server-side CSV/XLSX generation (via
  `openpyxl` or `pandas.to_excel`) for anything richer than the client-side
  export can do (e.g., a full-season report, not just one gameweek).
- **`pdf_generator.py`** — WeasyPrint (HTML/CSS → PDF, easiest if you
  template it like the existing dashboard HTML) or ReportLab (more control,
  more code) generates the season report PDF. Wire this behind a new
  `/api/v1/reports/season-pdf` route, have the JSX's "Preview report
  generation" button call it for real instead of just showing the staged
  loader.

---

## 10. `scripts/` — one-off and maintenance utilities

Same list as the prior plan, plus one addition (`fetch_historical_data.py`)
for the soccerdata backfill. Each of these is a `python scripts/x.py`
invocation, not part of the live app — `measure_accuracy.py` and
`calibrate_probabilities.py` in particular are what feed
`engine/calibration.py` and `engine/benchmark_suite.py` with real numbers
after each gameweek.

---

## 11. `requirements.txt` (draft)

```
flask>=3.0
flask-cors
sqlalchemy>=2.0
alembic
apscheduler
requests
httpx                 # used inside soccerdata/other clients even if Flask itself doesn't need it
soccerdata
penaltyblog
scraperfc
pandas
numpy
scipy
scikit-learn
xgboost
lightgbm
catboost
statsmodels
mlflow
openpyxl
weasyprint            # or reportlab
python-dotenv
pydantic-settings     # fine to use even outside FastAPI, for typed config loading
gunicorn              # production WSGI server
psycopg2-binary        # Postgres driver, for the Supabase production path
```

---

## 12. Roadmap (revised for this structure)

| Phase | Scope |
|---|---|
| **Phase 0** | Scaffold the folder tree above, `main.py` boots Flask + SQLite with zero config, `/health` responds |
| **Phase 1** | `data/fpl_client.py` + `data/soccerdata_integration.py` live, real clubs/fixtures/historical matches in the DB |
| **Phase 2** | Port Dixon-Coles + Monte Carlo (`probability_model.py`, `monte_carlo.py`) to Python, **fit ratings from soccerdata history** instead of illustrative numbers, `/api/v1/predict` and `/api/v1/simulate-season` live |
| **Phase 3** | Point the existing React dashboard at this Flask API instead of computing client-side; ship the Reports tab's PDF generation for real |
| **Phase 4** | `engine/ml_models.py` zoo + `ensemble_predictor.py`, walk-forward backtested via `benchmark_suite.py`, MLflow tracking |
| **Phase 5** | `elo_calculator.py`, `injury_model.py`, `fatigue_model.py`, `weather_model.py` as additional ensemble features; ScraperFC market-value enrichment |
| **Phase 6** | `huggingface_models.py` NLP layer, FPL Lab live on real gameweek data, `Next_seasons_modifications_guide.md` written from what you actually learned running Phase 0–5 through a real season |

---

## 13. Open questions for you

- Confirm you want the **current React dashboard kept as-is** (served as a
  static build from Flask) rather than rewritten as Jinja2 templates — my
  recommendation above assumes yes, since it's already built, tested, and
  more interactive than a server-rendered page would be.
- **Sportmonks EPL coverage** — worth 10 minutes checking their docs before
  Phase 4 if you want it as an additional live-data cross-check.
- Single-league (EPL) scope still assumed throughout — flag if that's
  changing.
- `Next_seasons_modifications_guide.md` is listed in the structure but its
  content only really exists *after* you've run a season and learned what
  needed changing — treat it as a Phase 6 deliverable, not something to
  draft speculatively now.

---

**Next step, same as last time:** pick a phase and I'll start writing the
actual Python files against this structure.
