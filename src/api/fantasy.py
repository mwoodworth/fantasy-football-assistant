"""
Fantasy football core feature API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..models.database import get_db
from ..models.user import User
from ..models.fantasy import League, FantasyTeam
from ..utils.dependencies import get_current_active_user
from ..services.draft_assistant import DraftAssistant
from ..services.lineup_optimizer import LineupOptimizer
from ..services.waiver_analyzer import WaiverAnalyzer
from ..services.trade_analyzer import TradeAnalyzer

router = APIRouter(prefix="/fantasy", tags=["fantasy"])


# Request/Response models
class LineupOptimizationRequest(BaseModel):
    fantasy_team_id: int
    week: int
    locked_players: Optional[List[int]] = []
    excluded_players: Optional[List[int]] = []


class TradeEvaluationRequest(BaseModel):
    team1_id: int
    team1_sends: List[int]
    team1_receives: List[int]
    team2_id: int
    team2_sends: List[int]
    team2_receives: List[int]
    week: Optional[int] = None


class WaiverRecommendationRequest(BaseModel):
    fantasy_team_id: int
    week: int
    position: Optional[str] = None
    limit: int = 20


# Draft Assistant Endpoints
@router.get("/draft/{league_id}/recommendations")
async def get_draft_recommendations(
    league_id: int,
    fantasy_team_id: int = Query(...),
    pick_number: int = Query(...),
    round_number: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get draft recommendations for a specific pick"""
    
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Verify user has access to this team
    team = db.query(FantasyTeam).filter(
        FantasyTeam.id == fantasy_team_id,
        FantasyTeam.owner_id == current_user.id
    ).first()
    if not team:
        raise HTTPException(status_code=403, detail="Access denied to this team")
    
    draft_assistant = DraftAssistant(db, league)
    recommendations = draft_assistant.get_draft_recommendations(
        fantasy_team_id, pick_number, round_number
    )
    
    return {
        "league_id": league_id,
        "fantasy_team_id": fantasy_team_id,
        "pick_number": pick_number,
        "round_number": round_number,
        "recommendations": recommendations
    }


