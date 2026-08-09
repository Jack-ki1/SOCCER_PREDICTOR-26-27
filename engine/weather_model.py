"""
Weather model.

Kept from the F1-project pattern (weather affected lap times there; it
affects scoring rates here) — heavy rain/wind measurably suppresses goals
per academic studies on weather and football scoring (fewer clean touches,
more error-prone finishing), though the effect size is modest compared to
team-quality differences. Treat this as a small multiplicative nudge on
top of the Dixon-Coles lambdas, not a primary signal.

Not wired into the live engine by default (no free, reliable per-fixture
forecast source is assumed here) — this module is ready to plug into
engine/predictor.py once you have a weather feed for each ground.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WeatherConditions:
    temperature_c: float | None = None
    wind_speed_kph: float | None = None
    precipitation_mm: float | None = None
    condition: str = "unknown"  # 'clear' | 'rain' | 'heavy_rain' | 'wind' | 'unknown'


# Illustrative, conservative multipliers — small effects, and only applied
# when conditions are known (never guess a game is rain-affected).
_CONDITION_GOAL_MULTIPLIER = {
    "clear": 1.00,
    "rain": 0.97,
    "heavy_rain": 0.92,
    "wind": 0.95,
    "unknown": 1.00,
}


def weather_lambda_adjustment(conditions: WeatherConditions) -> float:
    """Multiplicative adjustment to apply to both lambda_home and lambda_away."""
    mult = _CONDITION_GOAL_MULTIPLIER.get(conditions.condition, 1.0)
    if conditions.wind_speed_kph and conditions.wind_speed_kph > 40:
        mult *= 0.96  # extra dampening for genuinely disruptive wind, on top of the condition tag
    return mult


def classify_condition(precipitation_mm: float | None, wind_speed_kph: float | None) -> str:
    if precipitation_mm is None and wind_speed_kph is None:
        return "unknown"
    precipitation_mm = precipitation_mm or 0
    wind_speed_kph = wind_speed_kph or 0
    if precipitation_mm > 7.5:
        return "heavy_rain"
    if precipitation_mm > 1.0:
        return "rain"
    if wind_speed_kph > 30:
        return "wind"
    return "clear"
