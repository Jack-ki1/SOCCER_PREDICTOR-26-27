"""
ScraperFC integration — optional enrichment only (build plan §2). Squad
market value (via Transfermarkt) is a genuinely useful ML feature — a
team's transfer-market valuation correlates with quality independent of
current form — but this is a scraper against a site that can change
layout without warning, so it's gated behind
config.api_settings.SCRAPERFC_ENABLED and never a hard dependency for the
rest of the app to function.
"""
from __future__ import annotations

from config.api_settings import SCRAPERFC_ENABLED


class ScraperFCError(Exception):
    pass


def _require_enabled() -> None:
    if not SCRAPERFC_ENABLED:
        raise ScraperFCError(
            "ScraperFC integration is disabled by default (it scrapes Transfermarkt, which can "
            "change layout without warning). Set EPL_ENABLE_SCRAPERFC=true to opt in."
        )


def get_squad_market_values(club_name: str) -> dict:
    """
    Returns {'club': str, 'total_value_eur': float, 'players': [...]} for
    one club. Requires `pip install ScraperFC` and SCRAPERFC_ENABLED=true.
    Wrapped in a try/except because ScraperFC's Transfermarkt scraper is
    exactly the kind of "can break on a site redesign" dependency this
    module's docstring warns about — fail loudly and specifically rather
    than returning silently-wrong data.
    """
    _require_enabled()
    try:
        import ScraperFC as sfc
    except ImportError as exc:
        raise ScraperFCError("`pip install ScraperFC` to enable market-value enrichment.") from exc

    try:
        scraper = sfc.Transfermarkt()
        return scraper.scrape_club_market_values(club_name)
    except Exception as exc:
        raise ScraperFCError(f"ScraperFC market-value scrape failed for {club_name!r}: {exc}") from exc


def market_value_feature(total_value_eur: float, league_avg_value_eur: float) -> float:
    """Normalizes a club's total squad value against the league average, for use
    as one more engine/feature_engineering.py column — a ratio around 1.0 is average."""
    if league_avg_value_eur <= 0:
        return 1.0
    return total_value_eur / league_avg_value_eur
