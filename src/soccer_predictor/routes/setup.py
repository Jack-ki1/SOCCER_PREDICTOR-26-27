"""Setup and data health monitoring routes."""

from flask import Blueprint, render_template, jsonify, request
import os

from src.soccer_predictor.services.data_health_service import get_data_health_service
from src.soccer_predictor.services.fixture_service import get_fixture_service

bp = Blueprint('setup', __name__, url_prefix='/setup')

data_health_service = get_data_health_service()
fixture_service = get_fixture_service()


@bp.route('/')
def setup_page():
    """Setup and data health monitoring page."""
    # Using get_setup_requirements instead of get_overall_health
    health_data = data_health_service.get_setup_requirements()
    provider_status = data_health_service.get_provider_status()
    league_summary = data_health_service.get_league_data_summary()
    
    return render_template(
        'setup.html',
        health_data=health_data,
        provider_status=provider_status,
        league_summary=league_summary
    )


@bp.route('/api/health')
def api_health():
    """API endpoint for detailed health information."""
    # Using get_setup_requirements instead of get_overall_health
    health_data = data_health_service.get_setup_requirements()
    return jsonify(health_data)


@bp.route('/api/providers')
def api_providers():
    """API endpoint for provider status."""
    provider_status = data_health_service.get_provider_status()
    return jsonify(provider_status)


@bp.route('/api/configure', methods=['POST'])
def api_configure():
    """API endpoint to configure API keys via environment variables."""
    data = request.get_json() or {}
    
    # Update environment variables for the current session
    if 'football_data_key' in data and data['football_data_key']:
        os.environ['FOOTBALL_DATA_API_KEY'] = data['football_data_key']
    
    if 'odds_api_key' in data and data['odds_api_key']:
        os.environ['ODDS_API_KEY'] = data['odds_api_key']
    
    if 'rapidapi_key' in data and data['rapidapi_key']:
        os.environ['RAPIDAPI_KEY'] = data['rapidapi_key']
    
    # Clear the singleton instances so they get recreated with new API keys
    from src.soccer_predictor.services.data_health_service import _data_health_service
    from src.soccer_predictor.services.fixture_service import _fixture_service
    from src.soccer_predictor.services.api_service import _data_service
    
    # Reset the global instances by setting them to None
    import src.soccer_predictor.services.data_health_service as dh_module
    import src.soccer_predictor.services.fixture_service as f_module
    import src.soccer_predictor.services.api_service as api_module
    
    dh_module._data_health_service = None
    f_module._fixture_service = None
    api_module._data_service = None
    
    # Now get the fresh instances with new API keys
    from src.soccer_predictor.services.data_health_service import get_data_health_service
    updated_health_service = get_data_health_service()
    updated_provider_status = updated_health_service.get_provider_status()
    
    return jsonify({
        "status": "success",
        "message": "API keys configured successfully. Data will refresh shortly.",
        "provider_status": updated_provider_status
    })


@bp.route('/api/sync', methods=['POST'])
def api_sync_now():
    """Trigger manual data sync."""
    # TODO: Implement manual sync functionality
    return jsonify({
        "status": "success",
        "message": "Manual sync triggered",
        "timestamp": "2026-06-30T19:22:05"
    })