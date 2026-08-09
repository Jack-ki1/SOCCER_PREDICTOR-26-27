"""
FPL official API client — primary live data source (see build plan §2).
Free, no key, but no CORS headers, which doesn't matter here since this
runs server-side. This is the same contract as the standalone
backend/main.py FastAPI proxy from the earlier prototype session, just
folded into this project's Flask app instead of a separate service.

Response shapes documented here are believed accurate as of this project's
build date but are not officially/contractually stable — FPL's endpoints
have shifted shape before at season boundaries. `_require_keys` fails
loudly rather than silently ingesting a shape that's changed underneath us.
"""
from __future__ import annotations

from config.api_settings import FPL_BASE_URL, FPL_CACHE_TTL_SECONDS, FPL_REQUEST_TIMEOUT
from data.api_client import ApiClientError, get_json


class FplClientError(ApiClientError):
    pass


def _require_keys(data: dict, keys: list[str], context: str) -> None:
    missing = [k for k in keys if k not in data]
    if missing:
        raise FplClientError(f"FPL API response for {context} is missing expected keys {missing} — shape may have changed")


def get_bootstrap_static() -> dict:
    """Teams, players, gameweek (event) metadata — the FPL API's single biggest payload."""
    data = get_json(
        f"{FPL_BASE_URL}/bootstrap-static/",
        timeout=FPL_REQUEST_TIMEOUT, cache_key="fpl-bootstrap-static", cache_ttl_seconds=FPL_CACHE_TTL_SECONDS,
    )
    _require_keys(data, ["teams", "events", "elements"], "bootstrap-static")
    return data


def get_fixtures(event: int | None = None) -> list[dict]:
    params = {"event": event} if event else None
    cache_key = f"fpl-fixtures-{event or 'all'}"
    data = get_json(
        f"{FPL_BASE_URL}/fixtures/", params=params,
        timeout=FPL_REQUEST_TIMEOUT, cache_key=cache_key, cache_ttl_seconds=FPL_CACHE_TTL_SECONDS,
    )
    if not isinstance(data, list):
        raise FplClientError("FPL /fixtures/ did not return a list — shape may have changed")
    return data


def get_gameweek_live(event_id: int) -> dict:
    """Live/finished stats for a specific gameweek. Only worth polling frequently
    while that gameweek is actually in progress — check current_gameweek() first."""
    data = get_json(
        f"{FPL_BASE_URL}/event/{event_id}/live/",
        timeout=FPL_REQUEST_TIMEOUT, cache_key=f"fpl-live-{event_id}", cache_ttl_seconds=60,
    )
    _require_keys(data, ["elements"], f"event/{event_id}/live")
    return data


def current_gameweek(bootstrap: dict | None = None) -> dict | None:
    """Returns the FPL 'event' dict currently marked is_current, or None between seasons."""
    bootstrap = bootstrap or get_bootstrap_static()
    return next((e for e in bootstrap["events"] if e.get("is_current")), None)


def teams_with_real_ratings(bootstrap: dict | None = None) -> list[dict]:
    """
    Reshapes FPL's real, Premier-League-published team strength fields into
    this project's TEAMS schema (0-100ish scale), so it can be merged
    straight into config.constants.TEAMS_BY_ID / the database via
    database/migrations.py's seed(force=True) pattern. This is the
    single highest-value call in this whole client — see build plan §2.
    """
    bootstrap = bootstrap or get_bootstrap_static()
    teams = []
    for t in bootstrap["teams"]:
        def rescale(v: float) -> float:
            # FPL's strength_* fields run roughly 1000-1400; rescale to our 0-100 band.
            return round((v - 1000) / 4, 1)

        teams.append({
            "id": t["short_name"].lower(),
            "fpl_team_id": t["id"],
            "name": t["name"],
            "short": t["short_name"],
            "attack": rescale((t["strength_attack_home"] + t["strength_attack_away"]) / 2),
            "defense": 100 - rescale((t["strength_defence_home"] + t["strength_defence_away"]) / 2),
            "home_adv": rescale(t["strength_overall_home"]),
        })
    return teams
