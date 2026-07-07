"""Prediction service — wraps EnhancedPredictionService for backward compatibility."""

from typing import Dict, List, Optional
from src.soccer_predictor.services.enhanced_prediction_service import EnhancedPredictionService


# Singleton instance
_instance: Optional['PredictionService'] = None


class PredictionService:
    """Wrapper for enhanced prediction service maintaining backward compatibility."""
    
    def __init__(self):
        """Initialize prediction service."""
        self.ensemble = EnhancedPredictionService()
    
    def predict_match(
        self,
        match_id: str,
        weights: Dict = None,
        use_calibration: bool = True
    ) -> Dict:
        """Predict outcome for a single match.
        
        Args:
            match_id: Unique identifier for the match
            weights: Optional ensemble weights
            use_calibration: Whether to use probability calibration
            
        Returns:
            Dictionary with prediction results
        """
        try:
            return self.ensemble.predict_match(match_id, weights=weights, use_calibration=use_calibration)
        except Exception as e:
            # Return a default prediction with error information
            return {
                'error': str(e),
                'match_id': match_id,
                'home_win': 0.33,
                'draw': 0.34,
                'away_win': 0.33,
                'home_xg': 1.3,
                'away_xg': 1.3,
                'btts': 0.5,
                'over_25': 0.5,
                'correct_score': {'1-1': 0.1, '2-1': 0.1, '1-2': 0.1},
                'drivers': ['Error occurred during prediction'],
                'component_probs': {},
                'feature_importance': {},
                'calibrated': False,
                'confidence': 0.5,
                'value_bets': []
            }
    
    def predict_batch(
        self,
        match_ids: List[str],
        weights: Dict = None
    ) -> List[Dict]:
        """Predict outcomes for multiple matches.
        
        Args:
            match_ids: List of match identifiers
            weights: Optional ensemble weights
            
        Returns:
            List of prediction dictionaries
        """
        return [self.predict_match(mid, weights=weights) for mid in match_ids]
    
    def get_feature_importance(self) -> Dict:
        """Get feature importance from the underlying models.
        
        Returns:
            Dictionary mapping feature names to importance values
        """
        try:
            return self.ensemble.get_feature_importance()
        except AttributeError:
            # Fallback if method doesn't exist
            return {}
    
    def get_weights(self) -> Dict[str, float]:
        """Get current ensemble weights.
        
        Returns:
            Dictionary of model weights
        """
        try:
            return self.ensemble.get_weights()
        except AttributeError:
            # Fallback if method doesn't exist
            return {
                "poisson": 0.40,
                "elo": 0.25,
                "market": 0.20,
                "ml": 0.15,
            }
    
    def set_weights(self, **kwargs) -> None:
        """Update ensemble weights.
        
        Args:
            **kwargs: Weight updates as keyword arguments
        """
        try:
            self.ensemble.set_weights(**kwargs)
        except AttributeError:
            # Fallback if method doesn't exist
            pass


def get_prediction_service() -> PredictionService:
    """Get or create prediction service singleton.
    
    Returns:
        PredictionService instance
    """
    global _instance
    if _instance is None:
        _instance = PredictionService()
    return _instance