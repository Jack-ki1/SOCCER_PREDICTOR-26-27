"""Report generation and export routes."""

from flask import Blueprint, jsonify, request, send_file
from src.soccer_predictor.services.report_generator import get_report_generator
from src.soccer_predictor.services.database import get_database
from src.soccer_predictor.services.fixture_service import get_fixture_service

bp = Blueprint('reports', __name__, url_prefix='/reports')

report_generator = get_report_generator()
database = get_database()
fixture_service = get_fixture_service()


@bp.route('/match/<match_id>')
def match_report(match_id: str):
    """Generate match report."""
    match = fixture_service.get_fixture_by_id(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404
    
    # Generate report using real match data
    report_data = report_generator.generate_match_report(match)
    return jsonify(report_data)


@bp.route('/league/<league_name>')
def league_report(league_name: str):
    """Generate league report."""
    # TODO: Implement real league report using API data
    return jsonify({"error": "League report not yet implemented with real data"})


@bp.route('/export/<match_id>')
def export_report(match_id: str):
    """Export match report in various formats."""
    match = fixture_service.get_fixture_by_id(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404
    
    format_type = request.args.get('format', 'json')
    report_file = report_generator.export_match_report(match, format_type)
    
    if report_file:
        return send_file(report_file, as_attachment=True)
    else:
        return jsonify({"error": "Export failed"}), 500


@bp.route('/download/match/<match_id>')
def download_match_report(match_id):
    """Download match report as HTML file."""
    from flask import after_this_request
    import os
    
    match = get_match_by_id(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    prediction = {
        'home_win_prob': 0.55,
        'draw_prob': 0.25,
        'away_win_prob': 0.20,
        'predicted_home_goals': 2.1,
        'predicted_away_goals': 1.3,
        'predicted_score': '2-1',
        'confidence_score': 0.72
    }
    
    match_data = {
        'home_team': match.home_team.name,
        'away_team': match.away_team.name,
        'league': match.league,
        'date': str(match.date),
        'venue': 'Home Stadium'
    }
    
    generator = get_report_generator()
    html = generator.generate_match_preview(match_data, prediction)
    filepath = generator.save_report(html, f"match_{match_id}_download")
    
    return send_file(filepath, as_attachment=True, download_name=f"{match_id}_report.html")








