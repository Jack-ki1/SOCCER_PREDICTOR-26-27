"""
Lineup / rotation-risk analysis.

Analogous to the F1 project's pit_strategy.py in spirit — both are about
anticipating a tactical/personnel decision before it's confirmed. Here
that means: is a club likely to rotate its strongest XI for this fixture?
Feeds engine/injury_model.py's availability adjustment with a probability-
weighted estimate rather than requiring confirmed team news (which isn't
available until ~1 hour before kickoff).
"""
from __future__ import annotations

from dataclasses import dataclass

from config.constants import EUROPEAN_CLUB_IDS


@dataclass
class RotationRisk:
    club_id: str
    risk_score: float          # 0-1, higher = more likely to see changes from the strongest XI
    reasons: list[str]


def estimate_rotation_risk(
    club_id: str,
    days_since_last_match: int | None,
    days_until_next_match: int | None,
    is_cup_competition: bool = False,
    league_position_context: str = "mid_table",  # 'title_race' | 'europe_race' | 'relegation_battle' | 'mid_table'
) -> RotationRisk:
    """
    A heuristic score, not a trained model — there's no free, reliable feed
    of "confirmed starting XI intent" ahead of kickoff, so this stays
    explicit and explainable rather than pretending to more precision than
    the inputs support. Wire in real team-news scraping/NLP (see
    engine/huggingface_models.py) to sharpen this once you have a source.
    """
    score = 0.15  # baseline: most clubs mostly play their strongest team most of the time
    reasons = []

    if club_id in EUROPEAN_CLUB_IDS:
        score += 0.15
        reasons.append("Plays in Europe — midweek fixture load increases rotation likelihood")

    if days_until_next_match is not None and days_until_next_match <= 3:
        score += 0.20
        reasons.append(f"Only {days_until_next_match} days until the next fixture")

    if days_since_last_match is not None and days_since_last_match <= 3:
        score += 0.15
        reasons.append(f"Played only {days_since_last_match} days ago")

    if is_cup_competition:
        score += 0.20
        reasons.append("Cup competition — commonly rotated for domestic league priority")

    if league_position_context == "relegation_battle":
        score -= 0.15  # relegation-threatened teams tend to play strongest XI regardless of fatigue
        reasons.append("Relegation battle — likely to prioritize the strongest available XI anyway")
    elif league_position_context == "title_race":
        score -= 0.10
        reasons.append("Title race — squad depth still gets used, but less rotation than mid-table dead rubbers")

    score = max(0.0, min(1.0, score))
    return RotationRisk(club_id=club_id, risk_score=score, reasons=reasons)
