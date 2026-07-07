"""Probability utilities for soccer prediction models."""

import math
import numpy as np
from typing import Dict, Tuple, List


def poisson_pmf(k: int, lam: float) -> float:
    """Poisson probability mass function.
    
    Args:
        k: Number of events (goals)
        lam: Expected number of events (lambda)
        
    Returns:
        Probability of exactly k events
    """
    if lam <= 0:
        return 0.0 if k > 0 else 1.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)  # FIXED: math.factorial


def dixon_coles_tau(home_goals: int, away_goals: int,
                    home_lambda: float, away_lambda: float,
                    rho: float = -0.13) -> float:
    """Dixon-Coles low-score correction factor (tau).

    Corrects for underestimation of draws (0-0, 1-0, 0-1, 1-1).

    Args:
        home_goals: Home goals scored
        away_goals: Away goals scored
        home_lambda: Expected home goals
        away_lambda: Expected away goals
        rho: Correlation parameter (typically -0.13)

    Returns:
        Multiplicative correction factor
    """
    if home_goals == 0 and away_goals == 0:
        return 1 - home_lambda * away_lambda * rho
    elif home_goals == 1 and away_goals == 0:
        return 1 + away_lambda * rho
    elif home_goals == 0 and away_goals == 1:
        return 1 + home_lambda * rho
    elif home_goals == 1 and away_goals == 1:
        return 1 - rho
    return 1.0


def score_matrix(home_lambda: float, away_lambda: float,
                 max_goals: int = 8, rho: float = -0.13) -> np.ndarray:
    """Compute full Dixon-Coles corrected score probability matrix.

    Args:
        home_lambda: Expected home goals
        away_lambda: Expected away goals
        max_goals: Maximum goals to consider (per team)
        rho: Dixon-Coles rho parameter

    Returns:
        (max_goals+1 x max_goals+1) probability matrix
    """
    matrix = np.zeros((max_goals + 1, max_goals + 1))
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            base = poisson_pmf(h, home_lambda) * poisson_pmf(a, away_lambda)
            tau = dixon_coles_tau(h, a, home_lambda, away_lambda, rho)
            matrix[h, a] = base * tau
    total = matrix.sum()
    if total > 0:
        matrix /= total
    return matrix


def outcome_probs_from_matrix(matrix: np.ndarray) -> Dict[str, float]:
    """Extract outcome probabilities from score matrix.
    
    Args:
        matrix: Score probability matrix (home goals x away goals)
        
    Returns:
        Dictionary with home_win, draw, away_win probabilities
    """
    home_win = np.tril(matrix, -1).sum()  # Lower triangle (excluding diagonal)
    draw = np.diag(matrix).sum()          # Diagonal
    away_win = np.triu(matrix, 1).sum()   # Upper triangle (excluding diagonal)
    
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


def normalize_probs(probs: Dict[str, float]) -> Dict[str, float]:
    """Normalize probabilities to sum to 1.
    
    Args:
        probs: Dictionary of outcome probabilities
        
    Returns:
        Normalized probabilities
    """
    total = sum(probs.values())
    if total == 0:
        # Equal distribution if all zero
        n_outcomes = len(probs)
        return {k: 1.0 / n_outcomes for k in probs.keys()}
    return {k: v / total for k, v in probs.items()}


def normalize_three(home_prob: float, draw_prob: float, away_prob: float) -> tuple:
    """Normalize three probabilities to sum to 1.
    
    Args:
        home_prob: Home win probability
        draw_prob: Draw probability  
        away_prob: Away win probability
        
    Returns:
        Tuple of normalized probabilities
    """
    total = home_prob + draw_prob + away_prob
    if total == 0:
        return (1.0/3.0, 1.0/3.0, 1.0/3.0)
    return (home_prob/total, draw_prob/total, away_prob/total)


def calculate_over_under_prob(home_lambda: float, away_lambda: float, threshold: float = 2.5) -> Dict[str, float]:
    """Calculate over/under probabilities.
    
    Args:
        home_lambda: Home team expected goals
        away_lambda: Away team expected goals
        threshold: Goal threshold (default 2.5)
        
    Returns:
        Dictionary with 'over' and 'under' probabilities
    """
    total_lambda = home_lambda + away_lambda
    
    # Calculate P(X <= floor(threshold))
    under_prob = sum(poisson_pmf(k, total_lambda) for k in range(int(np.floor(threshold)) + 1))
    over_prob = 1.0 - under_prob
    
    return {
        'over': max(0.0, min(1.0, over_prob)),
        'under': max(0.0, min(1.0, under_prob))
    }


def calculate_btts_prob(home_lambda: float, away_lambda: float) -> float:
    """Calculate Both Teams To Score probability.
    
    Args:
        home_lambda: Home team expected goals
        away_lambda: Away team expected goals
        
    Returns:
        Probability both teams score at least 1 goal
    """
    # P(both score) = (1 - P(home=0)) * (1 - P(away=0))
    p_home_scores = 1.0 - poisson_pmf(0, home_lambda)
    p_away_scores = 1.0 - poisson_pmf(0, away_lambda)
    
    return p_home_scores * p_away_scores


def remove_bookmaker_vig(home_odds: float, draw_odds: float, away_odds: float) -> List[float]:
    """Remove bookmaker vig from decimal odds to get fair probabilities.
    
    Args:
        home_odds: Decimal odds for home win
        draw_odds: Decimal odds for draw
        away_odds: Decimal odds for away win
        
    Returns:
        List of fair probabilities [home, draw, away]
    """
    implied_probs = [1/home_odds, 1/draw_odds, 1/away_odds]
    overround = sum(implied_probs)
    return [p/overround for p in implied_probs]


def implied_kelly_fraction(model_prob: float, bookmaker_odds: float) -> float:
    """Calculate Kelly criterion fraction for value betting.
    
    Args:
        model_prob: Model's estimated probability
        bookmaker_odds: Decimal odds offered by bookmaker
        
    Returns:
        Optimal fraction of bankroll to bet (0.0 if no edge)
    """
    b = bookmaker_odds - 1.0  # Net odds
    edge = model_prob * b - (1.0 - model_prob)
    if edge <= 0:
        return 0.0
    return round(edge / b, 4)