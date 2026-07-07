"""Core modules for soccer prediction."""

from .model import PoissonDixonColesModel, EloBradleyTerryModel, EnsembleSoccerPredictor
from .ensemble_predictor import EnsemblePredictor
from .hybrid_rf import HybridRandomForestPredictor, HybridRFModel
from .ml_model import GradientBoostedSoccerModel, HybridRandomForestModel
from .entities import Match, Prediction, TeamRating, LeagueForecast
from .simulation import SimulationEngine, LeagueSimulator, simulate_league
from .probability import (
    poisson_pmf, 
    normalize_probs, 
    normalize_three, 
    calculate_btts_prob, 
    calculate_over_under_prob,
    score_matrix,
    outcome_probs_from_matrix,
    dixon_coles_tau,
    remove_bookmaker_vig,
    implied_kelly_fraction
)

__all__ = [
    "PoissonDixonColesModel",
    "EloBradleyTerryModel", 
    "EnsembleSoccerPredictor",
    "EnsemblePredictor",
    "HybridRandomForestPredictor",
    "HybridRFModel",
    "GradientBoostedSoccerModel",
    "HybridRandomForestModel",
    "Match",
    "Prediction", 
    "TeamRating",
    "LeagueForecast",
    "SimulationEngine",
    "LeagueSimulator",
    "simulate_league",
    "poisson_pmf",
    "normalize_probs",
    "normalize_three", 
    "calculate_btts_prob",
    "calculate_over_under_prob",
    "score_matrix",
    "outcome_probs_from_matrix",
    "dixon_coles_tau",
    "remove_bookmaker_vig",
    "implied_kelly_fraction"
]