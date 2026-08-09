"""
CLI: grid-search engine/config/feature_weights.py's tunable weights against
real finished fixtures, reporting which combination minimizes log-loss.

Usage: python scripts/optimize_weights.py [--season 2026-27]

This is intentionally a small grid search, not a heavy optimizer — with
only a season's worth of fixtures to validate against, a fine-grained
search would just be overfitting noise. Widen the grid once you have
multiple seasons of real results (see scripts/fetch_historical_data.py).
"""
import argparse
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.constants import SEASON  # noqa: E402
from config.feature_weights import get_weights  # noqa: E402
from data.season_2026 import finished_fixtures  # noqa: E402
from engine.benchmark_suite import evaluate_predictions  # noqa: E402
from engine.predictor import get_prediction  # noqa: E402

HOME_ADV_GRID = [40, 55, 70]
FORM_WEIGHT_GRID = [30, 50, 70]
RHO_GRID = [-0.20, -0.11, -0.02]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default=SEASON)
    args = parser.parse_args()

    fixtures = finished_fixtures(args.season)
    if not fixtures:
        print("No finished fixtures yet — nothing to optimize against.")
        return

    outcomes = [
        "H" if fx["home_goals"] > fx["away_goals"] else "A" if fx["home_goals"] < fx["away_goals"] else "D"
        for fx in fixtures
    ]

    results = []
    for haw, fw, rho in itertools.product(HOME_ADV_GRID, FORM_WEIGHT_GRID, RHO_GRID):
        weights = get_weights({"home_advantage_weight": haw, "recent_form_weight": fw, "dixon_coles_rho": rho})
        probs = []
        for fx in fixtures:
            pred = get_prediction(fx["home_id"], fx["away_id"], weights)
            probs.append({"H": pred.market.p_home, "D": pred.market.p_draw, "A": pred.market.p_away})
        r = evaluate_predictions(probs, outcomes, label=f"haw={haw} fw={fw} rho={rho}")
        results.append((r.log_loss, haw, fw, rho, r.accuracy))

    results.sort()
    print(f"\n=== Weight grid search — {len(fixtures)} fixtures, {len(results)} combinations ===")
    print(f"{'log_loss':>10} {'accuracy':>10} {'home_adv':>10} {'form_wt':>10} {'rho':>8}")
    for log_loss, haw, fw, rho, acc in results[:10]:
        print(f"{log_loss:>10.4f} {acc:>9.1%} {haw:>10} {fw:>10} {rho:>8.2f}")

    best = results[0]
    print(f"\nBest: home_advantage_weight={best[1]}, recent_form_weight={best[2]}, dixon_coles_rho={best[3]}")
    print("Update config/feature_weights.py's DEFAULT_WEIGHTS if this consistently wins across more data.")


if __name__ == "__main__":
    main()
