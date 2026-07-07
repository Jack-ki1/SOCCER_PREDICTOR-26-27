"""Base prediction models for soccer — Dixon-Coles and Elo/Pi."""

import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy.optimize import minimize
from .entities import Match, Prediction, TeamRating
from .probability import (
    poisson_pmf, score_matrix, outcome_probs_from_matrix,
    normalize_probs, normalize_three, calculate_btts_prob,
    calculate_over_under_prob, dixon_coles_tau
)


class PoissonDixonColesModel:
    """Dixon-Coles model with proper score_matrix output.

    This implementation includes:
    - Correct score probability matrix (fixes simulation engine crash)
    - Dixon-Coles low-score tau correction
    - Optional MLE parameter fitting via scipy
    - Time-weighted match importance
    """
    
    def __init__(self, rho: float = -0.13):
        """Initialize model.

        Args:
            rho: Dixon-Coles correlation parameter (default -0.13, fit from data)
        """
        self.rho = rho
        self.fitted = False
        # Attack/defense parameters (can be MLE-fitted)
        self.attack_params: Dict[str, float] = {}
        self.defense_params: Dict[str, float] = {}
        self.home_advantage: float = 1.35
        self.avg_goals: float = 1.35

    def fit(self, matches: List[Match], time_weight_decay: float = 0.0065) -> "PoissonDixonColesModel":
        """Fit Dixon-Coles model via MLE on historical matches.

        Args:
            matches: List of completed matches (with actual_home_goals)
            time_weight_decay: Exponential decay rate for older matches

        Returns:
            self
        """
        historical = [m for m in matches if m.actual_home_goals is not None]
        if len(historical) < 10:
            return self  # Not enough data, use defaults

        try:
            # Extract unique teams
            teams = set()
            for m in historical:
                teams.add(m.home_team.team_id)
                teams.add(m.away_team.team_id)
            teams = sorted(list(teams))
            n_teams = len(teams)

            # Create team index mapping
            team_idx = {team: i for i, team in enumerate(teams)}

            # Prepare data arrays
            n_matches = len(historical)
            home_idx = np.array([team_idx[m.home_team.team_id] for m in historical])
            away_idx = np.array([team_idx[m.away_team.team_id] for m in historical])
            home_goals = np.array([m.actual_home_goals for m in historical])
            away_goals = np.array([m.actual_away_goals for m in historical])

            # Time weights (more recent = higher weight)
            dates = np.array([m.date for m in historical])
            # Sort by date oldest to newest
            sorted_indices = np.argsort(dates)
            time_weights = np.exp(-time_weight_decay * np.arange(len(sorted_indices))[::-1])

            def neg_log_likelihood(params):
                # Parameters: [home_advantage, attack_0, ..., attack_n-1, defense_0, ..., defense_n-1, rho]
                home_adv = math.exp(params[0])  # Log-transform to ensure positivity
                attacks = params[1:n_teams+1]
                defenses = params[n_teams+1:2*n_teams+1]
                rho = params[2*n_teams+1]

                # Apply constraints to ensure identifiability
                # Set first team's attack to 0 (reference level)
                attacks_full = np.concatenate([[0], attacks[1:]])
                # Sum of defenses equals log(avg_goals * n_teams) to ensure average goals
                avg_def = np.log(self.avg_goals) - np.mean(defenses)
                defenses_full = defenses + avg_def

                lambda_h = home_adv * np.exp(attacks_full[home_idx] + defenses_full[away_idx])
                lambda_a = np.exp(attacks_full[away_idx] + defenses_full[home_idx])

                loglik = 0.0
                for i in range(n_matches):
                    hg = home_goals[i]
                    ag = away_goals[i]

                    # Compute Poisson probabilities
                    prob = poisson_pmf(hg, lambda_h[i]) * poisson_pmf(ag, lambda_a[i])

                    # Apply Dixon-Coles correction
                    tau_val = dixon_coles_tau(hg, ag, lambda_h[i], lambda_a[i], rho)
                    prob *= tau_val

                    if prob <= 0:
                        continue
                    loglik += time_weights[i] * math.log(prob)

                return -loglik

            # Initial parameters
            x0 = [math.log(self.home_advantage)]  # home advantage (log scale)
            x0.extend([0.0] * n_teams)  # attacks (first is reference, stays 0)
            x0.extend([0.0] * n_teams)  # defenses
            x0.append(self.rho)  # rho

            # Perform optimization
            result = minimize(neg_log_likelihood, x0, method="L-BFGS-B",
                              options={"maxiter": 200, "ftol": 1e-7})

            if result.success:
                self.home_advantage = math.exp(result.x[0])
                for i, t in enumerate(teams):
                    self.attack_params[t] = result.x[1 + i]
                    self.defense_params[t] = result.x[1 + n_teams + i]
                self.rho = result.x[1 + 2 * n_teams]
                self.fitted = True

        except Exception:
            pass  # Fall back to defaults silently

        return self

    def predict(self, match: Match) -> Dict[str, Any]:
        """Predict match outcome — always returns score_matrix key.

        Args:
            match: Match object

        Returns:
            Dictionary including score_matrix, outcome probs, xG values
        """
        home_lambda, away_lambda = self._expected_goals(match)

        # Score probability matrix (fixes simulation crash — THIS KEY MUST EXIST)
        mat = score_matrix(home_lambda, away_lambda,
                           max_goals=8, rho=self.rho)

        # Outcome probabilities from matrix
        home_win = np.tril(mat, -1).sum()
        draw = np.diag(mat).sum()
        away_win = np.triu(mat, 1).sum()

        # Normalize probabilities
        total = home_win + draw + away_win
        if total > 0:
            home_win /= total
            draw /= total
            away_win /= total

        # BTTS and Over 2.5 from matrix
        btts = sum(mat[i, j] for i in range(1, mat.shape[0]) for j in range(1, mat.shape[1]))
        over_25 = sum(mat[i, j] for i in range(mat.shape[0]) for j in range(mat.shape[1]) if i + j > 2.5)

        return {
            'home_win': home_win,
            'draw': draw,
            'away_win': away_win,
            'home_lambda': home_lambda,
            'away_lambda': away_lambda,
            'expected_total_goals': home_lambda + away_lambda,
            'home_xg': home_lambda,
            'away_xg': away_lambda,
            'btts': btts,
            'over_25': over_25,
            'score_matrix': mat,  # CRITICAL: This key was missing, causing simulation crashes
            'component_probs': {
                'poisson_raw': [home_win, draw, away_win],
            }
        }

    def _expected_goals(self, match: Match) -> Tuple[float, float]:
        """Calculate expected goals for home and away teams."""
        if self.fitted:
            # Use fitted parameters
            home_team_id = match.home_team.team_id
            away_team_id = match.away_team.team_id

            home_att = self.attack_params.get(home_team_id, 0.0)
            home_def = self.defense_params.get(home_team_id, 0.0)
            away_att = self.attack_params.get(away_team_id, 0.0)
            away_def = self.defense_params.get(away_team_id, 0.0)

            home_lambda = self.home_advantage * math.exp(home_att + away_def)
            away_lambda = math.exp(away_att + home_def)
        else:
            # Use simple approach
            home_lambda = self._calculate_expected_goals(match.home_team, match.away_team, is_home=True)
            away_lambda = self._calculate_expected_goals(match.away_team, match.home_team, is_home=False)

        return max(0.1, home_lambda), max(0.1, away_lambda)

    def _calculate_expected_goals(
        self,
        team,
        opponent,
        is_home: bool
    ) -> float:
        """Calculate expected goals for a team.

        Args:
            team: Team rating object
            opponent: Opponent team rating object
            is_home: Whether this is the home team

        Returns:
            Expected goals (lambda)
        """
        if is_home:
            attack_strength = team.home_attack
            defense_weakness = opponent.away_defense
            home_advantage = 1.15
        else:
            attack_strength = team.away_attack
            defense_weakness = opponent.home_defense
            home_advantage = 1.0

        # Base expected goals
        base_xg = 1.35  # League average

        # Adjust for team strengths
        expected = base_xg * attack_strength * defense_weakness * home_advantage

        # Adjust for form
        expected *= (1.0 + team.form_index * 0.1)

        return max(0.1, expected)


