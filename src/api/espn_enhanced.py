"""
Enhanced ESPN Integration API endpoints with live draft assistant
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
import logging
import uuid
from datetime import datetime, timedelta
import asyncio

from ..models.database import get_db
from ..models.user import User
from ..models.espn_league import (
    ESPNLeague, 
    DraftSession, 
    DraftRecommendation, 
    LeagueHistoricalData, 
    UserLeagueSettings
)
from ..utils.dependencies import get_current_active_user
from ..services.espn_integration import espn_service, ESPNServiceError, ESPNAuthError
from ..services.ai.claude_client import ai_client
from ..services.draft_assistant import draft_assistant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/espn", tags=["espn-enhanced"])


# Pydantic models for requests/responses
class ESPNLeagueConnection(BaseModel):
    espn_league_id: int = Field(..., description="ESPN League ID")
    season: int = Field(..., description="Season year")
    league_name: Optional[str] = Field(None, description="Custom league name")
    espn_s2: Optional[str] = Field(None, description="ESPN S2 cookie for private leagues")
    swid: Optional[str] = Field(None, description="ESPN SWID for private leagues")
    user_team_id: Optional[int] = Field(None, description="User's team ID in the league")
    
    @validator('season')
    def validate_season(cls, v):
        current_year = datetime.now().year
        if v < 2020 or v > current_year + 1:
            raise ValueError(f'Season must be between 2020 and {current_year + 1}')
        return v


class DraftSessionStart(BaseModel):
    league_id: int = Field(..., description="Internal league ID")
    draft_position: int = Field(..., description="User's draft position (1-based)")
    live_sync: bool = Field(True, description="Enable live ESPN sync")


class DraftPickEntry(BaseModel):
    player_id: int = Field(..., description="ESPN player ID")
    player_name: str = Field(..., description="Player name")
    position: str = Field(..., description="Player position")
    team: str = Field(..., description="NFL team")
    pick_number: int = Field(..., description="Overall pick number")
    drafted_by_user: bool = Field(False, description="Was this pick made by the user")


class LeagueResponse(BaseModel):
    id: int
    espn_league_id: int
    season: int
    league_name: str
    is_active: bool
    is_archived: bool
    team_count: int
    scoring_type: str
    draft_date: Optional[datetime]
    draft_completed: bool
    user_draft_position: Optional[int] = None
    sync_status: str
    last_sync: Optional[datetime]
    user_team_name: Optional[str]
    league_type_description: str
    espn_s2: Optional[str] = None
    swid: Optional[str] = None


class DraftSessionResponse(BaseModel):
    id: int
    session_token: str
    league_id: int
    current_pick: int
    current_round: int
    user_pick_position: int
    is_active: bool
    is_live_synced: bool
    next_user_pick: int
    picks_until_user_turn: int
    started_at: datetime
    total_rounds: int
    drafted_players: Optional[List[Dict]] = []


class DraftRecommendationResponse(BaseModel):
    id: int
    pick_number: int
    round_number: int
    recommended_players: List[Dict[str, Any]]
    primary_recommendation: Dict[str, Any]
    strategy_reasoning: str
    confidence_score: float
    recommendation_type: str
    ai_insights: Optional[List[str]] = []
    next_pick_strategy: Optional[str] = ""
    available_player_count: Optional[int] = 0
    generated_at: datetime


# Admin endpoints for league settings
@router.get("/admin/settings")
async def get_league_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current league settings (admin only)"""
    # TODO: Add admin role check
    settings = db.query(UserLeagueSettings).first()
    if not settings:
        # Create default settings
        settings = UserLeagueSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return {
        "max_leagues_per_user": settings.max_leagues_per_user,
        "allow_historical_access": settings.allow_historical_access,
        "historical_years_limit": settings.historical_years_limit,
        "auto_archive_old_seasons": settings.auto_archive_old_seasons,
        "require_league_verification": settings.require_league_verification
    }


