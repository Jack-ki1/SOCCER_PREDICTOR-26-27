"""Head-to-head comparison and championship forecasting routes."""

from flask import Blueprint, jsonify, request, render_template
from src.soccer_predictor.services.h2h_analyzer import get_h2h_analyzer
from src.soccer_predictor.services.championship_forecaster import get_championship_forecaster
from src.soccer_predictor.services.fixture_service import get_fixture_service

bp = Blueprint('comparison', __name__, url_prefix='/comparison')

h2h_analyzer = get_h2h_analyzer()
championship_forecaster = get_championship_forecaster()
fixture_service = get_fixture_service()


@bp.route('/h2h')
def h2h_page():
    """Head-to-head comparison page."""
    leagues = fixture_service.get_leagues()
    return render_template('comparison/h2h.html', leagues=leagues)


@bp.route('/api/h2h', methods=['POST'])
def api_h2h_compare():
    """API endpoint for H2H comparison."""
    data = request.json
    # TODO: Implement real H2H comparison using API data
    return jsonify({"error": "H2H comparison not yet implemented with real data"})


@bp.route('/championship')
def championship_page():
    """Championship forecasting page."""
    leagues = fixture_service.get_leagues()
    return render_template('comparison/championship.html', leagues=leagues)


@bp.route('/api/championship', methods=['POST'])
def api_championship_forecast():
    """API endpoint for championship forecasting."""
    data = request.json
    # TODO: Implement real championship forecasting using API data
    return jsonify({"error": "Championship forecasting not yet implemented with real data"})


@bp.route('/api/championship/report')
def api_championship_report():
    """Generate championship forecast HTML report."""
    from src.soccer_predictor.services.report_generator import get_report_generator
    
    league = request.args.get('league', 'Premier League')
    
    # Get forecast data (simplified for demo)
    forecaster = get_championship_forecaster()
    standings_list = get_league_standings(league)
    
    current_standings = {}
    for team_data in standings_list:
        current_standings[team_data['team_id']] = {
            'points': team_data['points'],
            'position': team_data['position']
        }
    
    forecast = forecaster.forecast_season(league, current_standings, [])
    
    # Generate report
    generator = get_report_generator()
    html = forecaster.generate_forecast_report(forecast)
    
    # Save report
    filepath = generator.save_report(html, f"championship_{league.replace(' ', '_')}")
    
    return jsonify({'report_path': filepath})
