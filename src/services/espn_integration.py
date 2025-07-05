"""
ESPN Service Integration

Python client for communicating with the Node.js ESPN service
Provides async methods to fetch ESPN data for integration with FastAPI
"""

import httpx
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from ..config import settings

logger = logging.getLogger(__name__)


class ESPNServiceError(Exception):
    """Custom exception for ESPN service errors"""
    pass


class ESPNServiceClient:
    """Client for communicating with Node.js ESPN service"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'espn_service_url', 'http://localhost:3001')
        self.api_key = getattr(settings, 'espn_service_api_key', None)
        self.timeout = 30.0
        self._client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._get_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Fantasy-Football-Assistant-Python/1.0'
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        return headers
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to ESPN service"""
        if not self._client:
            raise ESPNServiceError("Client not initialized. Use async context manager.")
        
        try:
            logger.debug(f"ESPN Service request: {method} {endpoint}")
            response = await self._client.request(method, endpoint, **kwargs)
            
            if response.status_code == 401:
                raise ESPNServiceError("ESPN service authentication failed")
            elif response.status_code == 403:
                raise ESPNServiceError("Access denied to ESPN resource")
            elif response.status_code == 404:
                raise ESPNServiceError("ESPN resource not found")
            elif response.status_code == 429:
                raise ESPNServiceError("ESPN service rate limit exceeded")
            elif response.status_code >= 500:
                raise ESPNServiceError(f"ESPN service error: {response.status_code}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            raise ESPNServiceError("ESPN service timeout")
        except httpx.RequestError as e:
            raise ESPNServiceError(f"ESPN service connection error: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check ESPN service health"""
        return await self._make_request('GET', '/health')
    
    async def espn_connectivity_check(self) -> Dict[str, Any]:
        """Check ESPN API connectivity through service"""
        return await self._make_request('GET', '/health/espn')
    
    # League Methods
    async def get_league_info(self, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Get league information"""
        return await self._make_request(
            'GET', 
            f'/api/leagues/{league_id}',
            params={'season': season}
        )
    
    async def get_league_settings(self, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Get league settings"""
        return await self._make_request(
            'GET',
            f'/api/leagues/{league_id}/settings',
            params={'season': season}
        )
    
    async def get_league_teams(self, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Get all teams in league"""
        return await self._make_request(
            'GET',
            f'/api/leagues/{league_id}/teams',
            params={'season': season}
        )
    
    async def get_league_standings(self, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Get league standings"""
        return await self._make_request(
            'GET',
            f'/api/leagues/{league_id}/standings',
            params={'season': season}
        )
    
    async def get_scoreboard(self, league_id: int, season: int = 2024, week: Optional[int] = None) -> Dict[str, Any]:
        """Get league scoreboard"""
        params = {'season': season}
        if week:
            params['week'] = week
        
        return await self._make_request(
            'GET',
            f'/api/leagues/{league_id}/scoreboard',
            params=params
        )
    
    # Team Methods
    async def get_team_roster(self, team_id: int, league_id: int, season: int = 2024, week: Optional[int] = None) -> Dict[str, Any]:
        """Get team roster"""
        params = {'leagueId': league_id, 'season': season}
        if week:
            params['week'] = week
        
        return await self._make_request(
            'GET',
            f'/api/teams/{team_id}/roster',
            params=params
        )
    
    async def get_team_stats(self, team_id: int, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Get team statistics"""
        return await self._make_request(
            'GET',
            f'/api/teams/{team_id}/stats',
            params={'leagueId': league_id, 'season': season}
        )
    
    async def get_team_matchups(self, team_id: int, league_id: int, season: int = 2024, week: Optional[int] = None) -> Dict[str, Any]:
        """Get team matchup history"""
        params = {'leagueId': league_id, 'season': season}
        if week:
            params['week'] = week
        
        return await self._make_request(
            'GET',
            f'/api/teams/{team_id}/matchups',
            params=params
        )
    
    async def compare_teams(self, team1_id: int, team2_id: int, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Compare two teams"""
        return await self._make_request(
            'GET',
            '/api/teams/compare',
            params={
                'leagueId': league_id,
                'team1Id': team1_id,
                'team2Id': team2_id,
                'season': season
            }
        )
    
    # Player Methods
    async def get_free_agents(self, league_id: int, season: int = 2024, position: Optional[str] = None, 
                            limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get available free agents"""
        params = {
            'leagueId': league_id,
            'season': season,
            'limit': limit,
            'offset': offset
        }
        
        if position:
            params['position'] = position
        
        return await self._make_request(
            'GET',
            '/api/players/free-agents',
            params=params
        )
    
    async def get_trending_players(self, league_id: int, season: int = 2024, limit: int = 20) -> Dict[str, Any]:
        """Get trending players"""
        return await self._make_request(
            'GET',
            '/api/players/trending',
            params={
                'leagueId': league_id,
                'season': season,
                'limit': limit
            }
        )
    
    async def search_players(self, league_id: int, name: str, season: int = 2024, 
                           include_rostered: bool = False, limit: int = 20) -> Dict[str, Any]:
        """Search players by name"""
        return await self._make_request(
            'GET',
            '/api/players/search',
            params={
                'leagueId': league_id,
                'name': name,
                'season': season,
                'includeRostered': include_rostered,
                'limit': limit
            }
        )
    
    async def get_players_by_position(self, position: str, league_id: int, season: int = 2024,
                                    available_only: bool = True, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get players by position"""
        return await self._make_request(
            'GET',
            f'/api/players/by-position/{position}',
            params={
                'leagueId': league_id,
                'season': season,
                'availableOnly': available_only,
                'limit': limit,
                'offset': offset
            }
        )
    
    # Draft Methods
    async def get_draft_results(self, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Get draft results"""
        return await self._make_request(
            'GET',
            f'/api/draft/{league_id}',
            params={'season': season}
        )
    
    async def get_draft_picks(self, league_id: int, season: int = 2024, round_num: Optional[int] = None,
                            team_id: Optional[int] = None, sort_by: str = 'overall') -> Dict[str, Any]:
        """Get draft picks with filtering"""
        params = {'season': season, 'sortBy': sort_by}
        
        if round_num:
            params['round'] = round_num
        if team_id:
            params['teamId'] = team_id
        
        return await self._make_request(
            'GET',
            f'/api/draft/{league_id}/picks',
            params=params
        )
    
    async def get_draft_grades(self, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Get draft grades by team"""
        return await self._make_request(
            'GET',
            f'/api/draft/{league_id}/grades',
            params={'season': season}
        )
    
    async def get_draft_summary(self, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Get draft summary statistics"""
        return await self._make_request(
            'GET',
            f'/api/draft/{league_id}/summary',
            params={'season': season}
        )


class ESPNDataService:
    """Higher-level service for ESPN data integration"""
    
    def __init__(self):
        self.client = ESPNServiceClient()
        self._cache = {}
        self._cache_ttl = timedelta(minutes=15)
    
    def _get_cache_key(self, method: str, *args, **kwargs) -> str:
        """Generate cache key for method call"""
        return f"{method}:{args}:{sorted(kwargs.items())}"
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cache entry is still valid"""
        return datetime.now() - timestamp < self._cache_ttl
    
    async def get_cached_or_fetch(self, method_name: str, *args, **kwargs):
        """Get data from cache or fetch from ESPN service"""
        cache_key = self._get_cache_key(method_name, *args, **kwargs)
        
        # Check cache
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if self._is_cache_valid(timestamp):
                logger.debug(f"Cache hit for {method_name}")
                return data
        
        # Fetch from service
        async with self.client as client:
            method = getattr(client, method_name)
            data = await method(*args, **kwargs)
            
            # Cache the result
            self._cache[cache_key] = (data, datetime.now())
            logger.debug(f"Cached result for {method_name}")
            
            return data
    
    async def sync_league_data(self, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Sync all league data for integration with database"""
        logger.info(f"Syncing ESPN data for league {league_id}")
        
        try:
            # Fetch all league data concurrently
            tasks = [
                self.get_cached_or_fetch('get_league_info', league_id, season),
                self.get_cached_or_fetch('get_league_teams', league_id, season),
                self.get_cached_or_fetch('get_free_agents', league_id, season, limit=100),
                self.get_cached_or_fetch('get_draft_results', league_id, season)
            ]
            
            league_info, teams, free_agents, draft = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any errors
            results = {}
            if not isinstance(league_info, Exception):
                results['league'] = league_info
            if not isinstance(teams, Exception):
                results['teams'] = teams
            if not isinstance(free_agents, Exception):
                results['free_agents'] = free_agents
            if not isinstance(draft, Exception):
                results['draft'] = draft
            
            logger.info(f"Successfully synced {len(results)} data types for league {league_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error syncing league data: {e}")
            raise ESPNServiceError(f"Failed to sync league data: {e}")
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        logger.info("ESPN data cache cleared")


# Singleton instance for use throughout the application
espn_service = ESPNDataService()