@router.post("/admin/settings")
async def update_league_settings(
    settings_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update league settings (admin only)"""
    # TODO: Add admin role check
    settings = db.query(UserLeagueSettings).first()
    if not settings:
        settings = UserLeagueSettings()
        db.add(settings)
    
    # Update settings
    for key, value in settings_data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    
    settings.updated_by_admin = current_user.id
    settings.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(settings)
    
    return {"message": "Settings updated successfully"}


# League management endpoints
@router.get("/my-leagues", response_model=List[LeagueResponse])
async def get_user_leagues(
    include_archived: bool = Query(False, description="Include archived leagues"),
    season: Optional[int] = Query(None, description="Filter by season"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's connected ESPN leagues"""
    query = db.query(ESPNLeague).filter(ESPNLeague.user_id == current_user.id)
    
    if not include_archived:
        query = query.filter(ESPNLeague.is_archived == False)
    
    if season:
        query = query.filter(ESPNLeague.season == season)
    
    leagues = query.order_by(desc(ESPNLeague.season), ESPNLeague.league_name).all()
    
    return [
        LeagueResponse(
            id=league.id,
            espn_league_id=league.espn_league_id,
            season=league.season,
            league_name=league.league_name,
            is_active=league.is_active,
            is_archived=league.is_archived,
            team_count=league.team_count,
            scoring_type=league.scoring_type,
            draft_date=league.draft_date,
            draft_completed=league.draft_completed,
            sync_status=league.sync_status,
            last_sync=league.last_sync,
            user_team_name=league.user_team_name,
            league_type_description=league.get_league_type_description(),
            espn_s2=league.espn_s2,
            swid=league.swid
        )
        for league in leagues
    ]


@router.post("/connect-league")
async def connect_espn_league(
    league_data: ESPNLeagueConnection,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Connect a new ESPN league to user's account"""
    
    # Check user's league limit
    settings = db.query(UserLeagueSettings).first()
    if not settings:
        # Create default settings if none exist
        settings = UserLeagueSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    user_league_count = db.query(ESPNLeague).filter(
        and_(
            ESPNLeague.user_id == current_user.id,
            ESPNLeague.is_archived == False
        )
    ).count()
    
    max_leagues = settings.max_leagues_per_user or 5  # Default to 5 if None
    if user_league_count >= max_leagues:
        raise HTTPException(
            status_code=400, 
            detail="Maximum league limit reached"
        )
    
    # Check if league already connected
    existing = db.query(ESPNLeague).filter(
        and_(
            ESPNLeague.user_id == current_user.id,
            ESPNLeague.espn_league_id == league_data.espn_league_id,
            ESPNLeague.season == league_data.season
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="League already connected")
    
    try:
        # Validate league access with ESPN
        # TODO: Update ESPN service to handle authentication cookies
        try:
            league_info = await espn_service.get_league_info(
                league_data.espn_league_id,
                league_data.season
            )
        except Exception as e:
            logger.warning(f"ESPN service unavailable, using mock data: {e}")
            # Use mock data when ESPN service is unavailable
            league_info = {
                'name': league_data.league_name or f'League {league_data.espn_league_id}',
                'size': 10,
                'roster_positions': {
                    'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BENCH': 6
                },
                'scoring_settings': {
                    '53': {'points': 1.0},  # PPR
                    '4': {'points': 4.0},   # Passing TD
                    '5': {'points': 6.0},   # Rushing TD
                    '6': {'points': 6.0},   # Receiving TD
                },
                'scoring_type': 'ppr',
                'draft_date': None,
                'user_team_id': 1,
                'user_team_name': 'My Team',
                'user_team_abbreviation': 'MT'
            }
        
        # Generate league group ID for multi-year tracking
        league_group_id = f"espn_{league_data.espn_league_id}"
        
        # Find previous season for this league
        previous_season = db.query(ESPNLeague).filter(
            and_(
                ESPNLeague.user_id == current_user.id,
                ESPNLeague.league_group_id == league_group_id,
                ESPNLeague.season == league_data.season - 1
            )
        ).first()
        
        # Try to get draft position from ESPN
        user_draft_position = None
        try:
            draft_results = await espn_service.get_draft_results(
                league_data.espn_league_id,
                league_data.season
            )
            # Extract user's draft position from draft results if available
            if draft_results and 'success' in draft_results and draft_results['success']:
                draft_data = draft_results.get('data', {})
                teams = draft_data.get('teams', [])
                user_team_id = league_info.get('user_team_id')
                if user_team_id and teams:
                    for team in teams:
                        if team.get('id') == user_team_id:
                            user_draft_position = team.get('draftPosition')
                            break
        except Exception as e:
            logger.warning(f"Could not fetch draft position for league {league_data.espn_league_id}: {e}")

        # Check if draft has been completed based on draft results
        draft_completed = False
        if draft_results and 'success' in draft_results and draft_results['success']:
            draft_data = draft_results.get('data', {})
            picks = draft_data.get('picks', [])
            total_rounds = draft_data.get('totalRounds', 16)
            expected_picks = league_info.get('size', 10) * total_rounds
            # If we have all picks, draft is complete
            if len(picks) >= expected_picks:
                draft_completed = True
        
        # Create new league record
        new_league = ESPNLeague(
            user_id=current_user.id,
            espn_league_id=league_data.espn_league_id,
            season=league_data.season,
            league_name=league_data.league_name or league_info.get('name', f'League {league_data.espn_league_id}'),
            league_group_id=league_group_id,
            previous_season_id=previous_season.id if previous_season else None,
            team_count=league_info.get('size', 10),
            roster_positions=league_info.get('roster_positions', {}),
            scoring_settings=league_info.get('scoring_settings', {}),
            scoring_type=league_info.get('scoring_type', 'standard'),
            draft_date=league_info.get('draft_date'),
            draft_completed=draft_completed,
            user_draft_position=user_draft_position,
            is_private=bool(league_data.espn_s2 or league_data.swid),
            espn_s2=league_data.espn_s2,  # TODO: Encrypt these
            swid=league_data.swid,        # TODO: Encrypt these
            user_team_id=league_data.user_team_id or league_info.get('user_team_id'),
            user_team_name=league_info.get('user_team_name'),
            user_team_abbreviation=league_info.get('user_team_abbreviation'),
            sync_status='active'
        )
        
        db.add(new_league)
        db.commit()
        db.refresh(new_league)
        
        # Schedule initial data sync
        background_tasks.add_task(sync_league_data, new_league.id)
        
        return {
            "message": "League connected successfully",
            "league_id": new_league.id,
            "league_name": new_league.league_name,
            "scoring_type": new_league.get_league_type_description()
        }
        
    except ESPNServiceError as e:
        logger.error(f"ESPN service error connecting league: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to connect to ESPN league: {str(e)}")
    except Exception as e:
        logger.error(f"Error connecting league: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect league")


@router.get("/leagues/{league_id}")
async def get_league_details(
    league_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get league details with teams"""
    league = db.query(ESPNLeague).filter(
        and_(
            ESPNLeague.id == league_id,
            ESPNLeague.user_id == current_user.id
        )
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get teams from ESPN
    try:
        teams_data = await espn_service.get_league_teams(
            league.espn_league_id,
            league.season,
            league.espn_s2,
            league.swid
        )
        
        # Format teams for frontend
        teams = []
        for team in teams_data.get('teams', []):
            teams.append({
                'id': team.get('id'),
                'name': team.get('name', f"Team {team.get('id')}"),
                'abbreviation': team.get('abbrev', team.get('name', '')[:3].upper())
            })
        
        return {
            'id': league.id,
            'team_count': league.team_count,
            'user_team_id': league.user_team_id,
            'teams': teams
        }
        
    except Exception as e:
        logger.error(f"Error fetching teams for league {league_id}: {e}")
        # Return basic info without teams
        return {
            'id': league.id,
            'team_count': league.team_count,
            'user_team_id': league.user_team_id,
            'teams': []
        }


@router.delete("/leagues/{league_id}")
async def disconnect_league(
    league_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disconnect an ESPN league"""
    league = db.query(ESPNLeague).filter(
        and_(
            ESPNLeague.id == league_id,
            ESPNLeague.user_id == current_user.id
        )
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Archive instead of delete to preserve historical data
    league.is_archived = True
    league.is_active = False
    league.sync_enabled = False
    league.archived_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "League disconnected successfully"}


@router.delete("/leagues/{league_id}/permanent")
async def permanently_delete_league(
    league_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Permanently delete an archived ESPN league"""
    league = db.query(ESPNLeague).filter(
        and_(
            ESPNLeague.id == league_id,
            ESPNLeague.user_id == current_user.id,
            ESPNLeague.is_archived == True  # Only allow deletion of archived leagues
        )
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="Archived league not found")
    
    # Delete all related data
    # Delete draft sessions
    db.query(DraftSession).filter(DraftSession.league_id == league_id).delete()
    
    # Delete draft recommendations
    db.query(DraftRecommendation).filter(
        DraftRecommendation.session_id.in_(
            db.query(DraftSession.id).filter(DraftSession.league_id == league_id)
        )
    ).delete()
    
    # Delete historical data
    db.query(LeagueHistoricalData).filter(LeagueHistoricalData.league_id == league_id).delete()
    
    # Finally delete the league
    db.delete(league)
    db.commit()
    
    return {"message": "League permanently deleted"}


@router.post("/leagues/{league_id}/sync")
async def sync_league(
    league_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Manually trigger league data sync"""
    league = db.query(ESPNLeague).filter(
        and_(
            ESPNLeague.id == league_id,
            ESPNLeague.user_id == current_user.id
        )
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Trigger background sync
    background_tasks.add_task(sync_league_data, league_id)
    
    return {"message": "League sync initiated"}


@router.put("/leagues/{league_id}/unarchive")
async def unarchive_league(
    league_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Unarchive/reconnect an ESPN league"""
    league = db.query(ESPNLeague).filter(
        and_(
            ESPNLeague.id == league_id,
            ESPNLeague.user_id == current_user.id,
            ESPNLeague.is_archived == True
        )
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="Archived league not found")
    
    # Reactivate the league
    league.is_archived = False
    league.is_active = True
    league.sync_enabled = True
    league.archived_at = None
    league.sync_status = 'active'
    
    db.commit()
    db.refresh(league)
    
    return {
        "message": "League reactivated successfully",
        "league_id": league.id,
        "league_name": league.league_name
    }


# Draft session endpoints
@router.get("/draft/{session_id}/live-status")
async def get_draft_live_status(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get live draft status and recent picks"""
    session = db.query(DraftSession).filter(
        and_(
            DraftSession.id == session_id,
            DraftSession.user_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    # Get recent picks (last 10)
    recent_picks = session.drafted_players[-10:] if session.drafted_players else []
    
    # Calculate time until next pick
    next_pick_info = None
    if session.available_players and isinstance(session.available_players, dict):
        next_user_pick = session.available_players.get('next_user_pick', 0)
        picks_until_turn = session.available_players.get('picks_until_turn', 0)
        next_pick_info = {
            'next_user_pick': next_user_pick,
            'picks_until_turn': picks_until_turn,
            'estimated_time': picks_until_turn * 90  # Assume 90 seconds per pick
        }
    
    return {
        'session_id': session.id,
        'draft_status': session.draft_status,
        'current_pick': session.current_pick,
        'current_round': session.current_round,
        'current_pick_team_id': session.current_pick_team_id,
        'is_user_turn': session.current_pick_team_id == session.league.user_team_id if session.league else False,
        'recent_picks': recent_picks,
        'next_pick_info': next_pick_info,
        'last_sync': session.last_espn_sync.isoformat() if session.last_espn_sync else None,
        'sync_errors': session.sync_errors or []
    }


@router.post("/draft/{session_id}/toggle-sync")
async def toggle_draft_sync(
    session_id: int,
    enable: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Enable or disable live sync for a draft session"""
    session = db.query(DraftSession).filter(
        and_(
            DraftSession.id == session_id,
            DraftSession.user_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    session.is_live_synced = enable
    session.last_activity = datetime.utcnow()
    db.commit()
    
    # Start or stop monitoring this session
    if enable:
        from ..services.draft_monitor import draft_monitor
        # The monitor will pick it up in the next polling cycle
        logger.info(f"Enabled live sync for draft session {session_id}")
    else:
        logger.info(f"Disabled live sync for draft session {session_id}")
    
    return {
        'message': f'Live sync {"enabled" if enable else "disabled"}',
        'session_id': session_id,
        'is_live_synced': session.is_live_synced
    }


@router.post("/draft/start", response_model=DraftSessionResponse)
async def start_draft_session(
    draft_data: DraftSessionStart,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start a new draft session"""
    
    # Validate league ownership
    league = db.query(ESPNLeague).filter(
        and_(
            ESPNLeague.id == draft_data.league_id,
            ESPNLeague.user_id == current_user.id
        )
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Check for existing active session
    existing_session = db.query(DraftSession).filter(
        and_(
            DraftSession.league_id == draft_data.league_id,
            DraftSession.user_id == current_user.id,
            DraftSession.is_active == True
        )
    ).first()
    
    if existing_session:
        return DraftSessionResponse(
            id=existing_session.id,
            session_token=existing_session.session_token,
            league_id=existing_session.league_id,
            current_pick=existing_session.current_pick,
            current_round=existing_session.current_round,
            user_pick_position=existing_session.user_pick_position,
            is_active=existing_session.is_active,
            is_live_synced=existing_session.is_live_synced,
            next_user_pick=existing_session.get_next_pick_number(),
            picks_until_user_turn=existing_session.get_picks_until_user_turn(),
            started_at=existing_session.started_at,
            total_rounds=existing_session.total_rounds,
            drafted_players=existing_session.drafted_players or []
        )
    
    # Create new draft session
    session_token = str(uuid.uuid4())
    total_rounds = 16  # Standard draft rounds
    total_picks = league.team_count * total_rounds
    
    new_session = DraftSession(
        user_id=current_user.id,
        league_id=draft_data.league_id,
        session_token=session_token,
        total_rounds=total_rounds,
        total_picks=total_picks,
        user_pick_position=draft_data.draft_position,
        is_live_synced=draft_data.live_sync,
        manual_mode=not draft_data.live_sync
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return DraftSessionResponse(
        id=new_session.id,
        session_token=new_session.session_token,
        league_id=new_session.league_id,
        current_pick=new_session.current_pick,
        current_round=new_session.current_round,
        user_pick_position=new_session.user_pick_position,
        is_active=new_session.is_active,
        is_live_synced=new_session.is_live_synced,
        next_user_pick=new_session.get_next_pick_number(),
        picks_until_user_turn=new_session.get_picks_until_user_turn(),
        started_at=new_session.started_at,
        total_rounds=new_session.total_rounds,
        drafted_players=new_session.drafted_players or []
    )


@router.get("/draft/session/{session_id}", response_model=DraftSessionResponse)
async def get_draft_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get draft session details"""
    session = db.query(DraftSession).filter(
        and_(
            DraftSession.id == session_id,
            DraftSession.user_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    return DraftSessionResponse(
        id=session.id,
        session_token=session.session_token,
        league_id=session.league_id,
        current_pick=session.current_pick,
        current_round=session.current_round,
        user_pick_position=session.user_pick_position,
        is_active=session.is_active,
        is_live_synced=session.is_live_synced,
        next_user_pick=session.get_next_pick_number(),
        picks_until_user_turn=session.get_picks_until_user_turn(),
        started_at=session.started_at,
        total_rounds=session.total_rounds,
        drafted_players=session.drafted_players or []
    )


@router.get("/draft/{session_id}/test")
async def test_draft_endpoint(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Test endpoint to debug issues"""
    return {"message": "Test successful", "session_id": session_id, "user_id": current_user.id}


@router.get("/draft/{session_id}/recommendations")
async def get_draft_recommendations(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI-generated draft recommendations for current pick"""
    
    try:
        logger.info(f"Starting draft recommendations for session {session_id}, user {current_user.id}")
        
        # Validate session ownership
        session = db.query(DraftSession).filter(
            and_(
                DraftSession.id == session_id,
                DraftSession.user_id == current_user.id,
                DraftSession.is_active == True
            )
        ).first()
        
        if not session:
            logger.warning(f"Draft session {session_id} not found or not active for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Draft session not found")
        
        # Get league info
        league = db.query(ESPNLeague).filter(ESPNLeague.id == session.league_id).first()
        if not league:
            raise HTTPException(status_code=404, detail="League not found")
        
        logger.info(f"Generating recommendations for pick {session.current_pick}")
        
        # Generate recommendations using draft assistant
        recommendations = await draft_assistant.generate_recommendations(
            session=session,
            league=league,
            available_players=None  # Will use mock data
        )
        
        # Format response for frontend
        formatted_recommendations = []
        for rec in recommendations.get("recommendations", [])[:10]:
            formatted_recommendations.append({
                "player_id": rec["player_id"],
                "name": rec["name"],
                "position": rec["position"],
                "team": rec["team"],
                "projected_points": rec["projected_points"],
                "vor": rec["vor"],
                "recommendation_score": rec["recommendation_score"],
                "tier": rec["tier"],
                "adp": rec["adp"],
                "reasoning": rec["reasoning"]
            })
        
        return {
            "recommendations": formatted_recommendations,
            "ai_analysis": recommendations.get("ai_analysis", {
                "overall_strategy": "Focus on best available player",
                "confidence": 0.8,
                "key_insights": ["Standard draft strategy recommended"],
                "next_pick_strategy": "Continue building roster depth"
            }),
            "positional_needs": [
                {
                    "position": need.position,
                    "filled": need.filled_slots,
                    "required": need.required_slots,
                    "need_level": need.need_level
                }
                for need in recommendations.get("positional_needs", [])
            ],
            "context": recommendations.get("context", {
                "pick_number": session.current_pick,
                "round": session.current_round,
                "next_user_pick": session.get_next_pick_number(),
                "picks_until_turn": session.get_picks_until_user_turn()
            })
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error in recommendations function: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return fallback response
        return {
            "recommendations": [{
                "player_id": 9999,
                "name": "Best Available Player",
                "position": "FLEX",
                "team": "NFL",
                "projected_points": 150.0,
                "vor": 10.0,
                "recommendation_score": 85.0,
                "tier": 2,
                "adp": session.current_pick if session else 1,
                "reasoning": "System error - using fallback recommendations"
            }],
            "ai_analysis": {
                "overall_strategy": "Focus on best available player",
                "confidence": 0.5,
                "key_insights": ["System temporarily using fallback recommendations"],
                "next_pick_strategy": "Continue with best available approach"
            },
            "positional_needs": [],
            "context": {
                "pick_number": session.current_pick if session else 1,
                "round": session.current_round if session else 1,
                "next_user_pick": session.get_next_pick_number() if session else -1,
                "picks_until_turn": session.get_picks_until_user_turn() if session else 0
            }
        }


@router.post("/draft/{session_id}/pick")
async def record_draft_pick(
    session_id: int,
    pick_data: DraftPickEntry,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Record a draft pick (manual or auto-synced)"""
    
    # Validate session
    session = db.query(DraftSession).filter(
        and_(
            DraftSession.id == session_id,
            DraftSession.user_id == current_user.id,
            DraftSession.is_active == True
        )
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    # Update drafted players
    drafted_players = session.drafted_players or []
    drafted_players.append({
        "player_id": pick_data.player_id,
        "player_name": pick_data.player_name,
        "position": pick_data.position,
        "team": pick_data.team,
        "pick_number": pick_data.pick_number,
        "round": session.current_round,
        "drafted_by_user": pick_data.drafted_by_user,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Update user roster if user's pick
    if pick_data.drafted_by_user:
        user_roster = session.user_roster or []
        user_roster.append({
            "player_id": pick_data.player_id,
            "player_name": pick_data.player_name,
            "position": pick_data.position,
            "team": pick_data.team,
            "round": session.current_round,
            "pick_number": pick_data.pick_number
        })
        session.user_roster = user_roster
    
    # Update session state
    session.drafted_players = drafted_players
    session.current_pick = pick_data.pick_number + 1
    session.current_round = ((pick_data.pick_number - 1) // session.league.team_count) + 1
    session.last_activity = datetime.utcnow()
    
    # Check if draft is complete
    if pick_data.pick_number >= session.total_picks:
        session.is_active = False
        session.completed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Pick recorded successfully", "draft_complete": not session.is_active}


@router.post("/draft/{session_id}/sync")
async def sync_draft_with_espn(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sync draft session with live ESPN draft data"""
    
    try:
        # Validate session ownership
        session = db.query(DraftSession).filter(
            and_(
                DraftSession.id == session_id,
                DraftSession.user_id == current_user.id,
                DraftSession.is_active == True
            )
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Draft session not found")
        
        # Get league info for ESPN API calls
        league = session.league
        if not league:
            raise HTTPException(status_code=404, detail="League not found for session")
        
        logger.info(f"Syncing draft session {session_id} with ESPN league {league.espn_league_id}")
        
        # Get current draft results from ESPN
        try:
            async with espn_service.client as client:
                draft_results = await client.get_draft_results(
                    league.espn_league_id,
                    league.season
                )
                
                if not draft_results.get('success'):
                    return {"message": "Draft not started yet in ESPN", "picks_synced": 0}
                
                draft_data = draft_results.get('data', {})
                picks = draft_data.get('picks', [])
                
                if not picks:
                    return {"message": "No picks found in ESPN draft", "picks_synced": 0}
                
                # Sort picks by pick number
                picks.sort(key=lambda p: p.get('overallPickNumber', 0))
                
                # Update session with latest picks
                updated_picks = []
                current_drafted = session.drafted_players or []
                existing_pick_numbers = {pick.get('pick_number') for pick in current_drafted}
                
                for pick in picks:
                    pick_number = pick.get('overallPickNumber')
                    if pick_number and pick_number not in existing_pick_numbers:
                        player_data = pick.get('player', {})
                        team_id = pick.get('teamId')
                        
                        new_pick = {
                            "player_id": player_data.get('id'),
                            "player_name": player_data.get('fullName', 'Unknown Player'),
                            "position": player_data.get('defaultPositionId', 'Unknown'),
                            "team": player_data.get('proTeamId', 'Unknown'),
                            "pick_number": pick_number,
                            "drafted_by_user": team_id == league.user_team_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "espn_sync": True
                        }
                        
                        updated_picks.append(new_pick)
                        current_drafted.append(new_pick)
                        
                        # Update user roster if it's user's pick
                        if new_pick["drafted_by_user"]:
                            user_roster = session.user_roster or []
                            user_roster.append({
                                "player_id": new_pick["player_id"],
                                "player_name": new_pick["player_name"],
                                "position": new_pick["position"],
                                "team": new_pick["team"],
                                "round": ((pick_number - 1) // league.team_count) + 1,
                                "pick_number": pick_number
                            })
                            session.user_roster = user_roster
                
                # Update session state
                session.drafted_players = current_drafted
                
                # Update current pick to next available
                if picks:
                    last_pick = max(pick.get('overallPickNumber', 0) for pick in picks)
                    session.current_pick = last_pick + 1
                    session.current_round = ((last_pick) // league.team_count) + 1
                
                # Check if draft is complete
                if session.current_pick > session.total_picks:
                    session.is_active = False
                    session.completed_at = datetime.utcnow()
                
                session.last_activity = datetime.utcnow()
                db.commit()
                
                return {
                    "message": "Draft synced successfully", 
                    "picks_synced": len(updated_picks),
                    "current_pick": session.current_pick,
                    "current_round": session.current_round,
                    "draft_complete": session.completed_at is not None,
                    "new_picks": updated_picks
                }
                
        except Exception as e:
            logger.error(f"Error syncing with ESPN: {e}")
            return {"message": f"Sync failed: {str(e)}", "picks_synced": 0}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in draft sync: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/draft/{session_id}/status")
async def get_draft_status(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current draft session status"""
    
    session = db.query(DraftSession).filter(
        and_(
            DraftSession.id == session_id,
            DraftSession.user_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    return {
        "session_id": session.id,
        "current_pick": session.current_pick,
        "current_round": session.current_round,
        "user_pick_position": session.user_pick_position,
        "next_user_pick": session.get_next_pick_number(),
        "picks_until_user_turn": session.get_picks_until_user_turn(),
        "is_active": session.is_active,
        "is_live_synced": session.is_live_synced,
        "total_picks": session.total_picks,
        "total_rounds": session.total_rounds,
        "drafted_players_count": len(session.drafted_players or []),
        "user_roster_count": len(session.user_roster or []),
        "draft_complete": session.completed_at is not None,
        "last_activity": session.last_activity
    }


# Helper functions
async def sync_league_data(league_id: int):
    """Background task to sync league data from ESPN"""
    from ..models.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get the league
        league = db.query(ESPNLeague).filter(ESPNLeague.id == league_id).first()
        if not league:
            logger.error(f"League {league_id} not found for sync")
            return
        
        # Get draft results if not already marked as completed
        if not league.draft_completed:
            try:
                draft_results = await espn_service.get_draft_results(
                    league.espn_league_id,
                    league.season
                )
                
                if draft_results and draft_results.get('success'):
                    draft_data = draft_results.get('data', {})
                    picks = draft_data.get('picks', [])
                    total_rounds = draft_data.get('totalRounds', 16)
                    expected_picks = league.team_count * total_rounds
                    
                    # Update draft status if complete
                    if len(picks) >= expected_picks:
                        league.draft_completed = True
                        league.last_sync = datetime.utcnow()
                        db.commit()
                        logger.info(f"Updated league {league_id} draft status to completed")
                        
            except Exception as e:
                logger.warning(f"Could not sync draft status for league {league_id}: {e}")
        
        # Update last sync time
        league.last_sync = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.error(f"Error syncing league {league_id}: {e}")
        db.rollback()
    finally:
        db.close()


async def generate_draft_recommendations(session: DraftSession, db: Session) -> DraftRecommendation:
    """Generate AI-powered draft recommendations using the draft assistant service"""
    
    # Get league with relationship loaded
    league = db.query(ESPNLeague).filter(ESPNLeague.id == session.league_id).first()
    if not league:
        raise ValueError("League not found for session")
    
    try:
        # Use the draft assistant service to generate comprehensive recommendations
        recommendation_data = await draft_assistant.generate_recommendations(
            session=session,
            league=league,
            available_players=None  # Will use mock data for now
        )
        
        # Extract recommendation details
        recommendations = recommendation_data.get("recommendations", [])
        ai_analysis = recommendation_data.get("ai_analysis", {})
        
        # Format recommendations for storage
        formatted_recommendations = [
            {
                "player_id": rec.get("player_id"),
                "name": rec.get("name"),
                "position": rec.get("position"),
                "team": rec.get("team"),
                "projected_points": rec.get("projected_points"),
                "vor": rec.get("vor"),
                "score": rec.get("recommendation_score"),
                "tier": rec.get("tier"),
                "adp": rec.get("adp"),
                "reasoning": rec.get("reasoning")
            }
            for rec in recommendations[:10]  # Top 10 recommendations
        ]
        
        # Create database record
        recommendation = DraftRecommendation(
            session_id=session.id,
            pick_number=session.current_pick,
            round_number=session.current_round,
            recommended_players=formatted_recommendations,
            primary_recommendation=formatted_recommendations[0] if formatted_recommendations else {},
            strategy_reasoning=ai_analysis.get("overall_strategy", "Strategic draft recommendation"),
            confidence_score=ai_analysis.get("confidence", 0.85),
            recommendation_type="ai_assisted",
            available_player_count=len(recommendation_data.get("available_players", [])),
            user_roster_positions=session.user_roster or [],
            scoring_adjustments_applied={
                "scoring_type": league.scoring_type,
                "ppr_value": league.scoring_settings.get("53", {}).get("points", 0) if league.scoring_settings else 0
            },
            ai_insights=ai_analysis.get("key_insights", []),
            next_pick_strategy=ai_analysis.get("next_pick_strategy", "Continue building roster depth")
        )
        
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        
        return recommendation
        
    except Exception as e:
        logger.error(f"Error generating recommendations with draft assistant: {e}")
        
        # Fallback to basic recommendation
        fallback_rec = {
            "player_id": 9999,
            "name": "Best Available Player",
            "position": "FLEX",
            "team": "NFL",
            "score": 85.0,
            "reasoning": "Fallback recommendation - system error occurred"
        }
        
        recommendation = DraftRecommendation(
            session_id=session.id,
            pick_number=session.current_pick,
            round_number=session.current_round,
            recommended_players=[fallback_rec],
            primary_recommendation=fallback_rec,
            strategy_reasoning="System temporarily using simplified recommendations",
            confidence_score=0.5,
            recommendation_type="fallback",
            available_player_count=0,
            user_roster_positions=session.user_roster or [],
            scoring_adjustments_applied={}
        )
        
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        
        return recommendation


class ESPNCookieUpdate(BaseModel):
    espn_s2: str = Field(..., min_length=1, description="ESPN S2 cookie")
    swid: str = Field(..., min_length=1, description="ESPN SWID cookie")


@router.put("/leagues/{league_id}/update-cookies")
async def update_espn_cookies(
    league_id: int,
    cookie_data: ESPNCookieUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update ESPN authentication cookies for a league"""
    
    logger.info(f"Updating cookies for league {league_id}, user {current_user.id}")
    logger.info(f"ESPN S2 length: {len(cookie_data.espn_s2)}, SWID length: {len(cookie_data.swid)}")
    
    # Get the league and verify ownership
    league = db.query(ESPNLeague).filter(
        and_(
            ESPNLeague.id == league_id,
            ESPNLeague.user_id == current_user.id
        )
    ).first()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found or access denied")
    
    try:
        # Validate cookies with ESPN service
        async with espn_service.client as client:
            validation_result = await client.validate_espn_cookies(
                cookie_data.espn_s2, 
                cookie_data.swid
            )
        
        if not validation_result.get('valid', False):
            raise HTTPException(
                status_code=400, 
                detail="Invalid ESPN cookies. Please check your s2 and swid values."
            )
        
        # Update league with new cookies
        league.espn_s2 = cookie_data.espn_s2  # TODO: Encrypt these
        league.swid = cookie_data.swid        # TODO: Encrypt these
        league.updated_at = datetime.utcnow()
        league.sync_status = 'active'
        
        # Clear any auth error flags
        if hasattr(league, 'needs_auth_update'):
            league.needs_auth_update = False
        
        db.commit()
        
        logger.info(f"Updated ESPN cookies for league {league_id} by user {current_user.id}")
        
        return {
            "message": "ESPN cookies updated successfully",
            "league_id": league_id,
            "validation_status": "valid"
        }
        
    except ESPNServiceError as e:
        logger.error(f"ESPN service error updating cookies for league {league_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to validate ESPN cookies: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating cookies for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update ESPN cookies")