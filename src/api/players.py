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