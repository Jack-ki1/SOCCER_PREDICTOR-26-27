"""
Fixture calendar for the 2026/27 season.

Matchweek 1 is the real confirmed opening round. Matchweeks 2-38 are a
generated double round-robin standing in for the staged official release —
see engine/monte_carlo.py's generate_schedule(). Swap get_fixtures() to
read from the database (populated by data/fpl_client.py) once real
fixtures are flowing in; the shape returned here matches what that will
look like, so nothing downstream needs to change.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from config.constants import KICKOFF_UTC, TEAMS_BY_ID
from engine.monte_carlo import ALL_FIXTURES, Fixture


def week_of(matchweek: int) -> datetime:
    """Indicative date for a matchweek — real broadcaster-confirmed kickoff times
    are only released in stages through the season, per the actual PL release pattern."""
    return KICKOFF_UTC + timedelta(days=(matchweek - 1) * 7)


def get_fixtures(matchweek: int | None = None) -> list[dict]:
    fixtures = ALL_FIXTURES if matchweek is None else [f for f in ALL_FIXTURES if f.round == matchweek]
    return [_serialize(f) for f in fixtures]


def _serialize(f: Fixture) -> dict:
    home, away = TEAMS_BY_ID[f.home], TEAMS_BY_ID[f.away]
    return {
        "round": f.round,
        "home_id": f.home, "away_id": f.away,
        "home_name": home["name"], "away_name": away["name"],
        "is_confirmed": f.round == 1,
        "week_of": week_of(f.round).isoformat(),
    }


def total_matchweeks() -> int:
    return max(f.round for f in ALL_FIXTURES)


def fixtures_for_club(club_id: str) -> list[dict]:
    return [_serialize(f) for f in ALL_FIXTURES if f.home == club_id or f.away == club_id]
