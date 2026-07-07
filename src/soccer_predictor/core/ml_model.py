"""Machine learning models for soccer prediction."""

from typing import Dict, List, Optional, Any
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier

from .entities import Match, Prediction


class GradientBoostedSoccerModel:
    """Gradient Boosting model for soccer prediction."""
    
    def __init__(self):
        """Initialize GBM model."""
        self.model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.fitted = False
    
    def predict(self, match: Match) -> Prediction:
        """Predict match outcome.
        
        Args:
            match: Match object
            
        Returns:
            Prediction object
        """
        # Placeholder implementation
        return Prediction(
            match_id=match.match_id,
            home_win=0.45,    # FIXED: was home_win_prob (wrong field name)
            draw=0.28,
            away_win=0.27,
            home_xg=1.35,
            away_xg=1.35,
            btts=0.50,
            over_25=0.50
        )


class HybridRandomForestModel:
    """Hybrid Random Forest model (alias for compatibility)."""
    
    def __init__(self):
        """Initialize hybrid RF model."""
        self.model = RandomForestClassifier(
            n_estimators=300,
            max_depth=15,
            random_state=42
        )
        self.fitted = False
    
    def predict(self, match: Match) -> Prediction:
        """Predict match outcome.
        
        Args:
            match: Match object
            
        Returns:
            Prediction object
        """
        # Placeholder implementation
        return Prediction(
            match_id=match.match_id,
            home_win=0.45,    # FIXED: was home_win_prob (wrong field name)
            draw=0.28,
            away_win=0.27,
            home_xg=1.35,
            away_xg=1.35,
            btts=0.50,
            over_25=0.50
        )