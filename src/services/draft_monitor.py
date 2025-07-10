"""
Draft Monitor Service - Polls ESPN API for live draft updates
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.database import SessionLocal
from ..models.espn_league import DraftSession, ESPNLeague
from ..models.user import User
from .espn_integration import espn_service, ESPNServiceError
from .websocket_server import (
    emit_pick_made,
    emit_user_on_clock,
    emit_draft_status_change,
    emit_sync_error
)
from ..config import settings

logger = logging.getLogger(__name__)


class DraftMonitor:
    """Service to monitor active drafts and sync with ESPN"""
    
    def __init__(self):
        self.active_sessions: Dict[int, DraftSession] = {}
        self.last_sync_times: Dict[int, datetime] = {}
        self.known_picks: Dict[int, Set[int]] = {}  # session_id -> set of pick numbers
        self.polling_interval = 5  # seconds
        self.is_running = False
        
    async def start(self):
        """Start the draft monitoring service"""
        if self.is_running:
            logger.warning("Draft monitor is already running")
            return
            
        self.is_running = True
        logger.info("Starting draft monitor service")
        
        # Start the main monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
    async def stop(self):
        """Stop the draft monitoring service"""
        self.is_running = False
        logger.info("Stopping draft monitor service")
        
    async def _monitoring_loop(self):
        """Main loop that monitors active drafts"""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.is_running:
            try:
                await self._check_active_drafts()
                consecutive_errors = 0  # Reset on success
                await asyncio.sleep(self.polling_interval)
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in monitoring loop (attempt {consecutive_errors}): {e}")
                
                # Exponential backoff
                backoff_time = min(self.polling_interval * (2 ** consecutive_errors), 60)
                await asyncio.sleep(backoff_time)
                
                # Stop monitoring if too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(f"Draft monitor stopping after {max_consecutive_errors} consecutive errors")
                    await self.stop()
                    break
                
    async def _check_active_drafts(self):
        """Check all active draft sessions and sync their state"""
        db = SessionLocal()
        try:
            # Get all active draft sessions
            active_sessions = db.query(DraftSession).filter(
                and_(
                    DraftSession.is_active == True,
                    DraftSession.is_live_synced == True
                )
            ).all()
            
            for session in active_sessions:
                # Check if we should sync this session
                if self._should_sync_session(session):
                    await self._sync_draft_session(session, db)
                    
        except Exception as e:
            logger.error(f"Error checking active drafts: {e}")
        finally:
            db.close()
            
    def _should_sync_session(self, session: DraftSession) -> bool:
        """Determine if a session should be synced based on last sync time"""
        last_sync = self.last_sync_times.get(session.id)
        if not last_sync:
            return True
            
        # Sync every polling_interval seconds
        return (datetime.utcnow() - last_sync).total_seconds() >= self.polling_interval
        
    async def _sync_draft_session(self, session: DraftSession, db: Session):
        """Sync a single draft session with ESPN"""
        try:
            logger.info(f"Syncing draft session {session.id} for league {session.league_id}")
            
            # Get the league info
            league = db.query(ESPNLeague).filter(
                ESPNLeague.id == session.league_id
            ).first()
            
            if not league:
                logger.error(f"League not found for session {session.id}")
                return
                
            # Fetch draft data from ESPN
            draft_data = await espn_service.get_draft_results(
                league.espn_league_id,
                league.season
            )
            
            if not draft_data or not draft_data.get('success'):
                logger.warning(f"Failed to fetch draft data for league {league.espn_league_id}")
                return
                
            # Process the draft data
            await self._process_draft_data(session, draft_data.get('data', {}), db)
            
            # Update last sync time
            self.last_sync_times[session.id] = datetime.utcnow()
            session.last_activity = datetime.utcnow()
            db.commit()
            
        except ESPNServiceError as e:
            logger.error(f"ESPN service error syncing session {session.id}: {e}")
            # Emit sync error to connected clients
            await emit_sync_error(str(session.id), f"ESPN API error: {str(e)}")
            # Don't mark session as failed on API errors - might be temporary
        except Exception as e:
            logger.error(f"Error syncing draft session {session.id}: {e}")
            # Emit sync error to connected clients
            await emit_sync_error(str(session.id), f"Sync error: {str(e)}")
            # Consider marking session as having sync issues
            
    async def _process_draft_data(self, session: DraftSession, draft_data: Dict, db: Session):
        """Process draft data from ESPN and update session"""
        # Check if draft is still in progress
        in_progress = draft_data.get('inProgress', False)
        completed = draft_data.get('drafted', False)
        
        if completed and session.is_active:
            # Draft has been completed
            logger.info(f"Draft completed for session {session.id}")
            session.is_active = False
            session.completed_at = datetime.utcnow()
            session.draft_status = 'completed'
            db.commit()
            
            # Emit draft completed event
            await emit_draft_status_change(str(session.id), 'completed')
            return
            
        if not in_progress:
            # Draft hasn't started yet
            return
            
        # Process picks
        picks = draft_data.get('picks', [])
        new_picks = self._find_new_picks(session.id, picks)
        
        if new_picks:
            logger.info(f"Found {len(new_picks)} new picks for session {session.id}")
            for pick in new_picks:
                await self._process_new_pick(session, pick, db)
                
        # Update current pick info
        current_pick_info = draft_data.get('currentPickTeam', {})
        if current_pick_info:
            await self._update_current_pick(session, current_pick_info, db)
            
    def _find_new_picks(self, session_id: int, picks: List[Dict]) -> List[Dict]:
        """Find picks that we haven't processed yet"""
        if session_id not in self.known_picks:
            self.known_picks[session_id] = set()
            
        known = self.known_picks[session_id]
        new_picks = []
        
        for pick in picks:
            pick_number = pick.get('overallPickNumber', 0)
            if pick_number and pick_number not in known:
                new_picks.append(pick)
                known.add(pick_number)
                
        return new_picks
        
    async def _process_new_pick(self, session: DraftSession, pick: Dict, db: Session):
        """Process a newly detected pick"""
        pick_data = {
            'player_id': pick.get('playerId'),
            'team_id': pick.get('teamId'),
            'pick_number': pick.get('overallPickNumber'),
            'round': pick.get('roundId'),
            'round_pick': pick.get('roundPickNumber')
        }
        
        # Update session's drafted players
        if not session.drafted_players:
            session.drafted_players = []
            
        session.drafted_players.append(pick_data)
        
        # Update current pick number
        session.current_pick = pick['overallPickNumber'] + 1
        session.current_round = pick['roundId']
        
        # Check if this was the user's pick
        league = db.query(ESPNLeague).filter(ESPNLeague.id == session.league_id).first()
        if league and pick['teamId'] == league.user_team_id:
            # Add to user's roster
            if not session.user_roster:
                session.user_roster = []
            session.user_roster.append(pick_data)
            
        db.commit()
        
        # Emit WebSocket event for real-time updates
        await emit_pick_made(str(session.id), {
            'pick_number': pick['overallPickNumber'],
            'player_id': pick.get('playerId'),
            'team_id': pick.get('teamId'),
            'round': pick.get('roundId'),
            'round_pick': pick.get('roundPickNumber'),
            'is_user_pick': pick['teamId'] == league.user_team_id if league else False
        })
        
        logger.info(f"Processed pick #{pick['overallPickNumber']} in session {session.id}")
        
    async def _update_current_pick(self, session: DraftSession, current_pick_info: Dict, db: Session):
        """Update who's currently on the clock"""
        # This would be used to show who's picking now
        # and calculate time until user's next pick
        current_team = current_pick_info.get('teamId')
        current_pick_num = current_pick_info.get('pickNumber')
        
        if current_pick_num:
            session.current_pick = current_pick_num
            
        # Calculate picks until user's turn
        if session.user_pick_position and current_pick_num:
            # Simple calculation - would need to be more sophisticated for snake drafts
            picks_per_round = session.total_picks // session.total_rounds
            current_round = ((current_pick_num - 1) // picks_per_round) + 1
            
            # This is simplified - real implementation would handle snake draft logic
            user_next_pick = self._calculate_next_user_pick(
                session.user_pick_position,
                current_pick_num,
                picks_per_round,
                current_round
            )
            
            # Store this for frontend display
            session.available_players = session.available_players or {}
            session.available_players['next_user_pick'] = user_next_pick
            session.available_players['picks_until_turn'] = max(0, user_next_pick - current_pick_num)
            
            # Emit event if it's user's turn
            if current_pick_num == user_next_pick:
                league = db.query(ESPNLeague).filter(ESPNLeague.id == session.league_id).first()
                if league:
                    await emit_user_on_clock(str(session.id), str(session.user_id))
            
        db.commit()
        
    def _calculate_next_user_pick(self, user_position: int, current_pick: int, 
                                  teams: int, current_round: int) -> int:
        """Calculate when user picks next in a snake draft"""
        # Snake draft logic
        if current_round % 2 == 1:  # Odd round (forward)
            if current_pick <= (current_round - 1) * teams + user_position:
                # User hasn't picked this round yet
                return (current_round - 1) * teams + user_position
            else:
                # User's next pick is in the next round (reverse)
                return current_round * teams + (teams - user_position + 1)
        else:  # Even round (reverse)
            if current_pick <= (current_round - 1) * teams + (teams - user_position + 1):
                # User hasn't picked this round yet
                return (current_round - 1) * teams + (teams - user_position + 1)
            else:
                # User's next pick is in the next round (forward)
                return current_round * teams + user_position


# Global draft monitor instance
draft_monitor = DraftMonitor()