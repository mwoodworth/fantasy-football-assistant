"""Yahoo Fantasy Sports API client."""

import logging
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class YahooFantasyClient:
    """Client for Yahoo Fantasy Sports API."""
    
    BASE_URL = "https://fantasysports.yahooapis.com/fantasy/v2"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Yahoo API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            Parsed JSON response
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Add format=json to get JSON responses instead of XML
        if params is None:
            params = {}
        params["format"] = "json"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Yahoo API request failed: {e}")
            raise
    
    def get_user_games(self) -> List[Dict[str, Any]]:
        """Get all games (sports) the user is playing.
        
        Returns:
            List of game dictionaries
        """
        data = self._make_request("users;use_login=1/games")
        games = data.get("fantasy_content", {}).get("users", {}).get("0", {}).get("user", {}).get("games", {})
        
        # Convert numbered keys to list
        game_list = []
        for key, value in games.items():
            if key.isdigit() and "game" in value:
                game_list.append(value["game"])
        
        return game_list
    
    def get_user_leagues(self, game_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user's leagues.
        
        Args:
            game_key: Game key (e.g., "nfl" or specific year like "423" for NFL 2024)
            
        Returns:
            List of league dictionaries
        """
        if game_key:
            endpoint = f"users;use_login=1/games;game_keys={game_key}/leagues"
        else:
            endpoint = "users;use_login=1/games/leagues"
        
        data = self._make_request(endpoint)
        
        # Parse the nested response structure
        leagues = []
        content = data.get("fantasy_content", {})
        users = content.get("users", {}).get("0", {}).get("user", {})
        games = users.get("games", {})
        
        for game_key, game_data in games.items():
            if game_key.isdigit() and "game" in game_data:
                game_leagues = game_data["game"].get("leagues", {})
                for league_key, league_data in game_leagues.items():
                    if league_key.isdigit() and "league" in league_data:
                        leagues.append(league_data["league"])
        
        return leagues
    
    def get_league(self, league_key: str) -> Dict[str, Any]:
        """Get detailed league information.
        
        Args:
            league_key: Yahoo league key (e.g., "423.l.12345")
            
        Returns:
            League dictionary
        """
        data = self._make_request(f"league/{league_key}")
        return data.get("fantasy_content", {}).get("league", {})
    
    def get_league_teams(self, league_key: str) -> List[Dict[str, Any]]:
        """Get all teams in a league.
        
        Args:
            league_key: Yahoo league key
            
        Returns:
            List of team dictionaries
        """
        data = self._make_request(f"league/{league_key}/teams")
        teams_data = data.get("fantasy_content", {}).get("league", {}).get("teams", {})
        
        teams = []
        for key, value in teams_data.items():
            if key.isdigit() and "team" in value:
                teams.append(value["team"])
        
        return teams
    
    def get_team_roster(self, team_key: str) -> List[Dict[str, Any]]:
        """Get roster for a specific team.
        
        Args:
            team_key: Yahoo team key (e.g., "423.l.12345.t.1")
            
        Returns:
            List of player dictionaries
        """
        data = self._make_request(f"team/{team_key}/roster/players")
        roster_data = data.get("fantasy_content", {}).get("team", {}).get("roster", {}).get("players", {})
        
        players = []
        for key, value in roster_data.items():
            if key.isdigit() and "player" in value:
                players.append(value["player"])
        
        return players
    
    def get_players(self, league_key: str, player_keys: List[str]) -> List[Dict[str, Any]]:
        """Get player information for multiple players.
        
        Args:
            league_key: Yahoo league key
            player_keys: List of player keys
            
        Returns:
            List of player dictionaries with stats
        """
        if not player_keys:
            return []
        
        # Yahoo limits to 25 players per request
        all_players = []
        for i in range(0, len(player_keys), 25):
            batch = player_keys[i:i+25]
            keys_str = ",".join(batch)
            
            data = self._make_request(f"league/{league_key}/players;player_keys={keys_str}/stats")
            players_data = data.get("fantasy_content", {}).get("league", {}).get("players", {})
            
            for key, value in players_data.items():
                if key.isdigit() and "player" in value:
                    all_players.append(value["player"])
        
        return all_players
    
    def search_players(self, league_key: str, search: str, position: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for players by name.
        
        Args:
            league_key: Yahoo league key
            search: Search query
            position: Optional position filter (e.g., "QB", "RB")
            
        Returns:
            List of matching players
        """
        params = {"search": search}
        if position:
            params["position"] = position
        
        data = self._make_request(f"league/{league_key}/players;search={search}", params)
        players_data = data.get("fantasy_content", {}).get("league", {}).get("players", {})
        
        players = []
        for key, value in players_data.items():
            if key.isdigit() and "player" in value:
                players.append(value["player"])
        
        return players
    
    def get_free_agents(self, league_key: str, position: Optional[str] = None, 
                       start: int = 0, count: int = 25) -> List[Dict[str, Any]]:
        """Get available free agents.
        
        Args:
            league_key: Yahoo league key
            position: Optional position filter
            start: Starting index for pagination
            count: Number of results to return
            
        Returns:
            List of available players
        """
        params = {
            "status": "FA",  # Free Agents
            "start": start,
            "count": count
        }
        if position:
            params["position"] = position
        
        endpoint = f"league/{league_key}/players;status=FA"
        if position:
            endpoint += f";position={position}"
        
        data = self._make_request(endpoint, params)
        players_data = data.get("fantasy_content", {}).get("league", {}).get("players", {})
        
        players = []
        for key, value in players_data.items():
            if key.isdigit() and "player" in value:
                players.append(value["player"])
        
        return players
    
    def get_league_transactions(self, league_key: str, types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get recent transactions in the league.
        
        Args:
            league_key: Yahoo league key
            types: Optional list of transaction types (add, drop, trade)
            
        Returns:
            List of transaction dictionaries
        """
        endpoint = f"league/{league_key}/transactions"
        if types:
            type_filter = ",".join(types)
            endpoint += f";types={type_filter}"
        
        data = self._make_request(endpoint)
        transactions_data = data.get("fantasy_content", {}).get("league", {}).get("transactions", {})
        
        transactions = []
        for key, value in transactions_data.items():
            if key.isdigit() and "transaction" in value:
                transactions.append(value["transaction"])
        
        return transactions
    
    def get_league_draft_results(self, league_key: str) -> List[Dict[str, Any]]:
        """Get draft results for a league.
        
        Args:
            league_key: Yahoo league key
            
        Returns:
            List of draft pick dictionaries
        """
        data = self._make_request(f"league/{league_key}/draftresults")
        draft_data = data.get("fantasy_content", {}).get("league", {}).get("draft_results", {})
        
        picks = []
        for key, value in draft_data.items():
            if key.isdigit() and "draft_result" in value:
                picks.append(value["draft_result"])
        
        return picks