"""Championship forecasting using Monte Carlo simulation.

Inspired by F1 Predictor's season-long championship simulation.
Predicts final league standings with probability distributions.
"""

from typing import Dict, List, Optional
from src.soccer_predictor.core.fast_simulation import get_monte_carlo


class ChampionshipForecaster:
    """Season-long championship probability forecasting."""
    
    def __init__(self, n_simulations: int = 10000):
        self.monte_carlo = get_monte_carlo(n_simulations)
        self.n_simulations = n_simulations
    
    def forecast_season(self, league: str, current_standings: Dict[str, Dict],
                       remaining_fixtures: List[Dict]) -> Dict:
        """
        Simulate rest of season and predict final standings.
        
        Args:
            league: League name
            current_standings: Current league table with points
            remaining_fixtures: List of remaining matches
        
        Returns:
            Championship probabilities and predictions
        """
        # Convert fixtures to Match objects for simulation
        from src.soccer_predictor.core.entities import Match, TeamRating
        
        fixtures_as_matches = []
        for fixture in remaining_fixtures:
            home_team = TeamRating(
                team_id=fixture['home_team_id'],
                name=fixture['home_team'],
                league=league,
                elo=fixture.get('home_elo', 1500),
                attack=fixture.get('home_attack', 1.5),
                defense=fixture.get('home_defense', 1.2)
            )
            
            away_team = TeamRating(
                team_id=fixture['away_team_id'],
                name=fixture['away_team'],
                league=league,
                elo=fixture.get('away_elo', 1500),
                attack=fixture.get('away_attack', 1.2),
                defense=fixture.get('away_defense', 1.5)
            )
            
            match = Match(
                match_id=fixture['match_id'],
                league=league,
                home_team=home_team,
                away_team=away_team,
                date=fixture.get('date')
            )
            fixtures_as_matches.append(match)
        
        # Run season simulation
        sim_results = self.monte_carlo.simulate_season(
            fixtures_as_matches, 
            current_standings
        )
        
        # Generate insights
        insights = self._generate_insights(sim_results, current_standings)
        
        return {
            'league': league,
            'simulations_run': self.n_simulations,
            'championship_probs': sim_results['championship_probs'],
            'top4_probs': sim_results['top4_probs'],
            'relegation_probs': sim_results['relegation_probs'],
            'expected_final_positions': sim_results['expected_positions'],
            'expected_points': sim_results['final_points_mean'],
            'points_uncertainty': sim_results['final_points_std'],
            'insights': insights,
            'current_leaders': list(current_standings.keys())[0] if current_standings else None
        }
    
    def _generate_insights(self, sim_results: Dict, current_standings: Dict) -> List[Dict]:
        """Generate narrative insights from simulation results."""
        insights = []
        
        # Find most likely champion
        champ_probs = sim_results['championship_probs']
        if champ_probs:
            likely_champion = max(champ_probs, key=champ_probs.get)
            prob = champ_probs[likely_champion] * 100
            
            if prob > 70:
                insights.append({
                    'type': 'championship',
                    'message': f"{likely_champion} are overwhelming favorites ({prob:.1f}% chance)",
                    'priority': 'high'
                })
            elif prob > 40:
                insights.append({
                    'type': 'championship',
                    'message': f"{likely_champion} lead the title race ({prob:.1f}% chance)",
                    'priority': 'medium'
                })
            else:
                insights.append({
                    'type': 'championship',
                    'message': "Title race is wide open - no clear favorite",
                    'priority': 'high'
                })
        
        # Check for tight top 4 race
        top4_probs = sim_results['top4_probs']
        teams_in_contention = sum(1 for p in top4_probs.values() if p > 0.3)
        
        if teams_in_contention > 6:
            insights.append({
                'type': 'top4',
                'message': f"Intense battle for top 4 - {teams_in_contention} teams still in contention",
                'priority': 'high'
            })
        
        # Check relegation battle
        relegation_probs = sim_results['relegation_probs']
        teams_at_risk = sum(1 for p in relegation_probs.values() if p > 0.2)
        
        if teams_at_risk > 5:
            insights.append({
                'type': 'relegation',
                'message': f"Tight relegation battle - {teams_at_risk} teams at serious risk",
                'priority': 'high'
            })
        
        # Find biggest overachievers/underachievers
        expected_positions = sim_results['expected_positions']
        for team_id, exp_pos in expected_positions.items():
            current_pos = list(current_standings.keys()).index(team_id) + 1 if team_id in current_standings else None
            
            if current_pos and abs(exp_pos - current_pos) > 5:
                direction = "overachieving" if exp_pos < current_pos else "underachieving"
                insights.append({
                    'type': 'performance',
                    'message': f"{team_id} are {direction} (current: {current_pos}, expected: {exp_pos:.0f})",
                    'priority': 'medium'
                })
        
        return insights
    
    def generate_forecast_report(self, forecast_data: Dict) -> str:
        """Generate HTML report for championship forecast."""
        from src.soccer_predictor.services.report_generator import get_report_generator
        
        generator = get_report_generator()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{forecast_data['league']} Championship Forecast</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
        h1 {{ color: #667eea; text-align: center; margin-bottom: 10px; }}
        .subtitle {{ text-align: center; color: #6b7280; margin-bottom: 40px; }}
        .chart-container {{ width: 100%; height: 500px; margin: 30px 0; }}
        .insights {{ background: #f9fafb; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .insight-item {{ padding: 10px; margin: 10px 0; border-left: 4px solid #667eea; background: white; }}
        .insight-high {{ border-left-color: #ef4444; }}
        .insight-medium {{ border-left-color: #f59e0b; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #667eea; color: white; }}
        tr:hover {{ background: #f9fafb; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 {forecast_data['league']} Championship Forecast</h1>
        <div class="subtitle">Based on {forecast_data['simulations_run']:,} Monte Carlo simulations</div>
        
        <div class="chart-container">
            <canvas id="championshipChart"></canvas>
        </div>
        
        <h2>Key Insights</h2>
        <div class="insights">
            {''.join([f'<div class="insight-item insight-{i["priority"]}">{i["message"]}</div>' 
                     for i in forecast_data.get('insights', [])])}
        </div>
        
        <h2>Expected Final Table</h2>
        <table>
            <tr>
                <th>Pos</th>
                <th>Team</th>
                <th>Current Pts</th>
                <th>Expected Pts</th>
                <th>Title Chance</th>
                <th>Top 4 Chance</th>
                <th>Relegation Risk</th>
            </tr>
            {''.join([self._format_team_row(team, forecast_data) 
                     for team in sorted(forecast_data['expected_final_positions'].keys(), 
                                      key=lambda x: forecast_data['expected_final_positions'][x])[:10]])}
        </table>
        
        <script>
            const teams = {list(forecast_data['championship_probs'].keys())[:10]};
            const probs = {[round(forecast_data['championship_probs'][t]*100, 1) for t in list(forecast_data['championship_probs'].keys())[:10]]};
            
            const ctx = document.getElementById('championshipChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: teams,
                    datasets: [{{
                        label: 'Championship Probability (%)',
                        data: probs,
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgb(102, 126, 234)',
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Title Race Probabilities',
                            font: {{ size: 18 }}
                        }}
                    }}
                }}
            }});
        </script>
    </div>
</body>
</html>"""
        
        return html
    
    def _format_team_row(self, team: str, forecast_data: Dict) -> str:
        """Format a team row for the table."""
        expected_pos = forecast_data['expected_final_positions'].get(team, 0)
        expected_pts = forecast_data['expected_points'].get(team, 0)
        title_chance = forecast_data['championship_probs'].get(team, 0) * 100
        top4_chance = forecast_data['top4_probs'].get(team, 0) * 100
        relegation_risk = forecast_data['relegation_probs'].get(team, 0) * 100
        
        return f"""
            <tr>
                <td>{expected_pos:.0f}</td>
                <td><strong>{team}</strong></td>
                <td>{expected_pts:.0f}</td>
                <td>{expected_pts:.1f} ± {forecast_data['points_uncertainty'].get(team, 0):.1f}</td>
                <td>{title_chance:.1f}%</td>
                <td>{top4_chance:.1f}%</td>
                <td style="color: {'red' if relegation_risk > 50 else 'inherit'}">{relegation_risk:.1f}%</td>
            </tr>
        """


# Global instance
_forecaster = None

def get_championship_forecaster(n_simulations: int = 10000) -> ChampionshipForecaster:
    """Get or create forecaster instance."""
    global _forecaster
    if _forecaster is None or _forecaster.n_simulations != n_simulations:
        _forecaster = ChampionshipForecaster(n_simulations)
    return _forecaster
