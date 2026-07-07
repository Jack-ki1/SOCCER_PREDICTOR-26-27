"""Feature engineering module for match prediction."""

from typing import Dict
from ..core.entities import Match, TeamRating
import numpy as np


def build_match_features(match: Match) -> Dict[str, float]:
    """Build features for ML models based on match data.
    
    Args:
        match: Match object containing teams, date, and other info
        
    Returns:
        Dictionary of features for ML models
    """
    # This is a simplified implementation - in a real system this would be more complex
    features = {}
    
    # Elo-based features
    features['elo_diff'] = getattr(match.home_team_rating, 'overall_elo', 1500) - getattr(match.away_team_rating, 'overall_elo', 1500)
    features['home_elo'] = getattr(match.home_team_rating, 'overall_elo', 1500)
    features['away_elo'] = getattr(match.away_team_rating, 'overall_elo', 1500)
    
    # Attack/Defense strength features
    features['home_attack'] = getattr(match.home_team_rating, 'attack_strength', 1.0)
    features['home_defense'] = getattr(match.home_team_rating, 'defense_strength', 1.0)
    features['away_attack'] = getattr(match.away_team_rating, 'attack_strength', 1.0)
    features['away_defense'] = getattr(match.away_team_rating, 'defense_strength', 1.0)
    
    # Home advantage features
    features['home_advantage'] = 0.1  # Placeholder value
    
    # Form features
    features['home_form'] = getattr(match.home_team_rating, 'form_index', 1.0)
    features['away_form'] = getattr(match.away_team_rating, 'form_index', 1.0)
    
    # xG features (if available)
    features['home_avg_xg'] = getattr(match.home_team_rating, 'avg_xg_for', 1.2)
    features['away_avg_xg'] = getattr(match.away_team_rating, 'avg_xg_against', 1.2)
    
    # Market value features (if available)
    features['home_market_value'] = getattr(match.home_team_rating, 'market_value', 50.0)
    features['away_market_value'] = getattr(match.away_team_rating, 'market_value', 50.0)
    
    # Date-based features
    features['day_of_week'] = match.date.weekday() if hasattr(match, 'date') and match.date else 0
    features['is_weekend'] = 1 if features['day_of_week'] in [5, 6] else 0  # Sat/Sun
    
    # Head-to-head record (if available)
    features['h2h_recent_home_wins'] = getattr(match, 'h2h_home_wins', 0)
    features['h2h_recent_draws'] = getattr(match, 'h2h_draws', 0)
    features['h2h_recent_away_wins'] = getattr(match, 'h2h_away_wins', 0)
    
    # Placeholder for additional features that might be calculated
    # These would typically come from more complex analysis of historical data
    features['recent_momentum_home'] = getattr(match.home_team_rating, 'momentum', 0.0)
    features['recent_momentum_away'] = getattr(match.away_team_rating, 'momentum', 0.0)
    
    # Weather and venue factors (if available)
    features['weather_impact'] = getattr(match, 'weather_factor', 0.0)
    features['venue_neutral'] = getattr(match, 'is_neutral_venue', False)
    
    return features


def extract_team_features(team_rating: TeamRating) -> Dict[str, float]:
    """Extract individual team features.
    
    Args:
        team_rating: TeamRating object
        
    Returns:
        Dictionary of team-specific features
    """
    features = {
        'elo': getattr(team_rating, 'overall_elo', 1500),
        'attack_strength': getattr(team_rating, 'attack_strength', 1.0),
        'defense_strength': getattr(team_rating, 'defense_strength', 1.0),
        'form_index': getattr(team_rating, 'form_index', 1.0),
        'reliability': getattr(team_rating, 'reliability_index', 1.0),
        'matches_played': getattr(team_rating, 'matches_played', 0),
    }
    
    # Add specialized ratings if available
    if hasattr(team_rating, 'set_piece_offense'):
        features['set_piece_offense'] = team_rating.set_piece_offense
    if hasattr(team_rating, 'counter_attack_efficiency'):
        features['counter_attack_efficiency'] = team_rating.counter_attack_efficiency
    if hasattr(team_rating, 'high_pressure_performance'):
        features['high_pressure_performance'] = team_rating.high_pressure_performance
        
    return features