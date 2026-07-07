"""Data ingestion and health monitoring."""

from typing import Dict, List
from dataclasses import dataclass

from src.soccer_predictor.services.data_health_service import get_data_health_service


@dataclass
class DataService:
    """Data quality and health monitoring."""

    def get_data_health(self, league: str = None) -> Dict:
        """Assess data health for a league."""
        health_service = get_data_health_service()
        if league:
            league_stats = health_service.get_league_coverage().get(league, {})
            return {
                "league": league,
                "teams": league_stats.get("fixtures_loaded", 0),  # Approximate
                "elo_coverage": 0.0,  # Will be implemented with real team data
                "xg_coverage": 0.0,   # Will be implemented with advanced stats
                "status": league_stats.get("status", "unknown"),
                "last_sync": league_stats.get("last_sync")
            }
        
        # Return overall health
        return health_service.get_overall_health()

    def get_league_stats(self, league: str) -> Dict:
        """Get aggregate statistics for a league.
        
        Note: This method will need to be updated when real data sources are available.
        """
        # Placeholder implementation - will be updated with real data source
        return {
            "league": league,
            "teams": 0,
            "avg_elo": 0.0,
            "elo_range": 0.0,
            "avg_market_value": 0.0,
            "total_market_value": 0.0,
            "competitiveness": 0.0,
        }


_data_service = None


def get_data_service() -> DataService:
    """Factory function to get or create the singleton DataService instance."""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service


# Alias for backward compatibility
get_data_service_instance = get_data_service
