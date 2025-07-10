"""
ESPN League-specific player endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..models.database import get_db
from ..models.user import User
from ..models.espn_league import ESPNLeague
from ..utils.dependencies import get_current_active_user
from ..services.espn_league_players import espn_league_players_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/espn/leagues", tags=["espn-league-players"])


@router.get("/{league_id}/players/trending")
async def get_league_trending_players(
    league_id: int,
    limit: int = Query(25, le=100, description="Number of players to return"),
    trend_type: str = Query("falling", regex="^(rising|falling)$", description="Trend direction"),
    position: Optional[str] = Query(None, description="Filter by position (QB, RB, WR, etc.)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get trending players specific to a league with ownership changes"""
    
    # Verify user has access to this league
    league = db.query(ESPNLeague).filter(
        ESPNLeague.id == league_id,
        ESPNLeague.user_id == current_user.id
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found or access denied")
    
    # Convert position to ID if provided
    position_filter = None
    if position:
        position_map = {
            "QB": 1, "RB": 2, "WR": 3, "TE": 4, "K": 5, "D/ST": 16, "DEF": 16
        }
        if position.upper() in position_map:
            position_filter = [position_map[position.upper()]]
    
    try:
        # Get trending players
        result = await espn_league_players_service.get_league_players_trending(
            league_id=league.espn_league_id,
            season=league.season,
            limit=limit,
            sort_by_change=True,
            position_filter=position_filter
        )
        
        # Filter based on trend type
        players = result.get('players', [])
        if trend_type == "rising":
            # Filter for positive changes
            players = [p for p in players if p.get('ownership_change', 0) > 0]
            players.sort(key=lambda p: p.get('ownership_change', 0), reverse=True)
        else:  # falling
            # Filter for negative changes
            players = [p for p in players if p.get('ownership_change', 0) < 0]
            players.sort(key=lambda p: p.get('ownership_change', 0))
        
        return {
            "league_id": league_id,
            "league_name": league.league_name,
            "trend_type": trend_type,
            "position_filter": position,
            "players": players[:limit],
            "count": len(players[:limit]),
            "fetched_at": result.get('fetched_at')
        }
        
    except Exception as e:
        logger.error(f"Error fetching trending players for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending players")


@router.get("/{league_id}/players/available")
async def get_top_available_players(
    league_id: int,
    limit: int = Query(50, le=100, description="Number of players to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get top available (unowned) players in a league"""
    
    # Verify user has access to this league
    league = db.query(ESPNLeague).filter(
        ESPNLeague.id == league_id,
        ESPNLeague.user_id == current_user.id
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found or access denied")
    
    try:
        result = await espn_league_players_service.get_top_available_players(
            league_id=league.espn_league_id,
            season=league.season,
            limit=limit
        )
        
        return {
            "league_id": league_id,
            "league_name": league.league_name,
            "available_players": result.get('available_players', []),
            "total_available": result.get('total_available', 0),
            "fetched_at": result.get('fetched_at')
        }
        
    except Exception as e:
        logger.error(f"Error fetching available players for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch available players")


@router.get("/{league_id}/players/ownership-analysis")
async def get_league_ownership_analysis(
    league_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get ownership analysis for a league"""
    
    # Verify user has access to this league
    league = db.query(ESPNLeague).filter(
        ESPNLeague.id == league_id,
        ESPNLeague.user_id == current_user.id
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found or access denied")
    
    try:
        # Get trending data for analysis
        rising_result = await espn_league_players_service.get_league_players_trending(
            league_id=league.espn_league_id,
            season=league.season,
            limit=100,
            sort_by_change=True
        )
        
        players = rising_result.get('players', [])
        
        # Analyze the data
        biggest_risers = [p for p in players if p.get('ownership_change', 0) > 0]
        biggest_fallers = [p for p in players if p.get('ownership_change', 0) < 0]
        
        biggest_risers.sort(key=lambda p: p.get('ownership_change', 0), reverse=True)
        biggest_fallers.sort(key=lambda p: p.get('ownership_change', 0))
        
        # Position breakdown
        position_trends = {}
        for player in players:
            pos = player.get('position', 'Unknown')
            if pos not in position_trends:
                position_trends[pos] = {
                    'rising': 0,
                    'falling': 0,
                    'total': 0,
                    'avg_change': 0,
                    'changes': []
                }
            
            change = player.get('ownership_change', 0)
            position_trends[pos]['total'] += 1
            position_trends[pos]['changes'].append(change)
            
            if change > 0:
                position_trends[pos]['rising'] += 1
            elif change < 0:
                position_trends[pos]['falling'] += 1
        
        # Calculate averages
        for pos, data in position_trends.items():
            if data['changes']:
                data['avg_change'] = sum(data['changes']) / len(data['changes'])
            del data['changes']  # Remove raw data from response
        
        return {
            "league_id": league_id,
            "league_name": league.league_name,
            "analysis": {
                "biggest_risers": biggest_risers[:10],
                "biggest_fallers": biggest_fallers[:10],
                "position_trends": position_trends,
                "total_players_analyzed": len(players)
            },
            "fetched_at": rising_result.get('fetched_at')
        }
        
    except Exception as e:
        logger.error(f"Error analyzing ownership for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze ownership data")