"""
Ensemble predictor — blends Dixon-Coles, Elo, and the ML model zoo.

Starts at 100% Dixon-Coles by default (config/feature_weights.py's
ensemble_blend) because that's the only component validated against real
data so far. Bring in Elo/ML weight only after engine/benchmark_suite.py
shows each one actually improves on the Dixon-Coles-alone baseline on
held-out seasons — see build plan §6.3. This module doesn't enforce that
discipline itself (it'll happily blend in an unvalidated model if you set
the weight), it just implements the blend; the discipline is a process
you apply via benchmark_suite.py before changing the weights.
"""
from __future__ import annotations

from dataclasses import dataclass

from config.feature_weights import DEFAULT_WEIGHTS
from engine.elo_calculator import elo_to_match_probabilities
from engine.probability_model import Prediction, predict_match


@dataclass
class EnsemblePrediction:
    p_home: float
    p_draw: float
    p_away: float
    components: dict  # {'dixon_coles': {...}, 'elo': {...}, 'ml_ensemble': {...}} — for transparency, not a black box
    dixon_coles_detail: Prediction  # the full DC prediction (lambdas, grid, BTTS/O2.5) — the ensemble
                                     # only re-blends the 1X2 numbers, everything else still comes
                                     # straight from the interpretable baseline


def _normalize(p_home: float, p_draw: float, p_away: float) -> tuple[float, float, float]:
    total = p_home + p_draw + p_away
    if total <= 0:
        return 1 / 3, 1 / 3, 1 / 3
    return p_home / total, p_draw / total, p_away / total


def predict_ensemble(
    home: dict, away: dict,
    weights: dict | None = None,
    elo_ratings: dict[str, float] | None = None,
    ml_prediction: dict[str, float] | None = None,
) -> EnsemblePrediction:
    """
    ml_prediction, if given, should be a {'H': p, 'D': p, 'A': p} dict —
    typically the output of a TrainedModel.predict_proba() from
    engine/ml_models.py, or an average across several trained models.
    Passed in rather than computed here because training/loading a model
    is a heavier operation that belongs in engine/predictor.py's
    orchestration, not repeated on every ensemble call.
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    blend = w["ensemble_blend"]

    dc = predict_match(home, away, weights)
    components = {"dixon_coles": {"H": dc.market.p_home, "D": dc.market.p_draw, "A": dc.market.p_away}}

    p_home = blend.get("dixon_coles", 1.0) * dc.market.p_home
    p_draw = blend.get("dixon_coles", 1.0) * dc.market.p_draw
    p_away = blend.get("dixon_coles", 1.0) * dc.market.p_away

    elo_weight = blend.get("elo", 0.0)
    if elo_weight > 0 and elo_ratings:
        elo_probs = elo_to_match_probabilities(
            elo_ratings.get(home["id"], 1500.0), elo_ratings.get(away["id"], 1500.0),
        )
        components["elo"] = {"H": elo_probs["p_home"], "D": elo_probs["p_draw"], "A": elo_probs["p_away"]}
        p_home += elo_weight * elo_probs["p_home"]
        p_draw += elo_weight * elo_probs["p_draw"]
        p_away += elo_weight * elo_probs["p_away"]

    ml_weight = blend.get("ml_ensemble", 0.0)
    if ml_weight > 0 and ml_prediction:
        components["ml_ensemble"] = ml_prediction
        p_home += ml_weight * ml_prediction.get("H", 0)
        p_draw += ml_weight * ml_prediction.get("D", 0)
        p_away += ml_weight * ml_prediction.get("A", 0)

    p_home, p_draw, p_away = _normalize(p_home, p_draw, p_away)

    return EnsemblePrediction(
        p_home=p_home, p_draw=p_draw, p_away=p_away,
        components=components, dixon_coles_detail=dc,
    )
