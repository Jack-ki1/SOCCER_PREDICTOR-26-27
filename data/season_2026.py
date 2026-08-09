"""
In-progress season state — results as they're played, read from/written to
the database (database/models.py's Fixture table). This is what
data/live_updater.py updates as gameweeks complete, and what
dashboard/api_routes.py reads for "current form" once the season has
actual results (as opposed to config/constants.py's static illustrative
form arrays, which only cover last season's closing stretch).
"""
from __future__ import annotations

from database.connection import session_scope
from database.models import Fixture


def record_result(fixture_db_id: int, home_goals: int, away_goals: int) -> None:
    with session_scope() as session:
        fixture = session.get(Fixture, fixture_db_id)
        if fixture is None:
            raise ValueError(f"No fixture with id {fixture_db_id}")
        fixture.home_goals = home_goals
        fixture.away_goals = away_goals
        fixture.finished = True


def finished_fixtures(season: str) -> list[dict]:
    with session_scope() as session:
        rows = session.query(Fixture).filter_by(season=season, finished=True).all()
        return [
            {
                "id": r.id, "matchweek": r.matchweek,
                "home_id": r.home_club_id, "away_id": r.away_club_id,
                "home_goals": r.home_goals, "away_goals": r.away_goals,
            }
            for r in rows
        ]


def current_form(season: str, club_id: str, last_n: int = 5) -> list[str]:
    """
    'W'/'D'/'L' sequence from the club's last N finished matches this
    season, most recent last — matches the shape config/constants.py's
    illustrative `form` arrays already use, so this is a drop-in
    replacement once there's enough real season data (roughly matchweek 5+).
    """
    with session_scope() as session:
        rows = (
            session.query(Fixture)
            .filter(Fixture.season == season, Fixture.finished == True)  # noqa: E712
            .filter((Fixture.home_club_id == club_id) | (Fixture.away_club_id == club_id))
            .order_by(Fixture.matchweek.desc())
            .limit(last_n)
            .all()
        )
    results = []
    for r in reversed(rows):
        is_home = r.home_club_id == club_id
        team_goals = r.home_goals if is_home else r.away_goals
        opp_goals = r.away_goals if is_home else r.home_goals
        if team_goals > opp_goals:
            results.append("W")
        elif team_goals == opp_goals:
            results.append("D")
        else:
            results.append("L")
    return results
