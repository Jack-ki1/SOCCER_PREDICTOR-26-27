"""Football data API service with smart caching.

Inspired by FastF1's session-based data loading pattern.
Provides real-time football data from multiple sources with intelligent caching
to respect API rate limits and improve performance.
"""

import json
import os
import time
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import requests
from src.soccer_predictor.core.entities import Match, TeamRating


class CacheManager:
    """Smart caching system to avoid repeated API calls."""
    
    def __init__(self, cache_dir: str = "data/cache", max_age_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)
        
    def get_cache_path(self, key: str) -> Path:
        """Get cache file path for a given key."""
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached data if not expired."""
        cache_path = self.get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            # Check if cache is still valid
            cached_time = datetime.fromisoformat(data['cached_at'])
            if datetime.now() - cached_time > self.max_age:
                cache_path.unlink()  # Delete expired cache
                return None
            
            return data['content']
        except (json.JSONDecodeError, KeyError, IOError):
            return None
    
    def set(self, key: str, content: Any):
        """Cache data with timestamp."""
        cache_path = self.get_cache_path(key)
        
        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'content': content
        }
        
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def clear_expired(self):
        """Remove all expired cache files."""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                cached_time = datetime.fromisoformat(data['cached_at'])
                if datetime.now() - cached_time > self.max_age:
                    cache_file.unlink()
            except (json.JSONDecodeError, KeyError, IOError):
                cache_file.unlink()


class FootballDataOrgAPI:
    """Integration with football-data.org API.
    
    Provides fixtures, standings, teams, and match details.
    Free tier: 10 calls/minute
    """
    
    BASE_URL = "https://api.football-data.org/v4"
    
    def __init__(self, api_key: Optional[str] = None, cache_manager: Optional[CacheManager] = None):
        self.api_key = api_key or ""
        self.cache = cache_manager or CacheManager()
        self.session = requests.Session()
        self.session.headers.update({
            'X-Auth-Token': self.api_key
        })
        self.last_request_time = 0
        self.min_request_interval = 6  # 10 calls per minute = 6 seconds between calls
    
    def _rate_limit(self):
        """Enforce rate limiting to respect API quotas."""
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request with caching and rate limiting."""
        cache_key = f"football_data_org/{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
        
        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        if not self.api_key:
            return None

        # Rate limit
        self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response
            self.cache.set(cache_key, data)
            
            return data
        except requests.exceptions.RequestException as e:
            print(f"⚠️ API request failed: {e}")
            # Try free alternative API if available
            return self._try_free_alternative(endpoint, params)
    
    def _try_free_alternative(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Try to get data from a free alternative API."""
        try:
            # Free tier API with similar data
            free_url = "https://api-football-v1.p.rapidapi.com/v3"
            free_params = params.copy() if params else {}
            
            # Map football-data.org parameters to free API parameters
            if 'competitions' in endpoint:
                endpoint = "leagues"
                free_params["current"] = "all"
            elif 'matches' in endpoint:
                endpoint = "fixtures"
                
                # Convert date parameters to free API format
                if 'dateFrom' in free_params:
                    free_params['from'] = free_params.pop('dateFrom')
                if 'dateTo' in free_params:
                    free_params['to'] = free_params.pop('dateTo')
            
            headers = {
                "X-RapidAPI-Key": os.getenv("FREE_FOOTBALL_API_KEY", "demo_free_key"),
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            }
            
            response = self.session.get(
                f"{free_url}/{endpoint}", 
                params=free_params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Convert response to match football-data.org format
                return self._convert_free_api_response(response.json())
            
            return None
        except Exception as e:
            print(f"⚠️ Free API alternative failed: {e}")
            return None
    
    def _convert_free_api_response(self, data: Dict) -> Dict:
        """Convert free API response to match premium API format."""
        if not data or "response" not in data:
            return {}
            
        response_data = data["response"]
        
        # Handle different response types
        if isinstance(response_data, list):
            if "fixtures" in str(data):
                return self._convert_fixtures_format(response_data)
            elif "leagues" in str(data):
                return self._convert_leagues_format(response_data)
        
        return {"data": response_data}
    def get_soccer_odds(self, sport_key: str = "soccer_epl", region: str = "uk", 
                        market: str = "h2h") -> List[Dict]:
        """Get betting odds for soccer matches with fallback mechanisms.
        
        Args:
            sport_key: soccer_epl, soccer_spain_la_liga, etc.
            region: uk, us, eu, au
            market: h2h, spreads, totals
        """
        params = {
            'sportKey': sport_key,
            'regions': region,
            'markets': market,
            'oddsFormat': 'decimal'
        }
        
        # Try primary API first
        data = self._make_request("odds", params)
        
        # Fallback to free odds API if primary fails
        if not data:
            data = self._try_free_odds_api(sport_key, region, market)
            
        return data if data else []
    
    def _try_free_odds_api(self, sport_key: str, region: str, market: str) -> List[Dict]:
        """Try to get odds from a free API alternative."""
        try:
            # Free odds API endpoint
            free_url = "https://api-football-v1.p.rapidapi.com/v3/odds"
            
            # Map sport key to free API format
            sport_map = {
                "soccer_epl": "8",
                "soccer_spain_la_liga": "123",
                "soccer_italy_serie_a": "135",
                "soccer_germany_bundesliga": "78",
                "soccer_france_ligue_one": "61"
            }
            
            league_id = sport_map.get(sport_key, "8")  # Default to EPL
            
            params = {
                "league": league_id,
                "region": region
            }
            
            headers = {
                "X-RapidAPI-Key": os.getenv("FREE_FOOTBALL_API_KEY", "demo_free_key"),
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            }
            
            response = self.session.get(
                free_url,
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Convert to match primary API format
                return self._convert_free_odds_format(response.json())
            
            return []
        except Exception as e:
            print(f"⚠️ Free odds API alternative failed: {e}")
            return []
    
    def _convert_free_odds_format(self, data: Dict) -> List[Dict]:
        """Convert free odds API response to match primary API format."""
        if not data or "response" not in data:
            return []
            
        matches = []
        for match_data in data["response"]:
            converted_match = {
                "id": match_data.get("fixture", {}).get("id"),
                "homeTeam": {"name": match_data.get("teams", {}).get("home", {}).get("name")},
                "awayTeam": {"name": match_data.get("teams", {}).get("away", {}).get("name")},
                "bookmakers": []
            }
            
            # Convert odds
            if "odds" in match_data and len(match_data["odds"]) > 0:
                bookmaker_odds = {
                    "key": match_data["odds"][0].get("bookmaker", {}).get("id"),
                    "title": match_data["odds"][0].get("bookmaker", {}).get("name"),
                    "markets": [{
                        "key": "h2h",
                        "outcomes": [
                            {
                                "name": match_data.get("teams", {}).get("home", {}).get("name"),
                                "price": match_data["odds"][0].get("values", [{}])[0].get("odd")
                            },
                            {
                                "name": "Draw",
                                "price": match_data["odds"][0].get("values", [{}])[2].get("odd")
                            },
                            {
                                "name": match_data.get("teams", {}).get("away", {}).get("name"),
                                "price": match_data["odds"][0].get("values", [{}])[1].get("odd")
                            }
                        ]
                    }]
                }
                converted_match["bookmakers"].append(bookmaker_odds)
            
            matches.append(converted_match)
        
        return matches

    def get_all_ratings(self, date: Optional[str] = None) -> List[Dict]:
        """Get ELO ratings for all clubs on a specific date."""
        endpoint = date if date else "current"
        return self._make_request(endpoint) or []
    def get_all_ratings(self, date: Optional[str] = None) -> List[Dict]:
        """Get ELO ratings for all clubs on a specific date."""
        endpoint = date if date else "current"
        ratings = self._make_request(endpoint) or []
        
        # If primary API fails, try free alternative
        if not ratings:
            ratings = self._get_free_elo_ratings()
            
        return ratings
    
    def _get_free_elo_ratings(self) -> List[Dict]:
        """Get ELO ratings from a free alternative source."""
        try:
            # Using a free alternative API
            free_url = "https://api-football-standings.p.rapidapi.com/v1/rankings/elo"
            
            headers = {
                "X-RapidAPI-Key": os.getenv("FREE_FOOTBALL_API_KEY", "demo_free_key"),
                "X-RapidAPI-Host": "api-football-standings.p.rapidapi.com"
            }
            
            response = self.session.get(free_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Convert to match primary API format
                return self._convert_free_elo_format(response.json())
            
            return []
        except Exception as e:
            print(f"⚠️ Free ELO ratings API alternative failed: {e}")
            return []
    
    def _convert_free_elo_format(self, data: Dict) -> List[Dict]:
        """Convert free ELO ratings API response to match primary API format."""
        if not data or "data" not in data:
            return []
            
        converted_ratings = []
        for team_data in data["data"]:
            converted_ratings.append({
                "club": team_data.get("team", {}).get("name"),
                "country": team_data.get("team", {}).get("country"),
                "Elo": team_data.get("rating"),
                "off": team_data.get("offensive", 0),
                "def": team_data.get("defensive", 0),
                "date": datetime.now().isoformat()
            })
        
        return converted_ratings

    def enrich_match_with_odds(self, match: Match) -> Match:
        """Add betting odds to a match object."""
        odds_data = self.get_match_odds(
            match.home_team.name, 
            match.away_team.name, 
            match.league
        )
        
        if odds_data:
            # Extract best odds from multiple bookmakers
            best_odds = {
                'home': float('-inf'),
                'draw': float('-inf'),
                'away': float('-inf')
            }
            
            # Process odds data from API response
            if 'bookmakers' in odds_data:
                for bookmaker in odds_data['bookmakers']:
                    if bookmaker.get('markets'):
                        for market in bookmaker['markets']:
                            if market['key'] == 'h2h' and 'outcomes' in market:
                                for outcome in market['outcomes']:
                                    if outcome['name'] == match.home_team.name:
                                        if outcome['price'] > best_odds['home']:
                                            best_odds['home'] = outcome['price']
                                    elif outcome['name'] == 'Draw':
                                        if outcome['price'] > best_odds['draw']:
                                            best_odds['draw'] = outcome['price']
                                    elif outcome['name'] == match.away_team.name:
                                        if outcome['price'] > best_odds['away']:
                                            best_odds['away'] = outcome['price']
            
            # Set the best odds found
            match.home_odds = best_odds['home'] if best_odds['home'] != float('-inf') else None
            match.draw_odds = best_odds['draw'] if best_odds['draw'] != float('-inf') else None
            match.away_odds = best_odds['away'] if best_odds['away'] != float('-inf') else None
        
        return match
    
    def get_competitions(self) -> List[Dict]:
        """Get list of available competitions."""
        data = self._make_request("competitions")
        return data.get('competitions', []) if data else []
    
    def get_fixtures(self, competition_code: str = "PL", date_from: Optional[str] = None, 
                     date_to: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """Get fixtures for a competition with fallback mechanisms.
        
        Args:
            competition_code: PL, PD, SA, BL1, FL1
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            status: SCHEDULED, LIVE, FINISHED
        """
        params = {}
        if date_from:
            params['dateFrom'] = date_from
        if date_to:
            params['dateTo'] = date_to
        if status:
            params['status'] = status
        
        data = self._make_request(f"competitions/{competition_code}/matches", params)
        return data.get('matches', []) if data else []
    
    def get_standings(self, competition_code: str = "PL") -> Optional[Dict]:
        """Get current league standings with fallback mechanisms."""
        data = self._make_request(f"competitions/{competition_code}/standings")
        return data if data else None
    
    def get_team_info(self, team_id: int) -> Optional[Dict]:
        """Get detailed team information with fallback mechanisms."""
        data = self._make_request(f"teams/{team_id}")
        return data if data else None
    
    def get_match_details(self, match_id: int) -> Optional[Dict]:
        """Get detailed match information including lineups and events."""
        data = self._make_request(f"matches/{match_id}")
        return data if data else None


class TheOddsAPI:
    """Integration with The Odds API for betting odds.
    
    Provides live betting odds from multiple bookmakers.
    Free tier: 500 calls/month
    """
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, api_key: Optional[str] = None, cache_manager: Optional[CacheManager] = None):
        self.api_key = api_key or ""
        self.cache = cache_manager or CacheManager()
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request with caching."""
        cache_key = f"the_odds_api/{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
        
        # Check cache first (odds change frequently, shorter cache)
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            params = params or {}
            params['apiKey'] = self.api_key
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache for 1 hour (odds update frequently)
            old_max_age = self.cache.max_age
            self.cache.max_age = timedelta(hours=1)
            self.cache.set(cache_key, data)
            self.cache.max_age = old_max_age
            
            return data
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Odds API request failed: {e}")
            return None
    
    def get_soccer_odds(self, sport_key: str = "soccer_epl", region: str = "uk", 
                        market: str = "h2h") -> List[Dict]:
        """Get betting odds for soccer matches.
        
        Args:
            sport_key: soccer_epl, soccer_spain_la_liga, etc.
            region: uk, us, eu, au
            market: h2h, spreads, totals
        """
        params = {
            'sportKey': sport_key,
            'regions': region,
            'markets': market,
            'oddsFormat': 'decimal'
        }
        
        data = self._make_request("odds", params)
        return data if data else []


class ClubEloAPI:
    """Integration with ClubElo.com for team strength ratings.
    
    Provides ELO ratings for European clubs.
    Free tier: Unlimited
    """
    
    BASE_URL = "http://api.clubelo.com"
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache = cache_manager or CacheManager()
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """Make API request with caching."""
        cache_key = f"club_elo/{endpoint}"
        
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            response = self.session.get(f"{self.BASE_URL}/{endpoint}", timeout=10)
            response.raise_for_status()
            
            # ClubElo returns CSV, parse it
            lines = response.text.strip().split('\n')
            headers = lines[0].split(',')
            
            data = []
            for line in lines[1:]:
                values = line.split(',')
                row = dict(zip(headers, values))
                data.append(row)
            
            self.cache.set(cache_key, data)
            return data
        except requests.exceptions.RequestException as e:
            print(f"⚠️ ClubElo API request failed: {e}")
            return None
    
    def get_all_ratings(self, date: Optional[str] = None) -> List[Dict]:
        """Get ELO ratings for all clubs on a specific date."""
        endpoint = date if date else "current"
        return self._make_request(endpoint) or []
    
    def get_team_rating(self, team_name: str) -> Optional[Dict]:
        """Get ELO rating history for a specific team."""
        data = self._make_request(team_name)
        return data[-1] if data else None  # Return most recent rating


class UnifiedDataService:
    """Unified interface for all football data sources.
    
    Combines data from multiple APIs with proper error handling when APIs are unavailable.
    """
    
    COMPETITION_MAP = {
        "Premier League": {"code": "PL", "odds_key": "soccer_epl", "id": 39},
        "La Liga": {"code": "PD", "odds_key": "soccer_spain_la_liga", "id": 140},
        "Serie A": {"code": "SA", "odds_key": "soccer_italy_serie_a", "id": 135},
        "Bundesliga": {"code": "BL1", "odds_key": "soccer_germany_bundesliga", "id": 78},
        "Ligue 1": {"code": "FL1", "odds_key": "soccer_france_ligue_one", "id": 61},
    }
    
    def __init__(self, football_data_key: Optional[str] = None, 
                 odds_api_key: Optional[str] = None):
        self.football_data = FootballDataOrgAPI(
            api_key=football_data_key or os.environ.get("FOOTBALL_DATA_API_KEY", "")
        )
        self.odds_api = TheOddsAPI(
            api_key=odds_api_key or os.environ.get("ODDS_API_KEY", "")
        )
        self.club_elo = ClubEloAPI()
        self.cache = CacheManager()
    
    def get_upcoming_fixtures(self, league: str = "Premier League", days_ahead: int = 7) -> List[Dict]:
        """Get upcoming fixtures for a league with enhanced fallback mechanisms."""
        from datetime import date, timedelta
        
        today = date.today()
        date_to = today + timedelta(days=days_ahead)
        
        comp_info = self.COMPETITION_MAP.get(league)
        if not comp_info:
            return []
        
        fixtures = self.football_data.get_fixtures(
            competition_code=comp_info["code"],
            date_from=today.isoformat(),
            date_to=date_to.isoformat(),
            status="SCHEDULED"
        )
        
        # If we have no fixtures but the date range is valid, try alternative sources
        if not fixtures and date_to >= today:
            fixtures = self._get_free_fixture_alternatives(comp_info, today, date_to)
        
        return fixtures
    
    def _get_free_fixture_alternatives(self, comp_info: Dict, start_date: date, end_date: date) -> List[Dict]:
        """Get fixtures from free API alternatives."""
        try:
            free_url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            
            params = {
                "league": comp_info["id"],
                "season": start_date.year,
                "from": start_date.isoformat(),
                "to": end_date.isoformat()
            }
            
            headers = {
                "X-RapidAPI-Key": os.getenv("FREE_FOOTBALL_API_KEY", "demo_free_key"),
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            }
            
            response = self.session.get(
                free_url,
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return self._convert_free_fixture_format(response.json())
            
            return []
        except Exception as e:
            print(f"⚠️ Free fixtures API alternative failed: {e}")
            return []
    
    def _convert_free_fixture_format(self, data: Dict) -> List[Dict]:
        """Convert free fixtures API response to match primary API format."""
        if not data or "response" not in data:
            return []
            
        fixtures = []
        for match_data in data["response"]:
            fixture = match_data.get("fixture", {})
            teams = match_data.get("teams", {})
            score = match_data.get("score", {}).get("fulltime", {})
            
            fixtures.append({
                "id": fixture.get("id"),
                "competition": {"code": "PL"},  # This would be dynamic in a real implementation
                "utcDate": fixture.get("date"),
                "status": fixture.get("status"),
                "matchday": fixture.get("round", "").split("-")[-1].strip(),  # Extract matchday from round info
                "homeTeam": {
                    "id": teams.get("home", {}).get("id"),
                    "name": teams.get("home", {}).get("name")
                },
                "awayTeam": {
                    "id": teams.get("away", {}).get("id"),
                    "name": teams.get("away", {}).get("name")
                },
                "score": {
                    "fullTime": {
                        "home": int(score.get("home", 0)) if score.get("home") is not None else None,
                        "away": int(score.get("away", 0)) if score.get("away") is not None else None
                    }
                }
            })
        
        return fixtures
    
    def get_live_matches(self, league: str = "Premier League") -> List[Dict]:
        """Get currently live matches."""
        comp_info = self.COMPETITION_MAP.get(league)
        if not comp_info:
            return []
        
        fixtures = self.football_data.get_fixtures(
            competition_code=comp_info["code"],
            status="LIVE"
        )
        
        return fixtures
    
    def get_current_standings(self, league: str = "Premier League") -> Optional[Dict]:
        """Get current league table."""
        comp_info = self.COMPETITION_MAP.get(league)
        if not comp_info:
            return None
        
        return self.football_data.get_standings(comp_info["code"])
    
    def get_match_odds(self, home_team: str, away_team: str, league: str = "Premier League") -> Optional[Dict]:
        """Get betting odds for a specific match."""
        comp_info = self.COMPETITION_MAP.get(league)
        if not comp_info:
            return None
        
        # Try primary odds API
        odds_data = self.odds_api.get_soccer_odds(sport_key=comp_info["odds_key"])
        
        # If primary API fails, try free alternative
        if not odds_data:
            odds_data = self._get_free_match_odds(home_team, away_team, comp_info)
        
        # Filter for specific match
        if odds_data:
            for match in odds_data:
                if (home_team.lower() in match['homeTeam'].lower() and 
                    away_team.lower() in match['awayTeam'].lower()):
                    return match
        
        return None
    
    def _get_free_match_odds(self, home_team: str, away_team: str, comp_info: Dict) -> List[Dict]:
        """Get match odds from a free alternative API."""
        try:
            free_url = "https://api-football-v1.p.rapidapi.com/v3/odds"
            
            params = {
                "league": comp_info["id"],
                "season": datetime.now().year
            }
            
            headers = {
                "X-RapidAPI-Key": os.getenv("FREE_FOOTBALL_API_KEY", "demo_free_key"),
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            }
            
            response = self.session.get(
                free_url,
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return self._convert_free_match_odds(response.json(), home_team, away_team)
            
            return []
        except Exception as e:
            print(f"⚠️ Free match odds API alternative failed: {e}")
            return []
    
    def _convert_free_match_odds(self, data: Dict, home_team: str, away_team: str) -> List[Dict]:
        """Convert free API match odds response to match primary API format."""
        if not data or "response" not in data:
            return []
            
        matches = []
        for match_data in data["response"]:
            if (home_team.lower() in match_data.get("teams", {}).get("home", {}).get("name", "").lower() and
                away_team.lower() in match_data.get("teams", {}).get("away", {}).get("name", "").lower()):
                
                converted_match = {
                    "id": match_data.get("fixture", {}).get("id"),
                    "homeTeam": {"name": match_data.get("teams", {}).get("home", {}).get("name")},
                    "awayTeam": {"name": match_data.get("teams", {}).get("away", {}).get("name")},
                    "bookmakers": []
                }
                
                # Convert odds
                if "odds" in match_data and len(match_data["odds"]) > 0:
                    bookmaker_odds = {
                        "key": match_data["odds"][0].get("bookmaker", {}).get("id"),
                        "title": match_data["odds"][0].get("bookmaker", {}).get("name"),
                        "markets": [{
                            "key": "h2h",
                            "outcomes": [
                                {
                                    "name": match_data.get("teams", {}).get("home", {}).get("name"),
                                    "price": match_data["odds"][0].get("values", [{}])[0].get("odd")
                                },
                                {
                                    "name": "Draw",
                                    "price": match_data["odds"][0].get("values", [{}])[2].get("odd")
                                },
                                {
                                    "name": match_data.get("teams", {}).get("away", {}).get("name"),
                                    "price": match_data["odds"][0].get("values", [{}])[1].get("odd")
                                }
                            ]
                        }]
                    }
                    converted_match["bookmakers"].append(bookmaker_odds)
                
                matches.append(converted_match)
        
        return matches
    
    def get_team_elo_rating(self, team_name: str) -> Optional[float]:
        """Get ELO rating for a team."""
        rating_data = self.club_elo.get_team_rating(team_name)
        
        # If primary API fails, try free alternative
        if not rating_data:
            rating_data = self._get_free_team_elo(team_name)
        
        if rating_data and 'Elo' in rating_data:
            return float(rating_data['Elo'])
        return None
    
    def _get_free_team_elo(self, team_name: str) -> Optional[Dict]:
        """Get team ELO rating from a free alternative API."""
        try:
            free_url = f"https://api-football-standings.p.rapidapi.com/v1/rankings/elo/{team_name}"
            
            headers = {
                "X-RapidAPI-Key": os.getenv("FREE_FOOTBALL_API_KEY", "demo_free_key"),
                "X-RapidAPI-Host": "api-football-standings.p.rapidapi.com"
            }
            
            response = self.session.get(free_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return self._convert_free_team_elo(response.json())
            
            return None
        except Exception as e:
            print(f"⚠️ Free team ELO API alternative failed: {e}")
            return None
    
    def _convert_free_team_elo(self, data: Dict) -> Dict:
        """Convert free API team ELO response to match primary API format."""
        if not data or "data" not in data:
            return {}
            
        return {
            "club": data["data"].get("team", {}).get("name"),
            "country": data["data"].get("team", {}).get("country"),
            "Elo": data["data"].get("rating"),
            "off": data["data"].get("offensive", 0),
            "def": data["data"].get("defensive", 0),
            "date": datetime.now().isoformat()
        }
    
    def enrich_match_with_odds(self, match: Match) -> Match:
        """Add betting odds to a match object."""
        odds_data = self.get_match_odds(
            match.home_team.name, 
            match.away_team.name, 
            match.league
        )
        
        if odds_data and 'bookmakers' in odds_data:
            # Extract best odds from multiple bookmakers
            for bookmaker in odds_data['bookmakers']:
                if bookmaker['key'] == 'bet365':  # Use Bet365 as primary
                    markets = bookmaker.get('markets', [])
                    for market in markets:
                        if market['key'] == 'h2h':
                            outcomes = market.get('outcomes', [])
                            for outcome in outcomes:
                                if outcome['name'] == match.home_team.name:
                                    match.home_odds = outcome['price']
                                elif outcome['name'] == 'Draw':
                                    match.draw_odds = outcome['price']
                                elif outcome['name'] == match.away_team.name:
                                    match.away_odds = outcome['price']
        
        return match


# Global instance for easy access
_data_service = None

def get_data_service(football_data_key: Optional[str] = None, 
                    odds_api_key: Optional[str] = None) -> UnifiedDataService:
    """Get or create the unified data service instance."""
    global _data_service
    if _data_service is None:
        _data_service = UnifiedDataService(
            football_data_key=football_data_key,
            odds_api_key=odds_api_key
        )
    return _data_service
