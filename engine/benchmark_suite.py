"""
Walk-forward backtesting suite.

This is the discipline described in the build plan §6.3, made runnable:
never shuffle-split football results, because they're time-ordered and a
random split leaks future information into "predicting" the past. Train
on seasons 1..N, test on N+1, roll forward.

Every baseline listed here should be beaten, in order, before you trust a
more complex model:
    1. "Always predict home win" — surprisingly hard to beat by much
    2. Dixon-Coles alone
    3. Bookmaker-implied probabilities, if you have odds data

scripts/measure_accuracy.py is the CLI entrypoint that calls this against
real historical data once data/soccerdata_integration.py is wired up.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class BacktestResult:
    label: str
    n_matches: int
    accuracy: float
    log_loss: float
    brier_score: float


def _log_loss(probs: list[dict], outcomes: list[str], eps: float = 1e-12) -> float:
    total = 0.0
    for p, y in zip(probs, outcomes):
        total += -np.log(max(p.get(y, eps), eps))
    return total / len(outcomes)


def _brier(probs: list[dict], outcomes: list[str]) -> float:
    """Multi-class Brier score: mean squared error across all three outcome probabilities, not just the winner."""
    total = 0.0
    for p, y in zip(probs, outcomes):
        for cls in ("H", "D", "A"):
            actual = 1.0 if y == cls else 0.0
            total += (p.get(cls, 0.0) - actual) ** 2
    return total / (len(outcomes) * 3)


def evaluate_predictions(probs: list[dict], outcomes: list[str], label: str = "model") -> BacktestResult:
    """
    probs: list of {'H': p, 'D': p, 'A': p} dicts, one per match.
    outcomes: list of 'H'/'D'/'A' actual results, same order/length.
    """
    if len(probs) != len(outcomes) or not probs:
        raise ValueError("probs and outcomes must be the same non-zero length")

    correct = sum(1 for p, y in zip(probs, outcomes) if max(p, key=p.get) == y)
    return BacktestResult(
        label=label,
        n_matches=len(outcomes),
        accuracy=correct / len(outcomes),
        log_loss=_log_loss(probs, outcomes),
        brier_score=_brier(probs, outcomes),
    )


def home_win_baseline(outcomes: list[str]) -> BacktestResult:
    """The baseline every model must beat first: always predict a home win."""
    probs = [{"H": 1.0, "D": 0.0, "A": 0.0} for _ in outcomes]
    return evaluate_predictions(probs, outcomes, label="always_home_win")


@dataclass
class WalkForwardReport:
    per_season: list[BacktestResult] = field(default_factory=list)
    baseline_per_season: list[BacktestResult] = field(default_factory=list)

    def beats_baseline(self) -> bool:
        """True only if the model beats the home-win baseline in every tested season, not just on average —
        a model that's great in easy seasons and bad in hard ones isn't actually reliable."""
        return all(m.accuracy > b.accuracy for m, b in zip(self.per_season, self.baseline_per_season))

    def summary(self) -> dict:
        return {
            "seasons_tested": len(self.per_season),
            "avg_accuracy": np.mean([r.accuracy for r in self.per_season]) if self.per_season else None,
            "avg_log_loss": np.mean([r.log_loss for r in self.per_season]) if self.per_season else None,
            "beats_home_win_baseline_every_season": self.beats_baseline(),
        }


def walk_forward_backtest(
    seasons: list[str],
    predict_fn,
    outcomes_by_season: dict[str, list[str]],
    probs_by_season: dict[str, list[dict]],
) -> WalkForwardReport:
    """
    Generic walk-forward harness. `predict_fn` isn't called directly here —
    by design, this function takes already-generated predictions per
    season (probs_by_season) so the actual model training/prediction logic
    stays in scripts/measure_accuracy.py, which knows how to build a
    proper train/test split per season without this module needing to
    know about data sources at all. This keeps benchmark_suite.py testable
    with synthetic data (see tests/test_benchmark_suite.py) independent of
    whether real historical data is loaded.
    """
    report = WalkForwardReport()
    for season in seasons:
        outcomes = outcomes_by_season[season]
        probs = probs_by_season[season]
        report.per_season.append(evaluate_predictions(probs, outcomes, label=f"model_{season}"))
        report.baseline_per_season.append(home_win_baseline(outcomes))
    return report
