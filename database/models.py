"""
SQLAlchemy models — see EPL_PREDICTOR_2026_BUILD_PLAN.md §7 for the schema
rationale. SQLite locally (zero setup), Postgres/Supabase in production;
SQLAlchemy abstracts the dialect so nothing here needs to change either way.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Club(Base):
    __tablename__ = "clubs"

    id = Column(String, primary_key=True)          # short code, e.g. 'ars'
    fpl_team_id = Column(Integer, unique=True, nullable=True)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    color_hex = Column(String, nullable=True)

    ratings = relationship("ClubSeasonRating", back_populates="club")


class ClubSeasonRating(Base):
    """
    One row per club per (season, as_of_date, source) — ratings are a
    time-varying snapshot, not a constant attribute of the club. This is
    what makes it possible to track how a fitted-from-data rating drifts
    across a season, and to compare 'fpl_seed' vs 'dixon_coles_fit' vs
    'ml_ensemble' side by side.
    """
    __tablename__ = "club_season_ratings"
    __table_args__ = (UniqueConstraint("club_id", "season", "as_of_date", "source"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    club_id = Column(String, ForeignKey("clubs.id"), nullable=False)
    season = Column(String, nullable=False)
    as_of_date = Column(DateTime, nullable=False, default=utcnow)
    attack_rating = Column(Float, nullable=False)
    defense_rating = Column(Float, nullable=False)
    home_advantage = Column(Float, nullable=False)
    elo = Column(Float, nullable=True)
    source = Column(String, nullable=False)         # 'illustrative_seed' | 'fpl_seed' | 'dixon_coles_fit' | 'ml_ensemble'
    model_version = Column(String, nullable=True)

    club = relationship("Club", back_populates="ratings")


class Fixture(Base):
    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(String, nullable=False)
    matchweek = Column(Integer, nullable=False)
    home_club_id = Column(String, ForeignKey("clubs.id"), nullable=False)
    away_club_id = Column(String, ForeignKey("clubs.id"), nullable=False)
    kickoff_utc = Column(DateTime, nullable=True)
    venue = Column(String, nullable=True)
    is_confirmed = Column(Boolean, default=False)   # real broadcaster-confirmed vs generated
    fpl_fixture_id = Column(Integer, unique=True, nullable=True)

    home_goals = Column(Integer, nullable=True)
    away_goals = Column(Integer, nullable=True)
    finished = Column(Boolean, default=False)
    home_xg = Column(Float, nullable=True)
    away_xg = Column(Float, nullable=True)

    predictions = relationship("Prediction", back_populates="fixture")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)
    model_version = Column(String, nullable=False)
    generated_at = Column(DateTime, default=utcnow)
    p_home = Column(Float, nullable=False)
    p_draw = Column(Float, nullable=False)
    p_away = Column(Float, nullable=False)
    lambda_home = Column(Float, nullable=False)
    lambda_away = Column(Float, nullable=False)
    p_btts = Column(Float, nullable=True)
    p_over_2_5 = Column(Float, nullable=True)
    score_matrix = Column(JSON, nullable=True)      # the 7x7 grid, for the correct-score UI
    was_correct_1x2 = Column(Boolean, nullable=True)  # filled in once the match is played

    fixture = relationship("Fixture", back_populates="predictions")


class SeasonSimulation(Base):
    __tablename__ = "season_simulations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    n_sims = Column(Integer, nullable=False)
    generated_at = Column(DateTime, default=utcnow)
    club_id = Column(String, ForeignKey("clubs.id"), nullable=False)
    title_prob = Column(Float, nullable=True)
    top4_prob = Column(Float, nullable=True)
    releg_prob = Column(Float, nullable=True)
    avg_points = Column(Float, nullable=True)


class ModelRun(Base):
    """Lightweight mirror of an MLflow run, for fast API queries without hitting MLflow at request time."""
    __tablename__ = "model_runs"

    run_id = Column(String, primary_key=True)
    model_type = Column(String, nullable=False)      # 'dixon_coles' | 'elo' | 'xgboost_1x2' | 'ensemble'
    trained_at = Column(DateTime, nullable=True)
    train_window = Column(String, nullable=True)      # e.g. '2022-23..2025-26'
    metrics = Column(JSON, nullable=True)             # {"log_loss": 0.98, "accuracy": 0.54, ...}
    is_active = Column(Boolean, default=False)
