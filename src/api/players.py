"""
Player API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..models.database import get_db
from ..models.user import User
from ..models.player import Player, PlayerStats
from ..utils.dependencies import get_current_active_user
from ..utils.schemas import PlayerResponse, PlayerStatsResponse
from ..services.player import PlayerService
from ..services.espn_integration import ESPNDataService

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/", response_model=List[PlayerResponse])
async def get_players(
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(50, le=100),
    search: Optional[str] = Query(None, description="Search by name or team"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get players with optional filtering"""
    
    if search:
        players = PlayerService.search_players(db, search, limit)
    elif position:
        players = PlayerService.get_players_by_position(db, position, limit)
    else:
        # Get top players across all positions
        all_positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']
        players = []
        per_position = limit // len(all_positions)
        
        for pos in all_positions:
            pos_players = PlayerService.get_players_by_position(db, pos, per_position)
            players.extend(pos_players)
    
    return players


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific player by ID"""
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return player


@router.get("/{player_id}/stats", response_model=List[PlayerStatsResponse])
async def get_player_stats(
    player_id: int,
    season: Optional[int] = Query(None),
    week: Optional[int] = Query(None),
    recent_weeks: Optional[int] = Query(None, description="Get recent N weeks"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get player statistics"""
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if recent_weeks:
        stats = PlayerService.get_player_recent_stats(db, player_id, recent_weeks)
    elif season and week:
        # Get specific week stats
        stats = db.query(PlayerStats).filter(
            PlayerStats.player_id == player_id,
            PlayerStats.season == season,
            PlayerStats.week == week
        ).all()
    elif season:
        # Get season stats
        season_stat = PlayerService.get_player_season_stats(db, player_id, season)
        stats = [season_stat] if season_stat else []
    else:
        # Get current season stats
        stats = PlayerService.get_player_recent_stats(db, player_id, 10)
    
    return stats


