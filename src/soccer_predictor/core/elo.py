"""Elo rating system adapted for soccer."""

import numpy as np
from typing import Dict


def expected_score(rating_a: float, rating_b: float, home_advantage: float = 65.0) -> float:
    """Expected score for team A (home) vs team B."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - (rating_a + home_advantage)) / 400.0))


def update_elo(
    rating: float,
    opponent_rating: float,
    actual_score: float,
    k_factor: float = 32.0,
    home_advantage: float = 0.0,
) -> float:
    """Update Elo rating after a match."""
    expected = expected_score(rating + home_advantage, opponent_rating, home_advantage=0.0)
    return rating + k_factor * (actual_score - expected)


def elo_to_xg_delta(elo_diff: float, scale: float = 0.0008) -> float:
    """Convert Elo difference to expected goal differential."""
    return elo_diff * scale


class EloSystem:
    """Elo rating system manager for teams."""
    
    def __init__(self, initial_rating: float = 1500.0, k_factor: float = 32.0):
        """Initialize Elo system.
        
        Args:
            initial_rating: Starting Elo rating for new teams
            k_factor: K-factor for rating updates
        """
        self.initial_rating = initial_rating
        self.k_factor = k_factor
        self.ratings: Dict[str, float] = {}
    
    def get_rating(self, team_id: str) -> float:
        """Get current Elo rating for a team.
        
        Args:
            team_id: Team identifier
            
        Returns:
            Current Elo rating
        """
        return self.ratings.get(team_id, self.initial_rating)
    
    def update_rating(
        self,
        team_id: str,
        opponent_id: str,
        result: str,
        is_home: bool = True
    ) -> float:
        """Update team's Elo rating after a match.
        
        Args:
            team_id: Team identifier
            opponent_id: Opponent team identifier
            result: Match result ('win', 'draw', 'loss')
            is_home: Whether team was playing at home
            
        Returns:
            New Elo rating
        """
        current_rating = self.get_rating(team_id)
        opponent_rating = self.get_rating(opponent_id)
        
        # Determine actual score
        if result == 'win':
            actual_score = 1.0
        elif result == 'draw':
            actual_score = 0.5
        else:  # loss
            actual_score = 0.0
        
        # Apply home advantage
        home_advantage = 65.0 if is_home else 0.0
        
        # Calculate new rating
        new_rating = update_elo(
            current_rating,
            opponent_rating,
            actual_score,
            self.k_factor,
            home_advantage
        )
        
        # Store updated rating
        self.ratings[team_id] = new_rating
        
        return new_rating
    
    def calculate_win_probability(
        self,
        home_team_id: str,
        away_team_id: str
    ) -> Dict[str, float]:
        """Calculate win probabilities based on Elo ratings.
        
        Args:
            home_team_id: Home team identifier
            away_team_id: Away team identifier
            
        Returns:
            Dictionary with home_win, draw, away_win probabilities
        """
        home_elo = self.get_rating(home_team_id)
        away_elo = self.get_rating(away_team_id)
        
        # Calculate home win probability
        elo_diff = home_elo - away_elo
        home_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        
        # Adjust for home advantage
        home_advantage = 0.1
        home_win_prob += home_advantage * (1 - home_win_prob)
        
        # Estimate draw probability
        draw_prob = 0.27
        
        # Away win is remainder
        away_win_prob = 1 - home_win_prob - draw_prob
        
        return {
            'home_win': max(0, min(1, home_win_prob)),
            'draw': max(0, min(1, draw_prob)),
            'away_win': max(0, min(1, away_win_prob))
        }
