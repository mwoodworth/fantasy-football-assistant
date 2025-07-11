"""Yahoo Fantasy Sports API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from ..models.database import get_db
from ..utils.dependencies import get_current_active_user
from ..models.user import User
from ..services.yahoo_integration import yahoo_integration
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/yahoo", tags=["Yahoo Fantasy"])

@router.get("/auth/url")
async def get_auth_url(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Get Yahoo OAuth authorization URL."""
    try:
        auth_url, state = yahoo_integration.get_authorization_url(current_user.id)
        return {
            "auth_url": auth_url,
            "state": state
        }
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate authorization URL")

@router.get("/auth/callback")
async def handle_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Handle Yahoo OAuth callback."""
    try:
        # Verify state matches user
        if not state.startswith(f"user_{current_user.id}_"):
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Build full callback URL
        callback_url = f"{yahoo_integration.oauth_client.REDIRECT_URI}?code={code}&state={state}"
        
        # Handle callback
        result = yahoo_integration.handle_callback(current_user.id, callback_url, db)
        
        return {
            "success": result["success"],
            "message": "Successfully connected to Yahoo Fantasy"
        }
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/auth/status")
async def get_auth_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Check Yahoo authentication status."""
    try:
        # Try to get client to check if authenticated
        client = yahoo_integration.get_client(current_user.id, db)
        return {
            "authenticated": True,
            "user_id": current_user.id
        }
    except ValueError:
        return {
            "authenticated": False,
            "user_id": current_user.id
        }

@router.post("/auth/disconnect")
async def disconnect_yahoo(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Disconnect Yahoo account."""
    try:
        current_user.yahoo_oauth_token = None
        db.commit()
        
        # Clear from cache
        if current_user.id in yahoo_integration._clients:
            del yahoo_integration._clients[current_user.id]
        
        return {"message": "Successfully disconnected from Yahoo"}
    except Exception as e:
        logger.error(f"Failed to disconnect Yahoo: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect")

@router.get("/leagues")
async def get_leagues(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all user's Yahoo leagues."""
    try:
        leagues = yahoo_integration.get_user_leagues(current_user.id, db)
        return leagues
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Not authenticated with Yahoo")
    except Exception as e:
        logger.error(f"Failed to get leagues: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch leagues")

@router.get("/leagues/{league_key}")
async def get_league_details(
    league_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed league information."""
    try:
        league_details = yahoo_integration.get_league_details(
            current_user.id, 
            league_key, 
            db
        )
        return league_details
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Not authenticated with Yahoo")
    except Exception as e:
        logger.error(f"Failed to get league details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch league details")

@router.get("/leagues/{league_key}/teams")
async def get_league_teams(
    league_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all teams in a league."""
    try:
        client = yahoo_integration.get_client(current_user.id, db)
        teams = client.get_league_teams(league_key)
        return teams
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Not authenticated with Yahoo")
    except Exception as e:
        logger.error(f"Failed to get teams: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch teams")

@router.get("/teams/{team_key}/roster")
async def get_team_roster(
    team_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get roster for a specific team."""
    try:
        roster = yahoo_integration.get_team_roster(
            current_user.id, 
            team_key, 
            db
        )
        # Map to standard format
        return [
            yahoo_integration.map_yahoo_player_to_standard(player) 
            for player in roster
        ]
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Not authenticated with Yahoo")
    except Exception as e:
        logger.error(f"Failed to get roster: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch roster")

@router.get("/leagues/{league_key}/players/search")
async def search_players(
    league_key: str,
    q: str = Query(..., description="Search query"),
    position: Optional[str] = Query(None, description="Position filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Search for players in a league."""
    try:
        players = yahoo_integration.search_players(
            current_user.id,
            league_key,
            q,
            position,
            db
        )
        # Map to standard format
        return [
            yahoo_integration.map_yahoo_player_to_standard(player) 
            for player in players
        ]
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Not authenticated with Yahoo")
    except Exception as e:
        logger.error(f"Failed to search players: {e}")
        raise HTTPException(status_code=500, detail="Failed to search players")

@router.get("/leagues/{league_key}/free-agents")
async def get_free_agents(
    league_key: str,
    position: Optional[str] = Query(None, description="Position filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get available free agents."""
    try:
        free_agents = yahoo_integration.get_free_agents(
            current_user.id,
            league_key,
            position,
            db
        )
        # Map to standard format
        return [
            yahoo_integration.map_yahoo_player_to_standard(player) 
            for player in free_agents
        ]
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Not authenticated with Yahoo")
    except Exception as e:
        logger.error(f"Failed to get free agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch free agents")

@router.get("/leagues/{league_key}/transactions")
async def get_league_transactions(
    league_key: str,
    types: Optional[str] = Query(None, description="Transaction types (comma-separated)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get recent transactions in the league."""
    try:
        client = yahoo_integration.get_client(current_user.id, db)
        
        # Parse transaction types
        type_list = types.split(",") if types else None
        
        transactions = client.get_league_transactions(league_key, type_list)
        return transactions
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Not authenticated with Yahoo")
    except Exception as e:
        logger.error(f"Failed to get transactions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")

@router.get("/leagues/{league_key}/draft")
async def get_draft_results(
    league_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get draft results for a league."""
    try:
        client = yahoo_integration.get_client(current_user.id, db)
        draft_results = client.get_league_draft_results(league_key)
        return draft_results
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Not authenticated with Yahoo")
    except Exception as e:
        logger.error(f"Failed to get draft results: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch draft results")

@router.post("/leagues/{league_key}/sync")
async def sync_league_data(
    league_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Sync all league data to local database."""
    try:
        result = yahoo_integration.sync_league_data(
            current_user.id,
            league_key,
            db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Not authenticated with Yahoo")
    except Exception as e:
        logger.error(f"Failed to sync league: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync league data")