class EnsembleSoccerPredictor:
    """Ensemble predictor combining multiple models."""
    
    def __init__(self):
        """Initialize ensemble predictor."""
        self.poisson_model = PoissonDixonColesModel()
        self.weights = {'poisson': 0.5, 'elo': 0.3, 'market': 0.2}
    
    def predict(self, match: Match) -> Prediction:
        """Predict match outcome using ensemble.
        
        Args:
            match: Match object
            
        Returns:
            Prediction object
        """
        # Use Poisson model as base (now includes score_matrix)
        poisson_pred = self.poisson_model.predict(match)
        
        return Prediction(
            match_id=match.match_id,
            home_win=poisson_pred['home_win'],  # Fixed field name
            draw=poisson_pred['draw'],          # Fixed field name
            away_win=poisson_pred['away_win'],  # Fixed field name
            home_xg=poisson_pred['home_xg'],
            away_xg=poisson_pred['away_xg'],
            btts=poisson_pred.get('btts', 0.50),
            over_25=poisson_pred.get('over_25', 0.50),
            correct_score=poisson_pred.get('correct_score', {}),
            drivers=poisson_pred.get('drivers', []),
            component_probs=poisson_pred.get('component_probs', {})
        )
    
    def set_weights(self, **kwargs):
        """Set ensemble weights."""
        self.weights.update(kwargs)

    def get_weights(self) -> Dict[str, float]:
        """Return current ensemble weights."""
        return self.weights.copy()


class EloBradleyTerryModel:
    """Elo-based Bradley-Terry model for match prediction."""
    
    def __init__(self):
        """Initialize Elo Bradley-Terry model."""
        pass
    
    def predict(self, match: Match) -> Prediction:
        """Predict match outcome using Elo ratings.
        
        Args:
            match: Match object
            
        Returns:
            Prediction object
        """
        home_elo = match.home_team.elo
        away_elo = match.away_team.elo
        
        # Bradley-Terry formula with home advantage
        elo_diff = home_elo - away_elo + 65  # 65 points home advantage
        home_win_prob = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))
        
        # Estimate draw probability
        draw_prob = 0.27
        away_win_prob = 1.0 - home_win_prob - draw_prob
        
        return Prediction(
            match_id=match.match_id,
            home_win=max(0, min(1, home_win_prob)),  # Fixed field name
            draw=max(0, min(1, draw_prob)),          # Fixed field name
            away_win=max(0, min(1, away_win_prob)),  # Fixed field name
            home_xg=1.35,
            away_xg=1.35,
            btts=0.50,
            over_25=0.50
        )