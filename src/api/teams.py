"""
Teams API endpoints for managing fantasy teams across platforms
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..models.database import get_db
from ..models.user import User
from ..models.fantasy import League, FantasyTeam
from ..models.espn_league import ESPNLeague
from ..utils.dependencies import get_current_active_user
from ..services.espn_bridge import get_espn_bridge_service

router = APIRouter(prefix="/teams", tags=["teams"])


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


@router.get("/", response_model=List[TeamResponse])
async def get_user_teams(
    include_espn: bool = True,
    include_manual: bool = True,
    season: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all teams for the current user across platforms"""
    
    teams = []
    
    # Get ESPN teams if requested
    if include_espn:
        espn_bridge = get_espn_bridge_service(db)
        espn_teams = espn_bridge.get_user_teams_data(current_user.id)
        
        for team in espn_teams:
            if season is None or team.get('season') == season:
                teams.append(TeamResponse(
                    id=team['id'],
                    name=team['name'],
                    league=team['league'],
                    platform=team['platform'],
                    season=team.get('season'),
                    record=team['record'],
                    points=team['points'],
                    rank=team['rank'],
                    playoffs=team['playoffs'],
                    active=team['active'],
                    espn_league_id=team.get('espn_league_id'),
                    draft_completed=team.get('draft_completed'),
                    scoring_type=team.get('scoring_type')
                ))
    
    # Get manual/generic teams if requested
    if include_manual:
        manual_teams = db.query(FantasyTeam).join(League).filter(
            FantasyTeam.owner_id == current_user.id,
            League.platform != "ESPN"  # Exclude ESPN teams handled above
        ).all()
        
        for team in manual_teams:
            if season is None or team.league.current_season == season:
                teams.append(TeamResponse(
                    id=f"manual_{team.id}",
                    name=team.name,
                    league=team.league.name,
                    platform=team.league.platform or "Manual",
                    season=team.league.current_season,
                    record=f"{team.wins}-{team.losses}" + (f"-{team.ties}" if team.ties > 0 else ""),
                    points=team.points_for,
                    rank=str(team.playoff_seed) if team.playoff_seed else "N/A",
                    playoffs=team.made_playoffs,
                    active=True,
                    espn_league_id=None,
                    draft_completed=None,
                    scoring_type=team.league.scoring_type
                ))
    
    return teams


@router.get("/{team_id}", response_model=TeamDetail)
async def get_team_detail(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information for a specific team"""
    
    if team_id.startswith("espn_"):
        # Handle ESPN team
        espn_league_id = int(team_id.replace("espn_", ""))
        espn_league = db.query(ESPNLeague).filter(
            ESPNLeague.id == espn_league_id,
            ESPNLeague.user_id == current_user.id
        ).first()
        
        if not espn_league:
            raise HTTPException(status_code=404, detail="ESPN team not found")
        
        return TeamDetail(
            id=team_id,
            name=espn_league.user_team_name or f"Team in {espn_league.league_name}",
            league=espn_league.league_name,
            platform="ESPN",
            roster=[],  # TODO: Get actual roster from ESPN
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
    
    # TODO: Implement actual ESPN sync
    # For now, just update the last sync timestamp
    from datetime import datetime
    espn_league.last_sync = datetime.utcnow()
    db.commit()
    
    return {"message": "Team data synced successfully", "last_sync": espn_league.last_sync}


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