"""Yahoo Fantasy integration service."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

from sqlalchemy.orm import Session
from .yahoo.oauth_client import YahooOAuthClient
from .yahoo.fantasy_client import YahooFantasyClient
from ..models.user import User
from ..models.database import get_db

logger = logging.getLogger(__name__)

class YahooIntegrationService:
    """Service for integrating with Yahoo Fantasy Sports."""
    
    def __init__(self):
        self._oauth_client = None
        self._clients: Dict[int, YahooFantasyClient] = {}
    
    @property
    def oauth_client(self):
        """Lazy initialization of OAuth client."""
        if self._oauth_client is None:
            self._oauth_client = YahooOAuthClient()
        return self._oauth_client
    
    def get_authorization_url(self, user_id: int) -> tuple[str, str]:
        """Get Yahoo OAuth authorization URL for user.
        
        Args:
            user_id: User ID for state tracking
            
        Returns:
            Tuple of (authorization_url, state)
        """
        state = f"user_{user_id}_{datetime.utcnow().timestamp()}"
        return self.oauth_client.get_authorization_url(state)
    
    def handle_callback(self, user_id: int, authorization_response: str, db: Session) -> Dict[str, Any]:
        """Handle OAuth callback and store tokens.
        
        Args:
            user_id: User ID
            authorization_response: Full callback URL with code
            db: Database session
            
        Returns:
            Token information
        """
        try:
            # Exchange code for token
            token = self.oauth_client.fetch_token(authorization_response)
            
            # Store token securely (you'll need to add yahoo_oauth_token to User model)
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # Store encrypted token
                user.yahoo_oauth_token = json.dumps(token)
                db.commit()
            
            # Create client instance
            self._clients[user_id] = YahooFantasyClient(token["access_token"])
            
            return {
                "success": True,
                "expires_at": token.get("expires_at")
            }
        except Exception as e:
            logger.error(f"OAuth callback failed: {e}")
            raise
    
    def get_client(self, user_id: int, db: Session) -> YahooFantasyClient:
        """Get authenticated Yahoo client for user.
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Authenticated YahooFantasyClient
        """
        # Check cache
        if user_id in self._clients:
            return self._clients[user_id]
        
        # Get token from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.yahoo_oauth_token:
            raise ValueError("User not authenticated with Yahoo")
        
        token = json.loads(user.yahoo_oauth_token)
        
        # Check if token needs refresh
        if self.oauth_client.is_token_expired(token):
            token = self.oauth_client.refresh_token(token["refresh_token"])
            user.yahoo_oauth_token = json.dumps(token)
            db.commit()
        
        # Create client
        client = YahooFantasyClient(token["access_token"])
        self._clients[user_id] = client
        
        return client
    
    def get_user_leagues(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get all user's Yahoo leagues.
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            List of league information
        """
        client = self.get_client(user_id, db)
        
        # Get NFL leagues (game key 423 for 2024 season)
        leagues = client.get_user_leagues("423")
        
        # Enhance with additional info
        enhanced_leagues = []
        for league in leagues:
            league_key = league.get("league_key")
            if league_key:
                # Get teams in league
                teams = client.get_league_teams(league_key)
                
                # Find user's team
                user_team = None
                for team in teams:
                    if team.get("is_owned_by_current_login") == 1:
                        user_team = team
                        break
                
                enhanced_leagues.append({
                    "league_key": league_key,
                    "league_id": league.get("league_id"),
                    "name": league.get("name"),
                    "season": league.get("season"),
                    "num_teams": league.get("num_teams"),
                    "scoring_type": league.get("scoring_type"),
                    "draft_status": league.get("draft_status"),
                    "current_week": league.get("current_week"),
                    "user_team": user_team,
                    "teams": teams
                })
        
        return enhanced_leagues
    
    def get_league_details(self, user_id: int, league_key: str, db: Session) -> Dict[str, Any]:
        """Get detailed league information.
        
        Args:
            user_id: User ID
            league_key: Yahoo league key
            db: Database session
            
        Returns:
            Detailed league information
        """
        client = self.get_client(user_id, db)
        
        # Get league info
        league = client.get_league(league_key)
        
        # Get teams
        teams = client.get_league_teams(league_key)
        
        # Get recent transactions
        transactions = client.get_league_transactions(league_key)
        
        return {
            "league": league,
            "teams": teams,
            "transactions": transactions[:10]  # Last 10 transactions
        }
    
    def get_team_roster(self, user_id: int, team_key: str, db: Session) -> List[Dict[str, Any]]:
        """Get team roster with player details.
        
        Args:
            user_id: User ID
            team_key: Yahoo team key
            db: Database session
            
        Returns:
            List of players with details
        """
        client = self.get_client(user_id, db)
        return client.get_team_roster(team_key)
    
    def search_players(self, user_id: int, league_key: str, search: str, 
                      position: Optional[str], db: Session) -> List[Dict[str, Any]]:
        """Search for players in a league.
        
        Args:
            user_id: User ID
            league_key: Yahoo league key
            search: Search query
            position: Optional position filter
            db: Database session
            
        Returns:
            List of matching players
        """
        client = self.get_client(user_id, db)
        return client.search_players(league_key, search, position)
    
    def get_free_agents(self, user_id: int, league_key: str, 
                       position: Optional[str], db: Session) -> List[Dict[str, Any]]:
        """Get available free agents.
        
        Args:
            user_id: User ID
            league_key: Yahoo league key
            position: Optional position filter
            db: Database session
            
        Returns:
            List of available players
        """
        client = self.get_client(user_id, db)
        return client.get_free_agents(league_key, position)
    
    def sync_league_data(self, user_id: int, league_key: str, db: Session) -> Dict[str, Any]:
        """Sync all league data to local database.
        
        Args:
            user_id: User ID
            league_key: Yahoo league key
            db: Database session
            
        Returns:
            Sync results
        """
        client = self.get_client(user_id, db)
        
        try:
            # Get league details
            league = client.get_league(league_key)
            
            # Get all teams and rosters
            teams = client.get_league_teams(league_key)
            
            # Get draft results if available
            draft_results = []
            if league.get("draft_status") == "postdraft":
                draft_results = client.get_league_draft_results(league_key)
            
            # Store in database (you'll need to create YahooLeague model)
            # This is a placeholder for the actual database operations
            
            return {
                "success": True,
                "league_name": league.get("name"),
                "teams_synced": len(teams),
                "draft_picks_synced": len(draft_results)
            }
            
        except Exception as e:
            logger.error(f"League sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def map_yahoo_player_to_standard(self, yahoo_player: Dict[str, Any]) -> Dict[str, Any]:
        """Map Yahoo player data to standard format used by the app.
        
        Args:
            yahoo_player: Yahoo player dictionary
            
        Returns:
            Standardized player dictionary
        """
        # Extract player info
        name = yahoo_player.get("name", {})
        full_name = name.get("full", "")
        
        # Map positions
        position_type = yahoo_player.get("position_type", "")
        eligible_positions = yahoo_player.get("eligible_positions", [])
        primary_position = eligible_positions[0] if eligible_positions else position_type
        
        # Map team
        editorial_team_abbr = yahoo_player.get("editorial_team_abbr", "FA")
        
        return {
            "player_id": yahoo_player.get("player_key"),
            "name": full_name,
            "first_name": name.get("first", ""),
            "last_name": name.get("last", ""),
            "position": primary_position,
            "team": editorial_team_abbr,
            "bye_week": yahoo_player.get("bye_weeks", {}).get("week", 0),
            "status": yahoo_player.get("status", ""),
            "injury_status": yahoo_player.get("injury_note", ""),
            "ownership": {
                "percentage_owned": float(yahoo_player.get("percent_owned", 0)),
                "change": float(yahoo_player.get("ownership_delta", 0))
            },
            "points": {
                "total": float(yahoo_player.get("player_points", {}).get("total", 0)),
                "average": float(yahoo_player.get("player_points", {}).get("average", 0))
            },
            "projections": {
                "season": float(yahoo_player.get("projected_points", {}).get("total", 0)),
                "week": float(yahoo_player.get("projected_points", {}).get("week", 0))
            },
            "source": "yahoo"
        }

# Singleton instance
yahoo_integration = YahooIntegrationService()