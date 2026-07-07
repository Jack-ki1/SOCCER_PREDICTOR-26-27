"""Monte Carlo league simulation engine."""

import numpy as np
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from .entities import Match, LeagueForecast, TeamRating
from .model import PoissonDixonColesModel


@dataclass
class SimulationEngine:
    """Monte Carlo league simulation with progress tracking."""
    model: PoissonDixonColesModel = field(default_factory=PoissonDixonColesModel)

    def simulate_league(
        self,
        matches: List[Match],
        iterations: int = 5000,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> LeagueForecast:
        """Run Monte Carlo simulation of remaining fixtures."""
        if not matches:
            return LeagueForecast(league="", season="", iterations=0)

        league = matches[0].league
        season = matches[0].season

        # Collect all teams
        teams = {}
        for m in matches:
            teams[m.home_team.team_id] = m.home_team
            teams[m.away_team.team_id] = m.away_team

        team_ids = sorted(teams.keys())
        n_teams = len(team_ids)

        # Accumulators
        points = {tid: np.zeros(iterations) for tid in team_ids}
        wins = {tid: np.zeros(iterations) for tid in team_ids}
        draws = {tid: np.zeros(iterations) for tid in team_ids}
        losses = {tid: np.zeros(iterations) for tid in team_ids}
        goals_for = {tid: np.zeros(iterations) for tid in team_ids}
        goals_against = {tid: np.zeros(iterations) for tid in team_ids}

        for iteration in range(iterations):
            # Simulate each match
            for match in matches:
                pred = self.model.predict(match)
                
                # Ensure score_matrix exists in prediction
                if "score_matrix" not in pred:
                    # Calculate score matrix from home/away lambda if not present
                    home_lambda = pred.get("home_lambda", pred.get("home_xg", 1.4))
                    away_lambda = pred.get("away_lambda", pred.get("away_xg", 1.2))
                    
                    # Create score matrix
                    max_goals = 8
                    matrix = np.zeros((max_goals + 1, max_goals + 1))
                    for h in range(max_goals + 1):
                        for a in range(max_goals + 1):
                            from .probability import poisson_pmf, dixon_coles_tau
                            base_prob = poisson_pmf(h, home_lambda) * poisson_pmf(a, away_lambda)
                            tau = dixon_coles_tau(h, a, home_lambda, away_lambda, -0.13)
                            matrix[h, a] = base_prob * tau
                    
                    total = matrix.sum()
                    if total > 0:
                        matrix /= total
                    pred["score_matrix"] = matrix

                matrix = pred["score_matrix"]

                # Sample score from matrix
                flat = matrix.flatten()
                flat = flat / flat.sum()  # Ensure normalized
                idx = np.random.choice(len(flat), p=flat)
                home_goals = idx // matrix.shape[1]
                away_goals = idx % matrix.shape[1]

                ht = match.home_team.team_id
                at = match.away_team.team_id

                goals_for[ht][iteration] += home_goals
                goals_for[at][iteration] += away_goals
                goals_against[ht][iteration] += away_goals
                goals_against[at][iteration] += home_goals

                if home_goals > away_goals:
                    points[ht][iteration] += 3
                    wins[ht][iteration] += 1
                    losses[at][iteration] += 1
                elif home_goals == away_goals:
                    points[ht][iteration] += 1
                    points[at][iteration] += 1
                    draws[ht][iteration] += 1
                    draws[at][iteration] += 1
                else:
                    points[at][iteration] += 3
                    wins[at][iteration] += 1
                    losses[ht][iteration] += 1

            if progress_callback and iteration % max(1, iterations // 100) == 0:
                progress_callback(int(100 * iteration / iterations))

        if progress_callback:
            progress_callback(100)

        # Build standings per iteration and compute statistics
        final_positions = {tid: [] for tid in team_ids}
        title_count = {tid: 0 for tid in team_ids}
        top4_count = {tid: 0 for tid in team_ids}
        relegation_count = {tid: 0 for tid in team_ids}

        for iteration in range(iterations):
            standings = []
            for tid in team_ids:
                standings.append({
                    "team_id": tid,
                    "team_name": teams[tid].name,
                    "points": points[tid][iteration],
                    "wins": wins[tid][iteration],
                    "draws": draws[tid][iteration],
                    "losses": losses[tid][iteration],
                    "gf": goals_for[tid][iteration],
                    "ga": goals_against[tid][iteration],
                    "gd": goals_for[tid][iteration] - goals_against[tid][iteration],
                })

            # Sort by points, then goal difference, then goals for, then name
            standings.sort(key=lambda x: (-x["points"], -x["gd"], -x["gf"], x["team_name"]))

            for pos, team in enumerate(standings, 1):
                final_positions[team["team_id"]].append(pos)
                if pos == 1:
                    title_count[team["team_id"]] += 1
                if pos <= 4:
                    top4_count[team["team_id"]] += 1
                if pos > n_teams - 3:
                    relegation_count[team["team_id"]] += 1

        # Build forecast output
        team_forecasts = []
        for tid in team_ids:
            positions = np.array(final_positions[tid])
            team_forecasts.append({
                "team_id": tid,
                "team_name": teams[tid].name,
                "avg_points": round(float(np.mean(points[tid])), 1),
                "avg_position": round(float(np.mean(positions)), 1),
                "position_std": round(float(np.std(positions)), 1),
                "title_probability": round(title_count[tid] / iterations, 4),
                "top4_probability": round(top4_count[tid] / iterations, 4),
                "relegation_probability": round(relegation_count[tid] / iterations, 4),
                "avg_goals_for": round(float(np.mean(goals_for[tid])), 1),
                "avg_goals_against": round(float(np.mean(goals_against[tid])), 1),
                "best_position": int(np.min(positions)),
                "worst_position": int(np.max(positions)),
            })

        # Sort by title probability descending
        team_forecasts.sort(key=lambda x: (-x["title_probability"], -x["avg_points"], x["avg_position"]))

        return LeagueForecast(
            league=league,
            season=season,
            iterations=iterations,
            team_forecasts=team_forecasts,
        )


def simulate_match_score(match: Match, model: PoissonDixonColesModel) -> tuple:
    """Simulate a single match score."""
    pred = model.predict(match)
    
    # Ensure score_matrix exists in prediction
    if "score_matrix" not in pred:
        # Calculate score matrix from home/away lambda if not present
        home_lambda = pred.get("home_lambda", pred.get("home_xg", 1.4))
        away_lambda = pred.get("away_lambda", pred.get("away_xg", 1.2))
        
        # Create score matrix
        max_goals = 8
        matrix = np.zeros((max_goals + 1, max_goals + 1))
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                from .probability import poisson_pmf, dixon_coles_tau
                base_prob = poisson_pmf(h, home_lambda) * poisson_pmf(a, away_lambda)
                tau = dixon_coles_tau(h, a, home_lambda, away_lambda, -0.13)
                matrix[h, a] = base_prob * tau
        
        total = matrix.sum()
        if total > 0:
            matrix /= total
        pred["score_matrix"] = matrix
    
    matrix = pred["score_matrix"]
    flat = matrix.flatten() / matrix.flatten().sum()
    idx = np.random.choice(len(flat), p=flat)
    home_goals = idx // matrix.shape[1]
    away_goals = idx % matrix.shape[1]
    return home_goals, away_goals


def simulate_league(matches: List[Match], iterations: int = 5000,
                    progress_callback: Optional[Callable[[int], None]] = None) -> LeagueForecast:
    """Convenience function."""
    engine = SimulationEngine()
    return engine.simulate_league(matches, iterations, progress_callback)


class LeagueSimulator:
    """Wrapper class for league simulation with simplified API.
    
    This class provides a simpler interface for the simulation service
    and maintains backward compatibility.
    """
    
    def __init__(self):
        """Initialize league simulator."""
        self.engine = SimulationEngine()
    
    def run_simulation(self, league: str = "Premier League", n_simulations: int = 1000) -> Dict:
        """Run league simulation.
        
        Args:
            league: League name to simulate
            n_simulations: Number of Monte Carlo iterations
            
        Returns:
            Dictionary with simulation results including standings and probabilities
        """
        from src.soccer_predictor.services.fixture_service import get_fixture_service
        
        # Get fixtures for the league from real API
        fixture_service = get_fixture_service()
        fixtures = fixture_service.get_fixtures_by_league(league)
        
        if not fixtures:
            return {
                'error': f'No fixtures found for league: {league}',
                'league': league
            }
        
        # Run simulation using the engine
        forecast = self.engine.simulate_league(fixtures, iterations=n_simulations)
        
        # Convert to dictionary format expected by service
        results = {
            'league': forecast.league,
            'season': forecast.season,
            'iterations': forecast.iterations,
            'standings': forecast.team_forecasts,
            'championship_probs': [
                {
                    'team_id': team['team_id'],
                    'team_name': team['team_name'],
                    'probability': team['title_probability']
                }
                for team in forecast.team_forecasts
            ]
        }
        
        return results