"""
football-data.org client — secondary fixtures/standings source (build plan
§2). Free tier, needs a key, 10 requests/minute. Used as a cross-check
against the FPL API, or a fallback if FPL's endpoints change shape.
"""
from __future__ import annotations

from config.api_settings import (
    FOOTBALL_DATA_ORG_BASE_URL, FOOTBALL_DATA_ORG_KEY, FOOTBALL_DATA_ORG_REQUEST_TIMEOUT,
)
from data.api_client import ApiClientError, get_json

COMPETITION_CODE = "PL"


class FootballDataOrgError(ApiClientError):
    pass


def _require_key() -> None:
    if not FOOTBALL_DATA_ORG_KEY:
        raise FootballDataOrgError(
            "FOOTBALL_DATA_API_KEY isn't set — register a free key at football-data.org and set it via env."
        )


def _get(path: str, params: dict | None = None, cache_key: str | None = None) -> dict:
    _require_key()
    try:
        return get_json(
            f"{FOOTBALL_DATA_ORG_BASE_URL}{path}", params=params,
            headers={"X-Auth-Token": FOOTBALL_DATA_ORG_KEY},
            timeout=FOOTBALL_DATA_ORG_REQUEST_TIMEOUT, cache_key=cache_key, cache_ttl_seconds=600,
        )
    except ApiClientError as exc:
        raise FootballDataOrgError(str(exc)) from exc


def get_matches(date_from: str | None = None, date_to: str | None = None) -> list[dict]:
    """date_from/date_to as 'YYYY-MM-DD' strings, per the API's own format."""
    params = {}
    if date_from:
        params["dateFrom"] = date_from
    if date_to:
        params["dateTo"] = date_to
    data = _get(f"/competitions/{COMPETITION_CODE}/matches", params=params or None, cache_key=f"fdo-matches-{date_from}-{date_to}")
    return data.get("matches", [])


def get_standings() -> list[dict]:
    data = _get(f"/competitions/{COMPETITION_CODE}/standings", cache_key="fdo-standings")
    tables = data.get("standings", [])
    total_table = next((t for t in tables if t.get("type") == "TOTAL"), None)
    return total_table.get("table", []) if total_table else []
