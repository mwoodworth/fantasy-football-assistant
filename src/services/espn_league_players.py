"""
ESPN League-specific player data service
"""

import logging
from typing import Dict, List, Any, Optional
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ESPNLeaguePlayersService:
    """Service for fetching league-specific player data from ESPN"""
    
    BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = timedelta(minutes=15)
    
    def _get_cache_key(self, league_id: int, filters: Dict[str, Any]) -> str:
        """Generate cache key"""
        return f"league_{league_id}_{hash(str(sorted(filters.items())))}"
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cache entry is still valid"""
        return datetime.now() - timestamp < self._cache_ttl
    
    async def get_league_players_trending(
        self, 
        league_id: int,
        season: int = 2025,
        limit: int = 25,
        sort_by_change: bool = True,
        position_filter: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get players with ownership trending data for a specific league
        
        Args:
            league_id: ESPN league ID
            season: Season year
            limit: Number of players to return
            sort_by_change: Sort by ownership change percentage
            position_filter: List of position IDs to filter (e.g., [2] for RB)
        """
        
        cache_key = self._get_cache_key(league_id, {
            'type': 'trending',
            'limit': limit,
            'sort_by_change': sort_by_change,
            'positions': position_filter
        })
        
        # Check cache
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if self._is_cache_valid(timestamp):
                logger.debug(f"Returning cached trending players for league {league_id}")
                return data
        
        # Build filter
        filter_obj = {
            "players": {
                "limit": limit,
                "sortPercChanged": {
                    "sortPriority": 1,
                    "sortAsc": False if sort_by_change else True
                },
                "filterStatsForTopScoringPeriodIds": {
                    "value": 2,
                    "additionalValue": ["002025", "102025", "002024", "022025"]
                }
            }
        }
        
        # Add position filter if specified
        if position_filter:
            slot_ids = []
            for pos_id in position_filter:
                # Map position IDs to slot IDs
                slot_map = {
                    1: [0],      # QB
                    2: [2],      # RB
                    3: [4],      # WR
                    4: [6],      # TE
                    5: [17],     # K
                    16: [16]     # D/ST
                }
                if pos_id in slot_map:
                    slot_ids.extend(slot_map[pos_id])
            
            if slot_ids:
                filter_obj["players"]["filterSlotIds"] = {"value": slot_ids}
        
        url = f"{self.BASE_URL}/seasons/{season}/segments/0/leagues/{league_id}"
        
        headers = {
            "accept": "application/json",
            "x-fantasy-filter": str(filter_obj).replace("'", '"'),
            "x-fantasy-platform": "kona-PROD-9488cfa0d0fb59d75804777bfee76c2f161a89b1",
            "x-fantasy-source": "kona",
            "referer": "https://fantasy.espn.com/",
            "user-agent": "Fantasy Football Assistant"
        }
        
        params = {
            "view": "kona_player_info"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                players_data = data.get('players', [])
                
                # Process and format the data
                formatted_players = []
                for player_entry in players_data:
                    player_info = player_entry.get('player', {})
                    if not player_info:
                        continue
                    
                    ownership = player_info.get('ownership', {})
                    
                    formatted_player = {
                        'id': player_info.get('id'),
                        'name': player_info.get('fullName'),
                        'first_name': player_info.get('firstName'),
                        'last_name': player_info.get('lastName'),
                        'position_id': player_info.get('defaultPositionId'),
                        'position': self._get_position_name(player_info.get('defaultPositionId')),
                        'team_id': player_info.get('proTeamId'),
                        'team': self._get_team_abbr(player_info.get('proTeamId')),
                        'ownership_percentage': ownership.get('percentOwned', 0),
                        'ownership_change': ownership.get('percentChange', 0),
                        'average_draft_position': ownership.get('averageDraftPosition'),
                        'percent_started': ownership.get('percentStarted', 0),
                        'injury_status': player_info.get('injuryStatus'),
                        'rankings': player_entry.get('ratings', {}),
                        'on_team_id': player_entry.get('onTeamId')
                    }
                    
                    formatted_players.append(formatted_player)
                
                result = {
                    'league_id': league_id,
                    'players': formatted_players,
                    'total_count': len(formatted_players),
                    'fetched_at': datetime.now().isoformat()
                }
                
                # Cache the result
                self._cache[cache_key] = (result, datetime.now())
                
                return result
                
            except httpx.HTTPError as e:
                logger.error(f"Error fetching league players: {e}")
                raise
    
    async def get_top_available_players(
        self,
        league_id: int,
        season: int = 2025,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get top available (unowned) players in a league"""
        
        filter_obj = {
            "players": {
                "limit": limit * 2,  # Get more to filter
                "filterStatus": {"value": ["FREEAGENT", "WAIVERS"]},
                "sortDraftRanks": {
                    "sortPriority": 1,
                    "sortAsc": True,
                    "value": "STANDARD"
                }
            }
        }
        
        url = f"{self.BASE_URL}/seasons/{season}/segments/0/leagues/{league_id}"
        
        headers = {
            "accept": "application/json",
            "x-fantasy-filter": str(filter_obj).replace("'", '"'),
            "x-fantasy-platform": "kona-PROD-9488cfa0d0fb59d75804777bfee76c2f161a89b1",
            "x-fantasy-source": "kona",
            "referer": "https://fantasy.espn.com/"
        }
        
        params = {
            "view": "kona_player_info"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                players_data = data.get('players', [])
                
                # Filter for truly available players
                available_players = []
                for player_entry in players_data:
                    if player_entry.get('onTeamId') == 0:  # Not on any team
                        player_info = player_entry.get('player', {})
                        if player_info:
                            ownership = player_info.get('ownership', {})
                            
                            available_players.append({
                                'id': player_info.get('id'),
                                'name': player_info.get('fullName'),
                                'position': self._get_position_name(player_info.get('defaultPositionId')),
                                'team': self._get_team_abbr(player_info.get('proTeamId')),
                                'ownership_percentage': ownership.get('percentOwned', 0),
                                'average_draft_position': ownership.get('averageDraftPosition'),
                                'rankings': player_entry.get('ratings', {})
                            })
                
                # Sort by ranking/ownership and limit
                available_players.sort(key=lambda p: p.get('ownership_percentage', 0), reverse=True)
                
                return {
                    'league_id': league_id,
                    'available_players': available_players[:limit],
                    'total_available': len(available_players),
                    'fetched_at': datetime.now().isoformat()
                }
                
            except httpx.HTTPError as e:
                logger.error(f"Error fetching available players: {e}")
                raise
    
    def _get_position_name(self, position_id: int) -> str:
        """Convert position ID to name"""
        position_map = {
            1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K",
            16: "D/ST", 9: "DL", 10: "LB", 11: "DB", 
            12: "CB", 13: "S"
        }
        return position_map.get(position_id, f"Unknown({position_id})")
    
    def _get_team_abbr(self, team_id: int) -> str:
        """Convert team ID to abbreviation"""
        team_map = {
            0: "FA", 1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN",
            5: "CLE", 6: "DAL", 7: "DEN", 8: "DET", 9: "GB",
            10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR",
            15: "MIA", 16: "MIN", 17: "NE", 18: "NO", 19: "NYG",
            20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC",
            25: "SF", 26: "SEA", 27: "TB", 28: "WSH", 29: "CAR",
            30: "JAX", 33: "BAL", 34: "HOU"
        }
        return team_map.get(team_id, "UNK")


# Singleton instance
espn_league_players_service = ESPNLeaguePlayersService()