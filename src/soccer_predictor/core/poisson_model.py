"""Poisson distribution model for soccer score prediction."""

import numpy as np
from typing import Dict, List, Tuple
from .probability import poisson_pmf, calculate_over_under_prob, calculate_btts_prob


class PoissonModel:
    """Poisson-based goal prediction model."""
    
    def __init__(self):
        """Initialize Poisson model."""
        pass
    
    def calculate_expected_goals(
        self,
        home_attack: float,
        home_defense: float,
        away_attack: float,
        away_defense: float,
        league_avg: float = 2.7
    ) -> Tuple[float, float]:
        """Calculate expected goals for both teams.
        
        Args:
            home_attack: Home team attack strength
            home_defense: Home team defense strength (goals conceded)
            away_attack: Away team attack strength
            away_defense: Away team defense strength (goals conceded)
            league_avg: League average total goals
            
        Returns:
            Tuple of (home_lambda, away_lambda)
        """
        # Base expected goals from attack/defense strengths
        home_lambda = (home_attack + away_defense) / 2.0
        away_lambda = (away_attack + home_defense) / 2.0
        
        # Adjust to match league average
        total = home_lambda + away_lambda
        if total > 0:
            adjustment = league_avg / total
            home_lambda *= adjustment
            away_lambda *= adjustment
        
        # Apply home advantage (typically +0.3 to +0.5 goals)
        home_lambda *= 1.15
        
        return max(0.1, home_lambda), max(0.1, away_lambda)
    
    def predict_match_outcome(
        self,
        home_lambda: float,
        away_lambda: float,
        max_goals: int = 10
    ) -> Dict[str, float]:
        """Predict match outcome probabilities.
        
        Args:
            home_lambda: Home team expected goals
            away_lambda: Away team expected goals
            max_goals: Maximum goals to consider
            
        Returns:
            Dictionary with home_win, draw, away_win probabilities
        """
        home_win = 0.0
        draw = 0.0
        away_win = 0.0
        
        for h in range(max_goals):
            for a in range(max_goals):
                prob = poisson_pmf(h, home_lambda) * poisson_pmf(a, away_lambda)
                
                if h > a:
                    home_win += prob
                elif h == a:
                    draw += prob
                else:
                    away_win += prob
        
        # Normalize
        total = home_win + draw + away_win
        if total > 0:
            home_win /= total
            draw /= total
            away_win /= total
        
        return {
            'home_win': home_win,
            'draw': draw,
            'away_win': away_win
        }
    
    def predict_exact_scores(
        self,
        home_lambda: float,
        away_lambda: float,
        top_n: int = 5,
        max_goals: int = 8
    ) -> List[Dict[str, any]]:
        """Predict most likely exact scores.
        
        Args:
            home_lambda: Home team expected goals
            away_lambda: Away team expected goals
            top_n: Number of top scorelines to return
            max_goals: Maximum goals to consider
            
        Returns:
            List of dictionaries with score and probability
        """
        scores = []
        
        for h in range(max_goals):
            for a in range(max_goals):
                prob = poisson_pmf(h, home_lambda) * poisson_pmf(a, away_lambda)
                scores.append({
                    'home_goals': h,
                    'away_goals': a,
                    'scoreline': f"{h}-{a}",
                    'probability': prob
                })
        
        # Sort by probability and return top N
        scores.sort(key=lambda x: x['probability'], reverse=True)
        return scores[:top_n]
    
    def calculate_over_under_probabilities(
        self,
        home_lambda: float,
        away_lambda: float,
        threshold: float = 2.5
    ) -> Dict[str, float]:
        """Calculate over/under probabilities.
        
        Args:
            home_lambda: Home team expected goals
            away_lambda: Away team expected goals
            threshold: Goal threshold
            
        Returns:
            Dictionary with over and under probabilities
        """
        return calculate_over_under_prob(home_lambda, away_lambda, threshold)
    
    def calculate_both_teams_to_score(
        self,
        home_lambda: float,
        away_lambda: float
    ) -> Dict[str, float]:
        """Calculate BTTS (Both Teams To Score) probability.
        
        Args:
            home_lambda: Home team expected goals
            away_lambda: Away team expected goals
            
        Returns:
            Dictionary with yes/no probabilities
        """
        btts_yes = calculate_btts_prob(home_lambda, away_lambda)
        btts_no = 1.0 - btts_yes
        
        return {
            'yes': btts_yes,
            'no': btts_no
        }


def integrate_with_elo(
    home_elo: float,
    away_elo: float,
    home_lambda: float,
    away_lambda: float,
    elo_weight: float = 0.3
) -> Tuple[float, float]:
    """Integrate Elo ratings with Poisson expected goals.
    
    Args:
        home_elo: Home team Elo rating
        away_elo: Away team Elo rating
        home_lambda: Home team Poisson lambda
        away_lambda: Away team Poisson lambda
        elo_weight: Weight given to Elo adjustment (0-1)
        
    Returns:
        Adjusted (home_lambda, away_lambda)
    """
    # Calculate Elo-based expected goal differential
    elo_diff = home_elo - away_elo
    elo_xg_delta = elo_diff * 0.0008  # Scale factor
    
    # Current goal differential from Poisson
    current_diff = home_lambda - away_lambda
    
    # Blend the two
    blended_diff = (1 - elo_weight) * current_diff + elo_weight * elo_xg_delta
    
    # Preserve total goals but adjust differential
    total_goals = home_lambda + away_lambda
    new_home_lambda = (total_goals + blended_diff) / 2.0
    new_away_lambda = (total_goals - blended_diff) / 2.0
    
    return max(0.1, new_home_lambda), max(0.1, new_away_lambda)
