"""Pydantic models for API requests/responses."""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import date


class PredictionRequest(BaseModel):
    """Single match prediction request."""
    match_id: str = Field(..., description="Unique match identifier")
    weights: Optional[Dict[str, float]] = Field(None, description="Custom ensemble weights")
    use_calibration: bool = Field(default=True, description="Apply probability calibration")
    use_sdr: bool = Field(default=True, description="Use SDR features")


class BatchPredictionRequest(BaseModel):
    """Batch prediction request."""
    match_ids: List[str] = Field(..., min_items=1, max_items=100, description="List of match IDs")
    weights: Optional[Dict[str, float]] = Field(None, description="Custom ensemble weights")

    @validator('match_ids')
    def validate_match_ids(cls, v):
        if not v:
            raise ValueError('match_ids cannot be empty')
        return v


class SimulationRequest(BaseModel):
    """League simulation request."""
    league: str = Field(..., description="League name")
    iterations: int = Field(default=5000, ge=1000, le=20000, description="Monte Carlo iterations")
    include_history: bool = Field(default=False, description="Include full simulation history")


class WeightUpdateRequest(BaseModel):
    """Ensemble weight update request."""
    poisson: float = Field(default=0.50, ge=0.0, le=1.0)
    elo: float = Field(default=0.30, ge=0.0, le=1.0)
    market: float = Field(default=0.20, ge=0.0, le=1.0)
    ml: float = Field(default=0.0, ge=0.0, le=1.0)

    @validator('poisson', 'elo', 'market', 'ml')
    def validate_weights(cls, v):
        return round(v, 4)

    @validator('poisson', 'elo', 'market', 'ml', pre=True)
    def normalize_weights(cls, values):
        # Weights are normalized in the service layer
        return values


class PredictionResponse(BaseModel):
    """Single match prediction response."""
    match_id: str
    home_win: float = Field(..., ge=0.0, le=1.0)
    draw: float = Field(..., ge=0.0, le=1.0)
    away_win: float = Field(..., ge=0.0, le=1.0)
    home_xg: float = Field(..., ge=0.0)
    away_xg: float = Field(..., ge=0.0)
    btts: float = Field(..., ge=0.0, le=1.0)
    over_25: float = Field(..., ge=0.0, le=1.0)
    correct_score: Dict[str, float] = Field(default_factory=dict)
    drivers: List[str] = Field(default_factory=list)
    calibrated: bool = Field(default=False)
    component_probs: Optional[Dict[str, List[float]]] = None


class LeagueForecastResponse(BaseModel):
    """League forecast response."""
    league: str
    season: str
    iterations: int
    team_forecasts: List[Dict]


class ModelInfoResponse(BaseModel):
    """Model architecture info response."""
    architecture: str
    components: List[Dict[str, str]]
    ensemble_weights: Dict[str, float]
    champion_model: str
    features: int
    evaluation_metrics: List[str]


class DriftStatusResponse(BaseModel):
    """Drift detection status response."""
    status: str
    drift_detected: bool
    current_rps: float
    baseline_rps: float
    recommendation: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    season: str
    endpoints: List[str]
