"""
Per-data-source API configuration.

See EPL_PREDICTOR_2026_BUILD_PLAN.md §2 for the full reasoning behind which
source plays which role. Short version:
    - FPL API:            primary live source (free, no key, no CORS issue
                           since this all runs server-side)
    - API-Football:       secondary/backup live source (free tier is only
                           100 req/day, so it's a cross-check, not primary)
    - football-data.org:  secondary fixtures/standings source
    - soccerdata (FBref):  primary historical/training data source
"""
import os

# --- FPL official API (fantasy.premierleague.com) -------------------------
FPL_BASE_URL = "https://fantasy.premierleague.com/api"
FPL_REQUEST_TIMEOUT = 10
FPL_CACHE_TTL_SECONDS = 300  # be polite — don't hammer a free, unauthenticated API

# --- API-Football (RapidAPI or direct) -------------------------------------
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "")
API_FOOTBALL_DAILY_LIMIT = 100  # free tier — data/api_football_client.py self-throttles to this
API_FOOTBALL_REQUEST_TIMEOUT = 10

# --- football-data.org ------------------------------------------------------
FOOTBALL_DATA_ORG_BASE_URL = "https://api.football-data.org/v4"
FOOTBALL_DATA_ORG_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "")
FOOTBALL_DATA_ORG_RATE_LIMIT_PER_MIN = 10
FOOTBALL_DATA_ORG_REQUEST_TIMEOUT = 10

# --- soccerdata (FBref / Understat via the soccerdata package) -----------
SOCCERDATA_LEAGUE = "ENG-Premier League"
# soccerdata's own season-string format, e.g. "2526" for 2025-26. Keep a
# short rolling window here — walk-forward training needs history, but you
# don't need to redownload the whole competition archive by default.
SOCCERDATA_TRAIN_SEASONS = ["2223", "2324", "2425", "2526"]

# --- ScraperFC (optional enrichment: Transfermarkt market values) --------
SCRAPERFC_ENABLED = os.environ.get("EPL_ENABLE_SCRAPERFC", "false").lower() in ("1", "true", "yes")

# --- Sportmonks (NOT integrated for v1 — see build plan §2) --------------
# Flagged here rather than wired up: their free-forever tier is capped to
# two leagues and EPL inclusion isn't confirmed. Verify before using.
SPORTMONKS_KEY = os.environ.get("SPORTMONKS_KEY", "")
