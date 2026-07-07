"""Global configuration constants."""

import os


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SEASON = "2026-2027"

    # Model defaults
    DEFAULT_ENSEMBLE_WEIGHTS = {"poisson": 0.50, "elo": 0.30, "market": 0.20, "ml": 0.0}
    MAX_GOALS = 8
    HOME_ADVANTAGE_XG = 0.18
    HOME_ADVANTAGE_ELO = 65
    ELO_K_FACTOR = 32

    # Simulation
    DEFAULT_SIMULATION_ITERATIONS = 5000
    MAX_SIMULATION_ITERATIONS = 20000

    # SDR
    SDR_LAG_MONTHS = 6
    SDR_N_DIRECTIONS = 2

    # Arena
    ARENA_CV_SPLITS = 5
    ARENA_PROMOTION_THRESHOLD = 0.001  # RPS improvement

    # Evaluation thresholds
    MIN_RPS = 0.190

    # Data
    ROLLING_WINDOWS = [5, 10, 20]
    FORM_DECAY = 0.95

    # UI
    PROBABILITY_PRECISION = 4
    CHART_THEME = "plotly_dark"


class DevelopmentConfig(Config):
    """Development overrides."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production overrides."""
    DEBUG = False
    TESTING = False
    SESSION_TYPE = "redis"
