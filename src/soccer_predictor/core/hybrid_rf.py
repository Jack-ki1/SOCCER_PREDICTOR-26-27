"""Hybrid Random Forest for goal prediction.

Predicts expected goals (xG) from aggregated match abilities, then plugs into
independent Poisson distributions for outcome probabilities.
Based on: "Hybrid Random Forests for Goal Prediction in Soccer" (2026).
"""

import numpy as np
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from .entities import Match, Prediction, TeamRating
from .probability import normalize_probs, poisson_pmf
from .features import build_match_features


@dataclass
class HybridRandomForestPredictor:
    """Two-stage model: RF -> xG -> Poisson outcomes."""
    n_estimators: int = 300
    max_depth: int = 15
    min_samples_leaf: int = 5

    home_xg_model: Optional[Any] = field(default=None, repr=False)
    away_xg_model: Optional[Any] = field(default=None, repr=False)
    outcome_model: Optional[Any] = field(default=None, repr=False)
    scaler: Optional[StandardScaler] = field(default=None, repr=False)
    feature_names: List[str] = field(default_factory=list)
    fitted: bool = False

    def __post_init__(self):
        if self.home_xg_model is None:
            self.home_xg_model = RandomForestRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                min_samples_leaf=self.min_samples_leaf,
                random_state=42,
                n_jobs=-1,
            )
        if self.away_xg_model is None:
            self.away_xg_model = RandomForestRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                min_samples_leaf=self.min_samples_leaf,
                random_state=43,
                n_jobs=-1,
            )
        if self.outcome_model is None:
            self.outcome_model = RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                min_samples_leaf=self.min_samples_leaf,
                random_state=44,
                n_jobs=-1,
            )

    def fit(self, matches: List[Match]):
        """Train on historical matches."""
        X_list, y_home, y_away, y_outcome = [], [], [], []

        for match in matches:
            if match.actual_home_goals is None or match.actual_away_goals is None:
                continue

            feats = build_match_features(match)
            if not self.feature_names:
                self.feature_names = list(feats.keys())

            X_list.append([feats[k] for k in self.feature_names])
            y_home.append(match.actual_home_goals)
            y_away.append(match.actual_away_goals)
            y_outcome.append(match.actual_result)

        if not X_list:
            return self

        X = np.array(X_list)
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.home_xg_model.fit(X_scaled, y_home)
        self.away_xg_model.fit(X_scaled, y_away)
        self.outcome_model.fit(X_scaled, y_outcome)

        self.fitted = True
        return self

    def predict(self, match: Match) -> Dict[str, Any]:
        """Predict xG and outcomes for a single match."""
        if not self.fitted or self.scaler is None:
            # Fallback to simple Poisson
            return self._fallback_prediction(match)

        feats = build_match_features(match)
        X = np.array([[feats[k] for k in self.feature_names]])
        X_scaled = self.scaler.transform(X)

        # Predict xG
        home_xg = max(self.home_xg_model.predict(X_scaled)[0], 0.1)
        away_xg = max(self.away_xg_model.predict(X_scaled)[0], 0.1)

        # Predict direct outcomes
        outcome_probs = self.outcome_model.predict_proba(X_scaled)[0]

        # Also derive from Poisson xG for markets
        max_goals = 8
        matrix = np.zeros((max_goals + 1, max_goals + 1))
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                matrix[i, j] = poisson_pmf(i, home_xg) * poisson_pmf(j, away_xg)

        matrix /= matrix.sum()

        home_win = np.tril(matrix, -1).sum()
        draw = np.diag(matrix).sum()
        away_win = np.triu(matrix, 1).sum()
        
        # FIXED: normalize_probs expects a dictionary, not positional arguments
        norm_probs = normalize_probs({'home_win': home_win, 'draw': draw, 'away_win': away_win})
        home_win, draw, away_win = norm_probs['home_win'], norm_probs['draw'], norm_probs['away_win']

        # Blend: 70% direct RF, 30% Poisson-derived
        blended_home = 0.7 * outcome_probs[0] + 0.3 * home_win
        blended_draw = 0.7 * outcome_probs[1] + 0.3 * draw
        blended_away = 0.7 * outcome_probs[2] + 0.3 * away_win
        
        # Normalize blended probabilities
        total = blended_home + blended_draw + blended_away
        if total > 0:
            blended_home /= total
            blended_draw /= total
            blended_away /= total

        # BTTS and Over 2.5 from Poisson
        btts = sum(matrix[i, j] for i in range(1, max_goals + 1) 
                   for j in range(1, max_goals + 1))
        over_25 = sum(matrix[i, j] for i in range(max_goals + 1) 
                      for j in range(max_goals + 1) if i + j > 2.5)

        # Top correct scores
        scores = []
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                scores.append((f"{i}-{j}", matrix[i, j]))
        scores.sort(key=lambda x: x[1], reverse=True)

        return {
            "home_win": blended_home,
            "draw": blended_draw,
            "away_win": blended_away,
            "home_xg": home_xg,
            "away_xg": away_xg,
            "btts": btts,
            "over_25": over_25,
            "correct_score": {s: p for s, p in scores[:10]},
            "component_probs": {
                "rf_direct": outcome_probs.tolist(),
                "poisson_derived": [home_win, draw, away_win],
            }
        }

    def _fallback_prediction(self, match: Match) -> Dict[str, Any]:
        """Simple fallback when model not trained."""
        from .model import PoissonDixonColesModel
        return PoissonDixonColesModel().predict(match)

    def get_feature_importance(self) -> Dict[str, float]:
        """Return aggregated feature importance."""
        if not self.fitted:
            return {}

        # Average importance across home_xg, away_xg, and outcome models
        imp_home = self.home_xg_model.feature_importances_
        imp_away = self.away_xg_model.feature_importances_
        imp_outcome = self.outcome_model.feature_importances_

        avg_imp = (imp_home + imp_away + imp_outcome) / 3

        if self.feature_names and len(self.feature_names) == len(avg_imp):
            return dict(zip(self.feature_names, avg_imp))
        return {f"feat_{i}": v for i, v in enumerate(avg_imp)}


# Alias for backward compatibility
HybridRFModel = HybridRandomForestPredictor