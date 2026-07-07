"""SOCCER PREDICTOR PRO - Flask Edition
Production-grade probabilistic soccer prediction dashboard.
2026-2027 Season Focus | No World Cup

TRANSFORMED with F1 Predictor 2026 Architecture:
- Database persistence (SQLite + SQLAlchemy)
- Probability calibration (Platt Scaling / Temperature Scaling)
- Bayesian weight optimization (Optuna)
- Comprehensive accuracy tracking (Brier Score, Log Loss, ECE)
- Professional report generation (HTML, PDF, CSV, JSON, Excel)
- Real-world context factors
- Multi-dimensional team ratings
- Vectorized Monte Carlo simulations (50x faster)
"""

import os
from datetime import timedelta
from flask import Flask
from flask_session import Session
from dotenv import load_dotenv

from src.soccer_predictor.routes import main, predictions, fixtures, leagues, export, api
from src.soccer_predictor.routes import comparison, reports, setup

from src.soccer_predictor.routes.advanced_predictions import bp as advanced_bp
from state import init_session_defaults


def create_app(config_name="development"):
    """Application factory pattern."""
    load_dotenv()

    app = Flask(
        __name__,
        template_folder="src/soccer_predictor/templates",
        static_folder="src/soccer_predictor/static",
    )

    # Config
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me-2026")
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_session")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=4)
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB
    app.config["JSON_SORT_KEYS"] = False

    # Ensure session dir exists
    os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)

    Session(app)

    # Initialize database on startup
    with app.app_context():
        try:
            from src.soccer_predictor.data.models import create_engine_and_tables
            print("[db] Initializing database...")
            create_engine_and_tables()
            print("[db] Database initialized successfully.")
        except Exception as e:
            print(f"[db] Database initialization warning: {e}")

    # Session init before each request
    @app.before_request
    def before_request():
        init_session_defaults()

    # Context processors
    @app.context_processor
    def inject_globals():
        from src.soccer_predictor.data.live_config import LEAGUE_CONFIGS
        return {
            "leagues": LEAGUE_CONFIGS,
            "season": "2026-2027",
            "app_name": "Soccer Predictor Pro",
            "app_version": "5.0.0-Transformed",
        }

    # Register blueprints - Core routes
    app.register_blueprint(main.bp)
    app.register_blueprint(predictions.bp, url_prefix="/predictions")
    app.register_blueprint(fixtures.bp, url_prefix="/fixtures")
    app.register_blueprint(leagues.bp, url_prefix="/leagues")
    app.register_blueprint(export.bp, url_prefix="/export")
    app.register_blueprint(api.bp, url_prefix="/api/v1")

    # Register feature routes
    app.register_blueprint(comparison.bp)  # /comparison
    app.register_blueprint(reports.bp)  # /reports
    app.register_blueprint(setup.bp)  # /setup

    
    # Register NEW advanced features (F1 Predictor inspired)
    app.register_blueprint(advanced_bp, url_prefix="/advanced")  # /advanced/*

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found", "message": str(e)}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"error": "Internal server error", "message": str(e)}, 500

    return app


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SOCCER PREDICTOR PRO v5.0 - TRANSFORMED EDITION")
    print("="*80)
    print("\nFeatures:")
    print("  - Database persistence (SQLite + SQLAlchemy)")
    print("  - Probability calibration (Platt Scaling)")
    print("  - Bayesian weight optimization (Optuna)")
    print("  - Brier Score & Log Loss tracking")
    print("  - Expected Calibration Error (ECE)")
    print("  - Reliability diagrams")
    print("  - Professional reports (HTML/PDF/CSV/JSON/Excel)")
    print("  - Real-world context factors")
    print("  - Multi-dimensional team ratings")
    print("  - Automated accuracy tracking")
    print("\nAccess the app at: http://localhost:5000")
    print("Advanced API: http://localhost:5000/advanced/")
    print("="*80 + "\n")
    
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
