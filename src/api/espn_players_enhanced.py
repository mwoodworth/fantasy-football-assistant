"""
Enhanced ESPN player fetching API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import httpx
import asyncio
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..models.database import get_db
from ..models.user import User
from ..utils.dependencies import get_current_active_user
from ..services.espn_integration import espn_service, ESPNServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/espn/players", tags=["espn-players"])


class ESPNPlayerResponse(BaseModel):
    id: int
    full_name: str
    first_name: str
    last_name: str
    position_id: int
    position: str
    team_id: int
    team_name: str
    eligible_slots: List[int]
    ownership_percentage: float
    is_injured: bool
    injury_status: Optional[str]
    jersey: Optional[str]
    stats: Optional[Dict[str, Any]]
    projections: Optional[Dict[str, Any]]


class PlayerSearchFilters(BaseModel):
    position: Optional[str] = None
    team_id: Optional[int] = None
    min_ownership: Optional[float] = None
    max_ownership: Optional[float] = None
    available_only: bool = False
    injured_only: bool = False
    search_name: Optional[str] = None


# Cache for all players data
_players_cache = {
    "data": None,
    "last_updated": None,
    "ttl": timedelta(hours=6)  # Cache for 6 hours
}


def get_position_name(position_id: int) -> str:
    """Convert position ID to position name"""
    position_map = {
        1: "QB",
        2: "RB",
        3: "WR",
        4: "TE",
        5: "K",
        16: "D/ST",
        9: "DL",
        10: "LB", 
        11: "DB",
        12: "CB",
        13: "S",
        14: "EDR",
        15: "DT"
    }
    return position_map.get(position_id, f"Unknown({position_id})")


def get_team_name(team_id: int) -> str:
    """Convert team ID to team abbreviation"""
    team_map = {
        0: "FA",  # Free Agent
        1: "ATL",
        2: "BUF",
        3: "CHI",
        4: "CIN",
        5: "CLE",
        6: "DAL",
        7: "DEN",
        8: "DET",
        9: "GB",
        10: "TEN",
        11: "IND",
        12: "KC",
        13: "LV",
        14: "LAR",
        15: "MIA",
        16: "MIN",
        17: "NE",
        18: "NO",
        19: "NYG",
        20: "NYJ",
        21: "PHI",
        22: "ARI",
        23: "PIT",
        24: "LAC",
        25: "SF",
        26: "SEA",
        27: "TB",
        28: "WSH",
        29: "CAR",
        30: "JAX",
        33: "BAL",
        34: "HOU"
    }
    return team_map.get(team_id, "UNK")


async def fetch_all_players_from_espn(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Fetch all players from ESPN API with caching"""
    
    # Check cache first
    if not force_refresh and _players_cache["data"] is not None:
        if _players_cache["last_updated"] and datetime.now() - _players_cache["last_updated"] < _players_cache["ttl"]:
            logger.info("Returning cached player data")
            return _players_cache["data"]
    
    logger.info("Fetching fresh player data from ESPN API")
    
    url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/players"
    
    headers = {
        "accept": "application/json",
        "x-fantasy-filter": '{"players":{"limit":5000,"offset":0,"sortPercOwned":{"sortAsc":false,"sortPriority":1}}}',
        "x-fantasy-platform": "kona-PROD-9488cfa0d0fb59d75804777bfee76c2f161a89b1",
        "x-fantasy-source": "kona",
        "referer": "https://fantasy.espn.com/",
        "user-agent": "Mozilla/5.0 Fantasy Football Assistant"
    }
    
    params = {
        "scoringPeriodId": "0",
        "view": "players_wl"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            players = response.json()
            
            # Update cache
            _players_cache["data"] = players
            _players_cache["last_updated"] = datetime.now()
            
            logger.info(f"Successfully fetched {len(players)} players from ESPN")
            return players
            
        except httpx.HTTPError as e:
            logger.error(f"Error fetching players from ESPN: {e}")
            raise ESPNServiceError(f"Failed to fetch players: {str(e)}")


@router.get("/all")
async def get_all_players(
    force_refresh: bool = Query(False, description="Force refresh from ESPN API"),
    limit: int = Query(100, le=1000, description="Maximum number of players to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_active_user)
):
    """Get all players with optional pagination"""
    
    try:
        players = await fetch_all_players_from_espn(force_refresh)
        
        # Apply pagination
        paginated_players = players[offset:offset + limit]
        
        # Format response
        formatted_players = []
        for player in paginated_players:
            formatted_players.append({
                "id": player.get("id"),
                "full_name": player.get("fullName"),
                "first_name": player.get("firstName"),
                "last_name": player.get("lastName"),
                "position_id": player.get("defaultPositionId"),
                "position": get_position_name(player.get("defaultPositionId", 0)),
                "team_id": player.get("proTeamId", 0),
                "team": get_team_name(player.get("proTeamId", 0)),
                "eligible_slots": player.get("eligibleSlots", []),
                "ownership_percentage": player.get("ownership", {}).get("percentOwned", 0),
                "is_droppable": player.get("droppable", True),
                "universe_id": player.get("universeId", 0)
            })
        
        return {
            "total_count": len(players),
            "count": len(formatted_players),
            "offset": offset,
            "limit": limit,
            "players": formatted_players,
            "cache_updated": _players_cache["last_updated"].isoformat() if _players_cache["last_updated"] else None
        }
        
    except ESPNServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_all_players: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/search")
async def search_players(
    filters: PlayerSearchFilters,
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_active_user)
):
    """Search players with advanced filters"""
    
    try:
        # Get all players
        all_players = await fetch_all_players_from_espn()
        
        # Apply filters
        filtered_players = all_players
        
        # Filter by position
        if filters.position:
            position_ids = {
                "QB": 1, "RB": 2, "WR": 3, "TE": 4, "K": 5,
                "D/ST": 16, "DEF": 16, "DL": 9, "LB": 10, "DB": 11
            }
            if filters.position.upper() in position_ids:
                pos_id = position_ids[filters.position.upper()]
                filtered_players = [p for p in filtered_players if p.get("defaultPositionId") == pos_id]
        
        # Filter by team
        if filters.team_id is not None:
            filtered_players = [p for p in filtered_players if p.get("proTeamId") == filters.team_id]
        
        # Filter by ownership
        if filters.min_ownership is not None:
            filtered_players = [p for p in filtered_players 
                              if p.get("ownership", {}).get("percentOwned", 0) >= filters.min_ownership]
        
        if filters.max_ownership is not None:
            filtered_players = [p for p in filtered_players 
                              if p.get("ownership", {}).get("percentOwned", 0) <= filters.max_ownership]
        
        # Filter by availability
        if filters.available_only:
            filtered_players = [p for p in filtered_players if p.get("droppable", True)]
        
        # Filter by name search
        if filters.search_name:
            search_lower = filters.search_name.lower()
            filtered_players = [
                p for p in filtered_players
                if search_lower in p.get("fullName", "").lower()
                or search_lower in p.get("firstName", "").lower()
                or search_lower in p.get("lastName", "").lower()
            ]
        
        # Sort by ownership percentage (descending)
        filtered_players.sort(
            key=lambda p: p.get("ownership", {}).get("percentOwned", 0),
            reverse=True
        )
        
        # Apply limit
        filtered_players = filtered_players[:limit]
        
        # Format response
        formatted_players = []
        for player in filtered_players:
            formatted_players.append({
                "id": player.get("id"),
                "full_name": player.get("fullName"),
                "first_name": player.get("firstName"),
                "last_name": player.get("lastName"),
                "position_id": player.get("defaultPositionId"),
                "position": get_position_name(player.get("defaultPositionId", 0)),
                "team_id": player.get("proTeamId", 0),
                "team": get_team_name(player.get("proTeamId", 0)),
                "eligible_slots": player.get("eligibleSlots", []),
                "ownership_percentage": player.get("ownership", {}).get("percentOwned", 0),
                "is_droppable": player.get("droppable", True)
            })
        
        return {
            "count": len(formatted_players),
            "filters_applied": filters.dict(exclude_none=True),
            "players": formatted_players
        }
        
    except ESPNServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error in search_players: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trending")
async def get_trending_players(
    trend_type: str = Query("most_owned", regex="^(most_owned|least_owned|rising|falling)$"),
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """Get trending players based on ownership"""
    
    try:
        all_players = await fetch_all_players_from_espn()
        
        # Filter by position if specified
        if position:
            position_ids = {
                "QB": 1, "RB": 2, "WR": 3, "TE": 4, "K": 5,
                "D/ST": 16, "DEF": 16, "DL": 9, "LB": 10, "DB": 11
            }
            if position.upper() in position_ids:
                pos_id = position_ids[position.upper()]
                all_players = [p for p in all_players if p.get("defaultPositionId") == pos_id]
        
        # Apply trend logic
        if trend_type == "most_owned":
            # Sort by ownership percentage descending
            all_players.sort(
                key=lambda p: p.get("ownership", {}).get("percentOwned", 0),
                reverse=True
            )
        elif trend_type == "least_owned":
            # Sort by ownership percentage ascending (but exclude 0%)
            filtered = [p for p in all_players if p.get("ownership", {}).get("percentOwned", 0) > 0]
            filtered.sort(
                key=lambda p: p.get("ownership", {}).get("percentOwned", 0)
            )
            all_players = filtered
        elif trend_type == "rising":
            # Sort by positive ownership change
            filtered = [p for p in all_players 
                       if p.get("ownership", {}).get("percentChange", 0) > 0]
            filtered.sort(
                key=lambda p: p.get("ownership", {}).get("percentChange", 0),
                reverse=True
            )
            all_players = filtered
        elif trend_type == "falling":
            # Sort by negative ownership change
            filtered = [p for p in all_players 
                       if p.get("ownership", {}).get("percentChange", 0) < 0]
            filtered.sort(
                key=lambda p: p.get("ownership", {}).get("percentChange", 0)
            )
            all_players = filtered
        
        # Apply limit
        trending_players = all_players[:limit]
        
        # Format response
        formatted_players = []
        for player in trending_players:
            ownership = player.get("ownership", {})
            formatted_players.append({
                "id": player.get("id"),
                "full_name": player.get("fullName"),
                "position": get_position_name(player.get("defaultPositionId", 0)),
                "team": get_team_name(player.get("proTeamId", 0)),
                "ownership_percentage": ownership.get("percentOwned", 0),
                "ownership_change": ownership.get("percentChange", 0),
                "average_draft_position": ownership.get("averageDraftPosition", None)
            })
        
        return {
            "trend_type": trend_type,
            "position_filter": position,
            "count": len(formatted_players),
            "players": formatted_players
        }
        
    except ESPNServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_trending_players: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/by-team/{team_id}")
async def get_players_by_team(
    team_id: int,
    position: Optional[str] = Query(None, description="Filter by position"),
    current_user: User = Depends(get_current_active_user)
):
    """Get all players from a specific NFL team"""
    
    try:
        all_players = await fetch_all_players_from_espn()
        
        # Filter by team
        team_players = [p for p in all_players if p.get("proTeamId") == team_id]
        
        # Filter by position if specified
        if position:
            position_ids = {
                "QB": 1, "RB": 2, "WR": 3, "TE": 4, "K": 5,
                "D/ST": 16, "DEF": 16, "DL": 9, "LB": 10, "DB": 11
            }
            if position.upper() in position_ids:
                pos_id = position_ids[position.upper()]
                team_players = [p for p in team_players if p.get("defaultPositionId") == pos_id]
        
        # Sort by ownership
        team_players.sort(
            key=lambda p: p.get("ownership", {}).get("percentOwned", 0),
            reverse=True
        )
        
        # Format response
        formatted_players = []
        for player in team_players:
            formatted_players.append({
                "id": player.get("id"),
                "full_name": player.get("fullName"),
                "position": get_position_name(player.get("defaultPositionId", 0)),
                "jersey": player.get("jersey", ""),
                "ownership_percentage": player.get("ownership", {}).get("percentOwned", 0),
                "is_droppable": player.get("droppable", True)
            })
        
        return {
            "team_id": team_id,
            "team": get_team_name(team_id),
            "position_filter": position,
            "count": len(formatted_players),
            "players": formatted_players
        }
        
    except ESPNServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_players_by_team: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/distribution")
async def get_player_distribution_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get statistical distribution of all players"""
    
    try:
        all_players = await fetch_all_players_from_espn()
        
        # Calculate distributions
        position_counts = {}
        team_counts = {}
        ownership_buckets = {
            "0-10%": 0,
            "10-25%": 0,
            "25-50%": 0,
            "50-75%": 0,
            "75-90%": 0,
            "90-100%": 0
        }
        
        for player in all_players:
            # Position distribution
            pos_id = player.get("defaultPositionId", 0)
            pos_name = get_position_name(pos_id)
            position_counts[pos_name] = position_counts.get(pos_name, 0) + 1
            
            # Team distribution
            team_id = player.get("proTeamId", 0)
            team_name = get_team_name(team_id)
            team_counts[team_name] = team_counts.get(team_name, 0) + 1
            
            # Ownership distribution
            ownership_pct = player.get("ownership", {}).get("percentOwned", 0)
            if ownership_pct <= 10:
                ownership_buckets["0-10%"] += 1
            elif ownership_pct <= 25:
                ownership_buckets["10-25%"] += 1
            elif ownership_pct <= 50:
                ownership_buckets["25-50%"] += 1
            elif ownership_pct <= 75:
                ownership_buckets["50-75%"] += 1
            elif ownership_pct <= 90:
                ownership_buckets["75-90%"] += 1
            else:
                ownership_buckets["90-100%"] += 1
        
        return {
            "total_players": len(all_players),
            "position_distribution": position_counts,
            "team_distribution": team_counts,
            "ownership_distribution": ownership_buckets,
            "cache_updated": _players_cache["last_updated"].isoformat() if _players_cache["last_updated"] else None
        }
        
    except ESPNServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_player_distribution_stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")