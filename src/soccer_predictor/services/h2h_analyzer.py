"""Head-to-head team comparison service.

Inspired by F1 Predictor's driver vs driver battle analysis.
Provides comprehensive team comparisons with radar charts and statistics.
"""

from typing import Dict, List, Optional
from src.soccer_predictor.core.fast_simulation import get_monte_carlo


class HeadToHeadAnalyzer:
    """Comprehensive team vs team comparison engine."""
    
    def __init__(self):
        self.monte_carlo = get_monte_carlo()
    
    def compare_teams(self, team_a_data: Dict, team_b_data: Dict,
                     historical_h2h: Optional[List[Dict]] = None) -> Dict:
        """
        Perform comprehensive head-to-head comparison.
        
        Args:
            team_a_data: Team A statistics and info
            team_b_data: Team B statistics and info
            historical_h2h: Previous meetings between teams
        
        Returns:
            Complete H2H analysis
        """
        # Calculate win probabilities
        team_a_xg = team_a_data.get('xg_for', 1.5)
        team_b_xg = team_b_data.get('xg_for', 1.2)
        
        h2h_result = self.monte_carlo.calculate_head_to_head(
            team_a_xg, team_b_xg, historical_h2h
        )
        
        # Generate radar chart data
        radar_chart = self._generate_radar_chart(team_a_data, team_b_data)
        
        # Compare recent form
        form_comparison = self._compare_form(team_a_data, team_b_data)
        
        # Analyze home/away splits
        venue_analysis = self._analyze_venue_performance(team_a_data, team_b_data)
        
        # Identify key battles
        key_battles = self._identify_key_battles(team_a_data, team_b_data)
        
        return {
            'teams': {
                'team_a': team_a_data,
                'team_b': team_b_data
            },
            'win_probabilities': h2h_result['simulation'],
            'historical_record': {
                'total_meetings': h2h_result['historical_meetings'],
                'meetings': historical_h2h or []
            },
            'radar_chart': radar_chart,
            'form_comparison': form_comparison,
            'venue_analysis': venue_analysis,
            'key_battles': key_battles,
            'recommendation': h2h_result['recommendation']
        }
    
    def _generate_radar_chart(self, team_a: Dict, team_b: Dict) -> Dict:
        """Generate radar chart data comparing team strengths."""
        dimensions = [
            'Attack Strength',
            'Defense Solidity',
            'Recent Form',
            'Home Performance',
            'Away Performance',
            'Set Pieces',
            'Counter Attack',
            'Possession'
        ]
        
        # Normalize values to 0-10 scale
        def normalize(value, max_value=100):
            return min(10, max(0, (value / max_value) * 10))
        
        team_a_values = [
            normalize(team_a.get('attack_strength', 50)),
            normalize(team_a.get('defense_strength', 50)),
            normalize(team_a.get('form_index', 0) * 10 + 5),
            normalize(team_a.get('home_win_rate', 50)),
            normalize(team_a.get('away_win_rate', 50)),
            normalize(team_a.get('set_piece_goals', 5)),
            normalize(team_a.get('counter_attack_goals', 5)),
            normalize(team_a.get('avg_possession', 50))
        ]
        
        team_b_values = [
            normalize(team_b.get('attack_strength', 50)),
            normalize(team_b.get('defense_strength', 50)),
            normalize(team_b.get('form_index', 0) * 10 + 5),
            normalize(team_b.get('home_win_rate', 50)),
            normalize(team_b.get('away_win_rate', 50)),
            normalize(team_b.get('set_piece_goals', 5)),
            normalize(team_b.get('counter_attack_goals', 5)),
            normalize(team_b.get('avg_possession', 50))
        ]
        
        return {
            'labels': dimensions,
            'team_a': {
                'name': team_a.get('name', 'Team A'),
                'values': team_a_values
            },
            'team_b': {
                'name': team_b.get('name', 'Team B'),
                'values': team_b_values
            }
        }
    
    def _compare_form(self, team_a: Dict, team_b: Dict) -> Dict:
        """Compare recent form of both teams."""
        team_a_form = team_a.get('recent_form', [])
        team_b_form = team_b.get('recent_form', [])
        
        def calculate_form_points(form_list):
            points = 0
            for result in form_list[-10:]:  # Last 10 matches
                if result.upper() == 'W':
                    points += 3
                elif result.upper() == 'D':
                    points += 1
            return points
        
        team_a_points = calculate_form_points(team_a_form)
        team_b_points = calculate_form_points(team_b_form)
        
        return {
            'team_a': {
                'form_string': ''.join(team_a_form[-5:]),
                'points_last_10': team_a_points,
                'wins': sum(1 for r in team_a_form if r.upper() == 'W'),
                'draws': sum(1 for r in team_a_form if r.upper() == 'D'),
                'losses': sum(1 for r in team_a_form if r.upper() == 'L')
            },
            'team_b': {
                'form_string': ''.join(team_b_form[-5:]),
                'points_last_10': team_b_points,
                'wins': sum(1 for r in team_b_form if r.upper() == 'W'),
                'draws': sum(1 for r in team_b_form if r.upper() == 'D'),
                'losses': sum(1 for r in team_b_form if r.upper() == 'L')
            },
            'momentum': 'team_a' if team_a_points > team_b_points else 'team_b'
        }
    
    def _analyze_venue_performance(self, team_a: Dict, team_b: Dict) -> Dict:
        """Analyze home and away performance splits."""
        return {
            'team_a': {
                'home_record': {
                    'played': team_a.get('home_played', 0),
                    'wins': team_a.get('home_wins', 0),
                    'goals_scored': team_a.get('home_goals_scored', 0),
                    'goals_conceded': team_a.get('home_goals_conceded', 0)
                },
                'away_record': {
                    'played': team_a.get('away_played', 0),
                    'wins': team_a.get('away_wins', 0),
                    'goals_scored': team_a.get('away_goals_scored', 0),
                    'goals_conceded': team_a.get('away_goals_conceded', 0)
                }
            },
            'team_b': {
                'home_record': {
                    'played': team_b.get('home_played', 0),
                    'wins': team_b.get('home_wins', 0),
                    'goals_scored': team_b.get('home_goals_scored', 0),
                    'goals_conceded': team_b.get('home_goals_conceded', 0)
                },
                'away_record': {
                    'played': team_b.get('away_played', 0),
                    'wins': team_b.get('away_wins', 0),
                    'goals_scored': team_b.get('away_goals_scored', 0),
                    'goals_conceded': team_b.get('away_goals_conceded', 0)
                }
            }
        }
    
    def _identify_key_battles(self, team_a: Dict, team_b: Dict) -> List[Dict]:
        """Identify key player matchups."""
        battles = []
        
        # Striker vs Defender
        if team_a.get('top_scorer') and team_b.get('top_defender'):
            battles.append({
                'type': 'Attack vs Defense',
                'player_a': team_a['top_scorer'],
                'player_b': team_b['top_defender'],
                'stat_a': f"{team_a.get('goals_per_game', 0):.2f} goals/game",
                'stat_b': f"{team_b.get('clean_sheets', 0)} clean sheets"
            })
        
        # Midfield battle
        if team_a.get('midfield_rating') and team_b.get('midfield_rating'):
            battles.append({
                'type': 'Midfield Control',
                'player_a': 'Midfield Unit',
                'player_b': 'Midfield Unit',
                'stat_a': f"{team_a['midfield_rating']:.1f}/10 rating",
                'stat_b': f"{team_b['midfield_rating']:.1f}/10 rating"
            })
        
        # Set pieces
        battles.append({
            'type': 'Set Pieces',
            'player_a': 'Team A',
            'player_b': 'Team B',
            'stat_a': f"{team_a.get('set_piece_goals', 0)} goals",
            'stat_b': f"{team_b.get('set_piece_goals', 0)} goals"
        })
        
        return battles
    
    def generate_comparison_report(self, comparison_data: Dict) -> str:
        """Generate HTML report for H2H comparison."""
        from src.soccer_predictor.services.report_generator import get_report_generator
        
        generator = get_report_generator()
        
        radar_data = comparison_data['radar_chart']
        win_probs = comparison_data['win_probabilities']
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{radar_data['team_a']['name']} vs {radar_data['team_b']['name']} - H2H Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }}
        h1 {{ color: #667eea; text-align: center; }}
        .chart-container {{ width: 100%; height: 500px; margin: 30px 0; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: #f9fafb; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #6b7280; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚔️ Head-to-Head Comparison</h1>
        <h2 style="text-align: center;">{radar_data['team_a']['name']} vs {radar_data['team_b']['name']}</h2>
        
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-value">{win_probs['home_win_prob']*100:.1f}%</div>
                <div class="stat-label">{radar_data['team_a']['name']} Win</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{win_probs['draw_prob']*100:.1f}%</div>
                <div class="stat-label">Draw</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{win_probs['away_win_prob']*100:.1f}%</div>
                <div class="stat-label">{radar_data['team_b']['name']} Win</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="radarChart"></canvas>
        </div>
        
        <script>
            const ctx = document.getElementById('radarChart').getContext('2d');
            new Chart(ctx, {{
                type: 'radar',
                data: {{
                    labels: {radar_data['labels']},
                    datasets: [{{
                        label: '{radar_data["team_a"]["name"]}',
                        data: {radar_data['team_a']['values']},
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.2)'
                    }}, {{
                        label: '{radar_data["team_b"]["name"]}',
                        data: {radar_data['team_b']['values']},
                        borderColor: 'rgb(245, 87, 108)',
                        backgroundColor: 'rgba(245, 87, 108, 0.2)'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        r: {{
                            beginAtZero: true,
                            max: 10
                        }}
                    }}
                }}
            }});
        </script>
    </div>
</body>
</html>"""
        
        return html


# Global instance
_h2h_analyzer = None

def get_h2h_analyzer() -> HeadToHeadAnalyzer:
    """Get or create H2H analyzer instance."""
    global _h2h_analyzer
    if _h2h_analyzer is None:
        _h2h_analyzer = HeadToHeadAnalyzer()
    return _h2h_analyzer