@router.get("/{player_id}/projections")
async def get_player_projections(
    player_id: int,
    week: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get player projections"""
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    projections = PlayerService.get_player_projections(db, player_id, week)
    if not projections:
        raise HTTPException(status_code=404, detail="No projections found")
    
    return projections


@router.get("/{player_id}/value")
async def get_player_value(
    player_id: int,
    scoring_type: str = Query("standard", regex="^(standard|ppr|half_ppr)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get player's calculated fantasy value"""
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    value = PlayerService.calculate_player_value(db, player_id, scoring_type)
    
    return {
        "player_id": player_id,
        "player_name": player.name,
        "position": player.position,
        "fantasy_value": value,
        "scoring_type": scoring_type
    }


@router.get("/rankings/{position}")
async def get_position_rankings(
    position: str,
    scoring_type: str = Query("standard", regex="^(standard|ppr|half_ppr)$"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get player rankings for a specific position"""
    
    rankings = PlayerService.get_position_rankings(db, position, scoring_type, limit)
    
    return {
        "position": position,
        "scoring_type": scoring_type,
        "rankings": rankings
    }


@router.get("/injury-report/")
async def get_injury_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current injury report"""
    
    injured_players = PlayerService.get_injury_report(db)
    
    return {
        "injury_report": injured_players,
        "total_injured": len(injured_players)
    }


@router.get("/bye-week/{week}")
async def get_bye_week_players(
    week: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get players on bye for a specific week"""
    
    bye_players = PlayerService.get_bye_week_players(db, week)
    
    return {
        "week": week,
        "bye_players": bye_players,
        "total_on_bye": len(bye_players)
    }


@router.get("/espn/search")
async def search_espn_players(
    query: str = Query(..., min_length=2, description="Player name to search"),
    league_id: Optional[int] = Query(None, description="ESPN league ID for context"),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search ESPN players by name"""
    
    try:
        espn_service = ESPNDataService()
        players = await espn_service.search_players(query, limit=limit)
        
        # If league_id provided, enrich with league-specific data
        if league_id:
            # Add ownership percentage, waiver status, etc.
            pass
        
        return {
            "query": query,
            "results": players,
            "count": len(players)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search ESPN players: {str(e)}"
        )


@router.get("/espn/{espn_player_id}")
async def get_espn_player_details(
    espn_player_id: int,
    league_id: Optional[int] = Query(None, description="ESPN league ID for context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed ESPN player information"""
    
    try:
        espn_service = ESPNDataService()
        
        # Get player details from ESPN
        player_data = await espn_service.get_player_details(espn_player_id)
        
        if not player_data:
            raise HTTPException(status_code=404, detail="Player not found in ESPN")
        
        # Check if we have this player in our database
        local_player = db.query(Player).filter(Player.espn_id == espn_player_id).first()
        
        return {
            "espn_data": player_data,
            "local_player_id": local_player.id if local_player else None,
            "synced": local_player is not None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ESPN player details: {str(e)}"
        )


@router.post("/espn/sync/{espn_player_id}")
async def sync_espn_player(
    espn_player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync a specific ESPN player to local database"""
    
    try:
        espn_service = ESPNDataService()
        
        # Get player from ESPN
        player_data = await espn_service.get_player_details(espn_player_id)
        
        if not player_data:
            raise HTTPException(status_code=404, detail="Player not found in ESPN")
        
        # Sync to local database
        local_player = PlayerService.sync_espn_player(db, player_data)
        
        return {
            "message": "Player synced successfully",
            "player_id": local_player.id,
            "espn_id": local_player.espn_id,
            "name": local_player.name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync ESPN player: {str(e)}"
        )


@router.get("/espn/rankings/{position}")
async def get_espn_position_rankings(
    position: str,
    scoring_type: str = Query("standard", regex="^(standard|ppr|half_ppr)$"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ESPN expert rankings by position"""
    
    # Validate position
    valid_positions = ["QB", "RB", "WR", "TE", "K", "DEF", "FLEX"]
    if position not in valid_positions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid position. Must be one of: {', '.join(valid_positions)}"
        )
    
    try:
        espn_service = ESPNDataService()
        
        rankings = await espn_service.get_position_rankings(
            position=position,
            scoring_type=scoring_type,
            limit=limit
        )
        
        return {
            "position": position,
            "scoring_type": scoring_type,
            "rankings": rankings,
            "count": len(rankings)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ESPN rankings: {str(e)}"
        )


@router.get("/espn/trending")
async def get_trending_players(
    trend_type: str = Query("add", regex="^(add|drop)$", description="Added or dropped"),
    hours: int = Query(24, le=168, description="Hours to look back"),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get trending players (most added/dropped)"""
    
    try:
        espn_service = ESPNDataService()
        
        trending = await espn_service.get_trending_players(
            trend_type=trend_type,
            hours=hours,
            limit=limit
        )
        
        return {
            "trend_type": trend_type,
            "hours": hours,
            "players": trending,
            "count": len(trending)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trending players: {str(e)}"
        )


@router.post("/espn/sync-league-players/{league_id}")
async def sync_league_players(
    league_id: int,
    force: bool = Query(False, description="Force resync even if recently synced"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync all players from an ESPN league"""
    
    # Check if user has access to this league
    from ..models.fantasy import ESPNLeague
    league = db.query(ESPNLeague).filter(
        ESPNLeague.id == league_id,
        ESPNLeague.user_id == current_user.id
    ).first()
    
    if not league:
        raise HTTPException(
            status_code=403,
            detail="You don't have access to this league"
        )
    
    try:
        espn_service = ESPNDataService()
        
        # Get all players in the league
        sync_result = await espn_service.sync_league_players(
            league_id=league.espn_id,
            season=league.season,
            force=force
        )
        
        return {
            "message": "League players synced successfully",
            "players_synced": sync_result.get("synced_count", 0),
            "players_updated": sync_result.get("updated_count", 0),
            "errors": sync_result.get("errors", [])
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync league players: {str(e)}"
        )