"""
EPL Predictor 2026/27 — main entry point.

Usage:
    python main.py          (or `py main.py` on Windows)

What this does, in order:
    1. Load config/settings.py, ensure cache/ directories exist
    2. Initialize the database (SQLite by default) and seed illustrative
       data if this is a fresh install
    3. Start the background scheduler (live-data refresh jobs), unless
       disabled via EPL_ENABLE_SCHEDULER=false
    4. Hand off to the Flask app (dashboard/app.py)

No external services required for a first run — SQLite + illustrative
ratings mean this works immediately after `pip install -r requirements.txt`,
with no .env file, no Postgres, no API keys. Everything past that point
(live FPL data, Postgres in production, API-Football cross-checks) is
additive, not required.
"""
from __future__ import annotations

import logging
import sys

from config import settings


def _configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _init_database() -> None:
    from database.migrations import run_migrations, seed

    run_migrations()
    summary = seed()
    if summary["clubs_added"]:
        logging.getLogger("epl_predictor.main").info("Fresh install detected — seeded %s", summary)


def _start_scheduler():
    """Returns the scheduler instance (so main() can shut it down cleanly) or None if disabled."""
    if not settings.ENABLE_SCHEDULER:
        logging.getLogger("epl_predictor.main").info("Scheduler disabled (EPL_ENABLE_SCHEDULER=false)")
        return None

    from apscheduler.schedulers.background import BackgroundScheduler

    from config.constants import SEASON
    from data.live_updater import current_gameweek_is_live, refresh_live_state

    scheduler = BackgroundScheduler()

    def _safe_refresh_live_state():
        try:
            refresh_live_state(SEASON)
        except Exception:
            logging.getLogger("epl_predictor.main").exception("Scheduled refresh_live_state failed")

    def _safe_gameweek_check():
        try:
            if current_gameweek_is_live():
                logging.getLogger("epl_predictor.main").info("Gameweek is live — a real deployment would poll live scores here")
        except Exception:
            logging.getLogger("epl_predictor.main").exception("Scheduled gameweek-live check failed")

    scheduler.add_job(_safe_refresh_live_state, "interval", minutes=settings.LIVE_REFRESH_INTERVAL_MIN, id="refresh_live_state")
    scheduler.add_job(_safe_gameweek_check, "interval", minutes=settings.GAMEWEEK_LIVE_REFRESH_MIN, id="gameweek_live_check")
    scheduler.start()
    logging.getLogger("epl_predictor.main").info(
        "Scheduler started: live refresh every %dmin, gameweek check every %dmin",
        settings.LIVE_REFRESH_INTERVAL_MIN, settings.GAMEWEEK_LIVE_REFRESH_MIN,
    )
    return scheduler


def main() -> int:
    _configure_logging()
    log = logging.getLogger("epl_predictor.main")

    log.info("EPL Predictor 2026/27 — starting up")
    settings.ensure_directories()
    _init_database()
    scheduler = _start_scheduler()

    from dashboard.app import create_app

    app = create_app()

    log.info("Serving on http://%s:%d (Ctrl+C to stop)", settings.HOST, settings.PORT)
    try:
        if settings.WSGI_SERVER == "production":
            from waitress import serve
            serve(app, host=settings.HOST, port=settings.PORT)
        else:
            app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG, use_reloader=False)
    except KeyboardInterrupt:
        log.info("Shutting down (Ctrl+C)")
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
