"""
CLI: after a matchweek finishes, back-fill each prediction's
was_correct_1x2 flag (database/models.py's Prediction table) by comparing
against the real result. Run this after data/live_updater.py has synced
the finished scores.

Usage: python scripts/post_match_evaluation.py --matchweek 1
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import session_scope  # noqa: E402
from database.models import Fixture, Prediction  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matchweek", type=int, required=True)
    parser.add_argument("--season", default=None)
    args = parser.parse_args()

    updated = 0
    with session_scope() as session:
        query = session.query(Fixture).filter_by(matchweek=args.matchweek, finished=True)
        if args.season:
            query = query.filter_by(season=args.season)
        fixtures = query.all()

        for fx in fixtures:
            actual = "H" if fx.home_goals > fx.away_goals else "A" if fx.home_goals < fx.away_goals else "D"
            predictions = session.query(Prediction).filter_by(fixture_id=fx.id).all()
            for pred in predictions:
                predicted = max(
                    [("H", pred.p_home), ("D", pred.p_draw), ("A", pred.p_away)],
                    key=lambda x: x[1],
                )[0]
                pred.was_correct_1x2 = predicted == actual
                updated += 1

    print(f"Evaluated {updated} prediction(s) for matchweek {args.matchweek}.")
    if updated == 0:
        print("Nothing to evaluate — either no finished fixtures this matchweek, or no predictions were logged for them.")


if __name__ == "__main__":
    main()
