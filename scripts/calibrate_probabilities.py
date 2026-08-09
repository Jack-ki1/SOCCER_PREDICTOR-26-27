"""
CLI: fit and evaluate probability calibration against real finished
fixtures. See engine/calibration.py for the methodology (isotonic
regression / Platt scaling).

Usage: python scripts/calibrate_probabilities.py [--season 2026-27] [--method isotonic]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.constants import SEASON  # noqa: E402
from data.season_2026 import finished_fixtures  # noqa: E402
from engine.calibration import evaluate_calibration  # noqa: E402
from engine.predictor import get_prediction  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default=SEASON)
    parser.add_argument("--method", default="isotonic", choices=["isotonic", "platt"])
    args = parser.parse_args()

    fixtures = finished_fixtures(args.season)
    if len(fixtures) < 20:
        print(f"Only {len(fixtures)} finished fixtures — calibration needs at least ~20 to be meaningful.")
        print("Run again once more of the season has been played.")
        return

    raw_home_probs, home_win_outcomes = [], []
    for fx in fixtures:
        pred = get_prediction(fx["home_id"], fx["away_id"])
        raw_home_probs.append(pred.market.p_home)
        home_win_outcomes.append(1 if fx["home_goals"] > fx["away_goals"] else 0)

    result = evaluate_calibration(raw_home_probs, home_win_outcomes, method=args.method)
    print(f"\n=== Calibration report ({args.method}, {len(fixtures)} fixtures) ===")
    print(f"Brier score before calibration: {result.brier_score_before:.4f}")
    print(f"Brier score after calibration:  {result.brier_score_after:.4f}")
    improved = result.brier_score_after < result.brier_score_before
    print(f"Improved: {improved}")
    if not improved:
        print("⚠ Calibration didn't help on this sample — may need more data, or the raw probabilities are already well-calibrated.")


if __name__ == "__main__":
    main()
