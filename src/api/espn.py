"""
ESPN Integration API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from ..models.database import get_db
from ..models.user import User
from ..utils.dependencies import get_current_active_user
from ..services.espn_integration import espn_service, ESPNServiceError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/espn", tags=["espn"])


# Pydantic models for request/response
class ESPNLoginRequest(BaseModel):
    email: str
    password: str

class ESPNCookieValidationRequest(BaseModel):
    espn_s2: str
    swid: str


@router.get("/health")
async def check_espn_service_health():
    """Check ESPN service health and connectivity"""
    try:
        async with espn_service.client as client:
            health = await client.health_check()
            espn_status = await client.espn_connectivity_check()
        
        return {
            "espn_service": health,
            "espn_api": espn_status,
            "integration_status": "healthy"
        }
    except ESPNServiceError as e:
        raise HTTPException(status_code=503, detail=f"ESPN service error: {str(e)}")
    except Exception as e:
        logger.error(f"ESPN health check error: {e}")
        raise HTTPException(status_code=500, detail="ESPN health check failed")


# Authentication endpoints (no user auth required)
@router.post("/auth/login")
async def espn_login(login_request: ESPNLoginRequest):
    """Login to ESPN and get cookies for private league access"""
    try:
        logger.info(f"ESPN login attempt for {login_request.email}")
        
        async with espn_service.client as client:
            result = await client.login_to_espn(login_request.email, login_request.password)
        
        logger.info(f"ESPN login successful for {login_request.email}")
        return result
        
    except ESPNServiceError as e:
        logger.error(f"ESPN login failed for {login_request.email}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"ESPN login error for {login_request.email}: {e}")
        raise HTTPException(status_code=500, detail="ESPN login failed")


@router.post("/auth/validate-cookies")
async def validate_espn_cookies(cookie_request: ESPNCookieValidationRequest):
    """Validate ESPN cookies for API access"""
    try:
        async with espn_service.client as client:
            result = await client.validate_espn_cookies(cookie_request.espn_s2, cookie_request.swid)
        
        return result
        
    except ESPNServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"ESPN cookie validation error: {e}")
        raise HTTPException(status_code=500, detail="Cookie validation failed")


@router.get("/auth/cookie-status")
async def get_espn_cookie_status():
    """Get current ESPN cookie configuration status"""
    try:
        async with espn_service.client as client:
            result = await client.get_cookie_status()
        
        return result
        
    except ESPNServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"ESPN cookie status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cookie status")


@router.get("/leagues/{league_id}")
async def get_league_info(
    league_id: int,
    season: int = Query(2024, description="NFL season year"),
    current_user: User = Depends(get_current_active_user)
):
    """Get ESPN league information"""
    try:
        league_data = await espn_service.get_cached_or_fetch(
            'get_league_info', league_id, season
        )
        
        return {
            "success": True,
            "data": league_data,
            "meta": {
                "league_id": league_id,
                "season": season,
                "requested_by": current_user.id
            }
        }
    except ESPNServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch league data")


@router.get("/leagues/{league_id}/teams")
async def get_league_teams(
    league_id: int,
    season: int = Query(2024, description="NFL season year"),
    current_user: User = Depends(get_current_active_user)
):
    """Get all teams in ESPN league"""
    try:
        teams_data = await espn_service.get_cached_or_fetch(
            'get_league_teams', league_id, season
        )
        
        return {
            "success": True,
            "data": teams_data,
            "meta": {
                "league_id": league_id,
                "season": season,
                "requested_by": current_user.id
            }
        }
    except ESPNServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching teams for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch teams data")


@router.get("/leagues/{league_id}/free-agents")
async def get_free_agents(
    league_id: int,
    season: int = Query(2024, description="NFL season year"),
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(50, le=100, description="Number of players to return"),
    current_user: User = Depends(get_current_active_user)
):
    """Get available free agents from ESPN league"""
    try:
        free_agents_data = await espn_service.get_cached_or_fetch(
            'get_free_agents', league_id, season, position, limit
        )
        
        return {
            "success": True,
            "data": free_agents_data,
            "meta": {
                "league_id": league_id,
                "season": season,
                "position": position or "all",
                "limit": limit,
                "requested_by": current_user.id
            }
        }
    except ESPNServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching free agents for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch free agents")


@router.get("/teams/{team_id}/roster")
async def get_team_roster(
    team_id: int,
    league_id: int = Query(..., description="ESPN league ID"),
    season: int = Query(2024, description="NFL season year"),
    week: Optional[int] = Query(None, description="Specific week"),
    current_user: User = Depends(get_current_active_user)
):
    """Get team roster from ESPN"""
    try:
        roster_data = await espn_service.get_cached_or_fetch(
            'get_team_roster', team_id, league_id, season, week
        )
        
        return {
            "success": True,
            "data": roster_data,
            "meta": {
                "team_id": team_id,
                "league_id": league_id,
                "season": season,
                "week": week or "current",
                "requested_by": current_user.id
            }
        }
    except ESPNServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching roster for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch team roster")


@router.get("/leagues/{league_id}/draft")
async def get_draft_results(
    league_id: int,
    season: int = Query(2024, description="NFL season year"),
    current_user: User = Depends(get_current_active_user)
):
    """Get draft results from ESPN league"""
    try:
        draft_data = await espn_service.get_cached_or_fetch(
            'get_draft_results', league_id, season
        )
        
        return {
            "success": True,
            "data": draft_data,
            "meta": {
                "league_id": league_id,
                "season": season,
                "requested_by": current_user.id
            }
        }
    except ESPNServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching draft for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch draft data")


@router.post("/leagues/{league_id}/sync")
async def sync_league_data(
    league_id: int,
    season: int = Query(2024, description="NFL season year"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sync all ESPN league data and optionally save to database"""
    try:
        logger.info(f"Starting ESPN data sync for league {league_id} by user {current_user.id}")
        
        # Sync all data from ESPN
        synced_data = await espn_service.sync_league_data(league_id, season)
        
        # Here you could add logic to save the ESPN data to your database
        # For example:
        # - Create/update League records
        # - Create/update FantasyTeam records
        # - Update player information
        # - Save draft results
        
        return {
            "success": True,
            "message": "League data synced successfully",
            "data": synced_data,
            "meta": {
                "league_id": league_id,
                "season": season,
                "synced_data_types": list(synced_data.keys()),
                "requested_by": current_user.id
            }
        }
    except ESPNServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error syncing league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync league data")


