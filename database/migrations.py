"""
Migrations.

For a fresh base template, SQLAlchemy's `Base.metadata.create_all()`
(called from `init_db()` in connection.py) is enough — it creates any
tables that don't exist yet and leaves existing ones alone. That's what
`scripts/migrate_db.py` calls.

This module additionally seeds the clubs table and the real Matchweek 1
fixtures on first run, since the dashboard is useless without them and
re-deriving them by hand every time you set up a new environment is
exactly the kind of thing that should be automated.

**Once the schema needs a real change** (adding a column to an existing
table, changing a type, etc.), `create_all()` isn't enough — at that point,
introduce Alembic (`pip install alembic`, `alembic init alembic`) and let
its autogenerate diff the models against the live DB. This file's `seed()`
function keeps working either way.
"""
from __future__ import annotations

from datetime import datetime, timezone

from config.constants import REAL_MATCHWEEK_1, SEASON, TEAMS
from database.connection import init_db, session_scope
from database.models import Club, ClubSeasonRating, Fixture


def run_migrations() -> None:
    """Create any missing tables. Idempotent — safe to call on every boot."""
    init_db()


def seed(force: bool = False) -> dict:
    """
    Populate clubs + illustrative ratings + Matchweek 1 fixtures if the DB
    is empty. Pass force=True to re-seed even if clubs already exist
    (existing rows are left alone; this only adds what's missing).
    """
    summary = {"clubs_added": 0, "ratings_added": 0, "fixtures_added": 0}
    with session_scope() as session:
        existing_club_ids = {c.id for c in session.query(Club).all()}

        for t in TEAMS:
            if t["id"] in existing_club_ids and not force:
                continue
            if t["id"] not in existing_club_ids:
                session.add(Club(
                    id=t["id"], name=t["name"], short_name=t["short"], color_hex=t["color"],
                ))
                summary["clubs_added"] += 1

            session.add(ClubSeasonRating(
                club_id=t["id"], season=SEASON, as_of_date=datetime.now(timezone.utc),
                attack_rating=t["attack"], defense_rating=t["defense"], home_advantage=t["home_adv"],
                source="illustrative_seed",
            ))
            summary["ratings_added"] += 1

        session.flush()

        existing_fixture_pairs = {
            (f.home_club_id, f.away_club_id) for f in session.query(Fixture).filter_by(matchweek=1).all()
        }
        for home, away in REAL_MATCHWEEK_1:
            if (home, away) in existing_fixture_pairs and not force:
                continue
            session.add(Fixture(
                season=SEASON, matchweek=1, home_club_id=home, away_club_id=away,
                is_confirmed=True,
            ))
            summary["fixtures_added"] += 1

    return summary
