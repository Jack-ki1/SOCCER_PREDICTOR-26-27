"""Data health and setup service for monitoring API connectivity and data quality."""

import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from src.soccer_predictor.services.api_service import get_data_service
from src.soccer_predictor.data.live_config import LEAGUE_CONFIGS


class DataHealthService:
    """Monitor and report on data provider health and connectivity."""
    
    def __init__(self):
        self.data_service = get_data_service()
    
    def get_provider_status(self) -> Dict[str, Dict]:
        """Get status of all configured data providers."""
        football_data_key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()
        odds_api_key = os.environ.get("ODDS_API_KEY", "").strip()
        rapidapi_key = os.environ.get("RAPIDAPI_KEY", "").strip()
        
        return {
            "football-data.org": {
                "configured": bool(football_data_key),
                "status": "active" if football_data_key else "missing_api_key",
                "last_sync": None,
                "supported_leagues": list(LEAGUE_CONFIGS.keys()) if football_data_key else []
            },
            "the-odds-api": {
                "configured": bool(odds_api_key),
                "status": "active" if odds_api_key else "missing_api_key",
                "last_sync": None,
                "supported_markets": ["h2h", "totals", "spreads"] if odds_api_key else []
            },
            "api-football": {
                "configured": bool(rapidapi_key),
                "status": "active" if rapidapi_key else "missing_api_key",
                "last_sync": None,
                "features": ["lineups", "statistics", "events"] if rapidapi_key else []
            }
        }
    
    def get_league_data_summary(self, league: str = None) -> Dict:
        """Get data summary for specific league or all leagues."""
        leagues = [league] if league else list(LEAGUE_CONFIGS.keys())
        summary = {
            "leagues": {},
            "total_fixtures": 0,
            "total_results": 0,
            "data_freshness": None
        }
        
        for lg in leagues:
            if lg not in LEAGUE_CONFIGS:
                continue
                
            try:
                # Get recent fixtures
                fixtures = self.data_service.football_data.get_fixtures(
                    competition_code=self._get_competition_code(lg),
                    date_from=(datetime.now().date()).isoformat(),
                    date_to=(datetime.now().date() + timedelta(days=30)).isoformat(),
                    status="SCHEDULED"
                )
                
                # Get recent results
                results = self.data_service.football_data.get_fixtures(
                    competition_code=self._get_competition_code(lg),
                    date_from=(datetime.now().date() - timedelta(days=7)).isoformat(),
                    date_to=datetime.now().date().isoformat(),
                    status="FINISHED"
                )
                
                summary["leagues"][lg] = {
                    "fixtures_count": len(fixtures),
                    "results_count": len(results),
                    "last_updated": datetime.utcnow().isoformat(),
                    "status": "healthy" if len(fixtures) > 0 or len(results) > 0 else "no_data"
                }
                
                summary["total_fixtures"] += len(fixtures)
                summary["total_results"] += len(results)
                
            except Exception as e:
                summary["leagues"][lg] = {
                    "fixtures_count": 0,
                    "results_count": 0,
                    "last_updated": None,
                    "status": "error",
                    "error": str(e)
                }
        
        if summary["total_fixtures"] > 0 or summary["total_results"] > 0:
            summary["data_freshness"] = "current"
        else:
            summary["data_freshness"] = "stale"
            
        return summary
    
    def get_setup_requirements(self) -> Dict:
        """Get setup requirements and missing configuration."""
        football_data_key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()
        
        return {
            "required_providers": ["football-data.org"],
            "optional_providers": ["the-odds-api", "api-football"],
            "missing_keys": [],
            "setup_complete": bool(football_data_key),
            "next_steps": []
        }
    
    def _get_competition_code(self, league_name: str) -> str:
        """Get competition code for football-data.org API."""
        competition_map = {
            "Premier League": "PL",
            "La Liga": "PD", 
            "Serie A": "SA",
            "Bundesliga": "BL1",
            "Ligue 1": "FL1"
        }
        return competition_map.get(league_name, league_name.replace(" ", "_").upper())


# Singleton instance
_data_health_service = None


def get_data_health_service() -> DataHealthService:
    """Get or create the data health service instance."""
    global _data_health_service
    if _data_health_service is None:
        _data_health_service = DataHealthService()
    return _data_health_service