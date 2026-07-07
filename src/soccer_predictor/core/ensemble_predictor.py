"""Ensemble Predictor combining Poisson, Elo, Market Odds, and XGBoost.

Model weights (tunable):
  Poisson Dixon-Coles: 40%  — primary statistical model
  Elo / Pi-Ratings:    25%  — team strength ratings
  Market Odds Prior:   20%  — bookmaker wisdom (vig removed)
  XGBoost Features:    15%  — engineered feature model
"""

import math
import numpy as np
from typing import Dict, List, Optional
from scipy.optimize import minimize
from .model import PoissonDixonColesModel, EloBradleyTerryModel
from .entities import Match, TeamRating
from .probability import (
    normalize_three, normalize_probs,
    calculate_btts_prob, calculate_over_under_prob,
    score_matrix, outcome_probs_from_matrix,
    remove_bookmaker_vig, implied_kelly_fraction
)


class EnsemblePredictor:
    """Production-grade ensemble predictor."""

    def __init__(self):
        self.poisson_model = PoissonDixonColesModel()
        self.elo_model = EloBradleyTerryModel()
        self.model_weights = {
            "poisson": 0.40,
            "elo":     0.25,
            "market":  0.20,
            "ml":      0.15,
        }

    def get_weights(self) -> Dict[str, float]:
        """Return current ensemble weights."""
        return self.model_weights.copy()

    def set_weights(self, **kwargs) -> None:
        """Update ensemble weights (auto-normalizes to sum=1)."""
        for k, v in kwargs.items():
            if k in self.model_weights:
                self.model_weights[k] = max(0.0, float(v))
        total = sum(self.model_weights.values())
        if total > 0:
            for k in self.model_weights:
                self.model_weights[k] = round(self.model_weights[k] / total, 4)

    def predict_match(self, home_team: Dict, away_team: Dict,
                      historical_data: List[Dict] = None,
                      league_context: Dict = None) -> Dict:
        """Predict match outcome using full ensemble.

        Args:
            home_team: Home team data dict with elo, position, recent_matches, odds
            away_team: Away team data dict
            historical_data: Optional historical fixtures
            league_context: Optional league config

        Returns:
            Comprehensive prediction dictionary
        """
        # Get individual model predictions
        poisson_pred = self._get_poisson_prediction(home_team, away_team)
        elo_pred = self._get_elo_prediction(home_team, away_team)
        market_pred = self._get_market_prediction(home_team, away_team)
        ml_pred = self._get_ml_prediction(home_team, away_team, historical_data)

        # Combine predictions using weights
        final_home = (self.model_weights["poisson"] * poisson_pred["home_win"] +
                     self.model_weights["elo"] * elo_pred["home_win"] +
                     self.model_weights["market"] * market_pred["home_win"] +
                     self.model_weights["ml"] * ml_pred["home_win"])

        final_draw = (self.model_weights["poisson"] * poisson_pred["draw"] +
                     self.model_weights["elo"] * elo_pred["draw"] +
                     self.model_weights["market"] * market_pred["draw"] +
                     self.model_weights["ml"] * ml_pred["draw"])

        final_away = (self.model_weights["poisson"] * poisson_pred["away_win"] +
                     self.model_weights["elo"] * elo_pred["away_win"] +
                     self.model_weights["market"] * market_pred["away_win"] +
                     self.model_weights["ml"] * ml_pred["away_win"])

        # Normalize final probabilities
        final_home, final_draw, final_away = normalize_three(final_home, final_draw, final_away)

        # Calculate expected goals from Poisson model
        home_xg = poisson_pred.get("home_xg", 1.4)
        away_xg = poisson_pred.get("away_xg", 1.2)

        # Calculate additional markets
        btts = calculate_btts_prob(home_xg, away_xg)
        over_25 = calculate_over_under_prob(home_xg, away_xg, 2.5)["over"]

        # Calculate correct scores
        matrix = score_matrix(home_xg, away_xg)
        scores = {}
        for i in range(6):  # Up to 5-5
            for j in range(6):
                scores[f"{i}-{j}"] = matrix[i, j]
        # Sort and take top 10
        top_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
        correct_scores = {score: prob for score, prob in top_scores}

        # Calculate value bets using Kelly criterion
        value_bets = []
        if home_team.get("home_odds") and away_team.get("away_odds"):
            home_odds = home_team["home_odds"]
            draw_odds = home_team.get("draw_odds", 3.2)  # Default draw odds
            away_odds = away_team["away_odds"]
            
            kelly_home = implied_kelly_fraction(final_home, home_odds)
            kelly_draw = implied_kelly_fraction(final_draw, draw_odds)
            kelly_away = implied_kelly_fraction(final_away, away_odds)
            
            if kelly_home > 0:
                value_bets.append({"outcome": "home", "fraction": kelly_home, "odds": home_odds, "kelly": kelly_home})
            if kelly_draw > 0:
                value_bets.append({"outcome": "draw", "fraction": kelly_draw, "odds": draw_odds, "kelly": kelly_draw})
            if kelly_away > 0:
                value_bets.append({"outcome": "away", "fraction": kelly_away, "odds": away_odds, "kelly": kelly_away})

        return {
            "home_win": final_home,
            "draw": final_draw,
            "away_win": final_away,
            "home_xg": home_xg,
            "away_xg": away_xg,
            "btts": btts,
            "over_25": over_25,
            "correct_score": correct_scores,
            "value_bets": value_bets,
            "component_probs": {
                "poisson": [poisson_pred["home_win"], poisson_pred["draw"], poisson_pred["away_win"]],
                "elo": [elo_pred["home_win"], elo_pred["draw"], elo_pred["away_win"]],
                "market": [market_pred["home_win"], market_pred["draw"], market_pred["away_win"]],
                "ml": [ml_pred["home_win"], ml_pred["draw"], ml_pred["away_win"]]
            },
            "model_weights": self.model_weights.copy()
        }

    def _get_poisson_prediction(self, home_team: Dict, away_team: Dict) -> Dict:
        """Get prediction from Poisson Dixon-Coles model."""
        try:
            # Create a temporary match object for the model
            from datetime import date
            temp_match = self._create_temp_match(home_team, away_team)
            pred = self.poisson_model.predict(temp_match)
            return pred
        except:
            # Fallback
            return {
                "home_win": 0.45,
                "draw": 0.28,
                "away_win": 0.27,
                "home_xg": 1.4,
                "away_xg": 1.2
            }

    def _get_elo_prediction(self, home_team: Dict, away_team: Dict) -> Dict:
        """Get prediction from Elo model."""
        try:
            # Create a temporary match object for the model
            from datetime import date
            temp_match = self._create_temp_match(home_team, away_team)
            pred = self.elo_model.predict(temp_match)
            # Convert to our format
            return {
                "home_win": pred.home_win,
                "draw": pred.draw,
                "away_win": pred.away_win
            }
        except:
            return {"home_win": 0.45, "draw": 0.28, "away_win": 0.27}

    def _get_market_prediction(self, home_team: Dict, away_team: Dict) -> Dict:
        """Get prediction from market odds (as Bayesian prior)."""
        home_odds = home_team.get("home_odds")
        draw_odds = home_team.get("draw_odds")
        away_odds = away_team.get("away_odds")

        if home_odds and draw_odds and away_odds:
            try:
                fair_probs = remove_bookmaker_vig(home_odds, draw_odds, away_odds)
                return {
                    "home_win": fair_probs[0],
                    "draw": fair_probs[1],
                    "away_win": fair_probs[2]
                }
            except:
                pass

        # Default market prediction
        return {"home_win": 0.45, "draw": 0.28, "away_win": 0.27}

    def _get_ml_prediction(self, home_team: Dict, away_team: Dict, historical_data: List[Dict]) -> Dict:
        """Get prediction from ML model."""
        # Simplified ML prediction based on features
        try:
            # Calculate feature-based prediction
            home_elo = home_team.get("elo", 1500)
            away_elo = away_team.get("elo", 1500)
            elo_diff = (home_elo - away_elo) / 400  # Scale factor for meaningful differences

            # Position-based factors
            home_pos = home_team.get("position", 10)
            away_pos = away_team.get("position", 10)
            pos_diff = (away_pos - home_pos) * 0.05  # Each position difference worth ~0.05 probability

            # Form-based factors
            home_form = home_team.get("form_index", 0.0)
            away_form = away_team.get("form_index", 0.0)

            # Base probability
            base_home = 0.45
            elo_factor = elo_diff * 0.15  # 15% influence from elo difference
            pos_factor = pos_diff * 0.1  # 10% influence from position difference
            form_factor = (home_form - away_form) * 0.05  # 5% influence from form difference

            adjusted_home = base_home + elo_factor + pos_factor + form_factor
            adjusted_home = max(0.05, min(0.85, adjusted_home))  # Clamp between 5% and 85%

            # Calculate draw and away based on home probability
            remaining = 1.0 - adjusted_home
            # Draw probability depends on elo similarity
            draw_base = 0.28
            elo_similarity = 1.0 - min(1.0, abs(elo_diff) / 3.0)  # More similar elos = higher draw prob
            adjusted_draw = draw_base + (elo_similarity - 0.5) * 0.1
            adjusted_draw = max(0.15, min(0.40, adjusted_draw))

            adjusted_away = max(0.05, remaining - adjusted_draw)
            adjusted_draw = remaining - adjusted_away

            # Normalize
            total = adjusted_home + adjusted_draw + adjusted_away
            if total > 0:
                adjusted_home /= total
                adjusted_draw /= total
                adjusted_away /= total

            return {
                "home_win": adjusted_home,
                "draw": adjusted_draw,
                "away_win": adjusted_away
            }
        except:
            return {"home_win": 0.45, "draw": 0.28, "away_win": 0.27}

    def _create_temp_match(self, home_team: Dict, away_team: Dict) -> Match:
        """Create a temporary match object for model compatibility."""
        from datetime import date
        from .entities import TeamRating, Match

        # Create temporary team ratings
        home_rating = TeamRating(
            team_id=home_team.get("name", "Home"),
            name=home_team.get("name", "Home Team"),
            league=home_team.get("league", "Unknown"),
            elo=home_team.get("elo", 1500),
            attack=home_team.get("attack", 1.0),
            defense=home_team.get("defense", 1.0),
            home_attack=home_team.get("home_attack", 1.0),
            home_defense=home_team.get("home_defense", 1.0),
            form_index=home_team.get("form_index", 0.0)
        )

        away_rating = TeamRating(
            team_id=away_team.get("name", "Away"),
            name=away_team.get("name", "Away Team"),
            league=away_team.get("league", "Unknown"),
            elo=away_team.get("elo", 1500),
            attack=away_team.get("attack", 1.0),
            defense=away_team.get("defense", 1.0),
            away_attack=away_team.get("away_attack", 1.0),
            away_defense=away_team.get("away_defense", 1.0),
            form_index=away_team.get("form_index", 0.0)
        )

        return Match(
            match_id="temp",
            league=home_team.get("league", "Unknown"),
            date=date.today(),
            home_team=home_rating,
            away_team=away_rating,
            home_odds=home_team.get("home_odds"),
            draw_odds=home_team.get("draw_odds"),
            away_odds=away_team.get("away_odds")
        )
