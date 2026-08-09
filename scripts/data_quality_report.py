"""
CLI: quick health check on what's actually in the database vs what's
expected — row counts, staleness, missing data. Run this before trusting
any report/prediction if you're not sure ingestion has been running.

Usage: python scripts/data_quality_report.py
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.constants import SEASON, TEAMS  # noqa: E402
from database.connection import session_scope  # noqa: E402
from database.models import Club, ClubSeasonRating, Fixture, Prediction  # noqa: E402


def main():
    with session_scope() as session:
        club_count = session.query(Club).count()
        rating_count = session.query(ClubSeasonRating).count()
        fixture_count = session.query(Fixture).filter_by(season=SEASON).count()
        finished_count = session.query(Fixture).filter_by(season=SEASON, finished=True).count()
        prediction_count = session.query(Prediction).count()

        latest_rating = (
            session.query(ClubSeasonRating)
            .order_by(ClubSeasonRating.as_of_date.desc())
            .first()
        )
        # Pull everything needed out of the ORM object now — it becomes
        # detached (unusable) the moment session_scope()'s `with` block exits.
        latest_rating_info = (
            {"as_of_date": latest_rating.as_of_date, "source": latest_rating.source}
            if latest_rating else None
        )
        rating_sources = {r[0] for r in session.query(ClubSeasonRating.source).distinct().all()}

    print("=== Data quality report ===")
    print(f"Clubs in DB: {club_count} (expect {len(TEAMS)})")
    print(f"Fixtures for {SEASON}: {fixture_count} (expect up to 380 once fully loaded, 10 for Matchweek 1 only)")
    print(f"Finished fixtures: {finished_count}")
    print(f"Rating rows: {rating_count}, from sources: {sorted(rating_sources) or 'none'}")
    print(f"Logged predictions: {prediction_count}")

    if latest_rating_info:
        age_hours = (datetime.now(timezone.utc) - latest_rating_info["as_of_date"].replace(tzinfo=timezone.utc)).total_seconds() / 3600
        print(f"Most recent rating snapshot: {latest_rating_info['as_of_date']} ({age_hours:.1f}h ago, source={latest_rating_info['source']})")
        if age_hours > 48 and "fpl_seed" not in rating_sources:
            print("⚠ No live (fpl_seed) ratings found and illustrative data is >48h old by this check's clock — "
                  "run data/live_updater.refresh_live_state() or scripts/migrate_db.py.")
    else:
        print("⚠ No ratings found at all — run scripts/migrate_db.py first.")

    if club_count == 0:
        print("\n⚠ Database looks empty. Run: python scripts/migrate_db.py")


if __name__ == "__main__":
    main()
