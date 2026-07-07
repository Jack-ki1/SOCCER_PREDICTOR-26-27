"""Professional report generation service.

Generates HTML, PDF, CSV, JSON, and Excel reports with embedded charts.
Inspired by F1 Predictor 2026's report generation system.
"""

import json
import csv
import io
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """
    Generates professional prediction reports in multiple formats.
    
    Supported formats:
    - HTML with embedded Plotly charts
    - PDF (via WeasyPrint)
    - CSV for data analysis
    - JSON for API integration
    - Excel with formatting
    """
    
    def __init__(self):
        """Initialize report generator."""
        self.templates_dir = Path(__file__).parent.parent / 'templates' / 'reports'
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(self, prediction: Dict, 
                            include_charts: bool = True) -> str:
        """
        Generate HTML report with embedded charts.
        
        Args:
            prediction: Prediction dictionary
            include_charts: Whether to include interactive charts
        
        Returns:
            HTML string
        """
        html_template = self._get_html_template()
        
        # Fill template with prediction data
        html_content = html_template.format(
            home_team=prediction.get('home_team', 'Home Team'),
            away_team=prediction.get('away_team', 'Away Team'),
            league=prediction.get('league', 'League'),
            match_date=prediction.get('match_date', datetime.utcnow()).strftime('%Y-%m-%d %H:%M'),
            home_win_prob=f"{prediction.get('home_win', 0) * 100:.1f}",
            draw_prob=f"{prediction.get('draw', 0) * 100:.1f}",
            away_win_prob=f"{prediction.get('away_win', 0) * 100:.1f}",
            home_xg=f"{prediction.get('home_xg', 0):.2f}",
            away_xg=f"{prediction.get('away_xg', 0):.2f}",
            btts_prob=f"{prediction.get('btts', 0) * 100:.1f}",
            over_25_prob=f"{prediction.get('over_25', 0) * 100:.1f}",
            generated_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            model_version=prediction.get('model_version', '1.0')
        )
        
        return html_content
    
    def generate_pdf_report(self, prediction: Dict, 
                           output_path: str = None) -> bytes:
        """
        Generate PDF report using WeasyPrint.
        
        Args:
            prediction: Prediction dictionary
            output_path: Optional file path to save PDF
        
        Returns:
            PDF bytes
        """
        try:
            from weasyprint import HTML, CSS
            
            # Generate HTML first
            html_content = self.generate_html_report(prediction)
            
            # Convert to PDF
            pdf = HTML(string=html_content).write_pdf()
            
            # Save if path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf)
            
            return pdf
        
        except ImportError:
            raise ImportError(
                "WeasyPrint is required for PDF generation. "
                "Install with: pip install weasyprint"
            )
    
    def generate_csv_report(self, predictions: List[Dict]) -> str:
        """
        Generate CSV report for multiple predictions.
        
        Args:
            predictions: List of prediction dictionaries
        
        Returns:
            CSV string
        """
        output = io.StringIO()
        
        if not predictions:
            return ""
        
        # Define CSV columns
        fieldnames = [
            'match_id', 'home_team', 'away_team', 'league', 'match_date',
            'home_win_prob', 'draw_prob', 'away_win_prob',
            'home_xg', 'away_xg', 'btts_prob', 'over_25_prob',
            'predicted_at', 'model_version'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for pred in predictions:
            row = {
                'match_id': pred.get('match_id', ''),
                'home_team': pred.get('home_team', ''),
                'away_team': pred.get('away_team', ''),
                'league': pred.get('league', ''),
                'match_date': pred.get('match_date', ''),
                'home_win_prob': f"{pred.get('home_win', 0) * 100:.1f}%",
                'draw_prob': f"{pred.get('draw', 0) * 100:.1f}%",
                'away_win_prob': f"{pred.get('away_win', 0) * 100:.1f}%",
                'home_xg': f"{pred.get('home_xg', 0):.2f}",
                'away_xg': f"{pred.get('away_xg', 0):.2f}",
                'btts_prob': f"{pred.get('btts', 0) * 100:.1f}%",
                'over_25_prob': f"{pred.get('over_25', 0) * 100:.1f}%",
                'predicted_at': pred.get('predicted_at', ''),
                'model_version': pred.get('model_version', '')
            }
            writer.writerow(row)
        
        return output.getvalue()
    
    def generate_json_report(self, prediction: Dict, pretty: bool = True) -> str:
        """
        Generate JSON report.
        
        Args:
            prediction: Prediction dictionary
            pretty: Whether to format with indentation
        
        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(prediction, indent=2, default=str)
        else:
            return json.dumps(prediction, default=str)
    
    def generate_excel_report(self, predictions: List[Dict], 
                             output_path: str = None) -> bytes:
        """
        Generate Excel report with formatting.
        
        Args:
            predictions: List of prediction dictionaries
            output_path: Optional file path to save Excel file
        
        Returns:
            Excel file bytes
        """
        try:
            import pandas as pd
            from io import BytesIO
            
            # Convert to DataFrame
            df_data = []
            for pred in predictions:
                df_data.append({
                    'Match ID': pred.get('match_id', ''),
                    'Home Team': pred.get('home_team', ''),
                    'Away Team': pred.get('away_team', ''),
                    'League': pred.get('league', ''),
                    'Date': pred.get('match_date', ''),
                    'Home Win %': f"{pred.get('home_win', 0) * 100:.1f}",
                    'Draw %': f"{pred.get('draw', 0) * 100:.1f}",
                    'Away Win %': f"{pred.get('away_win', 0) * 100:.1f}",
                    'Home xG': f"{pred.get('home_xg', 0):.2f}",
                    'Away xG': f"{pred.get('away_xg', 0):.2f}",
                    'BTTS %': f"{pred.get('btts', 0) * 100:.1f}",
                    'Over 2.5 %': f"{pred.get('over_25', 0) * 100:.1f}",
                    'Predicted At': pred.get('predicted_at', '')
                })
            
            df = pd.DataFrame(df_data)
            
            # Write to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Predictions')
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Predictions']
                
                # Add formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#4472C4',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Apply header format
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Auto-adjust column widths
                for idx, col in enumerate(df.columns):
                    max_len = max(
                        df[col].astype(str).map(len).max(),
                        len(str(col))
                    ) + 2
                    worksheet.set_column(idx, idx, max_len)
            
            excel_bytes = output.getvalue()
            
            # Save if path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(excel_bytes)
            
            return excel_bytes
        
        except ImportError:
            raise ImportError(
                "pandas and xlsxwriter are required for Excel generation. "
                "Install with: pip install pandas xlsxwriter"
            )
    
    def _get_html_template(self) -> str:
        """Get HTML report template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soccer Predictor Pro - Match Prediction Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .match-info {{
            display: flex;
            justify-content: space-around;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .team {{
            text-align: center;
            flex: 1;
        }}
        .team h2 {{
            margin: 0;
            color: #667eea;
            font-size: 1.8em;
        }}
        .vs {{
            font-size: 2em;
            font-weight: bold;
            color: #764ba2;
            margin: 0 20px;
        }}
        .probabilities {{
            margin: 30px 0;
        }}
        .probability-bar {{
            margin: 15px 0;
        }}
        .probability-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-weight: bold;
        }}
        .progress {{
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
        }}
        .progress-bar {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.3s ease;
        }}
        .home {{ background: linear-gradient(90deg, #28a745, #20c997); }}
        .draw {{ background: linear-gradient(90deg, #ffc107, #ffdb58); color: #333; }}
        .away {{ background: linear-gradient(90deg, #dc3545, #fd7e14); }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚽ Soccer Predictor Pro</h1>
            <p>Professional Match Prediction Report</p>
        </div>
        
        <div class="content">
            <div class="match-info">
                <div class="team">
                    <h2>{home_team}</h2>
                    <p>Home Team</p>
                </div>
                <div class="vs">VS</div>
                <div class="team">
                    <h2>{away_team}</h2>
                    <p>Away Team</p>
                </div>
            </div>
            
            <p style="text-align: center; color: #6c757d;">
                <strong>League:</strong> {league} | 
                <strong>Date:</strong> {match_date}
            </p>
            
            <div class="probabilities">
                <h3 style="color: #667eea;">Match Outcome Probabilities</h3>
                
                <div class="probability-bar">
                    <div class="probability-label">
                        <span>{home_team} Win</span>
                        <span>{home_win_prob}%</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar home" style="width: {home_win_prob}%">
                            {home_win_prob}%
                        </div>
                    </div>
                </div>
                
                <div class="probability-bar">
                    <div class="probability-label">
                        <span>Draw</span>
                        <span>{draw_prob}%</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar draw" style="width: {draw_prob}%">
                            {draw_prob}%
                        </div>
                    </div>
                </div>
                
                <div class="probability-bar">
                    <div class="probability-label">
                        <span>{away_team} Win</span>
                        <span>{away_win_prob}%</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar away" style="width: {away_win_prob}%">
                            {away_win_prob}%
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-label">Expected Goals (Home)</div>
                    <div class="metric-value">{home_xg}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Expected Goals (Away)</div>
                    <div class="metric-value">{away_xg}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Both Teams to Score</div>
                    <div class="metric-value">{btts_prob}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Over 2.5 Goals</div>
                    <div class="metric-value">{over_25_prob}%</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated on {generated_at} | Model Version: {model_version}</p>
            <p style="margin-top: 10px; font-size: 0.8em;">
                ⚠️ This prediction is for informational purposes only. Past performance does not guarantee future results.
            </p>
        </div>
    </div>
</body>
</html>"""
