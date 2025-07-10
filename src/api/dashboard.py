"""
Dashboard API endpoints for live data, scores, and analytics
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import logging
from pydantic import BaseModel

from ..models.database import get_db
from ..models.user import User
from ..models.espn_league import ESPNLeague
from ..utils.dependencies import get_current_active_user
from ..services.espn_bridge import get_espn_bridge_service
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# Response models
class LiveScore(BaseModel):
    gameId: str
    homeTeam: str
    awayTeam: str
    homeScore: int
    awayScore: int
    quarter: str
    timeRemaining: str
    status: str
    isComplete: bool
    gameTime: str


class Player(BaseModel):
    id: int
    name: str
    position: str
    team: str


class TopPerformer(BaseModel):
    player: Player
    points: float
    projectedPoints: float
    percentageOfProjected: float
    trend: str  # 'up', 'down', or 'stable'


class TrendingPlayer(BaseModel):
    player: Player
    trendDirection: str  # 'up' or 'down'
    trendPercentage: float
    reason: str
    ownershipChange: float
    addDropRatio: float


class WaiverTarget(BaseModel):
    player: Player
    ownershipPercentage: float
    projectedPoints: float
    upcomingMatchup: str
    matchupDifficulty: str  # 'easy', 'medium', or 'hard'
    recommendation: str
    priority: str  # 'high', 'medium', or 'low'


class DashboardOverview(BaseModel):
    total_teams: int
    active_leagues: int
    weekly_points: float
    season_rank: int
    next_matchup: Optional[str]
    waiver_claims: int


# Mock data generators
def generate_live_scores() -> List[LiveScore]:
    """Generate mock live scores"""
    games = [
        {"home": "BUF", "away": "MIA", "home_score": 21, "away_score": 14},
        {"home": "KC", "away": "LAC", "home_score": 28, "away_score": 17},
        {"home": "SF", "away": "SEA", "home_score": 14, "away_score": 10},
        {"home": "DAL", "away": "NYG", "home_score": 24, "away_score": 20},
        {"home": "GB", "away": "CHI", "home_score": 17, "away_score": 13},
    ]
    
    live_scores = []
    for i, game in enumerate(games):
        live_scores.append(LiveScore(
            gameId=f"game_{i+1}",
            homeTeam=game["home"],
            awayTeam=game["away"],
            homeScore=game["home_score"],
            awayScore=game["away_score"],
            quarter="Q3" if i % 2 == 0 else "Q2",
            timeRemaining="8:42" if i % 2 == 0 else "12:15",
            status="In Progress",
            isComplete=False,
            gameTime="1:00 PM ET"
        ))
    
    return live_scores


def generate_top_performers() -> List[TopPerformer]:
    """Generate mock top performers"""
    performers = [
        {"name": "Josh Allen", "position": "QB", "team": "BUF", "points": 28.4, "projected": 22.1},
        {"name": "Christian McCaffrey", "position": "RB", "team": "SF", "points": 24.7, "projected": 18.9},
        {"name": "Tyreek Hill", "position": "WR", "team": "MIA", "points": 22.3, "projected": 16.4},
        {"name": "Travis Kelce", "position": "TE", "team": "KC", "points": 19.8, "projected": 14.2},
        {"name": "Lamar Jackson", "position": "QB", "team": "BAL", "points": 26.1, "projected": 21.7},
    ]
    
    top_performers = []
    trends = ['up', 'down', 'stable']
    
    for i, perf in enumerate(performers):
        percentage = (perf["points"] / perf["projected"]) * 100
        top_performers.append(TopPerformer(
            player=Player(
                id=i+1,
                name=perf["name"],
                position=perf["position"],
                team=perf["team"]
            ),
            points=perf["points"],
            projectedPoints=perf["projected"],
            percentageOfProjected=percentage,
            trend=random.choice(trends)
        ))
    
    return top_performers


def generate_trending_players() -> List[TrendingPlayer]:
    """Generate mock trending players"""
    trending = [
        {
            "name": "Jerome Ford", "position": "RB", "team": "CLE", 
            "trend": 45.2, "reason": "Injury to starter", 
            "ownership_change": 15.3, "add_drop": 8.5
        },
        {
            "name": "Gus Edwards", "position": "RB", "team": "BAL", 
            "trend": 38.7, "reason": "Strong performance", 
            "ownership_change": 12.1, "add_drop": 6.2
        },
        {
            "name": "Rashid Shaheed", "position": "WR", "team": "NO", 
            "trend": 33.1, "reason": "Target increase", 
            "ownership_change": 10.8, "add_drop": 5.1
        },
        {
            "name": "Tyler Boyd", "position": "WR", "team": "CIN", 
            "trend": 29.4, "reason": "Favorable matchup", 
            "ownership_change": 8.9, "add_drop": 4.3
        },
    ]
    
    trending_players = []
    for i, player in enumerate(trending):
        trending_players.append(TrendingPlayer(
            player=Player(
                id=i+100,
                name=player["name"],
                position=player["position"],
                team=player["team"]
            ),
            trendDirection="up" if player["trend"] > 30 else "down",
            trendPercentage=player["trend"],
            reason=player["reason"],
            ownershipChange=player["ownership_change"],
            addDropRatio=player["add_drop"]
        ))
    
    return trending_players


def generate_waiver_targets() -> List[WaiverTarget]:
    """Generate mock waiver targets"""
    targets = [
        {
            "name": "Rico Dowdle", "position": "RB", "team": "DAL", 
            "ownership": 23.4, "projected": 12.8, "matchup": "vs NYG",
            "difficulty": "easy", "priority": "high",
            "recommendation": "Strong add - lead back role with good matchup"
        },
        {
            "name": "Rome Odunze", "position": "WR", "team": "CHI", 
            "ownership": 31.7, "projected": 11.2, "matchup": "@ GB",
            "difficulty": "hard", "priority": "medium",
            "recommendation": "Rookie with upside, tough matchup this week"
        },
        {
            "name": "Demarcus Robinson", "position": "WR", "team": "LAR", 
            "ownership": 18.9, "projected": 10.7, "matchup": "vs ARI",
            "difficulty": "medium", "priority": "low",
            "recommendation": "Desperation play only, low target share"
        },
        {
            "name": "Hunter Henry", "position": "TE", "team": "NE", 
            "ownership": 42.1, "projected": 9.4, "matchup": "@ MIA",
            "difficulty": "hard", "priority": "medium",
            "recommendation": "TE1 upside if you need help at the position"
        },
    ]
    
    waiver_targets = []
    for i, target in enumerate(targets):
        waiver_targets.append(WaiverTarget(
            player=Player(
                id=i+200,
                name=target["name"],
                position=target["position"],
                team=target["team"]
            ),
            ownershipPercentage=target["ownership"],
            projectedPoints=target["projected"],
            upcomingMatchup=target["matchup"],
            matchupDifficulty=target["difficulty"],
            recommendation=target["recommendation"],
            priority=target["priority"]
        ))
    
    return waiver_targets


# API endpoints
@router.get("/")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dashboard overview data from ESPN leagues"""
    
    # Get ESPN bridge service
    espn_bridge = get_espn_bridge_service(db)
    
    # Get user's ESPN leagues for stats
    espn_leagues = db.query(ESPNLeague).filter(
        ESPNLeague.user_id == current_user.id,
        ESPNLeague.is_archived == False
    ).all()
    
    if espn_leagues:
        # Use actual ESPN data
        dashboard_data = await espn_bridge.get_user_dashboard_data(current_user.id)
        
        # Convert team rank string to integer, handling various formats
        team_rank_str = dashboard_data.teamRank
        if team_rank_str == "--" or not team_rank_str:
            team_rank_value = None
        else:
            # Remove ordinal suffixes and convert to int
            team_rank_clean = team_rank_str.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
            team_rank_value = int(team_rank_clean) if team_rank_clean.isdigit() else None
        
        # Return the data in the format expected by the frontend
        return {
            "teamRank": dashboard_data.teamRank,
            "leagueSize": dashboard_data.leagueSize,
            "rankTrend": dashboard_data.rankTrend,
            "weeklyPoints": dashboard_data.weeklyPoints,
            "pointsProjected": dashboard_data.pointsProjected,
            "pointsTrend": dashboard_data.pointsTrend,
            "activePlayers": dashboard_data.activePlayers,
            "benchPlayers": dashboard_data.benchPlayers,
            "injuryAlerts": dashboard_data.injuryAlerts,
            "recentActivity": [
                {
                    "type": activity.type,
                    "title": activity.title,
                    "description": activity.description,
                    "timestamp": activity.timestamp,
                    "priority": activity.priority,
                    "actionUrl": activity.actionUrl
                }
                for activity in dashboard_data.recentActivity
            ],
            "injuries": []  # TODO: Implement injury data
        }
    else:
        # Fallback for users without ESPN leagues
        return {
            "teamRank": "--",
            "leagueSize": 0,
            "rankTrend": "stable",
            "weeklyPoints": "0",
            "pointsProjected": 0.0,
            "pointsTrend": "stable",
            "activePlayers": "0",
            "benchPlayers": 0,
            "injuryAlerts": 0,
            "recentActivity": [
                {
                    "type": "recommendation",
                    "title": "Connect ESPN League",
                    "description": "Connect your ESPN fantasy league to get personalized insights",
                    "timestamp": "Now",
                    "priority": "high",
                    "actionUrl": "/espn/leagues"
                }
            ],
            "injuries": []
        }


