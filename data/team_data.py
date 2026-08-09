"""
Club roster + metadata. Thin accessor layer over config/constants.py's
TEAMS — kept as its own module (rather than importing config.constants
directly everywhere) so that once club data starts coming from the
database (database/models.py's Club table) instead of the hardcoded
illustrative list, only this file needs to change.
"""
from __future__ import annotations

from config.constants import TEAMS, TEAMS_BY_ID


def get_all_teams() -> list[dict]:
    return TEAMS


def get_team(team_id: str) -> dict | None:
    return TEAMS_BY_ID.get(team_id)


def get_team_by_short_name(short: str) -> dict | None:
    short = short.upper()
    return next((t for t in TEAMS if t["short"] == short), None)


def promoted_teams() -> list[dict]:
    """The three clubs with no top-flight form yet — form=None is how config/constants.py marks this."""
    return [t for t in TEAMS if t["form"] is None]
