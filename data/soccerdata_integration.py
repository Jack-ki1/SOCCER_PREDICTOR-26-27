"""
soccerdata integration — primary historical/advanced-metrics data source
(build plan §2, the standout find from the API research). Free, no key,
actively maintained, and gives xG/shot data that plain historical CSVs
don't. This is the soccer-analytics equivalent of what FastF1 is to the
F1 project this structure is modeled on: a local package that quietly
handles the messy scraping/parsing and hands back a tidy DataFrame.

soccerdata does its own local caching (config.settings.SOCCERDATA_CACHE_DIR)
so repeated calls within a session don't re-scrape FBref every time.
"""
from __future__ import annotations

import pandas as pd

from config.api_settings import SOCCERDATA_LEAGUE, SOCCERDATA_TRAIN_SEASONS
from config.settings import SOCCERDATA_CACHE_DIR


class SoccerdataError(Exception):
    pass


def _get_fbref(seasons: list[str] | None = None):
    try:
        import soccerdata as sd
    except ImportError as exc:
        raise SoccerdataError("`pip install soccerdata` to enable historical data ingestion.") from exc

    try:
        return sd.FBref(
            leagues=SOCCERDATA_LEAGUE,
            seasons=seasons or SOCCERDATA_TRAIN_SEASONS,
            data_dir=SOCCERDATA_CACHE_DIR,
        )
    except Exception as exc:  # soccerdata raises a mix of its own + requests exceptions on scrape failures
        raise SoccerdataError(f"Could not initialize FBref reader: {exc}") from exc


def get_team_season_stats(seasons: list[str] | None = None) -> pd.DataFrame:
    """Season-level team stats (goals, xG, possession, etc.) — the richest single call for training features."""
    fbref = _get_fbref(seasons)
    try:
        return fbref.read_team_season_stats()
    except Exception as exc:
        raise SoccerdataError(f"FBref team-season-stats scrape failed: {exc}") from exc


def get_schedule(seasons: list[str] | None = None) -> pd.DataFrame:
    """Match-by-match schedule with final scores — this is the raw material
    engine/feature_engineering.py's `history` list gets built from."""
    fbref = _get_fbref(seasons)
    try:
        return fbref.read_schedule()
    except Exception as exc:
        raise SoccerdataError(f"FBref schedule scrape failed: {exc}") from exc


# FBref's team-name spelling conventions differ from config.constants' short
# ids in ways that are NOT safe to derive by truncation — e.g. "Manchester
# City" and "Manchester Utd" would both naively truncate to "man", silently
# merging two different clubs' histories. Map explicitly instead.
FBREF_NAME_TO_ID = {
    "Arsenal": "ars", "Manchester City": "mci", "Hull City": "hul",
    "Newcastle Utd": "new", "Newcastle United": "new",
    "Brighton": "bha", "Brighton & Hove Albion": "bha",
    "Brentford": "bre", "Fulham": "ful",
    "Nott'ham Forest": "nfo", "Nottingham Forest": "nfo",
    "Everton": "eve", "Ipswich Town": "ips", "Sunderland": "sun",
    "Crystal Palace": "cry", "Leeds United": "lee", "Leeds Utd": "lee",
    "Chelsea": "che", "Tottenham": "tot", "Tottenham Hotspur": "tot",
    "Aston Villa": "avl", "Liverpool": "liv",
    "Manchester Utd": "mun", "Manchester United": "mun",
    "Bournemouth": "bou", "Coventry City": "cov",
}


def _map_fbref_name(name: str) -> str:
    club_id = FBREF_NAME_TO_ID.get(str(name).strip())
    if club_id is None:
        raise SoccerdataError(
            f"No FBref-name mapping for {name!r} — add it to FBREF_NAME_TO_ID before trusting "
            "this data (do NOT fall back to truncation; that silently merges different clubs)."
        )
    return club_id


def schedule_to_history_format(schedule_df: pd.DataFrame) -> list[dict]:
    """
    Reshapes soccerdata's FBref schedule DataFrame into the plain-dict
    history format engine/feature_engineering.py expects
    ({date, home_id, away_id, home_goals, away_goals, season}). Column
    names follow soccerdata's documented FBref schedule schema; if a
    future soccerdata version renames columns, this is the one place
    that needs updating.
    """
    required = {"date", "home_team", "away_team", "home_score", "away_score"}
    missing = required - set(schedule_df.reset_index().columns)
    if missing:
        raise SoccerdataError(f"FBref schedule is missing expected columns {missing} — soccerdata's schema may have changed")

    history = []
    for _, row in schedule_df.reset_index().iterrows():
        if pd.isna(row.get("home_score")) or pd.isna(row.get("away_score")):
            continue  # fixture not yet played
        history.append({
            "date": pd.to_datetime(row["date"]).date(),
            "home_id": _map_fbref_name(row["home_team"]),
            "away_id": _map_fbref_name(row["away_team"]),
            "home_goals": int(row["home_score"]),
            "away_goals": int(row["away_score"]),
            "season": str(row.get("season", "")),
        })
    return history
