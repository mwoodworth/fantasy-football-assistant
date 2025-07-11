"""
Live Data Monitor Service - Monitors ESPN API for real-time updates
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.database import SessionLocal
from ..models.espn_league import ESPNLeague
from ..models.user import User
from .espn_integration import espn_service, ESPNServiceError
from .websocket_server import (
    emit_score_update,
    emit_player_status_change,
    emit_lineup_alert,
    emit_waiver_processed,
    emit_trade_update,
    emit_league_news,
    emit_to_user
)
from ..config import settings

logger = logging.getLogger(__name__)


class LiveDataMonitor:
    """Service to monitor live game data, player status, and league activity"""
    
    def __init__(self):
        self.active_leagues: Dict[int, ESPNLeague] = {}
        self.last_sync_times: Dict[str, datetime] = {}
        self.cached_data: Dict[str, Any] = {}
        self.polling_intervals = {
            'scores': 30,  # During games: 30 seconds
            'player_status': 300,  # 5 minutes
            'league_activity': 600,  # 10 minutes
            'lineup_check': 3600,  # 1 hour
        }
        self.is_running = False
        
    async def start(self):
        """Start the live data monitoring service"""
        if self.is_running:
            logger.warning("Live data monitor is already running")
            return
            
        self.is_running = True
        logger.info("Starting live data monitor service")
        
        # Start monitoring tasks
        asyncio.create_task(self._score_monitoring_loop())
        asyncio.create_task(self._player_status_loop())
        asyncio.create_task(self._league_activity_loop())
        asyncio.create_task(self._lineup_check_loop())
        
    async def stop(self):
        """Stop the live data monitoring service"""
        self.is_running = False
        logger.info("Stopping live data monitor service")
        
    async def _score_monitoring_loop(self):
        """Monitor live scores during game days"""
        while self.is_running:
            try:
                if self._is_game_day():
                    await self._check_live_scores()
                    await asyncio.sleep(self.polling_intervals['scores'])
                else:
                    # Check less frequently when no games
                    await asyncio.sleep(3600)  # 1 hour
            except Exception as e:
                logger.error(f"Error in score monitoring: {e}")
                await asyncio.sleep(60)
                
    async def _player_status_loop(self):
        """Monitor player status changes (injuries, etc.)"""
        while self.is_running:
            try:
                await self._check_player_statuses()
                await asyncio.sleep(self.polling_intervals['player_status'])
            except Exception as e:
                logger.error(f"Error in player status monitoring: {e}")
                await asyncio.sleep(300)
                
    async def _league_activity_loop(self):
        """Monitor league activity (trades, waivers, etc.)"""
        while self.is_running:
            try:
                await self._check_league_activity()
                await asyncio.sleep(self.polling_intervals['league_activity'])
            except Exception as e:
                logger.error(f"Error in league activity monitoring: {e}")
                await asyncio.sleep(600)
                
    async def _lineup_check_loop(self):
        """Check for lineup issues (inactive players, etc.)"""
        while self.is_running:
            try:
                await self._check_lineups()
                await asyncio.sleep(self.polling_intervals['lineup_check'])
            except Exception as e:
                logger.error(f"Error in lineup check: {e}")
                await asyncio.sleep(3600)
                
    def _is_game_day(self) -> bool:
        """Check if today is a game day (Thursday, Sunday, Monday)"""
        today = datetime.utcnow()
        # NFL games are typically on Thu (3), Sun (6), Mon (0)
        return today.weekday() in [3, 6, 0]
        
    def _should_sync(self, sync_type: str, league_id: int) -> bool:
        """Check if we should sync based on last sync time"""
        key = f"{sync_type}_{league_id}"
        last_sync = self.last_sync_times.get(key)
        if not last_sync:
            return True
            
        interval = self.polling_intervals.get(sync_type, 300)
        return (datetime.utcnow() - last_sync).total_seconds() >= interval
        
    def _update_sync_time(self, sync_type: str, league_id: int):
        """Update last sync time"""
        key = f"{sync_type}_{league_id}"
        self.last_sync_times[key] = datetime.utcnow()
        
    async def _get_active_leagues(self) -> List[ESPNLeague]:
        """Get all active leagues that need monitoring"""
        db = SessionLocal()
        try:
            leagues = db.query(ESPNLeague).filter(
                ESPNLeague.is_active == True
            ).all()
            return leagues
        finally:
            db.close()
            
    async def _check_live_scores(self):
        """Check and emit live score updates"""
        leagues = await self._get_active_leagues()
        
        for league in leagues:
            if not self._should_sync('scores', league.id):
                continue
                
            try:
                # Get current league info
                league_data = await espn_service.get_league_info(
                    league.espn_league_id,
                    league.season,
                    espn_s2=league.espn_s2,
                    swid=league.swid
                )
                
                if not league_data or not league_data.get('success'):
                    continue
                    
                current_week = league_data.get('data', {}).get('status', {}).get('currentMatchupPeriod', 0)
                if current_week == 0:
                    continue
                    
                # Get scoreboard for current week
                scores_data = await espn_service.get_scoreboard(
                    league.espn_league_id,
                    league.season,
                    current_week
                )
                
                if scores_data and scores_data.get('success'):
                    await self._process_score_updates(league, scores_data['data'])
                    
                self._update_sync_time('scores', league.id)
                
            except Exception as e:
                logger.error(f"Error checking scores for league {league.id}: {e}")
                
    async def _process_score_updates(self, league: ESPNLeague, scores_data: Dict[str, Any]):
        """Process and emit score updates"""
        cache_key = f"scores_{league.id}"
        old_scores = self.cached_data.get(cache_key, {})
        new_scores = {}
        
        matchups = scores_data.get('schedule', [])
        
        for matchup in matchups:
            if matchup.get('matchupPeriodId') != scores_data.get('scoringPeriodId'):
                continue
                
            home_team = matchup.get('home', {})
            away_team = matchup.get('away', {})
            
            # Track scores by team ID
            for team in [home_team, away_team]:
                if team and team.get('teamId'):
                    team_id = team['teamId']
                    current_score = team.get('totalPoints', 0)
                    new_scores[team_id] = current_score
                    
                    # Check if score changed
                    if team_id in old_scores and old_scores[team_id] != current_score:
                        # Score changed - emit update
                        await self._emit_score_update_for_team(league, team_id, {
                            'team_id': team_id,
                            'team_name': team.get('teamName', 'Unknown'),
                            'current_score': current_score,
                            'previous_score': old_scores[team_id],
                            'opponent_id': away_team['teamId'] if team == home_team else home_team['teamId'],
                            'opponent_score': away_team.get('totalPoints', 0) if team == home_team else home_team.get('totalPoints', 0),
                            'week': scores_data.get('scoringPeriodId'),
                            'is_home': team == home_team
                        })
                        
        # Update cache
        self.cached_data[cache_key] = new_scores
        
    async def _emit_score_update_for_team(self, league: ESPNLeague, team_id: int, update_data: Dict[str, Any]):
        """Emit score update to users who own this team"""
        db = SessionLocal()
        try:
            # Find users who own this team
            users = db.query(User).join(ESPNLeague).filter(
                and_(
                    ESPNLeague.espn_league_id == league.espn_league_id,
                    ESPNLeague.user_team_id == team_id
                )
            ).all()
            
            for user in users:
                await emit_score_update(str(user.id), update_data)
                
        finally:
            db.close()
            
    async def _check_player_statuses(self):
        """Check for player status changes"""
        leagues = await self._get_active_leagues()
        
        for league in leagues:
            if not self._should_sync('player_status', league.id):
                continue
                
            try:
                # Get all teams in the league to check rosters
                teams_data = await espn_service.get_league_teams(
                    league.espn_league_id,
                    league.season,
                    espn_s2=league.espn_s2,
                    swid=league.swid
                )
                
                if not teams_data or not teams_data.get('success'):
                    continue
                    
                # Extract the actual data, handling both list and dict responses
                data = teams_data.get('data', {})
                if isinstance(data, dict) and 'teams' in data:
                    # If data is a dict with 'teams' key, use it as is
                    await self._process_player_status_changes(league, data)
                elif isinstance(data, list):
                    # If data is a list, pass it directly
                    await self._process_player_status_changes(league, data)
                else:
                    # If data is in an unexpected format, log and skip
                    logger.warning(f"Unexpected data format for league {league.id}: {type(data)}")
                    continue
                self._update_sync_time('player_status', league.id)
                
            except Exception as e:
                logger.error(f"Error checking player statuses for league {league.id}: {e}")
                
    async def _process_player_status_changes(self, league: ESPNLeague, roster_data: Dict[str, Any]):
        """Process player status changes and emit updates"""
        cache_key = f"player_status_{league.id}"
        old_statuses = self.cached_data.get(cache_key, {})
        new_statuses = {}
        
        # Handle both list and dict formats from ESPN API
        if isinstance(roster_data, list):
            teams = roster_data
        else:
            teams = roster_data.get('teams', [])
        
        for team in teams:
            team_id = team.get('id')
            roster = team.get('roster', {}).get('entries', [])
            
            for entry in roster:
                player_data = entry.get('playerPoolEntry', {}).get('player', {})
                player_id = player_data.get('id')
                
                if not player_id:
                    continue
                    
                injury_status = player_data.get('injuryStatus', 'ACTIVE')
                new_statuses[player_id] = injury_status
                
                # Check if status changed
                if player_id in old_statuses and old_statuses[player_id] != injury_status:
                    # Status changed - emit update
                    await self._emit_player_status_change(league, team_id, {
                        'player_id': player_id,
                        'player_name': player_data.get('fullName', 'Unknown'),
                        'team': player_data.get('proTeamId'),
                        'position': self._get_position_abbr(player_data.get('defaultPositionId')),
                        'old_status': old_statuses[player_id],
                        'new_status': injury_status,
                        'team_id': team_id
                    })
                    
        # Update cache
        self.cached_data[cache_key] = new_statuses
        
    async def _emit_player_status_change(self, league: ESPNLeague, team_id: int, update_data: Dict[str, Any]):
        """Emit player status change to affected users"""
        db = SessionLocal()
        try:
            # Find user who owns this team
            user = db.query(User).join(ESPNLeague).filter(
                and_(
                    ESPNLeague.espn_league_id == league.espn_league_id,
                    ESPNLeague.user_team_id == team_id
                )
            ).first()
            
            if user:
                await emit_player_status_change(str(user.id), update_data)
                
                # If player is now injured and in starting lineup, send lineup alert
                if update_data['new_status'] != 'ACTIVE':
                    await emit_lineup_alert(str(user.id), {
                        'type': 'injured_starter',
                        'player': update_data,
                        'message': f"{update_data['player_name']} is now {update_data['new_status']}"
                    })
                    
        finally:
            db.close()
            
    async def _check_league_activity(self):
        """Check for league activity (trades, waivers, etc.)"""
        leagues = await self._get_active_leagues()
        
        for league in leagues:
            if not self._should_sync('league_activity', league.id):
                continue
                
            try:
                # For now, skip transaction history as the endpoint is not implemented
                # TODO: Implement transaction history endpoint in ESPN bridge service
                logger.info(f"Skipping league activity check for league {league.id} - endpoint not implemented")
                
                # Still update sync time to prevent continuous retries
                self._update_sync_time('league_activity', league.id)
                
            except Exception as e:
                logger.error(f"Error checking league activity for {league.id}: {e}")
                
    async def _process_league_activity(self, league: ESPNLeague, activity_data: Dict[str, Any]):
        """Process league activity and emit relevant updates"""
        cache_key = f"activity_{league.id}"
        old_activities = self.cached_data.get(cache_key, set())
        new_activities = set()
        
        topics = activity_data.get('topics', [])
        
        for topic in topics:
            topic_id = topic.get('id')
            if not topic_id:
                continue
                
            new_activities.add(topic_id)
            
            # Check if this is a new activity
            if topic_id not in old_activities:
                activity_type = topic.get('type', '')
                
                if 'WAIVER' in activity_type:
                    await self._process_waiver_activity(league, topic)
                elif 'TRADE' in activity_type:
                    await self._process_trade_activity(league, topic)
                else:
                    # General league news
                    await emit_league_news(str(league.espn_league_id), {
                        'type': activity_type,
                        'message': topic.get('headline', ''),
                        'date': topic.get('date'),
                        'details': topic.get('body', '')
                    })
                    
        # Update cache
        self.cached_data[cache_key] = new_activities
        
    async def _process_waiver_activity(self, league: ESPNLeague, activity: Dict[str, Any]):
        """Process waiver claim activity"""
        messages = activity.get('messages', [])
        
        for message in messages:
            # Parse waiver details from message
            for_team_id = message.get('for')
            
            if for_team_id:
                db = SessionLocal()
                try:
                    user = db.query(User).join(ESPNLeague).filter(
                        and_(
                            ESPNLeague.espn_league_id == league.espn_league_id,
                            ESPNLeague.user_team_id == for_team_id
                        )
                    ).first()
                    
                    if user:
                        await emit_waiver_processed(str(user.id), {
                            'type': 'waiver_processed',
                            'message': activity.get('headline', ''),
                            'details': message,
                            'date': activity.get('date')
                        })
                finally:
                    db.close()
                    
    async def _process_trade_activity(self, league: ESPNLeague, activity: Dict[str, Any]):
        """Process trade activity"""
        messages = activity.get('messages', [])
        
        for message in messages:
            # Get teams involved in trade
            team_ids = []
            if 'for' in message:
                team_ids.append(message['for'])
            if 'to' in message:
                team_ids.append(message['to'])
                
            # Notify all involved teams
            db = SessionLocal()
            try:
                for team_id in team_ids:
                    user = db.query(User).join(ESPNLeague).filter(
                        and_(
                            ESPNLeague.espn_league_id == league.espn_league_id,
                            ESPNLeague.user_team_id == team_id
                        )
                    ).first()
                    
                    if user:
                        await emit_trade_update(str(user.id), {
                            'type': 'trade_activity',
                            'message': activity.get('headline', ''),
                            'details': message,
                            'date': activity.get('date'),
                            'status': 'completed'  # or parse from activity
                        })
            finally:
                db.close()
                
    async def _check_lineups(self):
        """Check for lineup issues"""
        leagues = await self._get_active_leagues()
        
        for league in leagues:
            if not self._should_sync('lineup_check', league.id):
                continue
                
            try:
                # Only check lineups close to game time
                if self._is_near_game_time():
                    await self._check_league_lineups(league)
                    
                self._update_sync_time('lineup_check', league.id)
                
            except Exception as e:
                logger.error(f"Error checking lineups for league {league.id}: {e}")
                
    def _is_near_game_time(self) -> bool:
        """Check if we're within 2 hours of typical game start times"""
        now = datetime.utcnow()
        
        # NFL games typically start at:
        # Thu: 8:20 PM ET (00:20 UTC Friday)
        # Sun: 1:00 PM, 4:00 PM, 8:20 PM ET (18:00, 21:00, 01:20 UTC Monday)
        # Mon: 8:15 PM ET (01:15 UTC Tuesday)
        
        # Simplified check - alert 2 hours before common start times
        hour = now.hour
        weekday = now.weekday()
        
        if weekday == 4:  # Friday UTC (Thursday night game)
            return 22 <= hour or hour <= 2
        elif weekday == 0:  # Monday UTC (Sunday games)
            return 16 <= hour or hour <= 2
        elif weekday == 1:  # Tuesday UTC (Monday night game)
            return 23 <= hour or hour <= 3
            
        return False
        
    async def _check_league_lineups(self, league: ESPNLeague):
        """Check all lineups in a league for issues"""
        db = SessionLocal()
        try:
            # Get all teams in the league
            users = db.query(User).join(ESPNLeague).filter(
                ESPNLeague.espn_league_id == league.espn_league_id
            ).all()
            
            for user in users:
                user_league = db.query(ESPNLeague).filter(
                    and_(
                        ESPNLeague.user_id == user.id,
                        ESPNLeague.espn_league_id == league.espn_league_id
                    )
                ).first()
                
                if user_league and user_league.user_team_id:
                    await self._check_team_lineup(user, user_league)
                    
        finally:
            db.close()
            
    async def _check_team_lineup(self, user: User, league: ESPNLeague):
        """Check a specific team's lineup for issues"""
        try:
            # Get team roster
            roster = await espn_service.get_team_roster(
                league.user_team_id,
                league.espn_league_id,
                league.season,
                espn_s2=league.espn_s2,
                swid=league.swid
            )
            
            if not roster or not roster.get('success'):
                return
                
            lineup_issues = []
            roster_data = roster.get('data', {})
            
            # Handle both list and dict formats
            if isinstance(roster_data, list):
                # If it's a list of entries directly
                entries = roster_data
            else:
                # If it's a dict with entries key
                entries = roster_data.get('entries', [])
            
            # Check for injured/bye week players in starting lineup
            starters = [e for e in entries
                       if e.get('lineupSlotId') not in [20, 21, 23]]  # Not bench/IR slots
            
            for entry in starters:
                player = entry.get('playerPoolEntry', {}).get('player', {})
                
                # Check injury status
                if player.get('injuryStatus') not in ['ACTIVE', None]:
                    lineup_issues.append({
                        'type': 'injured_starter',
                        'player_name': player.get('fullName'),
                        'status': player.get('injuryStatus'),
                        'position': self._get_position_abbr(player.get('defaultPositionId'))
                    })
                    
                # Check bye week
                # This would need current week info and team schedules
                
            # Check for empty roster spots
            required_slots = roster_data.get('lineup_settings', {})
            # Would need to implement logic to check if all required slots are filled
            
            if lineup_issues:
                await emit_lineup_alert(str(user.id), {
                    'issues': lineup_issues,
                    'team_id': league.user_team_id,
                    'message': f"Found {len(lineup_issues)} lineup issue(s)"
                })
                
        except Exception as e:
            logger.error(f"Error checking lineup for user {user.id}: {e}")
            
    def _get_position_abbr(self, position_id: Optional[int]) -> str:
        """Convert ESPN position ID to abbreviation"""
        position_map = {
            1: 'QB', 2: 'RB', 3: 'WR', 4: 'TE', 5: 'K',
            16: 'D/ST', 17: 'IDP', 18: 'FLEX'
        }
        return position_map.get(position_id, 'UNKNOWN')


# Global live monitor instance
live_monitor = LiveDataMonitor()