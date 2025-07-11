"""Yahoo Fantasy Draft API endpoints."""

import logging
import secrets
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from ..models import User, YahooLeague, YahooDraftSession, YahooDraftRecommendation, YahooDraftEvent
from ..models.database import get_db
from ..utils.dependencies import get_current_active_user
from ..services.yahoo_integration import YahooIntegrationService as YahooIntegration
from ..services.yahoo_draft_monitor import YahooDraftMonitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yahoo/draft", tags=["yahoo-draft"])

# Keep track of active draft monitors
active_monitors: Dict[int, YahooDraftMonitor] = {}

@router.post("/start")
async def start_draft_session(
    league_key: str,
    draft_position: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Start a new Yahoo draft session."""
    try:
        # Get league details
        league = db.query(YahooLeague).filter(
            YahooLeague.user_id == current_user.id,
            YahooLeague.league_key == league_key
        ).first()
        
        if not league:
            raise HTTPException(status_code=404, detail="League not found")
        
        # Check if draft has started
        if league.draft_status != "drafting":
            # Update draft status from Yahoo
            yahoo_integration = YahooIntegration()
            client = yahoo_integration.get_client(current_user.id, db)
            league_data = client.get_league(league_key)
            
            # Update local league draft status
            draft_status = league_data.get("draft_status", "predraft")
            league.draft_status = draft_status
            db.commit()
            
            if draft_status != "drafting":
                raise HTTPException(
                    status_code=400, 
                    detail=f"Draft is not active. Current status: {draft_status}"
                )
        
        # Check for existing active session
        existing = db.query(YahooDraftSession).filter(
            YahooDraftSession.league_id == league.id,
            YahooDraftSession.draft_status == "drafting"
        ).first()
        
        if existing:
            return {
                "session_id": existing.id,
                "session_token": existing.session_token,
                "message": "Resumed existing draft session"
            }
        
        # Create new draft session
        session = YahooDraftSession(
            user_id=current_user.id,
            league_id=league.id,
            session_token=secrets.token_urlsafe(32),
            draft_status="drafting",
            user_draft_position=draft_position,
            user_team_key=league.user_team_key,
            draft_order=list(range(1, league.num_teams + 1))  # Will be updated from Yahoo
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Start draft monitor
        monitor = YahooDraftMonitor(
            session_id=session.id,
            league_key=league_key,
            user_id=current_user.id,
            db=db
        )
        active_monitors[session.id] = monitor
        monitor.start()
        
        return {
            "session_id": session.id,
            "session_token": session.session_token,
            "draft_position": draft_position,
            "league_name": league.name,
            "num_teams": league.num_teams,
            "message": "Draft session started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start draft session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start draft session")

@router.get("/session/{session_id}")
async def get_draft_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get draft session details."""
    session = db.query(YahooDraftSession).filter(
        YahooDraftSession.id == session_id,
        YahooDraftSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    # Get league details
    league = session.league
    
    # Calculate picks until user's turn
    picks_until_turn = session.get_picks_until_user_turn(league.num_teams)
    
    return {
        "session_id": session.id,
        "status": session.draft_status,
        "current_pick": session.current_pick,
        "current_round": session.current_round,
        "user_draft_position": session.user_draft_position,
        "picks_until_turn": picks_until_turn,
        "drafted_players": session.drafted_players or [],
        "live_sync_enabled": session.live_sync_enabled,
        "last_sync": session.last_sync.isoformat() if session.last_sync else None,
        "league": {
            "key": league.league_key,
            "name": league.name,
            "num_teams": league.num_teams
        }
    }

@router.get("/{session_id}/recommendations")
async def get_draft_recommendations(
    session_id: int,
    force_refresh: bool = Query(False, description="Force regenerate recommendations"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get AI-powered draft recommendations."""
    session = db.query(YahooDraftSession).filter(
        YahooDraftSession.id == session_id,
        YahooDraftSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    # Check for existing recommendations for current pick
    if not force_refresh:
        existing = db.query(YahooDraftRecommendation).filter(
            YahooDraftRecommendation.draft_session_id == session_id,
            YahooDraftRecommendation.current_pick == session.current_pick
        ).order_by(YahooDraftRecommendation.created_at.desc()).first()
        
        if existing:
            return {
                "recommendations": existing.recommended_players,
                "primary": existing.primary_recommendation,
                "positional_needs": existing.positional_needs,
                "value_picks": existing.value_picks,
                "sleepers": existing.sleepers,
                "avoid_players": existing.avoid_players,
                "ai_insights": existing.ai_insights,
                "confidence_score": existing.confidence_score,
                "generated_at": existing.created_at.isoformat()
            }
    
    # Generate new recommendations
    try:
        # Get available players from Yahoo
        yahoo_integration = YahooIntegration()
        client = yahoo_integration.get_client(current_user.id, db)
        
        # Get draft results to see who's been drafted
        draft_results = client.get_league_draft_results(session.league.league_key)
        drafted_player_keys = {pick.get("player_key") for pick in draft_results}
        
        # Get top available players
        all_players = client.get_league_players(session.league.league_key, status="A")
        available_players = [p for p in all_players if p.get("player_key") not in drafted_player_keys]
        
        # Build current roster from drafted players
        user_picks = [p for p in session.drafted_players if p.get("team_key") == session.user_team_key]
        
        # Generate recommendations using available data
        recommendations = _generate_yahoo_draft_recommendations(
            available_players=available_players[:100],  # Top 100 available
            current_roster=user_picks,
            league_settings=session.league.settings or {},
            scoring_settings=session.league.scoring_settings or {},
            draft_position=session.user_draft_position,
            current_pick=session.current_pick,
            current_round=session.current_round,
            num_teams=session.league.num_teams
        )
        
        # Save recommendations
        rec = YahooDraftRecommendation(
            draft_session_id=session_id,
            recommended_players=recommendations.get("recommended_players", []),
            primary_recommendation=recommendations.get("primary_recommendation"),
            positional_needs=recommendations.get("positional_needs", {}),
            value_picks=recommendations.get("value_picks", []),
            sleepers=recommendations.get("sleepers", []),
            avoid_players=recommendations.get("avoid_players", []),
            confidence_score=recommendations.get("confidence_score", 0.8),
            ai_insights=recommendations.get("ai_insights", ""),
            current_pick=session.current_pick,
            current_round=session.current_round,
            team_roster=user_picks,
            available_players=available_players[:50]  # Store top 50 for context
        )
        
        db.add(rec)
        db.commit()
        
        return {
            "recommendations": rec.recommended_players,
            "primary": rec.primary_recommendation,
            "positional_needs": rec.positional_needs,
            "value_picks": rec.value_picks,
            "sleepers": rec.sleepers,
            "avoid_players": rec.avoid_players,
            "ai_insights": rec.ai_insights,
            "confidence_score": rec.confidence_score,
            "generated_at": rec.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")

@router.get("/{session_id}/live-status")
async def get_live_draft_status(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get live draft status with recent picks."""
    session = db.query(YahooDraftSession).filter(
        YahooDraftSession.id == session_id,
        YahooDraftSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    # Get recent draft events
    recent_events = db.query(YahooDraftEvent).filter(
        YahooDraftEvent.draft_session_id == session_id,
        YahooDraftEvent.event_type == "pick_made"
    ).order_by(YahooDraftEvent.created_at.desc()).limit(10).all()
    
    # Check if it's user's turn
    league = session.league
    picks_until_turn = session.get_picks_until_user_turn(league.num_teams)
    is_user_turn = picks_until_turn == 0
    
    return {
        "status": session.draft_status,
        "current_pick": session.current_pick,
        "current_round": session.current_round,
        "is_user_turn": is_user_turn,
        "picks_until_turn": picks_until_turn,
        "recent_picks": [
            {
                "pick_number": event.pick_number,
                "round": event.round_number,
                "team_key": event.team_key,
                "player_name": event.player_name,
                "player_key": event.player_key,
                "timestamp": event.created_at.isoformat()
            }
            for event in recent_events
        ],
        "last_sync": session.last_sync.isoformat() if session.last_sync else None,
        "sync_enabled": session.live_sync_enabled
    }

@router.post("/{session_id}/toggle-sync")
async def toggle_live_sync(
    session_id: int,
    enable: bool,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Enable or disable live draft sync."""
    session = db.query(YahooDraftSession).filter(
        YahooDraftSession.id == session_id,
        YahooDraftSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    session.live_sync_enabled = enable
    db.commit()
    
    # Start or stop monitor
    if enable and session_id not in active_monitors:
        monitor = YahooDraftMonitor(
            session_id=session.id,
            league_key=session.league.league_key,
            user_id=current_user.id,
            db=db
        )
        active_monitors[session_id] = monitor
        monitor.start()
    elif not enable and session_id in active_monitors:
        active_monitors[session_id].stop()
        del active_monitors[session_id]
    
    return {
        "sync_enabled": enable,
        "message": f"Live sync {'enabled' if enable else 'disabled'}"
    }

@router.post("/{session_id}/sync")
async def manual_sync_draft(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Manually sync draft status with Yahoo."""
    session = db.query(YahooDraftSession).filter(
        YahooDraftSession.id == session_id,
        YahooDraftSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    try:
        # Get Yahoo client
        yahoo_integration = YahooIntegration()
        client = yahoo_integration.get_client(current_user.id, db)
        
        # Get current draft results
        draft_results = client.get_league_draft_results(session.league.league_key)
        
        # Update session with latest draft state
        if draft_results:
            latest_pick = len(draft_results)
            session.current_pick = latest_pick + 1
            session.current_round = ((latest_pick - 1) // session.league.num_teams) + 1
            
            # Update drafted players
            session.drafted_players = [
                {
                    "pick": pick.get("pick"),
                    "round": pick.get("round"),
                    "team_key": pick.get("team_key"),
                    "player_key": pick.get("player_key"),
                    "player_name": pick.get("player_name", {}).get("full", "Unknown")
                }
                for pick in draft_results
            ]
        
        session.last_sync = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "current_pick": session.current_pick,
            "current_round": session.current_round,
            "total_picks": len(draft_results),
            "message": "Draft synced successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to sync draft: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync draft")

@router.get("/{session_id}/status")
async def get_draft_status(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive draft status."""
    session = db.query(YahooDraftSession).filter(
        YahooDraftSession.id == session_id,
        YahooDraftSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    # Get draft events count
    events_count = db.query(YahooDraftEvent).filter(
        YahooDraftEvent.draft_session_id == session_id
    ).count()
    
    # Get recommendations count
    recs_count = db.query(YahooDraftRecommendation).filter(
        YahooDraftRecommendation.draft_session_id == session_id
    ).count()
    
    return {
        "session": {
            "id": session.id,
            "status": session.draft_status,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        },
        "draft_state": {
            "current_pick": session.current_pick,
            "current_round": session.current_round,
            "total_picks": len(session.drafted_players) if session.drafted_players else 0,
            "user_picks": len([p for p in (session.drafted_players or []) if p.get("team_key") == session.user_team_key])
        },
        "sync_status": {
            "enabled": session.live_sync_enabled,
            "last_sync": session.last_sync.isoformat() if session.last_sync else None,
            "monitor_active": session_id in active_monitors
        },
        "statistics": {
            "events_tracked": events_count,
            "recommendations_generated": recs_count
        }
    }

@router.delete("/{session_id}")
async def end_draft_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """End a draft session."""
    session = db.query(YahooDraftSession).filter(
        YahooDraftSession.id == session_id,
        YahooDraftSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Draft session not found")
    
    # Stop monitor if active
    if session_id in active_monitors:
        active_monitors[session_id].stop()
        del active_monitors[session_id]
    
    # Update session status
    session.draft_status = "completed"
    session.completed_at = datetime.utcnow()
    session.live_sync_enabled = False
    db.commit()
    
    return {
        "message": "Draft session ended",
        "session_id": session_id,
        "total_picks": len(session.drafted_players) if session.drafted_players else 0
    }


def _generate_yahoo_draft_recommendations(
    available_players: List[Dict[str, Any]],
    current_roster: List[Dict[str, Any]],
    league_settings: Dict[str, Any],
    scoring_settings: Dict[str, Any],
    draft_position: int,
    current_pick: int,
    current_round: int,
    num_teams: int
) -> Dict[str, Any]:
    """Generate draft recommendations for Yahoo leagues."""
    
    # Analyze current roster composition
    roster_positions = {}
    for pick in current_roster:
        # Extract position from player data if available
        pos = pick.get("position", "Unknown")
        roster_positions[pos] = roster_positions.get(pos, 0) + 1
    
    # Standard roster requirements
    position_limits = {
        "QB": 2,
        "RB": 5,
        "WR": 5,
        "TE": 2,
        "K": 1,
        "DEF": 1
    }
    
    # Calculate positional needs
    positional_needs = {}
    for pos, limit in position_limits.items():
        current = roster_positions.get(pos, 0)
        need = max(0, limit - current) / limit
        positional_needs[pos] = need
    
    # Sort players by projected points
    sorted_players = sorted(
        available_players,
        key=lambda p: p.get("projected_season_points", 0) or 0,
        reverse=True
    )
    
    # Get top players by position
    position_players = {"QB": [], "RB": [], "WR": [], "TE": [], "K": [], "DEF": []}
    for player in sorted_players:
        positions = player.get("eligible_positions", [])
        if isinstance(positions, list):
            for pos in positions:
                if pos in position_players and len(position_players[pos]) < 10:
                    position_players[pos].append(player)
        elif isinstance(positions, str):
            pos = positions
            if pos in position_players and len(position_players[pos]) < 10:
                position_players[pos].append(player)
    
    # Identify value picks (players available later than expected)
    value_picks = []
    for player in sorted_players[:20]:
        # Simple value calculation based on ranking vs current pick
        player_rank = sorted_players.index(player) + 1
        if player_rank < current_pick * 0.8:  # Available 20% later than expected
            value_picks.append(player)
    
    # Identify sleepers (later round targets)
    sleepers = []
    if current_round > 8:
        for player in sorted_players[50:100]:
            if player.get("percent_owned", 100) < 50:
                sleepers.append(player)
    
    # Primary recommendation based on needs and value
    primary_rec = None
    max_score = 0
    
    for player in sorted_players[:10]:
        # Calculate recommendation score
        proj_points = player.get("projected_season_points", 0) or 0
        positions = player.get("eligible_positions", [])
        if isinstance(positions, str):
            positions = [positions]
        
        # Get highest need position for this player
        max_need = 0
        for pos in positions:
            if pos in positional_needs:
                max_need = max(max_need, positional_needs[pos])
        
        # Score = projected points * positional need factor
        score = proj_points * (1 + max_need)
        
        if score > max_score:
            max_score = score
            primary_rec = player
    
    # Generate AI insights
    ai_insights = f"Based on your roster needs and available players, "
    if primary_rec:
        ai_insights += f"I recommend {primary_rec.get('name_full', 'Unknown')} "
        positions = primary_rec.get("eligible_positions", [])
        if positions:
            ai_insights += f"({positions[0] if isinstance(positions, list) else positions}). "
    
    # Add context about draft position
    if current_round <= 3:
        ai_insights += "Focus on elite talent at RB/WR positions. "
    elif current_round <= 6:
        ai_insights += "Balance your roster with a mix of RB/WR and consider an elite TE. "
    elif current_round <= 10:
        ai_insights += "Target high-upside players and handcuffs for your RBs. "
    else:
        ai_insights += "Look for sleepers, backup RBs with standalone value, and fill out your bench. "
    
    return {
        "recommended_players": sorted_players[:10],
        "primary_recommendation": primary_rec,
        "positional_needs": positional_needs,
        "value_picks": value_picks[:5],
        "sleepers": sleepers[:5],
        "avoid_players": [],  # Could add injury-prone players here
        "confidence_score": 0.75,  # Static for now
        "ai_insights": ai_insights
    }