@router.get("/live-scores", response_model=List[LiveScore])
async def get_live_scores(
    current_user: User = Depends(get_current_active_user)
):
    """Get live game scores"""
    return generate_live_scores()


@router.get("/top-performers", response_model=List[TopPerformer])
async def get_top_performers(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get top performing players this week"""
    # Get user's ESPN leagues
    espn_leagues = db.query(ESPNLeague).filter(
        ESPNLeague.user_id == current_user.id,
        ESPNLeague.is_active == True,
        ESPNLeague.is_archived == False
    ).all()
    
    if not espn_leagues:
        # Return empty list if no leagues
        return []
    
    # For pre-season, return empty list (no games played yet)
    # TODO: Once season starts, fetch actual top performers from ESPN
    # This would involve:
    # 1. Getting current week number
    # 2. Fetching player stats for the week
    # 3. Sorting by points scored
    # 4. Returning top N performers
    
    # For now, return empty list for pre-season
    return []


@router.get("/trending-players", response_model=List[TrendingPlayer])
async def get_trending_players(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get trending players (pickup percentage increase)"""
    # Get user's ESPN leagues
    espn_leagues = db.query(ESPNLeague).filter(
        ESPNLeague.user_id == current_user.id,
        ESPNLeague.is_active == True,
        ESPNLeague.is_archived == False
    ).all()
    
    if not espn_leagues:
        # Return empty list if no leagues
        return []
    
    try:
        # Get the primary league (first active league)
        primary_league = espn_leagues[0]
        
        # Fetch trending players from ESPN
        from ..services.espn_integration import espn_service
        trending_data = await espn_service.get_trending_players(
            trend_type="add",
            hours=24,
            limit=limit,
            league_id=primary_league.espn_league_id
        )
        
        # Convert ESPN data to our format
        trending_players = []
        if trending_data and 'players' in trending_data:
            for i, player in enumerate(trending_data['players'][:limit]):
                trending_players.append(TrendingPlayer(
                    player=Player(
                        id=player.get('id', i),
                        name=player.get('fullName', 'Unknown'),
                        position=player.get('defaultPositionId', 'FLEX'),
                        team=player.get('proTeamId', 'FA')
                    ),
                    trendDirection="up",
                    trendPercentage=player.get('ownership', {}).get('percentChange', 0.0),
                    reason=f"Added by {player.get('ownership', {}).get('percentOwned', 0):.1f}% of leagues",
                    ownershipChange=player.get('ownership', {}).get('percentChange', 0.0),
                    addDropRatio=player.get('ownership', {}).get('auctionValueAverage', 0.0)
                ))
        
        return trending_players
        
    except Exception as e:
        logger.error(f"Error fetching trending players: {e}")
        # Return empty list on error
        return []


@router.get("/waiver-targets", response_model=List[WaiverTarget])
async def get_waiver_targets(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    position: Optional[str] = None,
    limit: int = 10
):
    """Get recommended waiver wire targets"""
    # Get user's ESPN leagues
    espn_leagues = db.query(ESPNLeague).filter(
        ESPNLeague.user_id == current_user.id,
        ESPNLeague.is_active == True,
        ESPNLeague.is_archived == False
    ).all()
    
    if not espn_leagues:
        # Return empty list if no leagues
        return []
    
    try:
        # Get the primary league (first active league)
        primary_league = espn_leagues[0]
        
        # Fetch free agents from ESPN
        from ..services.espn_integration import espn_service
        free_agents = await espn_service.get_free_agents(
            league_id=primary_league.espn_league_id,
            season=primary_league.season,
            position=position,
            limit=limit * 2,  # Get more to filter
            espn_s2=primary_league.espn_s2,
            swid=primary_league.swid
        )
        
        # Convert ESPN data to our format
        waiver_targets = []
        if free_agents and 'players' in free_agents:
            for i, player in enumerate(free_agents['players'][:limit]):
                player_info = player.get('player', {})
                
                # Calculate matchup difficulty based on opponent defense ranking
                # For now, use a simple calculation
                ownership_pct = player_info.get('ownership', {}).get('percentOwned', 0)
                if ownership_pct < 20:
                    difficulty = "easy"
                    priority = "low"
                elif ownership_pct < 40:
                    difficulty = "medium"
                    priority = "medium"
                else:
                    difficulty = "hard"
                    priority = "high"
                
                waiver_targets.append(WaiverTarget(
                    player=Player(
                        id=player_info.get('id', i),
                        name=player_info.get('fullName', 'Unknown'),
                        position=player_info.get('defaultPositionId', 'FLEX'),
                        team=player_info.get('proTeamId', 'FA')
                    ),
                    ownershipPercentage=ownership_pct,
                    projectedPoints=player_info.get('stats', [{}])[0].get('appliedTotal', 0.0) if player_info.get('stats') else 0.0,
                    upcomingMatchup=f"vs {player_info.get('proTeamId', 'TBD')}",
                    matchupDifficulty=difficulty,
                    recommendation=f"{'High' if priority == 'high' else 'Medium' if priority == 'medium' else 'Low'} priority add",
                    priority=priority
                ))
        
        # Sort by projected points descending
        waiver_targets.sort(key=lambda x: x.projectedPoints, reverse=True)
        
        return waiver_targets[:limit]
        
    except Exception as e:
        logger.error(f"Error fetching waiver targets: {e}")
        # Return empty list on error
        return []


@router.get("/injury-report")
async def get_injury_report(
    current_user: User = Depends(get_current_active_user)
):
    """Get injury report for fantasy-relevant players"""
    # Mock injury data
    injuries = [
        {
            "player_name": "Christian McCaffrey",
            "position": "RB",
            "team": "SF",
            "injury": "Achilles",
            "status": "Out",
            "expected_return": "Week 15",
            "impact": "high"
        },
        {
            "player_name": "Ja'Marr Chase",
            "position": "WR", 
            "team": "CIN",
            "injury": "Hip",
            "status": "Questionable",
            "expected_return": "This week",
            "impact": "medium"
        },
        {
            "player_name": "Nick Chubb",
            "position": "RB",
            "team": "CLE", 
            "injury": "Knee",
            "status": "Doubtful",
            "expected_return": "Week 16",
            "impact": "high"
        }
    ]
    
    return {"injuries": injuries}