"""Flask session default values and initialization."""

from flask import session


def init_session_defaults():
    """Initialize default session values."""
    defaults = {
        "selected_league": "Premier League",
        "selected_date_range": "next_7_days",
        "prediction_filters": {
            "min_confidence": 0.6,
            "show_value_bets": True,
            "max_kelly_fraction": 0.10
        },
        "ui_settings": {
            "theme": "dark",
            "compact_view": False,
            "show_prob_percent": True,
            "precision": 2
        },
        "model_weights": {
            "poisson": 0.40,  # ← FIXED: Match config
            "elo": 0.25,
            "market": 0.20,
            "ml": 0.15
        },
        "last_api_refresh": None,
        "api_status": {
            "football_data": False,
            "api_football": False
        },
        "market_odds_enabled": True,  # NEW: Enable market odds integration
        "calibration_enabled": True,  # NEW: Enable probability calibration
        "drift_alert_threshold": 0.02,  # NEW: Threshold for drift detection alerts
        "last_calibration_time": None,  # NEW: Track last calibration time
    }
    
    for key, value in defaults.items():
        if key not in session:
            session[key] = value
