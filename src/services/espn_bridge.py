"""
ESPN Bridge Service

Connects ESPN league data with existing fantasy football features.
Provides a unified interface for all fantasy data regardless of platform.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.espn_league import ESPNLeague, DraftSession
from ..models.fantasy import League, FantasyTeam
from ..models.user import User
# Define data classes since we can't import from frontend service
from dataclasses import dataclass
from typing import List

@dataclass
class DashboardData:
    teamRank: str
    leagueSize: int
    rankTrend: str
    weeklyPoints: str
    pointsProjected: float
    pointsTrend: str
    activePlayers: str
    benchPlayers: int
    injuryAlerts: int
    recentActivity: List['Activity']
    injuries: List['InjuryAlert']

@dataclass 
class Activity:
    type: str
    title: str
    description: str
    timestamp: str
    priority: str = 'medium'
    actionUrl: str = None

@dataclass
class InjuryAlert:
    pass  # Placeholder for now

logger = logging.getLogger(__name__)


class ESPNBridgeService:
    """Service to bridge ESPN data with existing fantasy features"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_dashboard_data(self, user_id: int) -> DashboardData:
        """Generate dashboard data from user's ESPN leagues"""
        
        # Get user's active ESPN leagues
        espn_leagues = self.db.query(ESPNLeague).filter(
            ESPNLeague.user_id == user_id,
            ESPNLeague.is_active == True,
            ESPNLeague.is_archived == False
        ).all()
        
        if not espn_leagues:
            return self._get_fallback_dashboard_data()
        
        # Aggregate data from all ESPN leagues
        primary_league = espn_leagues[0]  # Use first league as primary
        
        dashboard_data = DashboardData(
            teamRank=self._calculate_team_rank(primary_league),
            leagueSize=primary_league.team_count,
            rankTrend='stable',  # TODO: Calculate actual trend
            weeklyPoints=self._get_weekly_points(primary_league),
            pointsProjected=0.0,  # TODO: Calculate projections
            pointsTrend='stable',
            activePlayers=str(self._count_active_players(primary_league)),
            benchPlayers=self._count_bench_players(primary_league),
            injuryAlerts=0,  # TODO: Calculate actual injuries
            recentActivity=self._generate_recent_activity(espn_leagues),
            injuries=[]  # TODO: Get actual injury data
        )
        
        return dashboard_data
    
    def get_user_teams_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Get formatted team data for Teams page from ESPN leagues"""
        
        espn_leagues = self.db.query(ESPNLeague).filter(
            ESPNLeague.user_id == user_id,
            ESPNLeague.is_archived == False
        ).all()
        
        teams_data = []
        for league in espn_leagues:
            team_data = {
                'id': f"espn_{league.id}",
                'name': league.user_team_name or f"Team in {league.league_name}",
                'league': league.league_name,
                'platform': 'ESPN',
                'season': league.season,
                'record': self._get_team_record(league),
                'points': self._get_team_points(league),
                'rank': self._calculate_team_rank(league),
                'playoffs': self._is_in_playoffs(league),
                'active': league.is_active,
                'espn_league_id': league.espn_league_id,
                'draft_completed': league.draft_completed,
                'scoring_type': league.scoring_type
            }
            teams_data.append(team_data)
        
        return teams_data
    
    def get_ai_context_for_user(self, user_id: int) -> Dict[str, Any]:
        """Generate AI context from user's ESPN leagues"""
        
        espn_leagues = self.db.query(ESPNLeague).filter(
            ESPNLeague.user_id == user_id,
            ESPNLeague.is_active == True
        ).all()
        
        context = {
            "user_leagues": [
                {
                    "league_name": league.league_name,
                    "platform": "ESPN",
                    "scoring_type": league.scoring_type,
                    "team_count": league.team_count,
                    "user_team": league.user_team_name,
                    "draft_completed": league.draft_completed,
                    "season": league.season
                }
                for league in espn_leagues
            ],
            "active_leagues_count": len(espn_leagues),
            "primary_scoring_types": list(set(league.scoring_type for league in espn_leagues)),
            "has_active_drafts": any(not league.draft_completed for league in espn_leagues)
        }
        
        return context
    
    async def sync_espn_to_fantasy_league(self, espn_league: ESPNLeague) -> Optional[League]:
        """Convert ESPN league to generic League model for compatibility"""
        
        # Check if generic league already exists
        existing = self.db.query(League).filter(
            League.external_id == str(espn_league.espn_league_id),
            League.platform == "ESPN"
        ).first()
        
        if existing:
            # Update existing league
            existing.name = espn_league.league_name
            existing.team_count = espn_league.team_count
            existing.scoring_type = espn_league.scoring_type
            existing.current_season = espn_league.season
            existing.updated_at = datetime.utcnow()
        else:
            # Create new generic league
            existing = League(
                name=espn_league.league_name,
                platform="ESPN",
                external_id=str(espn_league.espn_league_id),
                team_count=espn_league.team_count,
                scoring_type=espn_league.scoring_type,
                current_season=espn_league.season,
                # Map ESPN roster settings to generic format
                starting_qb=espn_league.roster_positions.get('QB', 1) if espn_league.roster_positions else 1,
                starting_rb=espn_league.roster_positions.get('RB', 2) if espn_league.roster_positions else 2,
                starting_wr=espn_league.roster_positions.get('WR', 2) if espn_league.roster_positions else 2,
                starting_te=espn_league.roster_positions.get('TE', 1) if espn_league.roster_positions else 1,
                starting_flex=espn_league.roster_positions.get('FLEX', 1) if espn_league.roster_positions else 1,
                starting_k=espn_league.roster_positions.get('K', 1) if espn_league.roster_positions else 1,
                starting_def=espn_league.roster_positions.get('DEF', 1) if espn_league.roster_positions else 1,
                bench_spots=espn_league.roster_positions.get('BENCH', 6) if espn_league.roster_positions else 6
            )
            self.db.add(existing)
        
        self.db.commit()
        return existing
    
    async def create_fantasy_team_from_espn(self, espn_league: ESPNLeague, user: User) -> Optional[FantasyTeam]:
        """Create FantasyTeam record from ESPN league data"""
        
        # Get or create the generic league
        generic_league = await self.sync_espn_to_fantasy_league(espn_league)
        if not generic_league:
            return None
        
        # Check if team already exists
        existing_team = self.db.query(FantasyTeam).filter(
            FantasyTeam.league_id == generic_league.id,
            FantasyTeam.owner_id == user.id
        ).first()
        
        if existing_team:
            # Update existing team
            existing_team.name = espn_league.user_team_name or f"Team in {espn_league.league_name}"
            existing_team.updated_at = datetime.utcnow()
        else:
            # Create new team
            existing_team = FantasyTeam(
                name=espn_league.user_team_name or f"Team in {espn_league.league_name}",
                league_id=generic_league.id,
                owner_id=user.id
                # TODO: Add more ESPN-specific data mapping
            )
            self.db.add(existing_team)
        
        self.db.commit()
        return existing_team
    
    # Private helper methods
    
    def _calculate_team_rank(self, league: ESPNLeague) -> str:
        """Calculate team rank (mock implementation)"""
        # TODO: Implement actual rank calculation from ESPN data
        return "3rd"
    
    def _get_weekly_points(self, league: ESPNLeague) -> str:
        """Get weekly points (mock implementation)"""
        # TODO: Get actual weekly points from ESPN
        return "127.4"
    
    def _count_active_players(self, league: ESPNLeague) -> int:
        """Count active players (mock implementation)"""
        # TODO: Count actual active players from roster
        return 15
    
    def _count_bench_players(self, league: ESPNLeague) -> int:
        """Count bench players (mock implementation)"""
        # TODO: Count actual bench players
        return league.roster_positions.get('BENCH', 6) if league.roster_positions else 6
    
    def _get_team_record(self, league: ESPNLeague) -> str:
        """Get team record (mock implementation)"""
        # TODO: Get actual team record from ESPN
        return "8-5"
    
    def _get_team_points(self, league: ESPNLeague) -> float:
        """Get team points (mock implementation)"""
        # TODO: Get actual team points from ESPN
        return 1247.8
    
    def _is_in_playoffs(self, league: ESPNLeague) -> bool:
        """Check if team is in playoffs (mock implementation)"""
        # TODO: Check actual playoff status
        return True
    
    def _generate_recent_activity(self, leagues: List[ESPNLeague]) -> List[Activity]:
        """Generate recent activity from ESPN leagues"""
        activities = []
        
        for league in leagues:
            # Check for active drafts
            if not league.draft_completed:
                activities.append(Activity(
                    type='recommendation',
                    title='Draft in Progress',
                    description=f'Continue your draft in {league.league_name}',
                    timestamp='Now',
                    priority='high',
                    actionUrl=f'/espn/leagues'
                ))
            
            # Add league-specific activities
            activities.append(Activity(
                type='lineup',
                title='ESPN League Update',
                description=f'Latest sync from {league.league_name}',
                timestamp='1 hour ago',
                priority='low'
            ))
        
        return activities[:5]  # Return most recent 5
    
    def _get_fallback_dashboard_data(self) -> DashboardData:
        """Return default dashboard data when no ESPN leagues exist"""
        return DashboardData(
            teamRank="--",
            leagueSize=0,
            rankTrend='stable',
            weeklyPoints="0",
            pointsProjected=0.0,
            pointsTrend='stable',
            activePlayers="0",
            benchPlayers=0,
            injuryAlerts=0,
            recentActivity=[
                Activity(
                    type='recommendation',
                    title='Connect ESPN League',
                    description='Connect your ESPN fantasy league to get personalized insights',
                    timestamp='Now',
                    priority='high',
                    actionUrl='/espn/leagues'
                )
            ],
            injuries=[]
        )


# Global service function for dependency injection
def get_espn_bridge_service(db: Session) -> ESPNBridgeService:
    """Factory function to create ESPN bridge service"""
    return ESPNBridgeService(db)