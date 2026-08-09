"""
General application settings.

Everything here reads from the environment first, with sane local-dev
defaults, so `py main.py` works immediately after a fresh clone with zero
configuration — no .env file required to just try it out.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Core -------------------------------------------------------------
DEBUG = os.environ.get("EPL_DEBUG", "true").lower() in ("1", "true", "yes")
SEASON = os.environ.get("EPL_SEASON", "2026-27")
SECRET_KEY = os.environ.get("EPL_SECRET_KEY", "dev-only-change-me-before-any-real-deployment")

HOST = os.environ.get("EPL_HOST", "127.0.0.1")
PORT = int(os.environ.get("EPL_PORT", "8000"))

# Set EPL_WSGI_SERVER=production to have main.py serve via waitress instead
# of Flask's dev server. Dev server is fine for local use and demos.
WSGI_SERVER = os.environ.get("EPL_WSGI_SERVER", "dev")

# --- Paths --------------------------------------------------------------
CACHE_DIR = BASE_DIR / "cache"
API_CACHE_DIR = CACHE_DIR / "api_responses"
SOCCERDATA_CACHE_DIR = CACHE_DIR / "soccerdata_cache"

# --- Database -------------------------------------------------------------
# Local dev: SQLite, zero setup. Production: point DB_URL at Postgres
# (Supabase or otherwise) — SQLAlchemy abstracts the dialect, nothing else
# in the codebase needs to change.
DB_URL = os.environ.get("EPL_DB_URL", f"sqlite:///{BASE_DIR / 'epl_predictor.db'}")

# --- Scheduler ------------------------------------------------------------
# Minutes between live-state refreshes while the season is active.
LIVE_REFRESH_INTERVAL_MIN = int(os.environ.get("EPL_LIVE_REFRESH_MIN", "20"))
# Minutes between live-gameweek score refreshes (only runs while a gameweek
# is actually in progress — see data/live_updater.py).
GAMEWEEK_LIVE_REFRESH_MIN = int(os.environ.get("EPL_GAMEWEEK_LIVE_REFRESH_MIN", "3"))
# Set to false to disable all background jobs (useful for tests / CI).
ENABLE_SCHEDULER = os.environ.get("EPL_ENABLE_SCHEDULER", "true").lower() in ("1", "true", "yes")

# --- Logging ----------------------------------------------------------
LOG_LEVEL = os.environ.get("EPL_LOG_LEVEL", "INFO")


def ensure_directories() -> None:
    """Create cache/db directories if they don't exist yet. Called from main.py on boot."""
    for d in (CACHE_DIR, API_CACHE_DIR, SOCCERDATA_CACHE_DIR):
        d.mkdir(parents=True, exist_ok=True)
