"""Database models using SQLAlchemy ORM."""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()


class Prediction(Base):
    """Store match predictions."""
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(100), nullable=False, index=True)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    league = Column(String(100), nullable=False)
    match_date = Column(DateTime, nullable=False)
    
    # Raw probabilities (before calibration)
    raw_home_win = Column(Float, nullable=False)
    raw_draw = Column(Float, nullable=False)
    raw_away_win = Column(Float, nullable=False)
    
    # Calibrated probabilities
    calibrated_home_win = Column(Float)
    calibrated_draw = Column(Float)
    calibrated_away_win = Column(Float)
    is_calibrated = Column(Boolean, default=False)
    
    # Additional markets
    home_xg = Column(Float)
    away_xg = Column(Float)
    btts_prob = Column(Float)
    over_25_prob = Column(Float)
    
    # Model configuration
    model_weights = Column(JSON)  # Store weights used for this prediction
    model_version = Column(String(50))
    
    # Metadata
    predicted_at = Column(DateTime, default=datetime.utcnow)
    simulation_count = Column(Integer, default=50000)
    
    # Relationship to actual result
    result = relationship("MatchResult", back_populates="prediction", uselist=False)
    
    def __repr__(self):
        return f"<Prediction {self.home_team} vs {self.away_team} on {self.match_date}>"


class MatchResult(Base):
    """Store actual match results for accuracy tracking."""
    __tablename__ = 'match_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(100), nullable=False, unique=True, index=True)
    home_goals = Column(Integer, nullable=False)
    away_goals = Column(Integer, nullable=False)
    match_date = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    # Derived outcomes
    home_win = Column(Boolean)  # True if home won
    draw = Column(Boolean)  # True if draw
    away_win = Column(Boolean)  # True if away won
    
    # Relationship to prediction
    prediction_id = Column(Integer, ForeignKey('predictions.id'))
    prediction = relationship("Prediction", back_populates="result")
    
    def calculate_outcomes(self):
        """Calculate win/draw/loss outcomes."""
        self.home_win = self.home_goals > self.away_goals
        self.draw = self.home_goals == self.away_goals
        self.away_win = self.away_goals > self.home_goals


class AccuracyMetric(Base):
    """Store daily/weekly accuracy metrics."""
    __tablename__ = 'accuracy_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    
    # Core metrics
    total_predictions = Column(Integer, default=0)
    matched_predictions = Column(Integer, default=0)  # Predictions with actual results
    
    # Accuracy metrics
    outcome_accuracy = Column(Float)  # % correct outcome predictions
    exact_score_accuracy = Column(Float)  # % exact score predictions
    
    # Probability quality metrics
    brier_score = Column(Float)
    log_loss = Column(Float)
    expected_calibration_error = Column(Float)  # ECE
    
    # Goal prediction errors
    avg_home_goal_error = Column(Float)
    avg_away_goal_error = Column(Float)
    avg_total_goal_error = Column(Float)
    
    # Market accuracy
    btts_accuracy = Column(Float)
    over_25_accuracy = Column(Float)
    
    # Value bet performance
    value_bet_count = Column(Integer, default=0)
    value_bet_wins = Column(Integer, default=0)
    value_bet_roi = Column(Float)
    
    # Trend indicators
    trend_indicator = Column(String(20))  # 'improving', 'declining', 'stable'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AccuracyMetric {self.metric_date} ({self.period_type})>"


class CalibrationParams(Base):
    """Store calibration parameters for different model versions."""
    __tablename__ = 'calibration_params'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_version = Column(String(50), nullable=False, unique=True)
    calibration_method = Column(String(50), nullable=False)  # 'platt', 'temperature', 'isotonic'
    
    # Platt Scaling parameters
    platt_a_home = Column(Float)
    platt_b_home = Column(Float)
    platt_a_draw = Column(Float)
    platt_b_draw = Column(Float)
    platt_a_away = Column(Float)
    platt_b_away = Column(Float)
    
    # Temperature Scaling parameter
    temperature = Column(Float)
    
    # Calibration quality
    calibration_brier_score = Column(Float)
    calibration_ece = Column(Float)
    
    # Training data info
    training_samples = Column(Integer)
    trained_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<CalibrationParams {self.model_version} ({self.calibration_method})>"


