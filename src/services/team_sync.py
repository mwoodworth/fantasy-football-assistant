"""
Team Sync Service
Handles synchronization of ESPN league teams and rosters with the database
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session

from ..models.espn_league import ESPNLeague
from ..models.espn_team import ESPNTeam, TeamSyncLog
from .espn_integration import espn_service, ESPNServiceError

logger = logging.getLogger(__name__)


class TeamSyncService:
    """Service for syncing ESPN teams and rosters to database"""
    
    def __init__(self):
        self.espn_service = espn_service
    
    async def sync_league_teams(self, db: Session, espn_league: ESPNLeague, 
                              force_refresh: bool = False) -> TeamSyncLog:
        """
        Sync all teams in a league to the database
        
        Args:
            db: Database session
            espn_league: ESPNLeague instance
            force_refresh: Whether to force refresh even if recently synced
            
        Returns:
            TeamSyncLog: Log of the sync operation
        """
        # Create sync log
        sync_log = TeamSyncLog(
            espn_league_id=espn_league.id,
            sync_type="manual" if force_refresh else "scheduled",
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(sync_log)
        db.commit()
        
        try:
            logger.info(f"Starting team sync for league {espn_league.league_name} (ID: {espn_league.espn_league_id})")
            
            # Check if we need to sync (skip if recent sync and not forced)
            if not force_refresh and not self._should_sync_teams(db, espn_league):
                sync_log.status = "skipped"
                sync_log.sync_summary = {"message": "Recent sync found, skipping"}
                sync_log.mark_completed("skipped")
                db.commit()
                return sync_log
            
            # Fetch teams from ESPN
            teams_data = await self.espn_service.sync_league_teams(
                espn_league.espn_league_id,
                espn_league.season,
                espn_league.espn_s2,
                espn_league.swid
            )
            
            if not teams_data.get('success'):
                raise ESPNServiceError(f"Failed to sync teams: {teams_data.get('error')}")
            
            teams = teams_data.get('teams', [])
            teams_processed = 0
            teams_updated = 0
            teams_failed = 0
            
            # Process each team
            for team_data in teams:
                try:
                    updated = self._upsert_team(db, espn_league, team_data)
                    teams_processed += 1
                    if updated:
                        teams_updated += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process team {team_data.get('id', 'unknown')}: {e}")
                    teams_failed += 1
            
            # Update sync log
            sync_log.teams_processed = teams_processed
            sync_log.teams_updated = teams_updated
            sync_log.teams_failed = teams_failed
            sync_log.sync_summary = {
                "total_teams": len(teams),
                "processed": teams_processed,
                "updated": teams_updated,
                "failed": teams_failed,
                "synced_at": datetime.utcnow().isoformat()
            }
            
            if teams_failed == 0:
                sync_log.mark_completed("success")
            else:
                sync_log.mark_completed("partial")
            
            logger.info(f"Team sync completed: {teams_processed} processed, {teams_updated} updated, {teams_failed} failed")
            
        except Exception as e:
            logger.error(f"Team sync failed: {e}")
            sync_log.error_details = {"error": str(e)}
            sync_log.mark_completed("failed")
        
        finally:
            db.commit()
        
        return sync_log
    
    def _should_sync_teams(self, db: Session, espn_league: ESPNLeague) -> bool:
        """Check if teams should be synced (not synced recently)"""
        # Check if any team was synced in the last hour
        recent_sync = db.query(ESPNTeam).filter(
            ESPNTeam.espn_league_id == espn_league.id,
            ESPNTeam.last_synced > datetime.utcnow() - timedelta(hours=1)
        ).first()
        
        return recent_sync is None
    
    def _upsert_team(self, db: Session, espn_league: ESPNLeague, team_data: Dict[str, Any]) -> bool:
        """
        Insert or update a team in the database
        
        Returns:
            bool: True if team was updated, False if created
        """
        espn_team_id = team_data.get('id')
        if not espn_team_id:
            raise ValueError("Team data missing ESPN team ID")
        
        # Check if team exists
        existing_team = db.query(ESPNTeam).filter(
            ESPNTeam.espn_league_id == espn_league.id,
            ESPNTeam.espn_team_id == espn_team_id
        ).first()
        
        # Extract team info
        team_info = self._extract_team_info(team_data)
        roster_analysis = self._analyze_roster(team_info['roster_data'])
        
        if existing_team:
            # Update existing team
            for key, value in team_info.items():
                setattr(existing_team, key, value)
            
            # Update roster analysis
            existing_team.position_strengths = roster_analysis['position_strengths']
            existing_team.position_depth_scores = roster_analysis['position_depth_scores']
            existing_team.tradeable_assets = roster_analysis['tradeable_assets']
            existing_team.team_needs = roster_analysis['team_needs']
            existing_team.last_synced = datetime.utcnow()
            existing_team.sync_status = "success"
            existing_team.sync_error_message = None
            
            # Mark as user team if this is the league owner's team
            if espn_team_id == espn_league.user_team_id:
                existing_team.is_user_team = True
            
            db.commit()
            return True
        else:
            # Create new team
            new_team = ESPNTeam(
                espn_league_id=espn_league.id,
                espn_team_id=espn_team_id,
                is_user_team=(espn_team_id == espn_league.user_team_id),
                last_synced=datetime.utcnow(),
                sync_status="success",
                **team_info,
                **roster_analysis
            )
            
            db.add(new_team)
            db.commit()
            return False
    
    def _extract_team_info(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic team information from ESPN data"""
        roster = team_data.get('roster', [])
        
        # Handle nested ESPN data structure
        owner_info = team_data.get('owner', {})
        record_info = team_data.get('record', {})
        standings_info = team_data.get('standings', {})
        
        # Process roster data - ESPN returns it under 'entries'
        if isinstance(roster, dict) and 'entries' in roster:
            roster_entries = roster.get('entries', [])
        elif isinstance(roster, list):
            roster_entries = roster
        else:
            roster_entries = []
        
        # Convert ESPN roster format to our format
        processed_roster = []
        for entry in roster_entries:
            if isinstance(entry, dict) and 'player' in entry:
                player = entry['player']
                processed_player = {
                    'id': player.get('id'),
                    'name': player.get('name'),
                    'position': player.get('position'),
                    'team': player.get('team'),
                    'injury_status': player.get('injuryStatus', 'ACTIVE'),
                    'status': 'starter' if entry.get('lineupSlotId', 20) < 20 else 'bench'  # ESPN uses 20+ for bench
                }
                processed_roster.append(processed_player)
        
        return {
            'team_name': team_data.get('name', 'Unknown Team'),
            'owner_name': owner_info.get('displayName', ''),
            'team_abbreviation': team_data.get('abbreviation', ''),
            'wins': record_info.get('wins', 0),
            'losses': record_info.get('losses', 0),
            'ties': record_info.get('ties', 0),
            'points_for': float(standings_info.get('pointsFor', 0)),
            'points_against': float(standings_info.get('pointsAgainst', 0)),
            'roster_data': processed_roster,
            'starting_lineup': [p for p in processed_roster if p.get('status') == 'starter'],
            'bench_players': [p for p in processed_roster if p.get('status') != 'starter'],
            'is_active': True
        }
    
    def _analyze_roster(self, roster: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze roster to determine strengths, weaknesses, and trade opportunities
        
        Returns:
            Dict with position_strengths, position_depth_scores, tradeable_assets, team_needs
        """
        if not roster:
            return {
                'position_strengths': {},
                'position_depth_scores': {},
                'tradeable_assets': [],
                'team_needs': []
            }
        
        # Count players by position
        position_counts = {}
        starters_by_position = {}
        bench_by_position = {}
        
        for player in roster:
            pos = player.get('position', 'UNKNOWN')
            status = player.get('status', 'bench')
            
            position_counts[pos] = position_counts.get(pos, 0) + 1
            
            if status == 'starter':
                starters_by_position[pos] = starters_by_position.get(pos, 0) + 1
            else:
                bench_by_position[pos] = bench_by_position.get(pos, 0) + 1
        
        # Define position thresholds for analysis
        position_thresholds = {
            'QB': {'ideal': 2, 'minimum': 1, 'surplus': 3},
            'RB': {'ideal': 4, 'minimum': 2, 'surplus': 6},
            'WR': {'ideal': 5, 'minimum': 3, 'surplus': 7},
            'TE': {'ideal': 2, 'minimum': 1, 'surplus': 3},
            'K': {'ideal': 1, 'minimum': 1, 'surplus': 2},
            'D/ST': {'ideal': 1, 'minimum': 1, 'surplus': 2}
        }
        
        # Analyze strengths and weaknesses
        position_strengths = {}
        position_depth_scores = {}
        tradeable_assets = []
        team_needs = []
        
        for pos, thresholds in position_thresholds.items():
            count = position_counts.get(pos, 0)
            
            if count >= thresholds['surplus']:
                position_strengths[pos] = 'surplus'
                depth_score = min(1.0, count / thresholds['surplus'])
                
                # Identify tradeable assets (bench players at surplus positions)
                bench_players = [p for p in roster 
                               if p.get('position') == pos and p.get('status') != 'starter']
                for player in bench_players[:2]:  # Top 2 bench players
                    tradeable_assets.append({
                        'player_id': player.get('id'),
                        'name': player.get('name'),
                        'position': pos,
                        'team': player.get('team'),
                        'reason': 'Position surplus'
                    })
                    
            elif count >= thresholds['ideal']:
                position_strengths[pos] = 'strong'
                depth_score = 0.8
            elif count >= thresholds['minimum']:
                position_strengths[pos] = 'adequate'
                depth_score = 0.6
            else:
                position_strengths[pos] = 'weak'
                depth_score = count / thresholds['minimum'] * 0.4
                team_needs.append(pos)
            
            position_depth_scores[pos] = round(depth_score, 2)
        
        return {
            'position_strengths': position_strengths,
            'position_depth_scores': position_depth_scores,
            'tradeable_assets': tradeable_assets,
            'team_needs': team_needs
        }
    
    async def get_teams_needing_sync(self, db: Session, hours_old: int = 24) -> List[ESPNLeague]:
        """Get leagues whose teams need syncing (haven't been synced recently)"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
        
        # Find leagues where no teams have been synced recently
        leagues = db.query(ESPNLeague).filter(
            ESPNLeague.is_active == True,
            ESPNLeague.sync_enabled == True
        ).all()
        
        leagues_to_sync = []
        for league in leagues:
            recent_team_sync = db.query(ESPNTeam).filter(
                ESPNTeam.espn_league_id == league.id,
                ESPNTeam.last_synced > cutoff_time
            ).first()
            
            if not recent_team_sync:
                leagues_to_sync.append(league)
        
        return leagues_to_sync


# Singleton instance
team_sync_service = TeamSyncService()