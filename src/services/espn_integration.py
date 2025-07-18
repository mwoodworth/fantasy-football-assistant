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
from ..middleware.rate_limiter import espn_rate_limiter

logger = logging.getLogger(__name__)


class ESPNServiceError(Exception):
    """Custom exception for ESPN service errors"""
    pass


class ESPNAuthError(ESPNServiceError):
    """Exception for ESPN authentication errors requiring user action"""
    def __init__(self, message: str, requires_auth_update: bool = True):
        super().__init__(message)
        self.requires_auth_update = requires_auth_update


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
    
    def _get_headers(self, espn_s2: str = None, swid: str = None) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Fantasy-Football-Assistant-Python/1.0'
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        # Add ESPN cookies if provided
        if espn_s2 and swid:
            headers['X-ESPN-S2'] = espn_s2
            headers['X-ESPN-SWID'] = swid
        
        return headers
    
    async def _make_request(self, method: str, endpoint: str, espn_s2: str = None, swid: str = None, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to ESPN service with rate limiting"""
        if not self._client:
            raise ESPNServiceError("Client not initialized. Use async context manager.")
        
        # Wait for rate limit if needed
        await espn_rate_limiter.wait_if_needed()
        
        # Add ESPN cookies to headers if provided
        headers = kwargs.get('headers', {})
        if espn_s2 and swid:
            headers.update({
                'X-ESPN-S2': espn_s2,
                'X-ESPN-SWID': swid
            })
        kwargs['headers'] = headers
        
        try:
            logger.debug(f"ESPN Service request: {method} {endpoint}")
            response = await self._client.request(method, endpoint, **kwargs)
            
            if response.status_code == 401:
                raise ESPNAuthError("ESPN authentication failed. Please update your s2 and swid cookies in your league settings.")
            elif response.status_code == 403:
                raise ESPNAuthError("Access denied to ESPN resource. Please update your s2 and swid cookies in your league settings.")
            elif response.status_code == 404:
                raise ESPNServiceError("ESPN resource not found")
            elif response.status_code == 429:
                # ESPN is rate limiting us, back off
                logger.warning(f"ESPN rate limit hit for {endpoint}")
                raise ESPNServiceError("ESPN service rate limit exceeded. Please try again later.")
            elif response.status_code >= 500:
                raise ESPNServiceError(f"ESPN service error: {response.status_code}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            raise ESPNServiceError("ESPN service timeout - the ESPN integration service may not be running")
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to ESPN service at {self.base_url}: {e}")
            raise ESPNServiceError(f"ESPN integration service is not available. Please ensure the ESPN service is running at {self.base_url}")
        except httpx.RequestError as e:
            logger.error(f"ESPN service request error: {e}")
            raise ESPNServiceError(f"ESPN service connection error: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check ESPN service health"""
        return await self._make_request('GET', '/health')
    
    async def espn_connectivity_check(self) -> Dict[str, Any]:
        """Check ESPN API connectivity through service"""
        return await self._make_request('GET', '/health/espn')
    
    # League Methods
    async def get_league_info(self, league_id: int, season: int = 2024, espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
        """Get league information"""
        return await self._make_request(
            'GET', 
            f'/api/leagues/{league_id}',
            params={'season': season},
            espn_s2=espn_s2,
            swid=swid
        )
    
    async def get_league_settings(self, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Get league settings"""
        return await self._make_request(
            'GET',
            f'/api/leagues/{league_id}/settings',
            params={'season': season}
        )
    
    async def get_league_teams(self, league_id: int, season: int = 2024, espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
        """Get all teams in league"""
        return await self._make_request(
            'GET',
            f'/api/leagues/{league_id}/teams',
            params={'season': season},
            espn_s2=espn_s2,
            swid=swid
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
    async def get_team_roster(self, team_id: int, league_id: int, season: int = 2024, week: Optional[int] = None, espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
        """Get team roster"""
        params = {'leagueId': league_id, 'season': season}
        if week:
            params['week'] = week
        
        return await self._make_request(
            'GET',
            f'/api/teams/{team_id}/roster',
            espn_s2=espn_s2,
            swid=swid,
            params=params
        )
    
    async def get_team_stats(self, team_id: int, league_id: int, season: int = 2024, espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
        """Get team statistics"""
        return await self._make_request(
            'GET',
            f'/api/teams/{team_id}/stats',
            espn_s2=espn_s2,
            swid=swid,
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
                            limit: int = 50, offset: int = 0, espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
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
            params=params,
            espn_s2=espn_s2,
            swid=swid
        )
    
    async def get_trending_players(self, trend_type: str = "add", hours: int = 24, limit: int = 20, league_id: Optional[int] = None) -> Dict[str, Any]:
        """Get trending players (most added/dropped)"""
        try:
            # If no league_id provided, we need to get one from the user's leagues
            if not league_id:
                # This would need to be passed from the calling code
                # For now, return empty if no league specified
                return {"players": [], "message": "No league ID provided"}
            
            params = {
                'leagueId': league_id,
                'season': 2024,
                'limit': limit,
                'type': trend_type  # 'add' or 'drop'
            }
            
            return await self._make_request(
                'GET',
                '/api/players/trending',
                params=params
            )
        except Exception as e:
            raise ESPNServiceError(f"Failed to get trending players: {str(e)}")
    
    async def search_players(self, query: str, limit: int = 20, league_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search players by name"""
        try:
            # If no league_id provided, we need to get one from the user's leagues
            if not league_id:
                # This would need to be passed from the calling code
                # For now, return empty if no league specified
                return []
            
            params = {
                'name': query,
                'leagueId': league_id,
                'limit': limit
            }
            
            response = await self._make_request(
                'GET',
                '/api/players/search',
                params=params
            )
            
            # Extract players from response
            return response.get('players', []) if isinstance(response, dict) else response
        except Exception as e:
            raise ESPNServiceError(f"Failed to search players: {str(e)}")
    
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
    
    # Transaction Methods
    async def get_transaction_history(self, league_id: int, season: int = 2024, 
                                    limit: int = 50, offset: int = 0,
                                    espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
        """Get transaction history for a league"""
        return await self._make_request(
            'GET',
            f'/api/leagues/{league_id}/transactions',
            params={'season': season, 'limit': limit, 'offset': offset},
            espn_s2=espn_s2,
            swid=swid
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
    
    # Authentication Methods
    async def login_to_espn(self, email: str, password: str) -> Dict[str, Any]:
        """Login to ESPN and get cookies"""
        return await self._make_request(
            'POST',
            '/auth/login',
            json={'email': email, 'password': password}
        )
    
    async def validate_espn_cookies(self, espn_s2: str, swid: str) -> Dict[str, Any]:
        """Validate ESPN cookies"""
        return await self._make_request(
            'POST',
            '/auth/validate-cookies',
            json={'espn_s2': espn_s2, 'swid': swid}
        )
    
    async def get_cookie_status(self) -> Dict[str, Any]:
        """Get current ESPN cookie status"""
        return await self._make_request('GET', '/auth/cookie-status')


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
    
    async def get_league_info(self, league_id: int, season: int = 2024, espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
        """Get league information from ESPN"""
        try:
            async with self.client as client:
                return await client.get_league_info(league_id, season, espn_s2, swid)
        except ESPNServiceError as e:
            # Re-raise with more context
            raise ESPNServiceError(f"Failed to get league {league_id} info for season {season}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting league info: {e}")
            raise ESPNServiceError(f"Unexpected error accessing ESPN league data: {str(e)}")
    
    async def get_draft_results(self, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """Get draft results from ESPN"""
        try:
            async with self.client as client:
                return await client.get_draft_results(league_id, season)
        except ESPNServiceError as e:
            # Re-raise with more context
            raise ESPNServiceError(f"Failed to get draft results for league {league_id} season {season}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting draft results: {e}")
            raise ESPNServiceError(f"Unexpected error accessing ESPN draft data: {str(e)}")
    
    async def search_players(self, query: str, limit: int = 20, league_id: Optional[int] = None, espn_s2: str = None, swid: str = None) -> List[Dict[str, Any]]:
        """Search players by name"""
        try:
            async with self.client as client:
                return await client.search_players(query, limit, league_id)
        except ESPNServiceError as e:
            raise ESPNServiceError(f"Failed to search players: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error searching players: {e}")
            raise ESPNServiceError(f"Unexpected error searching players: {str(e)}")
    
    async def sync_league_teams(self, league_id: int, season: int = 2024, espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
        """Sync all teams in a league with their rosters"""
        logger.info(f"Syncing teams for league {league_id}")
        
        try:
            async with self.client as client:
                # Use the new sync-teams endpoint
                response = await client._make_request(
                    'POST',
                    f'/api/leagues/{league_id}/sync-teams',
                    espn_s2=espn_s2,
                    swid=swid,
                    params={'season': season}
                )
                
                if response.get('success'):
                    return {
                        'success': True,
                        'teams': response.get('teams', []),
                        'teams_synced': response.get('teams_synced', 0),
                        'synced_at': response.get('meta', {}).get('syncedAt', datetime.now().isoformat())
                    }
                else:
                    raise ESPNServiceError(f"Sync teams failed: {response.get('error', 'Unknown error')}")
                    
        except Exception as e:
            logger.error(f"Error syncing league teams: {e}")
            return {
                'success': False,
                'error': str(e),
                'teams': [],
                'teams_synced': 0
            }
    
    async def sync_single_team_roster(self, team_id: int, league_id: int, season: int = 2024, 
                                    espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
        """Sync a single team's roster data"""
        logger.info(f"Syncing roster for team {team_id} in league {league_id}")
        
        try:
            async with self.client as client:
                roster_response = await client.get_team_roster(
                    team_id, league_id, season, espn_s2=espn_s2, swid=swid
                )
                
                if roster_response.get('success'):
                    return {
                        'success': True,
                        'roster': roster_response.get('data', []),
                        'synced_at': datetime.now().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'error': roster_response.get('error', 'Unknown error'),
                        'roster': []
                    }
                    
        except Exception as e:
            logger.error(f"Error syncing team roster: {e}")
            return {
                'success': False,
                'error': str(e),
                'roster': []
            }
    
    async def get_player_details(self, espn_player_id: int) -> Dict[str, Any]:
        """Get detailed information for a specific ESPN player"""
        try:
            async with self.client as client:
                # Get player details from ESPN
                return await client.get_player_details(espn_player_id)
        except Exception as e:
            raise ESPNServiceError(f"Failed to get player details for ID {espn_player_id}: {str(e)}")
    
    async def get_position_rankings(self, position: str, scoring_type: str = "standard", limit: int = 50) -> List[Dict[str, Any]]:
        """Get ESPN expert rankings by position"""
        try:
            async with self.client as client:
                # Get position rankings from ESPN
                return await client.get_position_rankings(
                    position=position,
                    scoring_type=scoring_type,
                    limit=limit
                )
        except Exception as e:
            raise ESPNServiceError(f"Failed to get {position} rankings: {str(e)}")
    
    async def get_scoreboard(self, league_id: int, season: int = 2024, week: Optional[int] = None) -> Dict[str, Any]:
        """Get league scoreboard"""
        try:
            async with self.client as client:
                return await client.get_scoreboard(league_id, season, week)
        except Exception as e:
            raise ESPNServiceError(f"Failed to get scoreboard for league {league_id}: {str(e)}")
    
    async def get_league_teams(self, league_id: int, season: int = 2024, espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
        """Get all teams in league"""
        try:
            async with self.client as client:
                return await client.get_league_teams(league_id, season, espn_s2, swid)
        except Exception as e:
            raise ESPNServiceError(f"Failed to get teams for league {league_id}: {str(e)}")
    
    async def get_team_roster(self, team_id: int, league_id: int, season: int = 2024, 
                            week: Optional[int] = None, espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
        """Get team roster"""
        try:
            async with self.client as client:
                return await client.get_team_roster(team_id, league_id, season, week, espn_s2, swid)
        except Exception as e:
            raise ESPNServiceError(f"Failed to get roster for team {team_id}: {str(e)}")
    
    async def get_transaction_history(self, league_id: int, season: int = 2024, 
                                    limit: int = 50, offset: int = 0,
                                    espn_s2: str = None, swid: str = None) -> Dict[str, Any]:
        """Get transaction history for a league"""
        try:
            async with self.client as client:
                return await client.get_transaction_history(league_id, season, limit, offset, espn_s2, swid)
        except Exception as e:
            raise ESPNServiceError(f"Failed to get transaction history for league {league_id}: {str(e)}")
    
    async def sync_league_players(self, league_id: int, season: int = 2024, force: bool = False) -> Dict[str, Any]:
        """Sync all players from an ESPN league to local database"""
        try:
            # Import here to avoid circular dependency
            from ..models.database import SessionLocal
            from .player_sync import player_sync_service
            
            db = SessionLocal()
            try:
                # Use the player sync service to sync all players
                # In the future, this could be optimized to only sync league-specific players
                result = await player_sync_service.sync_all_players(db, force=force)
                
                return {
                    "synced_count": result.get("synced_count", 0),
                    "updated_count": result.get("updated_count", 0),
                    "errors": result.get("errors", [])
                }
            finally:
                db.close()
                
        except Exception as e:
            raise ESPNServiceError(f"Failed to sync league players: {str(e)}")


# Singleton instance for use throughout the application
espn_service = ESPNDataService()