"""
Probability calibration.

A model can be "accurate" (picks the right winner often) while still being
poorly *calibrated* (says 90% when it's actually right 60% of the time).
This module fits a calibration curve on top of whatever raw probabilities
come out of engine/probability_model.py or engine/ensemble_predictor.py,
using held-out (not training) results — the standard fix for the
overconfidence that raw tree-ensemble/logistic outputs are known to have.

Two standard techniques, both from scikit-learn: Platt scaling (fits a
logistic curve — good default when you don't have a lot of data) and
isotonic regression (more flexible, non-parametric, needs more data to
avoid overfitting the calibration curve itself). Isotonic is the safer
default once you have a full season or more of predictions to calibrate
against; Platt scaling is fine for the first season with thinner data.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


@dataclass
class CalibrationResult:
    method: str
    brier_score_before: float
    brier_score_after: float


def brier_score(predicted_probs: list[float], outcomes: list[int]) -> float:
    """Mean squared error between predicted probability and the binary outcome (0/1).
    Lower is better calibrated. This is the standard scoring rule for probabilistic forecasts."""
    p = np.array(predicted_probs)
    y = np.array(outcomes)
    return float(np.mean((p - y) ** 2))


class PlattCalibrator:
    def __init__(self):
        self._model = LogisticRegression()

    def fit(self, raw_probs: list[float], outcomes: list[int]) -> "PlattCalibrator":
        X = np.array(raw_probs).reshape(-1, 1)
        y = np.array(outcomes)
        self._model.fit(X, y)
        return self

    def transform(self, raw_probs: list[float]) -> list[float]:
        X = np.array(raw_probs).reshape(-1, 1)
        return self._model.predict_proba(X)[:, 1].tolist()


class IsotonicCalibrator:
    def __init__(self):
        self._model = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)

    def fit(self, raw_probs: list[float], outcomes: list[int]) -> "IsotonicCalibrator":
        self._model.fit(raw_probs, outcomes)
        return self

    def transform(self, raw_probs: list[float]) -> list[float]:
        return self._model.predict(raw_probs).tolist()


def evaluate_calibration(raw_probs: list[float], outcomes: list[int], method: str = "isotonic") -> CalibrationResult:
    """
    Fits a calibrator on (raw_probs, outcomes) and reports the Brier score
    before/after. In real use, fit on one period's predictions and evaluate
    on the next (same walk-forward discipline as model training, see build
    plan §6.3) — fitting and evaluating on the same data will always show
    improvement and tells you nothing about generalization.
    """
    before = brier_score(raw_probs, outcomes)
    calibrator = IsotonicCalibrator() if method == "isotonic" else PlattCalibrator()
    calibrator.fit(raw_probs, outcomes)
    calibrated = calibrator.transform(raw_probs)
    after = brier_score(calibrated, outcomes)
    return CalibrationResult(method=method, brier_score_before=before, brier_score_after=after)
