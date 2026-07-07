"""Model Arena for comparing different prediction models."""

from typing import Dict, List, Optional
from .entities import Match


class ModelArena:
    """Compare and evaluate multiple prediction models."""
    
    def __init__(self):
        """Initialize model arena."""
        self.models = {}
        self.results = {}
    
    def register_model(self, name: str, model):
        """Register a model for comparison.
        
        Args:
            name: Model name
            model: Model instance
        """
        self.models[name] = model
    
    def compare_models(self, match: Match) -> Dict[str, Dict]:
        """Compare all registered models on a match.
        
        Args:
            match: Match to predict
            
        Returns:
            Dictionary of predictions by model
        """
        predictions = {}
        for name, model in self.models.items():
            try:
                pred = model.predict(match)
                predictions[name] = {
                    'home_win': getattr(pred, 'home_win_prob', 0.33),
                    'draw': getattr(pred, 'draw_prob', 0.34),
                    'away_win': getattr(pred, 'away_win_prob', 0.33)
                }
            except Exception as e:
                predictions[name] = {'error': str(e)}
        
        return predictions
    
    def get_model_performance(self) -> Dict:
        """Get performance metrics for all models.
        
        Returns:
            Dictionary of model performance metrics
        """
        return {
            name: {'status': 'registered'}
            for name in self.models.keys()
        }