@router.delete("/cache")
async def clear_espn_cache(
    current_user: User = Depends(get_current_active_user)
):
    """Clear ESPN service cache"""
    try:
        espn_service.clear_cache()
        
        logger.info(f"ESPN cache cleared by user {current_user.id}")
        
        return {
            "success": True,
            "message": "ESPN cache cleared successfully",
            "cleared_by": current_user.id
        }
    except Exception as e:
        logger.error(f"Error clearing ESPN cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/players/search")
async def search_players(
    league_id: int = Query(..., description="ESPN league ID"),
    name: str = Query(..., min_length=2, description="Player name to search"),
    season: int = Query(2024, description="NFL season year"),
    include_rostered: bool = Query(False, description="Include rostered players"),
    limit: int = Query(20, le=50, description="Number of results"),
    current_user: User = Depends(get_current_active_user)
):
    """Search for players by name in ESPN league"""
    try:
        search_results = await espn_service.get_cached_or_fetch(
            'search_players', league_id, name, season, include_rostered, limit
        )
        
        return {
            "success": True,
            "data": search_results,
            "meta": {
                "league_id": league_id,
                "search_term": name,
                "season": season,
                "include_rostered": include_rostered,
                "limit": limit,
                "requested_by": current_user.id
            }
        }
    except ESPNServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching players in league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to search players")