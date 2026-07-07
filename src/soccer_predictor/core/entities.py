"""Data models and entities for the prediction system."""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import date, datetime


@dataclass
class TeamRating:
    """Team strength and metadata."""
    team_id: str
    name: str
    league: str
    elo: float = 1500.0
    attack: float = 1.0
    defense: float = 1.0
    home_attack: float = 1.0
    home_defense: float = 1.0
    away_attack: float = 1.0
    away_defense: float = 1.0
    form_index: float = 0.0  # -1.0 to +1.0
    xg_for: float = 0.0
    xg_against: float = 0.0
    ppda: float = 0.0  # passes per defensive action
    market_value: float = 0.0  # in millions
    squad_size: int = 25
    injuries: int = 0
    rest_days: int = 7

    # SDR trajectory features
    elo_trajectory: List[float] = field(default_factory=list)
    form_trajectory: List[float] = field(default_factory=list)


@dataclass
class Match:
    """Fixture / match representation."""
    match_id: str
    league: str
    date: date
    home_team: TeamRating
    away_team: TeamRating
    matchday: int = 1
    season: str = "2026-2027"
    neutral_venue: bool = False

    # Market odds (decimal)
    home_odds: Optional[float] = None
    draw_odds: Optional[float] = None
    away_odds: Optional[float] = None
    over_25_odds: Optional[float] = None
    btts_odds: Optional[float] = None

    # Context
    weather: str = "clear"
    temperature: float = 15.0
    referee: str = ""
    attendance: int = 0

    # Historical (for training)
    actual_home_goals: Optional[int] = None
    actual_away_goals: Optional[int] = None
    actual_result: Optional[int] = None  # 0=home, 1=draw, 2=away

    # Live/API metadata
    status: str = "SCHEDULED"
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    data_source: str = "sample"
    last_updated: Optional[datetime] = None


@dataclass
class Prediction:
    """Probabilistic match prediction output."""
    match_id: str
    home_win: float           # ← canonical field name (was wrong in ml_model.py)
    draw: float
    away_win: float
    home_xg: float = 1.35
    away_xg: float = 1.35
    btts: float = 0.50
    over_25: float = 0.50
    correct_score: Dict[str, float] = field(default_factory=dict)
    drivers: List[str] = field(default_factory=list)
    component_probs: Dict[str, List[float]] = field(default_factory=dict)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    calibrated: bool = False
    confidence: float = 0.5
    value_bets: List[Dict] = field(default_factory=list)  # New: Kelly signals

    # Backward-compat properties (old code used _prob suffix)
    @property
    def home_win_prob(self) -> float:
        return self.home_win

    @property
    def draw_prob(self) -> float:
        return self.draw

    @property
    def away_win_prob(self) -> float:
        return self.away_win

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_id": self.match_id,
            "home_win": round(self.home_win, 4),
            "draw": round(self.draw, 4),
            "away_win": round(self.away_win, 4),
            "home_xg": round(self.home_xg, 2),
            "away_xg": round(self.away_xg, 2),
            "btts": round(self.btts, 4),
            "over_25": round(self.over_25, 4),
            "correct_score": {k: round(v, 4) for k, v in self.correct_score.items()},
            "drivers": self.drivers,
            "component_probs": self.component_probs,
            "feature_importance": self.feature_importance,
            "calibrated": self.calibrated,
        }


@dataclass
class LeagueForecast:
    """League simulation output."""
    league: str
    season: str
    iterations: int
    team_forecasts: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "league": self.league,
            "season": self.season,
            "iterations": self.iterations,
            "team_forecasts": self.team_forecasts,
        }
