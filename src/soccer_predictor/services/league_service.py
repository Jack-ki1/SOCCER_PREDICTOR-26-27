"""League and simulation service."""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from src.soccer_predictor.core.simulation import simulate_league
from src.soccer_predictor.core.entities import LeagueForecast
from src.soccer_predictor.services.fixture_service import get_fixture_service


@dataclass
class LeagueService:
    """League forecasting and table management."""
    
    fixture_service = get_fixture_service()

    def get_league_forecast(self, league: str, iterations: int = 5000) -> Dict:
        """Run Monte Carlo simulation for a league."""
        fixtures = self.fixture_service.get_fixtures_by_league(league)
        if not fixtures:
            return {"error": f"No fixtures found for {league}"}

        forecast = simulate_league(fixtures, iterations=iterations)
        return forecast.to_dict()

    def get_league_teams(self, league: str) -> List[Dict]:
        """Get teams in a league."""
        # TODO: Implement real team retrieval from API data
        # For now, extract teams from fixtures
        fixtures = self.fixture_service.get_fixtures_by_league(league)
        teams = set()
        for fixture in fixtures:
            teams.add(fixture.home_team.name)
            teams.add(fixture.away_team.name)
        
        return [{"team_id": i, "name": team} for i, team in enumerate(sorted(teams))]

    def get_league_table(self, league: str) -> List[Dict]:
        """Get current league table."""
        standings = self.fixture_service.get_standings(league)
        return standings


_league_service: Optional[LeagueService] = None


def get_league_service() -> LeagueService:
    """Factory function to get or create the singleton LeagueService instance."""
    global _league_service
    if _league_service is None:
        _league_service = LeagueService()
    return _league_service