@router.get("/draft/{league_id}/board")
async def get_draft_board(
    league_id: int,
    top_n: int = Query(200, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get overall draft board rankings"""
    
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    draft_assistant = DraftAssistant(db, league)
    draft_board = draft_assistant.get_draft_board(top_n)
    
    return {
        "league_id": league_id,
        "draft_board": draft_board,
        "total_players": len(draft_board)
    }


@router.get("/draft/{league_id}/analysis/{fantasy_team_id}")
async def get_draft_analysis(
    league_id: int,
    fantasy_team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Analyze draft performance for a team"""
    
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Verify user has access to this team
    team = db.query(FantasyTeam).filter(
        FantasyTeam.id == fantasy_team_id,
        FantasyTeam.owner_id == current_user.id
    ).first()
    if not team:
        raise HTTPException(status_code=403, detail="Access denied to this team")
    
    draft_assistant = DraftAssistant(db, league)
    analysis = draft_assistant.analyze_draft_capital(fantasy_team_id)
    
    return analysis


# Lineup Optimizer Endpoints
@router.post("/lineup/optimize")
async def optimize_lineup(
    request: LineupOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Optimize lineup for maximum projected points"""
    
    # Verify user has access to this team
    team = db.query(FantasyTeam).filter(
        FantasyTeam.id == request.fantasy_team_id,
        FantasyTeam.owner_id == current_user.id
    ).first()
    if not team:
        raise HTTPException(status_code=403, detail="Access denied to this team")
    
    league = team.league
    optimizer = LineupOptimizer(db, league)
    
    result = optimizer.optimize_lineup(
        request.fantasy_team_id,
        request.week,
        request.locked_players,
        request.excluded_players
    )
    
    return result


@router.get("/lineup/start-sit/{fantasy_team_id}")
async def get_start_sit_recommendations(
    fantasy_team_id: int,
    week: int = Query(...),
    position: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get start/sit recommendations for close decisions"""
    
    # Verify user has access to this team
    team = db.query(FantasyTeam).filter(
        FantasyTeam.id == fantasy_team_id,
        FantasyTeam.owner_id == current_user.id
    ).first()
    if not team:
        raise HTTPException(status_code=403, detail="Access denied to this team")
    
    league = team.league
    optimizer = LineupOptimizer(db, league)
    
    recommendations = optimizer.get_start_sit_recommendations(
        fantasy_team_id, week, position
    )
    
    return {
        "fantasy_team_id": fantasy_team_id,
        "week": week,
        "position": position,
        "recommendations": recommendations
    }


# Waiver Wire Endpoints
@router.post("/waivers/recommendations")
async def get_waiver_recommendations(
    request: WaiverRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get waiver wire pickup recommendations"""
    
    # Verify user has access to this team
    team = db.query(FantasyTeam).filter(
        FantasyTeam.id == request.fantasy_team_id,
        FantasyTeam.owner_id == current_user.id
    ).first()
    if not team:
        raise HTTPException(status_code=403, detail="Access denied to this team")
    
    league = team.league
    waiver_analyzer = WaiverAnalyzer(db, league)
    
    recommendations = waiver_analyzer.get_waiver_recommendations(
        request.fantasy_team_id,
        request.week,
        request.position,
        request.limit
    )
    
    return {
        "fantasy_team_id": request.fantasy_team_id,
        "week": request.week,
        "position": request.position,
        "recommendations": recommendations
    }


@router.get("/waivers/{league_id}/trending")
async def get_trending_players(
    league_id: int,
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get players trending up in performance"""
    
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    waiver_analyzer = WaiverAnalyzer(db, league)
    trending = waiver_analyzer.get_trending_players(limit)
    
    return {
        "league_id": league_id,
        "trending_players": trending
    }


@router.get("/waivers/{league_id}/claims/{week}")
async def analyze_waiver_claims(
    league_id: int,
    week: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Analyze waiver claim competition for the week"""
    
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    waiver_analyzer = WaiverAnalyzer(db, league)
    analysis = waiver_analyzer.analyze_waiver_claims(week)
    
    return analysis


# Trade Analyzer Endpoints
@router.post("/trades/evaluate")
async def evaluate_trade(
    request: TradeEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Evaluate a proposed trade"""
    
    # Verify user has access to at least one of the teams
    team1 = db.query(FantasyTeam).filter(FantasyTeam.id == request.team1_id).first()
    team2 = db.query(FantasyTeam).filter(FantasyTeam.id == request.team2_id).first()
    
    if not team1 or not team2:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team1.owner_id != current_user.id and team2.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to these teams")
    
    league = team1.league
    trade_analyzer = TradeAnalyzer(db, league)
    
    evaluation = trade_analyzer.evaluate_trade(
        request.team1_id, request.team1_sends, request.team1_receives,
        request.team2_id, request.team2_sends, request.team2_receives,
        request.week
    )
    
    return evaluation


@router.get("/trades/{fantasy_team_id}/targets")
async def get_trade_targets(
    fantasy_team_id: int,
    position_needed: str = Query(...),
    max_players_to_send: int = Query(2, le=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get trade target suggestions for a team"""
    
    # Verify user has access to this team
    team = db.query(FantasyTeam).filter(
        FantasyTeam.id == fantasy_team_id,
        FantasyTeam.owner_id == current_user.id
    ).first()
    if not team:
        raise HTTPException(status_code=403, detail="Access denied to this team")
    
    league = team.league
    trade_analyzer = TradeAnalyzer(db, league)
    
    suggestions = trade_analyzer.suggest_trade_targets(
        fantasy_team_id, position_needed, max_players_to_send
    )
    
    return {
        "fantasy_team_id": fantasy_team_id,
        "position_needed": position_needed,
        "suggestions": suggestions
    }


# General Fantasy Endpoints
@router.get("/leagues/{league_id}/summary")
async def get_league_summary(
    league_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get league summary and current standings"""
    
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get all teams in league
    teams = db.query(FantasyTeam).filter(
        FantasyTeam.league_id == league_id
    ).order_by(FantasyTeam.wins.desc(), FantasyTeam.points_for.desc()).all()
    
    return {
        "league": league,
        "teams": teams,
        "current_week": league.current_week,
        "total_teams": len(teams)
    }