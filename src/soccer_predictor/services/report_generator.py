"""Professional HTML report generator for match predictions.

Inspired by F1 Predictor's publication-quality report generation.
Creates beautiful, interactive HTML reports with charts and comprehensive analysis.
"""

from typing import Dict, List, Optional
from datetime import datetime


class MatchReportGenerator:
    """Generate professional HTML match preview reports."""
    
    def __init__(self):
        self.template = self._get_base_template()
    
    def _get_base_template(self) -> str:
        """Base HTML template with modern styling."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .prediction-box {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 30px;
            border-radius: 15px;
            margin: 20px 0;
            border-left: 5px solid #667eea;
        }}
        
        .probability-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        
        .prob-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .prob-card:hover {{
            transform: translateY(-5px);
        }}
        
        .prob-card.home {{
            border-top: 4px solid #10b981;
        }}
        
        .prob-card.draw {{
            border-top: 4px solid #f59e0b;
        }}
        
        .prob-card.away {{
            border-top: 4px solid #3b82f6;
        }}
        
        .prob-label {{
            font-size: 0.9em;
            color: #6b7280;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .prob-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #1f2937;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .stat-card {{
            background: #f9fafb;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #e5e7eb;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #6b7280;
            margin-bottom: 5px;
        }}
        
        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #1f2937;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 30px 0;
        }}
        
        .value-bet-alert {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
        }}
        
        .team-comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 20px 0;
        }}
        
        .team-box {{
            background: #f9fafb;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #e5e7eb;
        }}
        
        .team-name {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 15px;
            text-align: center;
        }}
        
        .form-indicator {{
            display: inline-block;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            text-align: center;
            line-height: 30px;
            margin: 2px;
            font-weight: bold;
            color: white;
        }}
        
        .form-w {{ background: #10b981; }}
        .form-d {{ background: #f59e0b; }}
        .form-l {{ background: #ef4444; }}
        
        .footer {{
            background: #f9fafb;
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 0.9em;
        }}
        
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
        }}
        
        @media (max-width: 768px) {{
            .probability-grid {{
                grid-template-columns: 1fr;
            }}
            .team-comparison {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>"""
    
    def generate_match_preview(self, match_data: Dict, prediction: Dict, 
                              team_stats: Optional[Dict] = None) -> str:
        """Generate complete match preview report."""
        
        title = f"{match_data['home_team']} vs {match_data['away_team']} - Match Preview"
        
        content = self._build_header(match_data)
        content += self._build_prediction_summary(prediction)
        content += self._build_probability_chart(prediction)
        
        if team_stats:
            content += self._build_team_comparison(team_stats)
        
        content += self._build_value_bet_section(prediction)
        content += self._build_footer()
        
        return self.template.format(title=title, content=content)
    
    def _build_header(self, match_data: Dict) -> str:
        """Build report header section."""
        return f"""
        <div class="header">
            <h1>{match_data['home_team']} vs {match_data['away_team']}</h1>
            <div class="subtitle">
                {match_data.get('league', 'League')} • 
                {match_data.get('date', 'Date')} • 
                {match_data.get('venue', 'Venue')}
            </div>
        </div>
        <div class="content">
        """
    
    def _build_prediction_summary(self, prediction: Dict) -> str:
        """Build prediction summary section."""
        home_prob = prediction.get('home_win_prob', 0) * 100
        draw_prob = prediction.get('draw_prob', 0) * 100
        away_prob = prediction.get('away_win_prob', 0) * 100
        
        predicted_score = prediction.get('predicted_score', 'N/A')
        confidence = prediction.get('confidence_score', 0) * 100
        
        return f"""
        <div class="section">
            <h2 class="section-title">🎯 Prediction Summary</h2>
            
            <div class="prediction-box">
                <div class="probability-grid">
                    <div class="prob-card home">
                        <div class="prob-label">Home Win</div>
                        <div class="prob-value">{home_prob:.1f}%</div>
                    </div>
                    <div class="prob-card draw">
                        <div class="prob-label">Draw</div>
                        <div class="prob-value">{draw_prob:.1f}%</div>
                    </div>
                    <div class="prob-card away">
                        <div class="prob-label">Away Win</div>
                        <div class="prob-value">{away_prob:.1f}%</div>
                    </div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Predicted Score</div>
                        <div class="stat-value">{predicted_score}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Model Confidence</div>
                        <div class="stat-value">{confidence:.1f}%</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Expected Goals (Home)</div>
                        <div class="stat-value">{prediction.get('predicted_home_goals', 0):.2f}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Expected Goals (Away)</div>
                        <div class="stat-value">{prediction.get('predicted_away_goals', 0):.2f}</div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _build_probability_chart(self, prediction: Dict) -> str:
        """Build interactive probability distribution chart."""
        return f"""
        <div class="section">
            <h2 class="section-title">📊 Probability Distribution</h2>
            <div class="chart-container">
                <canvas id="probabilityChart"></canvas>
            </div>
            <script>
                const ctx = document.getElementById('probabilityChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: ['Home Win', 'Draw', 'Away Win'],
                        datasets: [{{
                            label: 'Probability (%)',
                            data: [{prediction.get('home_win_prob', 0)*100}, 
                                   {prediction.get('draw_prob', 0)*100}, 
                                   {prediction.get('away_win_prob', 0)*100}],
                            backgroundColor: [
                                'rgba(16, 185, 129, 0.8)',
                                'rgba(245, 158, 11, 0.8)',
                                'rgba(59, 130, 246, 0.8)'
                            ],
                            borderColor: [
                                'rgb(16, 185, 129)',
                                'rgb(245, 158, 11)',
                                'rgb(59, 130, 246)'
                            ],
                            borderWidth: 2
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                display: false
                            }},
                            title: {{
                                display: true,
                                text: 'Match Outcome Probabilities',
                                font: {{
                                    size: 18
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                max: 100,
                                ticks: {{
                                    callback: function(value) {{
                                        return value + '%';
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            </script>
        </div>
        """
    
    def _build_team_comparison(self, team_stats: Dict) -> str:
        """Build team comparison section."""
        home_stats = team_stats.get('home', {})
        away_stats = team_stats.get('away', {})
        
        home_form = home_stats.get('recent_form', [])
        away_form = away_stats.get('recent_form', [])
        
        def format_form(form_list):
            return ''.join([f'<span class="form-indicator form-{r.lower()}">{r.upper()}</span>' 
                           for r in form_list[-5:]])
        
        return f"""
        <div class="section">
            <h2 class="section-title">⚔️ Team Comparison</h2>
            <div class="team-comparison">
                <div class="team-box">
                    <div class="team-name">{home_stats.get('name', 'Home Team')}</div>
                    <div style="margin: 15px 0;">
                        <strong>Recent Form:</strong><br>
                        {format_form(home_form)}
                    </div>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Avg Goals Scored</div>
                            <div class="stat-value">{home_stats.get('avg_goals_scored', 0):.2f}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Avg Goals Conceded</div>
                            <div class="stat-value">{home_stats.get('avg_goals_conceded', 0):.2f}</div>
                        </div>
                    </div>
                </div>
                
                <div class="team-box">
                    <div class="team-name">{away_stats.get('name', 'Away Team')}</div>
                    <div style="margin: 15px 0;">
                        <strong>Recent Form:</strong><br>
                        {format_form(away_form)}
                    </div>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Avg Goals Scored</div>
                            <div class="stat-value">{away_stats.get('avg_goals_scored', 0):.2f}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Avg Goals Conceded</div>
                            <div class="stat-value">{away_stats.get('avg_goals_conceded', 0):.2f}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _build_value_bet_section(self, prediction: Dict) -> str:
        """Build value bet alert section."""
        if not prediction.get('value_bet_detected'):
            return ""
        
        bet_type = prediction.get('value_bet_type', 'Unknown')
        expected_value = prediction.get('expected_value', 0) * 100
        
        return f"""
        <div class="section">
            <div class="value-bet-alert">
                💰 VALUE BET DETECTED!<br>
                <small>Bet Type: {bet_type} | Expected Value: {expected_value:.1f}%</small>
            </div>
        </div>
        """
    
    def _build_footer(self) -> str:
        """Build report footer."""
        return f"""
        </div>
        <div class="footer">
            <p>Generated by Soccer Predictor Pro • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin-top: 10px; font-size: 0.8em;">
                Disclaimer: This is a statistical prediction model. Past performance does not guarantee future results.
            </p>
        </div>
        """
    
    def save_report(self, html_content: str, filename: str, directory: str = "reports"):
        """Save HTML report to file."""
        from pathlib import Path
        
        report_dir = Path(directory)
        report_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = report_dir / f"{filename}.html"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(filepath)
    
    def generate_championship_forecast(self, league: str, simulations: Dict) -> str:
        """Generate championship forecast report."""
        title = f"{league} Championship Forecast"
        
        teams = simulations.get('teams', [])
        probs = simulations.get('championship_probs', {})
        
        content = f"""
        <div class="header">
            <h1>{league} Championship Forecast</h1>
            <div class="subtitle">Monte Carlo Simulation Results</div>
        </div>
        <div class="content">
            <div class="section">
                <h2 class="section-title">🏆 Championship Probabilities</h2>
                <div class="chart-container">
                    <canvas id="championshipChart"></canvas>
                </div>
                <script>
                    const ctx = document.getElementById('championshipChart').getContext('2d');
                    new Chart(ctx, {{
                        type: 'bar',
                        data: {{
                            labels: {json.dumps(list(probs.keys())[:10])},
                            datasets: [{{
                                label: 'Championship Probability (%)',
                                data: {[probs[t]*100 for t in list(probs.keys())[:10]]},
                                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                                borderColor: 'rgb(102, 126, 234)',
                                borderWidth: 2
                            }}]
                        }},
                        options: {{
                            indexAxis: 'y',
                            responsive: true,
                            maintainAspectRatio: false,
                        }}
                    }});
                </script>
            </div>
        </div>
        <div class="footer">
            <p>Generated by Soccer Predictor Pro • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """
        
        return self.template.format(title=title, content=content)


# Import json for championship forecast
import json


# Global instance
_report_generator = None

def get_report_generator() -> MatchReportGenerator:
    """Get or create report generator instance."""
    global _report_generator
    if _report_generator is None:
        _report_generator = MatchReportGenerator()
    return _report_generator
