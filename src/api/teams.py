"""
Teams API endpoints for managing fantasy teams across platforms
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta
import time

from ..models.database import get_db
from ..models.user import User
from ..models.fantasy import League, FantasyTeam
from ..models.espn_league import ESPNLeague
from ..models.espn_team import ESPNTeam, TradeRecommendation
from ..utils.dependencies import get_current_active_user
from ..services.espn_bridge import get_espn_bridge_service
from ..services.espn_integration import espn_service, ESPNServiceError, ESPNAuthError
from ..config import settings

router = APIRouter(prefix="/teams", tags=["teams"])
logger = logging.getLogger(__name__)

# Simple in-memory cache for ESPN roster data
roster_cache = {}
CACHE_DURATION = 300  # 5 minutes in seconds

def get_cache_key(league_id: int, team_id: int, season: int) -> str:
    """Generate cache key for roster data"""
    return f"roster_{league_id}_{team_id}_{season}"

def get_cached_roster(league_id: int, team_id: int, season: int) -> Optional[List[Dict[str, Any]]]:
    """Get cached roster data if available and not expired"""
    cache_key = get_cache_key(league_id, team_id, season)
    if cache_key in roster_cache:
        cached_data, timestamp = roster_cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            logger.info(f"Using cached roster data for {cache_key}")
            return cached_data
        else:
            # Remove expired cache entry
            del roster_cache[cache_key]
    return None

def cache_roster(league_id: int, team_id: int, season: int, roster_data: List[Dict[str, Any]]) -> None:
    """Cache roster data with timestamp"""
    cache_key = get_cache_key(league_id, team_id, season)
    roster_cache[cache_key] = (roster_data, time.time())
    logger.info(f"Cached roster data for {cache_key}")


# Response models
class TeamResponse(BaseModel):
    id: str
    name: str
    league: str
    platform: str
    season: Optional[int] = None
    record: str
    points: float
    rank: str
    playoffs: bool
    active: bool
    espn_league_id: Optional[int] = None
    user_team_id: Optional[int] = None
    draft_completed: Optional[bool] = None
    scoring_type: Optional[str] = None


class TeamDetail(BaseModel):
    id: str
    name: str
    league: str
    platform: str
    roster: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    settings: Dict[str, Any]


@router.get("/debug")
async def debug_teams(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to test teams functionality"""
    try:
        espn_leagues = db.query(ESPNLeague).filter(
            ESPNLeague.user_id == current_user.id,
            ESPNLeague.is_archived == False
        ).all()
        
        return {
            "user_id": current_user.id,
            "use_mock_data": settings.use_mock_data,
            "espn_leagues_count": len(espn_leagues),
            "leagues": [
                {
                    "id": league.id,
                    "name": league.league_name,
                    "espn_league_id": league.espn_league_id,
                    "season": league.season,
                    "active": league.is_active
                }
                for league in espn_leagues
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/simple")
async def get_simple_teams(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Simple teams endpoint for testing"""
    
    espn_leagues = db.query(ESPNLeague).filter(
        ESPNLeague.user_id == current_user.id,
        ESPNLeague.is_archived == False
    ).all()
    
    teams = []
    for league in espn_leagues:
        teams.append({
            "id": f"espn_{league.id}",
            "name": league.user_team_name or f"Team in {league.league_name}",
            "league": league.league_name,
            "platform": "ESPN",
            "season": league.season,
            "active": league.is_active,
            "espn_league_id": league.espn_league_id,
            "draft_completed": league.draft_completed,
            "scoring_type": league.scoring_type
        })
    
    return {"teams": teams}


@router.get("/", include_in_schema=True)
async def get_user_teams(
    include_espn: bool = True,
    include_manual: bool = True,
    season: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all teams for the current user across platforms"""
    
    # Check if we should use mock data
    if settings.use_mock_data:
        logger.info(f"Using mock data for user {current_user.id}")
        return get_mock_teams()
    
    # Get ESPN leagues directly from database
    espn_leagues = db.query(ESPNLeague).filter(
        ESPNLeague.user_id == current_user.id,
        ESPNLeague.is_archived == False
    ).all()
    
    logger.info(f"Found {len(espn_leagues)} ESPN leagues for user {current_user.id}")
    
    teams = []
    for league in espn_leagues:
        if season is None or league.season == season:
            # Use database values directly instead of external API calls
            teams.append({
                "id": f"espn_{league.id}",
                "name": league.user_team_name or f"Team in {league.league_name}",
                "league": league.league_name,
                "platform": "ESPN",
                "season": league.season,
                "record": "0-0",  # Will be populated by sync
                "points": 0.0,    # Will be populated by sync
                "rank": "--",     # Will be populated by sync
                "playoffs": False, # Will be populated by sync
                "active": league.is_active,
                "espn_league_id": league.espn_league_id,
                "user_team_id": league.user_team_id,  # Include user's team ID
                "draft_completed": league.draft_completed,
                "scoring_type": league.scoring_type
            })
    
    return teams


@router.get("/{team_id}", response_model=TeamDetail)
async def get_team_detail(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information for a specific team"""
    logger.info(f"Getting team detail for team_id: {team_id}")
    
    if team_id.startswith("espn_"):
        # Handle ESPN team
        espn_league_id = int(team_id.replace("espn_", ""))
        espn_league = db.query(ESPNLeague).filter(
            ESPNLeague.id == espn_league_id,
            ESPNLeague.user_id == current_user.id
        ).first()
        
        if not espn_league:
            raise HTTPException(status_code=404, detail="ESPN team not found")
        
        # Get roster data - try live ESPN data first, fall back to mock
        if settings.use_mock_data:
            roster_data = get_mock_espn_roster(espn_league.scoring_type or "PPR")
        else:
            # Try to get live ESPN roster data
            try:
                # Get the ESPN team ID from the league record
                espn_team_id = espn_league.user_team_id or 1  # Default to 1 if not set
                roster_data = await get_live_espn_roster(
                    espn_league.espn_league_id, 
                    espn_team_id, 
                    espn_league.season,
                    espn_league.espn_s2,
                    espn_league.swid
                )
            except Exception as e:
                logger.warning(f"Failed to get live ESPN roster for team {team_id}: {e}")
                roster_data = get_mock_espn_roster(espn_league.scoring_type or "PPR")
        
        logger.info(f"Returning roster with {len(roster_data)} players for team {team_id}")
        return TeamDetail(
            id=team_id,
            name=espn_league.user_team_name or f"Team in {espn_league.league_name}",
            league=espn_league.league_name,
            platform="ESPN",
            roster=roster_data,
            recent_activity=[
                {
                    "type": "draft" if not espn_league.draft_completed else "league",
                    "description": "Draft in progress" if not espn_league.draft_completed else "Season active",
                    "timestamp": espn_league.updated_at.isoformat() if espn_league.updated_at else None
                }
            ],
            settings={
                "scoring_type": espn_league.scoring_type,
                "team_count": espn_league.team_count,
                "roster_positions": espn_league.roster_positions or {},
                "season": espn_league.season,
                "draft_completed": espn_league.draft_completed
            }
        )
    
    elif team_id.startswith("manual_"):
        # Handle manual team
        manual_team_id = int(team_id.replace("manual_", ""))
        manual_team = db.query(FantasyTeam).filter(
            FantasyTeam.id == manual_team_id,
            FantasyTeam.owner_id == current_user.id
        ).first()
        
        if not manual_team:
            raise HTTPException(status_code=404, detail="Manual team not found")
        
        return TeamDetail(
            id=team_id,
            name=manual_team.name,
            league=manual_team.league.name,
            platform=manual_team.league.platform or "Manual",
            roster=[],  # TODO: Get roster from Roster model
            recent_activity=[
                {
                    "type": "record",
                    "description": f"Record: {manual_team.wins}-{manual_team.losses}",
                    "timestamp": manual_team.updated_at.isoformat() if manual_team.updated_at else None
                }
            ],
            settings={
                "scoring_type": manual_team.league.scoring_type,
                "team_count": manual_team.league.team_count,
                "wins": manual_team.wins,
                "losses": manual_team.losses,
                "points_for": manual_team.points_for,
                "points_against": manual_team.points_against
            }
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid team ID format")


@router.post("/{team_id}/sync")
async def sync_team_data(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sync team data from external platform (ESPN)"""
    
    if not team_id.startswith("espn_"):
        raise HTTPException(status_code=400, detail="Sync only available for ESPN teams")
    
    espn_league_id = int(team_id.replace("espn_", ""))
    espn_league = db.query(ESPNLeague).filter(
        ESPNLeague.id == espn_league_id,
        ESPNLeague.user_id == current_user.id
    ).first()
    
    if not espn_league:
        raise HTTPException(status_code=404, detail="ESPN team not found")
    
    try:
        # Sync team data from ESPN
        async with espn_service.client as client:
            # Get all teams in the league
            teams_response = await client.get_league_teams(
                espn_league.espn_league_id,
                espn_league.season
            )
            
            if teams_response.get('success'):
                teams_data = teams_response.get('data', [])
                
                # For now, we'll manually set team 8 based on our discovery
                # TODO: In the future, we should identify the user's team automatically
                user_team_data = next((team for team in teams_data if team['id'] == 8), None)
                
                if user_team_data:
                    espn_league.user_team_id = user_team_data['id']
                    espn_league.user_team_name = user_team_data['name']
                    espn_league.user_team_abbreviation = user_team_data['abbreviation']
                    espn_league.user_draft_position = user_team_data['draft']['position']
                
        from datetime import datetime
        espn_league.last_sync = datetime.utcnow()
        db.commit()
        
        return {
            "message": "Team data synced successfully", 
            "last_sync": espn_league.last_sync,
            "team_id": espn_league.user_team_id,
            "team_name": espn_league.user_team_name
        }
        
    except Exception as e:
        logger.error(f"Error syncing team data: {e}")
        from datetime import datetime
        espn_league.last_sync = datetime.utcnow()
        db.commit()
        return {"message": "Sync completed with errors", "last_sync": espn_league.last_sync, "error": str(e)}


@router.post("/{team_id}/waiver-recommendations")
async def get_team_waiver_recommendations(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get waiver recommendations for ESPN team"""
    
    if not team_id.startswith("espn_"):
        raise HTTPException(status_code=400, detail="Waiver recommendations only available for ESPN teams")
    
    espn_league_id = int(team_id.replace("espn_", ""))
    logger.info(f"Looking for ESPNLeague with id={espn_league_id} for user={current_user.id}")
    
    espn_league = db.query(ESPNLeague).filter(
        ESPNLeague.id == espn_league_id,
        ESPNLeague.user_id == current_user.id
    ).first()
    
    if not espn_league:
        logger.warning(f"ESPN team not found in DB: id={espn_league_id}, user={current_user.id}")
        # If we're using mock data, create a fake league object
        if settings.use_mock_data or espn_league_id <= 3:  # Support mock team IDs 1-3
            class MockESPNLeague:
                id = espn_league_id
                espn_league_id = 12345 + espn_league_id
                user_team_name = ["Thunder Bolts", "Fantasy Phenoms", "Draft Kings"][espn_league_id - 1] if espn_league_id <= 3 else f"Team {espn_league_id}"
                league_name = ["Mock League Championship", "Friends & Family League", "Work League"][espn_league_id - 1] if espn_league_id <= 3 else f"League {espn_league_id}"
                scoring_type = ["PPR", "Standard", "Half-PPR"][espn_league_id - 1] if espn_league_id <= 3 else "PPR"
            espn_league = MockESPNLeague()
            logger.info(f"Using mock data for team {team_id}")
        else:
            raise HTTPException(status_code=404, detail="ESPN team not found")
    
    # Get team-specific info for better recommendations
    team_info = {
        "team_id": team_id,
        "league_id": espn_league.espn_league_id,
        "team_name": espn_league.user_team_name or f"Team in {espn_league.league_name}",
        "scoring_type": espn_league.scoring_type or "PPR"
    }
    
    logger.info(f"Generating waiver recommendations for team: {team_info['team_name']} (ID: {team_id})")
    
    # Fetch real free agents from ESPN
    try:
        from ..services.espn_integration import espn_service
        
        # Get free agents from ESPN
        free_agents = await espn_service.get_free_agents(
            league_id=espn_league.espn_league_id,
            season=espn_league.season if hasattr(espn_league, 'season') else 2024,
            limit=50,
            espn_s2=espn_league.espn_s2 if hasattr(espn_league, 'espn_s2') else None,
            swid=espn_league.swid if hasattr(espn_league, 'swid') else None
        )
        
        # Convert ESPN data to our waiver recommendation format
        recommendations = []
        if free_agents and 'players' in free_agents:
            for player in free_agents['players'][:20]:  # Top 20 free agents
                player_info = player.get('player', {})
                
                # Calculate recommendation score based on ownership and projections
                ownership_pct = player_info.get('ownership', {}).get('percentOwned', 0)
                projected_points = player_info.get('stats', [{}])[0].get('appliedTotal', 0.0) if player_info.get('stats') else 0.0
                
                # Simple scoring: higher projection + lower ownership = better pickup
                recommendation_score = min(100, int(projected_points * 5 + (100 - ownership_pct) / 2))
                
                # Determine priority
                if recommendation_score >= 80:
                    priority = "high"
                    faab_bid = 15 + int((recommendation_score - 80) / 2)
                elif recommendation_score >= 60:
                    priority = "medium"
                    faab_bid = 8 + int((recommendation_score - 60) / 4)
                else:
                    priority = "low"
                    faab_bid = max(1, int(recommendation_score / 10))
                
                # Get position
                position = player_info.get('defaultPositionId', 'FLEX')
                if isinstance(position, int):
                    position_map = {1: 'QB', 2: 'RB', 3: 'WR', 4: 'TE', 5: 'K', 16: 'D/ST'}
                    position = position_map.get(position, 'FLEX')
                
                recommendation = {
                    "player_id": player_info.get('id', 0),
                    "name": player_info.get('fullName', 'Unknown'),
                    "position": position,
                    "team": player_info.get('proTeamId', 'FA'),
                    "ownership_percentage": ownership_pct,
                    "recommendation_score": recommendation_score,
                    "pickup_priority": priority,
                    "suggested_faab_bid": faab_bid,
                    "analysis": f"Available in {100 - ownership_pct:.1f}% of leagues. Projected for {projected_points:.1f} points.",
                    "trending_direction": "up" if ownership_pct > 10 else "stable",
                    "recent_performance": {},  # TODO: Add recent game stats
                    "matchup_analysis": f"Projected {projected_points:.1f} points this week",
                    "injury_status": player_info.get('injuryStatus', 'ACTIVE')
                }
                
                recommendations.append(recommendation)
        
        # Sort by recommendation score
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return {
            "recommendations": recommendations[:10],  # Return top 10
            "team_info": {
                "team_id": team_id,
                "team_name": team_info["team_name"],
                "league_id": team_info["league_id"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching ESPN free agents: {e}")
        # Fall back to empty recommendations on error
        return {
            "recommendations": [],
            "team_info": {
                "team_id": team_id,
                "team_name": team_info["team_name"],
                "league_id": team_info["league_id"]
            },
            "error": "Unable to fetch waiver recommendations at this time"
        }
    


@router.post("/{team_id}/trade-targets")
async def get_team_trade_targets(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dynamic trade targets for ESPN team"""
    
    if not team_id.startswith("espn_"):
        raise HTTPException(status_code=400, detail="Trade targets only available for ESPN teams")
    
    espn_league_id = int(team_id.replace("espn_", ""))
    logger.info(f"Getting trade targets for team {team_id} (league ID: {espn_league_id})")
    
    # Get ESPN league
    espn_league = db.query(ESPNLeague).filter(
        ESPNLeague.id == espn_league_id,
        ESPNLeague.user_id == current_user.id
    ).first()
    
    if not espn_league:
        raise HTTPException(status_code=404, detail="ESPN league not found")
    
    # Get user's team
    user_team = db.query(ESPNTeam).filter(
        ESPNTeam.espn_league_id == espn_league.id,
        ESPNTeam.is_user_team == True
    ).first()
    
    if not user_team:
        # If no user team found, sync teams first
        logger.info(f"No user team found, syncing teams for league {espn_league.id}")
        from ..services.team_sync import team_sync_service
        await team_sync_service.sync_league_teams(db, espn_league, force_refresh=False)
        
        # Try to find user team again
        user_team = db.query(ESPNTeam).filter(
            ESPNTeam.espn_league_id == espn_league.id,
            ESPNTeam.is_user_team == True
        ).first()
        
        if not user_team:
            raise HTTPException(status_code=404, detail="User team not found in league")
    
    # Check for valid cached recommendations
    from ..models.espn_team import TradeRecommendation
    cached_recommendations = db.query(TradeRecommendation).filter(
        TradeRecommendation.user_team_id == user_team.id,
        TradeRecommendation.is_expired == False,
        TradeRecommendation.expires_at > datetime.utcnow()
    ).all()
    
    # If we have valid cached recommendations, return them
    if cached_recommendations:
        logger.info(f"Found {len(cached_recommendations)} cached trade recommendations")
        targets = [rec.to_api_response() for rec in cached_recommendations]
        
        return {
            "targets": targets,
            "team_info": {
                "team_id": team_id,
                "team_name": user_team.team_name,
                "league_id": espn_league.espn_league_id
            },
            "cache_info": {
                "cached": True,
                "generated_at": cached_recommendations[0].generated_at.isoformat() if cached_recommendations else None,
                "expires_in_days": min(rec.get_days_until_expiration() for rec in cached_recommendations)
            }
        }
    
    # No valid cache, generate new recommendations
    logger.info("No valid cached recommendations found, generating new ones")
    
    try:
        # Import here to avoid circular imports
        from ..services.trade_analyzer_new import trade_analysis_engine
        
        # Generate new recommendations
        recommendations = await trade_analysis_engine.generate_trade_recommendations(
            db, user_team, max_recommendations=5
        )
        
        # Convert to API response format
        targets = [rec.to_api_response() for rec in recommendations]
        
        return {
            "targets": targets,
            "team_info": {
                "team_id": team_id,
                "team_name": user_team.team_name,
                "league_id": espn_league.espn_league_id
            },
            "cache_info": {
                "cached": False,
                "generated_at": datetime.utcnow().isoformat(),
                "expires_in_days": 5
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating trade recommendations: {e}")
        # Fall back to mock data for now
        return {
            "targets": [],
            "team_info": {
                "team_id": team_id,
                "team_name": user_team.team_name,
                "league_id": espn_league.espn_league_id
            },
            "error": "Failed to generate recommendations, please try refreshing"
        }


@router.post("/{team_id}/trade-targets/refresh")
async def refresh_trade_targets(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Force refresh trade targets for ESPN team"""
    
    if not team_id.startswith("espn_"):
        raise HTTPException(status_code=400, detail="Trade targets only available for ESPN teams")
    
    espn_league_id = int(team_id.replace("espn_", ""))
    logger.info(f"Force refreshing trade targets for team {team_id}")
    
    # Get ESPN league
    espn_league = db.query(ESPNLeague).filter(
        ESPNLeague.id == espn_league_id,
        ESPNLeague.user_id == current_user.id
    ).first()
    
    if not espn_league:
        raise HTTPException(status_code=404, detail="ESPN league not found")
    
    # Get user's team
    user_team = db.query(ESPNTeam).filter(
        ESPNTeam.espn_league_id == espn_league.id,
        ESPNTeam.is_user_team == True
    ).first()
    
    if not user_team:
        raise HTTPException(status_code=404, detail="User team not found in league")
    
    # Sync teams first to get latest data
    from ..services.team_sync import team_sync_service
    sync_log = await team_sync_service.sync_league_teams(db, espn_league, force_refresh=True)
    
    # Expire old recommendations
    from ..models.espn_team import TradeRecommendation
    old_recommendations = db.query(TradeRecommendation).filter(
        TradeRecommendation.user_team_id == user_team.id,
        TradeRecommendation.is_expired == False
    ).all()
    
    for rec in old_recommendations:
        rec.mark_expired()
    
    db.commit()
    
    # Generate new recommendations
    try:
        from ..services.trade_analyzer_new import trade_analysis_engine
        
        recommendations = await trade_analysis_engine.generate_trade_recommendations(
            db, user_team, max_recommendations=5
        )
        
        targets = [rec.to_api_response() for rec in recommendations]
        
        return {
            "targets": targets,
            "team_info": {
                "team_id": team_id,
                "team_name": user_team.team_name,
                "league_id": espn_league.espn_league_id
            },
            "refresh_info": {
                "refreshed": True,
                "teams_synced": sync_log.teams_processed,
                "generated_at": datetime.utcnow().isoformat(),
                "expires_in_days": 5
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating trade recommendations after refresh: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations after refresh")


def get_mock_teams() -> List[Dict[str, Any]]:
    """Return mock team data for testing"""
    return [
        {
            "id": "espn_1",  # Changed to ESPN format
            "name": "Thunder Bolts",
            "league": "Mock League Championship",
            "platform": "ESPN",
            "season": 2024,
            "record": "8-5",
            "points": 1456.7,
            "rank": "3rd",
            "playoffs": True,
            "active": True,
            "espn_league_id": 12345,
            "user_team_id": 3,  # Team 3 is the user's selected team in this league
            "draft_completed": True,
            "scoring_type": "PPR"
        },
        {
            "id": "espn_2",  # Changed to ESPN format
            "name": "Fantasy Phenoms",
            "league": "Friends & Family League",
            "platform": "ESPN",
            "season": 2024,
            "record": "6-7",
            "points": 1312.4,
            "rank": "7th",
            "playoffs": False,
            "active": True,
            "espn_league_id": 67890,
            "user_team_id": None,  # No team selected in this league
            "draft_completed": True,
            "scoring_type": "Standard"
        },
        {
            "id": "espn_3",  # Changed to ESPN format even though it's manual for consistency
            "name": "Draft Kings",
            "league": "Work League",
            "platform": "ESPN",  # Changed to ESPN so it works with our endpoints
            "season": 2024,
            "record": "10-3",
            "points": 1589.2,
            "rank": "1st",
            "playoffs": True,
            "active": True,
            "espn_league_id": None,
            "user_team_id": None,
            "draft_completed": None,
            "scoring_type": "Half-PPR"
        }
    ]


async def get_live_espn_roster(espn_league_id: int, team_id: int, season: int = 2024, espn_s2: str = None, swid: str = None) -> List[Dict[str, Any]]:
    """Get live roster data from ESPN service with caching"""
    
    # Check cache first
    cached_roster = get_cached_roster(espn_league_id, team_id, season)
    if cached_roster is not None:
        return cached_roster
    
    try:
        # Get roster data from ESPN service with cookies
        async with espn_service.client as client:
            roster_response = await client.get_team_roster(
                team_id,
                espn_league_id,
                season,
                espn_s2=espn_s2,
                swid=swid
            )
        
        if not roster_response.get('success'):
            raise ESPNServiceError("Failed to fetch roster from ESPN")
        
        roster_data = roster_response.get('data', {})
        entries = roster_data.get('entries', [])
        
        # Convert ESPN roster format to our format
        formatted_roster = []
        for entry in entries:
            player = entry.get('player', {})
            if not player:
                continue
                
            formatted_player = {
                "id": player.get('id', 0),
                "name": player.get('name', 'Unknown Player'),
                "position": player.get('position', 'UNKNOWN'),
                "team": player.get('team', 'FA'),
                "status": 'starter' if entry.get('position') != 'BENCH' else 'bench',
                "points": 0.0,  # ESPN stats would need to be processed
                "projected_points": 0.0,  # Would need projection data
                "injury_status": player.get('injuryStatus', 'ACTIVE')
            }
            formatted_roster.append(formatted_player)
        
        # Cache the processed roster data
        cache_roster(espn_league_id, team_id, season, formatted_roster)
        
        return formatted_roster
        
    except ESPNAuthError as e:
        logger.warning(f"ESPN authentication error getting roster: {e}")
        # Re-raise auth errors so they can be handled by the frontend
        raise HTTPException(
            status_code=401, 
            detail={
                "message": str(e),
                "requires_auth_update": True,
                "action": "update_espn_cookies"
            }
        )
    except ESPNServiceError as e:
        logger.error(f"ESPN service error getting roster: {e}")
        # Fall back to mock data if ESPN service fails
        return get_mock_espn_roster()
    except Exception as e:
        logger.error(f"Unexpected error getting ESPN roster: {e}")
        # Fall back to mock data if anything else fails
        return get_mock_espn_roster()


def get_mock_espn_roster(scoring_type: str = "PPR") -> List[Dict[str, Any]]:
    """Return mock ESPN roster data with realistic players and points based on scoring type"""
    
    # Adjust points based on scoring type
    ppr_bonus = 1.0 if scoring_type == "PPR" else (0.5 if scoring_type == "Half-PPR" else 0.0)
    
    roster = [
        # Starting lineup
        {
            "id": 1,
            "name": "Josh Allen",
            "position": "QB",
            "team": "BUF",
            "status": "starter",
            "points": 287.4,
            "projected_points": 22.3,
            "injury_status": "Healthy"
        },
        {
            "id": 2,
            "name": "Christian McCaffrey", 
            "position": "RB",
            "team": "SF",
            "status": "starter",
            "points": 234.7 + (15 * ppr_bonus),  # CMC gets lots of catches
            "projected_points": 19.8,
            "injury_status": "OUT - Achilles"
        },
        {
            "id": 3,
            "name": "Saquon Barkley",
            "position": "RB", 
            "team": "PHI",
            "status": "starter",
            "points": 198.3 + (8 * ppr_bonus),
            "projected_points": 16.2,
            "injury_status": "Healthy"
        },
        {
            "id": 4,
            "name": "CeeDee Lamb",
            "position": "WR",
            "team": "DAL", 
            "status": "starter",
            "points": 189.7 + (12 * ppr_bonus),
            "projected_points": 15.4,
            "injury_status": "Healthy"
        },
        {
            "id": 5,
            "name": "Tyreek Hill",
            "position": "WR",
            "team": "MIA",
            "status": "starter", 
            "points": 176.2 + (11 * ppr_bonus),
            "projected_points": 14.8,
            "injury_status": "Healthy"
        },
        {
            "id": 6,
            "name": "Travis Kelce",
            "position": "TE",
            "team": "KC",
            "status": "starter",
            "points": 156.8 + (9 * ppr_bonus),
            "projected_points": 12.1,
            "injury_status": "Healthy"
        },
        {
            "id": 7,
            "name": "Ja'Marr Chase",
            "position": "WR",
            "team": "CIN",
            "status": "starter",
            "points": 145.2 + (7 * ppr_bonus),
            "projected_points": 13.7,
            "injury_status": "QUESTIONABLE - Hip"
        },
        {
            "id": 8,
            "name": "Justin Tucker",
            "position": "K", 
            "team": "BAL",
            "status": "starter",
            "points": 98.5,
            "projected_points": 8.2,
            "injury_status": "Healthy"
        },
        {
            "id": 9,
            "name": "Dallas Cowboys",
            "position": "DEF",
            "team": "DAL",
            "status": "starter", 
            "points": 87.3,
            "projected_points": 7.4,
            "injury_status": "Healthy"
        },
        
        # Bench players
        {
            "id": 10,
            "name": "Dak Prescott",
            "position": "QB",
            "team": "DAL",
            "status": "bench",
            "points": 134.9,
            "projected_points": 18.1,
            "injury_status": "Healthy"
        },
        {
            "id": 11,
            "name": "Tony Pollard",
            "position": "RB",
            "team": "TEN", 
            "status": "bench",
            "points": 121.7 + (6 * ppr_bonus),
            "projected_points": 11.3,
            "injury_status": "Healthy"
        },
        {
            "id": 12,
            "name": "DJ Moore",
            "position": "WR",
            "team": "CHI",
            "status": "bench",
            "points": 112.4 + (8 * ppr_bonus),
            "projected_points": 12.8,
            "injury_status": "Healthy"
        },
        {
            "id": 13,
            "name": "Kyle Pitts",
            "position": "TE",
            "team": "ATL",
            "status": "bench", 
            "points": 89.6 + (4 * ppr_bonus),
            "projected_points": 9.7,
            "injury_status": "Healthy"
        },
        {
            "id": 14,
            "name": "Jerome Ford",
            "position": "RB",
            "team": "CLE",
            "status": "bench",
            "points": 76.2 + (3 * ppr_bonus),
            "projected_points": 8.1,
            "injury_status": "Healthy"
        },
        {
            "id": 15,
            "name": "Rome Odunze",
            "position": "WR", 
            "team": "CHI",
            "status": "bench",
            "points": 67.8 + (5 * ppr_bonus),
            "projected_points": 7.4,
            "injury_status": "Healthy"
        }
    ]
    
    return roster


@router.get("/{team_id}/draft")
async def get_team_draft_info(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get draft information for ESPN team"""
    
    if not team_id.startswith("espn_"):
        raise HTTPException(status_code=400, detail="Draft info only available for ESPN teams")
    
    espn_league_id = int(team_id.replace("espn_", ""))
    espn_league = db.query(ESPNLeague).filter(
        ESPNLeague.id == espn_league_id,
        ESPNLeague.user_id == current_user.id
    ).first()
    
    if not espn_league:
        raise HTTPException(status_code=404, detail="ESPN team not found")
    
    return {
        "league_id": espn_league.id,
        "league_name": espn_league.league_name,
        "draft_completed": espn_league.draft_completed,
        "draft_date": espn_league.draft_date.isoformat() if espn_league.draft_date else None,
        "can_start_draft": not espn_league.draft_completed and espn_league.is_active
    }