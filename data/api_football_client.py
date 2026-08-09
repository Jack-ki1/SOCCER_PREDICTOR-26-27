"""
API-Football client — secondary/backup live source (see build plan §2).
Free tier is only 100 requests/day, so this is for cross-checking or
filling gaps FPL's API doesn't cover, not for regular polling. Requires
API_FOOTBALL_KEY (config/api_settings.py, env-driven) — every function
here raises clearly if it's unset rather than silently no-op'ing.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from config.api_settings import (
    API_FOOTBALL_BASE_URL, API_FOOTBALL_DAILY_LIMIT, API_FOOTBALL_KEY, API_FOOTBALL_REQUEST_TIMEOUT,
)
from config.settings import API_CACHE_DIR
from data.api_client import ApiClientError, get_json, is_cached

PREMIER_LEAGUE_ID = 39  # API-Football's numeric league id for the EPL
_USAGE_FILE = API_CACHE_DIR / "api_football_usage.json"


class ApiFootballError(ApiClientError):
    pass


class ApiFootballQuotaError(ApiFootballError):
    pass


def _require_key() -> None:
    if not API_FOOTBALL_KEY:
        raise ApiFootballError("API_FOOTBALL_KEY isn't set — see config/api_settings.py / your .env file")


def _today_usage() -> int:
    if not _USAGE_FILE.exists():
        return 0
    try:
        data = json.loads(_USAGE_FILE.read_text())
        return data.get(str(date.today()), 0)
    except (json.JSONDecodeError, OSError):
        return 0


def _record_usage() -> None:
    API_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    if _USAGE_FILE.exists():
        try:
            data = json.loads(_USAGE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            data = {}
    key = str(date.today())
    data[key] = data.get(key, 0) + 1
    _USAGE_FILE.write_text(json.dumps(data))


def _self_throttled_get(path: str, params: dict | None = None, cache_key: str | None = None) -> dict:
    """Refuses to call the API once today's usage hits the free-tier daily limit,
    rather than letting the account get rate-limited or (on some plans) billed."""
    _require_key()
    will_hit_cache = cache_key is not None and is_cached(cache_key, ttl_seconds=600)
    if not will_hit_cache and _today_usage() >= API_FOOTBALL_DAILY_LIMIT:
        raise ApiFootballQuotaError(
            f"API-Football daily free-tier limit ({API_FOOTBALL_DAILY_LIMIT} requests) reached — "
            "wait until tomorrow (UTC) or upgrade your plan."
        )
    try:
        data = get_json(
            f"{API_FOOTBALL_BASE_URL}{path}", params=params,
            headers={"x-apisports-key": API_FOOTBALL_KEY},
            timeout=API_FOOTBALL_REQUEST_TIMEOUT, cache_key=cache_key, cache_ttl_seconds=600,
        )
    except ApiClientError as exc:
        raise ApiFootballError(str(exc)) from exc
    if not will_hit_cache:
        _record_usage()  # only count real network calls against the quota, not cache hits
    return data


def get_fixtures(season_year: int, from_date: datetime | None = None, to_date: datetime | None = None) -> list[dict]:
    params = {"league": PREMIER_LEAGUE_ID, "season": season_year}
    if from_date:
        params["from"] = from_date.strftime("%Y-%m-%d")
    if to_date:
        params["to"] = to_date.strftime("%Y-%m-%d")
    data = _self_throttled_get("/fixtures", params=params, cache_key=f"apif-fixtures-{season_year}")
    return data.get("response", [])


def get_standings(season_year: int) -> list[dict]:
    data = _self_throttled_get(
        "/standings", params={"league": PREMIER_LEAGUE_ID, "season": season_year},
        cache_key=f"apif-standings-{season_year}",
    )
    return data.get("response", [])


def remaining_quota_today() -> int:
    return max(0, API_FOOTBALL_DAILY_LIMIT - _today_usage())
