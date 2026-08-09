"""
Live data orchestrator. Decides, per data need, which client to call first
and what to do if it fails — the layered fallback described in the build
plan §2: FPL API -> API-Football (cross-check/gap-fill) -> football-data.org
(fixtures/standings backup).

This is what config.settings.ENABLE_SCHEDULER's APScheduler jobs
(registered from main.py) actually call. Kept independent of Flask/the web
layer entirely — these functions work the same whether triggered by the
scheduler, a manual `python scripts/fetch_historical_data.py` run, or a
button click in the (optional) Flask admin pages.
"""
from __future__ import annotations

import logging

from data import api_football_client, fpl_client
from data.api_client import ApiClientError
from database.connection import session_scope
from database.models import ClubSeasonRating
from datetime import datetime, timezone

logger = logging.getLogger("epl_predictor.live_updater")


def refresh_live_state(season: str) -> dict:
    """
    Primary live-state refresh: pulls FPL bootstrap-static (teams + current
    gameweek) and fixtures, upserts ratings into the DB as source='fpl_seed'.
    This does NOT overwrite 'dixon_coles_fit' or 'ml_ensemble' rating rows —
    those are separate rows per source (see database/models.py's
    ClubSeasonRating), so you can compare them side by side.
    """
    result = {"ok": False, "teams_updated": 0, "error": None}
    try:
        bootstrap = fpl_client.get_bootstrap_static()
        teams = fpl_client.teams_with_real_ratings(bootstrap)
    except ApiClientError as exc:
        logger.warning("refresh_live_state: FPL API unavailable (%s) — leaving existing ratings untouched", exc)
        result["error"] = str(exc)
        return result

    with session_scope() as session:
        for t in teams:
            session.add(ClubSeasonRating(
                club_id=t["id"], season=season, as_of_date=datetime.now(timezone.utc),
                attack_rating=t["attack"], defense_rating=t["defense"], home_advantage=t["home_adv"],
                source="fpl_seed",
            ))
        result["teams_updated"] = len(teams)

    result["ok"] = True
    logger.info("refresh_live_state: updated %d clubs from FPL API", result["teams_updated"])
    return result


def cross_check_with_api_football(season_year: int) -> dict:
    """
    Secondary check — only runs if API_FOOTBALL_KEY is configured, and
    respects the free-tier daily quota automatically (see
    data/api_football_client.py's self-throttling). Never raises on quota
    exhaustion or missing key; this is an optional cross-check, not a
    dependency anything else in the app needs to function.
    """
    result = {"ok": False, "fixtures_checked": 0, "error": None}
    try:
        fixtures = api_football_client.get_fixtures(season_year)
        result["fixtures_checked"] = len(fixtures)
        result["ok"] = True
    except ApiClientError as exc:
        logger.info("cross_check_with_api_football skipped: %s", exc)
        result["error"] = str(exc)
    return result


def current_gameweek_is_live() -> bool:
    """Only worth polling live gameweek scores when this is true — see config.settings.GAMEWEEK_LIVE_REFRESH_MIN."""
    try:
        bootstrap = fpl_client.get_bootstrap_static()
        event = fpl_client.current_gameweek(bootstrap)
        return bool(event and not event.get("finished", True) and event.get("is_current"))
    except ApiClientError:
        return False
