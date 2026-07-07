"""Bayesian optimization for ensemble weights using Optuna.

Automatically tunes model weights to minimize Brier Score and maximize accuracy.
Inspired by F1 Predictor 2026's weight optimization system.
"""

import optuna
from typing import Dict, List, Tuple, Optional
import numpy as np
from datetime import datetime


class WeightOptimizer:
    """
    Optimizes ensemble model weights using Bayesian optimization (Optuna).
    
    Objective: Minimize Brier Score while maintaining good calibration.
    """
    
    def __init__(self, n_trials: int = 100):
        """
        Initialize optimizer.
        
        Args:
            n_trials: Number of optimization trials to run
        """
        self.n_trials = n_trials
        self.best_weights = None
        self.best_score = float('inf')
        self.optimization_history = []
    
    def optimize_weights(self, 
                        predictions: List[Dict],
                        actual_results: List[Dict],
                        current_weights: Dict[str, float] = None) -> Dict[str, float]:
        """
        Optimize ensemble weights to minimize Brier Score.
        
        Args:
            predictions: List of prediction dictionaries with component probabilities
            actual_results: List of actual match results
            current_weights: Current weights as starting point
        
        Returns:
            Optimized weights dictionary
        """
        def objective(trial):
            """Optuna objective function."""
            # Suggest weights for each model
            w_poisson = trial.suggest_float('poisson', 0.0, 1.0)
            w_elo = trial.suggest_float('elo', 0.0, 1.0)
            w_ml = trial.suggest_float('ml', 0.0, 1.0)
            w_market = trial.suggest_float('market', 0.0, 1.0)
            
            # Normalize weights to sum to 1
            total = w_poisson + w_elo + w_ml + w_market
            if total == 0:
                return float('inf')
            
            weights = {
                'poisson': w_poisson / total,
                'elo': w_elo / total,
                'ml': w_ml / total,
                'market': w_market / total
            }
            
            # Calculate Brier Score with these weights
            brier_score = self._calculate_weighted_brier_score(
                predictions, actual_results, weights
            )
            
            # Store trial info
            trial.set_user_attr('weights', weights)
            trial.set_user_attr('brier_score', brier_score)
            
            return brier_score
        
        # Create study
        study = optuna.create_study(
            direction='minimize',
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        
        # Run optimization
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)
        
        # Extract best weights
        self.best_weights = study.best_trial.user_attrs['weights']
        self.best_score = study.best_value
        self.optimization_history = [
            {
                'trial': t.number,
                'brier_score': t.value,
                'weights': t.user_attrs.get('weights', {})
            }
            for t in study.trials
        ]
        
        return self.best_weights
    
    def _calculate_weighted_brier_score(self,
                                       predictions: List[Dict],
                                       actual_results: List[Dict],
                                       weights: Dict[str, float]) -> float:
        """
        Calculate Brier Score for given weights.
        
        Args:
            predictions: List of predictions with component probabilities
            actual_results: List of actual outcomes
            weights: Model weights to apply
        
        Returns:
            Brier Score
        """
        squared_errors = []
        
        for pred, result in zip(predictions, actual_results):
            # Get component probabilities
            components = pred.get('component_probs', {})
            
            # Calculate weighted probability
            home_prob = (
                weights['poisson'] * components.get('poisson', [0.45, 0.28, 0.27])[0] +
                weights['elo'] * components.get('elo', [0.45, 0.28, 0.27])[0] +
                weights['ml'] * components.get('ml', [0.45, 0.28, 0.27])[0] +
                weights['market'] * components.get('market', [0.45, 0.28, 0.27])[0]
            )
            
            draw_prob = (
                weights['poisson'] * components.get('poisson', [0.45, 0.28, 0.27])[1] +
                weights['elo'] * components.get('elo', [0.45, 0.28, 0.27])[1] +
                weights['ml'] * components.get('ml', [0.45, 0.28, 0.27])[1] +
                weights['market'] * components.get('market', [0.45, 0.28, 0.27])[1]
            )
            
            away_prob = (
                weights['poisson'] * components.get('poisson', [0.45, 0.28, 0.27])[2] +
                weights['elo'] * components.get('elo', [0.45, 0.28, 0.27])[2] +
                weights['ml'] * components.get('ml', [0.45, 0.28, 0.27])[2] +
                weights['market'] * components.get('market', [0.45, 0.28, 0.27])[2]
            )
            
            # Normalize
            total = home_prob + draw_prob + away_prob
            if total > 0:
                home_prob /= total
                draw_prob /= total
                away_prob /= total
            
            # Calculate squared error based on actual outcome
            actual_outcome = result.get('outcome')  # 'home', 'draw', or 'away'
            
            if actual_outcome == 'home':
                squared_error = (1 - home_prob)**2 + (0 - draw_prob)**2 + (0 - away_prob)**2
            elif actual_outcome == 'draw':
                squared_error = (0 - home_prob)**2 + (1 - draw_prob)**2 + (0 - away_prob)**2
            elif actual_outcome == 'away':
                squared_error = (0 - home_prob)**2 + (0 - draw_prob)**2 + (1 - away_prob)**2
            else:
                continue
            
            squared_errors.append(squared_error)
        
        # Return mean Brier Score
        return np.mean(squared_errors) if squared_errors else float('inf')
    
    def get_optimization_report(self) -> Dict:
        """
        Generate optimization report.
        
        Returns:
            Dictionary with optimization results
        """
        return {
            'best_weights': self.best_weights,
            'best_brier_score': self.best_score,
            'n_trials': len(self.optimization_history),
            'optimization_history': self.optimization_history[-10:],  # Last 10 trials
            'timestamp': datetime.utcnow().isoformat()
        }


def suggest_initial_weights(method: str = 'balanced') -> Dict[str, float]:
    """
    Suggest initial weights based on strategy.
    
    Args:
        method: Strategy ('balanced', 'poisson_focused', 'ml_focused', 'market_focused')
    
    Returns:
        Initial weights dictionary
    """
    strategies = {
        'balanced': {
            'poisson': 0.40,
            'elo': 0.25,
            'ml': 0.20,
            'market': 0.15
        },
        'poisson_focused': {
            'poisson': 0.60,
            'elo': 0.20,
            'ml': 0.10,
            'market': 0.10
        },
        'ml_focused': {
            'poisson': 0.25,
            'elo': 0.20,
            'ml': 0.40,
            'market': 0.15
        },
        'market_focused': {
            'poisson': 0.20,
            'elo': 0.20,
            'ml': 0.15,
            'market': 0.45
        }
    }
    
    return strategies.get(method, strategies['balanced'])