class ModelWeights(Base):
    """Store ensemble model weights over time."""
    __tablename__ = 'model_weights'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Model weights
    poisson_weight = Column(Float, nullable=False)
    elo_weight = Column(Float, nullable=False)
    ml_weight = Column(Float, nullable=False)
    market_weight = Column(Float, nullable=False)
    
    # Optimization info
    optimized_by = Column(String(50))  # 'manual', 'optuna', 'auto'
    optimization_metric = Column(String(50))  # 'brier_score', 'log_loss', 'accuracy'
    optimization_score = Column(Float)  # Score achieved with these weights
    
    # Context
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<ModelWeights at {self.timestamp}>"


class TeamRating(Base):
    """Store multi-dimensional team ratings."""
    __tablename__ = 'team_ratings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_name = Column(String(100), nullable=False, index=True)
    league = Column(String(100), nullable=False)
    season = Column(String(20), nullable=False)
    
    # Basic ratings
    overall_elo = Column(Float, default=1500)
    home_elo = Column(Float, default=1500)
    away_elo = Column(Float, default=1500)
    
    # Attack/Defense dimensions
    attack_strength = Column(Float, default=1.0)
    defense_strength = Column(Float, default=1.0)
    home_attack = Column(Float, default=1.0)
    home_defense = Column(Float, default=1.0)
    away_attack = Column(Float, default=1.0)
    away_defense = Column(Float, default=1.0)
    
    # Specialized ratings
    set_piece_offense = Column(Float, default=1.0)
    set_piece_defense = Column(Float, default=1.0)
    counter_attack_efficiency = Column(Float, default=1.0)
    high_pressure_performance = Column(Float, default=1.0)
    
    # Form metrics
    form_index = Column(Float, default=1.0)
    recent_form_5games = Column(Float)  # Last 5 games weighted
    recent_form_10games = Column(Float)  # Last 10 games weighted
    
    # Reliability
    reliability_index = Column(Float, default=1.0)  # Consistency measure
    injury_resilience = Column(Float, default=1.0)
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow)
    matches_played = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<TeamRating {self.team_name} (ELO: {self.overall_elo:.0f})>"


class ContextFactor(Base):
    """Store real-world context factors for matches."""
    __tablename__ = 'context_factors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(100), nullable=False, index=True)
    
    # Weather conditions
    weather_condition = Column(String(50))  # 'clear', 'rain', 'snow', etc.
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    precipitation_probability = Column(Float)
    
    # Referee information
    referee_name = Column(String(100))
    referee_cards_per_game = Column(Float)  # Average cards given
    referee_penalty_rate = Column(Float)  # Penalties per game
    
    # Team context
    home_injuries_count = Column(Integer, default=0)
    away_injuries_count = Column(Integer, default=0)
    home_suspensions_count = Column(Integer, default=0)
    away_suspensions_count = Column(Integer, default=0)
    
    # Motivation factors
    is_derby = Column(Boolean, default=False)
    is_title_decider = Column(Boolean, default=False)
    is_relegation_battle = Column(Boolean, default=False)
    motivation_score_home = Column(Float, default=1.0)
    motivation_score_away = Column(Float, default=1.0)
    
    # Travel fatigue
    home_travel_distance_km = Column(Float, default=0)
    away_travel_distance_km = Column(Float)
    home_rest_days = Column(Integer)
    away_rest_days = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ContextFactor {self.match_id}>"


# Database engine and session factory
def get_database_url():
    """Get database URL from environment or use default."""
    return os.getenv('DATABASE_URL', 'sqlite:///soccer_predictor.db')


def create_engine_and_tables():
    """Create database engine and all tables."""
    engine = create_engine(get_database_url(), echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Create and return a database session."""
    engine = create_engine_and_tables()
    Session = sessionmaker(bind=engine)
    return Session()


# Initialize database if run directly
if __name__ == '__main__':
    print("Creating database tables...")
    engine = create_engine_and_tables()
    print("✅ Database tables created successfully!")
    print(f"Database location: {get_database_url()}")
