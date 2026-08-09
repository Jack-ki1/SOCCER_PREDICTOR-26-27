"""
CLI: measure the current engine's accuracy against real finished fixtures
in the database, and against the "always predict home win" baseline.

Usage: python scripts/measure_accuracy.py [--season 2026-27]

Note: this only has something to measure once fixtures have actual
results (database/models.py's Fixture.finished=True) — early in a season,
or before real data ingestion is wired up, it'll correctly report "no
finished fixtures yet" rather than fabricating a number.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.constants import SEASON  # noqa: E402
from data.season_2026 import finished_fixtures  # noqa: E402
from engine.benchmark_suite import evaluate_predictions, home_win_baseline  # noqa: E402
from engine.predictor import get_prediction  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default=SEASON)
    args = parser.parse_args()

    fixtures = finished_fixtures(args.season)
    if not fixtures:
        print(f"No finished fixtures found for {args.season} yet — nothing to measure.")
        print("This is expected pre-season; run again once results start coming in via data/live_updater.py.")
        return

    probs, outcomes = [], []
    for fx in fixtures:
        pred = get_prediction(fx["home_id"], fx["away_id"])
        probs.append({"H": pred.market.p_home, "D": pred.market.p_draw, "A": pred.market.p_away})
        result = "H" if fx["home_goals"] > fx["away_goals"] else "A" if fx["home_goals"] < fx["away_goals"] else "D"
        outcomes.append(result)

    model_result = evaluate_predictions(probs, outcomes, label="dixon_coles_v1")
    baseline_result = home_win_baseline(outcomes)

    print(f"\n=== Accuracy report — {args.season} ({len(outcomes)} finished fixtures) ===")
    print(f"Model:    accuracy={model_result.accuracy:.1%}  log_loss={model_result.log_loss:.3f}  brier={model_result.brier_score:.3f}")
    print(f"Baseline: accuracy={baseline_result.accuracy:.1%}  log_loss={baseline_result.log_loss:.3f}  brier={baseline_result.brier_score:.3f}")
    beats = model_result.accuracy > baseline_result.accuracy
    print(f"\nModel beats 'always home win' baseline: {beats}")
    if not beats:
        print("⚠ This is worth investigating before trusting the model's predictions further.")


if __name__ == "__main__":
    main()
