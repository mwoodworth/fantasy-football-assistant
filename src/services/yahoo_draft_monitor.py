"""Yahoo Draft Monitor Service for real-time draft tracking."""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..models import YahooDraftSession, YahooDraftEvent, YahooLeague
from ..services.yahoo_integration import YahooIntegrationService as YahooIntegration
from ..services.websocket_utils import ws_manager

logger = logging.getLogger(__name__)

class YahooDraftMonitor:
    """Monitor Yahoo draft in real-time and emit WebSocket events."""
    
    def __init__(self, session_id: int, league_key: str, user_id: int, db: Session):
        self.session_id = session_id
        self.league_key = league_key
        self.user_id = user_id
        self.db = db
        self.yahoo_integration = YahooIntegration()
        
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_pick_count = 0
        self._error_count = 0
        self._max_errors = 5
        
    def start(self):
        """Start monitoring the draft."""
        if self._thread and self._thread.is_alive():
            logger.warning(f"Draft monitor already running for session {self.session_id}")
            return
            
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop)
        self._thread.daemon = True
        self._thread.start()
        logger.info(f"Started draft monitor for session {self.session_id}")
        
    def stop(self):
        """Stop monitoring the draft."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info(f"Stopped draft monitor for session {self.session_id}")
        
    def _monitor_loop(self):
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                # Get current session
                session = self.db.query(YahooDraftSession).filter(
                    YahooDraftSession.id == self.session_id
                ).first()
                
                if not session or not session.live_sync_enabled:
                    logger.info(f"Draft sync disabled for session {self.session_id}")
                    break
                    
                if session.draft_status == "completed":
                    logger.info(f"Draft completed for session {self.session_id}")
                    break
                
                # Sync draft state
                self._sync_draft_state(session)
                
                # Reset error count on successful sync
                self._error_count = 0
                
                # Wait for next sync interval
                time.sleep(session.sync_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in draft monitor: {e}")
                self._error_count += 1
                
                # Stop monitoring after too many errors
                if self._error_count >= self._max_errors:
                    logger.error(f"Too many errors, stopping monitor for session {self.session_id}")
                    self._emit_error_event("Too many sync errors, monitoring stopped")
                    break
                    
                # Wait longer on error
                time.sleep(30)
                
    def _sync_draft_state(self, session: YahooDraftSession):
        """Sync draft state from Yahoo."""
        try:
            # Get Yahoo client
            client = self.yahoo_integration.get_client(self.user_id, self.db)
            
            # Get current draft results
            draft_results = client.get_league_draft_results(self.league_key)
            
            if not draft_results:
                return
                
            # Check for new picks
            current_pick_count = len(draft_results)
            if current_pick_count > self._last_pick_count:
                # Process new picks
                new_picks = draft_results[self._last_pick_count:]
                self._process_new_picks(session, new_picks)
                self._last_pick_count = current_pick_count
                
            # Update session state
            league = session.league
            total_picks = league.num_teams * 15  # Assuming 15 rounds
            
            session.current_pick = current_pick_count + 1
            session.current_round = ((current_pick_count) // league.num_teams) + 1
            
            # Check if draft is complete
            if current_pick_count >= total_picks:
                session.draft_status = "completed"
                session.completed_at = datetime.utcnow()
                self._emit_draft_completed_event()
            
            # Update drafted players list
            session.drafted_players = [
                {
                    "pick": pick.get("pick"),
                    "round": pick.get("round"), 
                    "team_key": pick.get("team_key"),
                    "player_key": pick.get("player_key"),
                    "player_name": self._extract_player_name(pick)
                }
                for pick in draft_results
            ]
            
            session.last_sync = datetime.utcnow()
            self.db.commit()
            
            # Check if it's user's turn
            self._check_user_turn(session)
            
        except Exception as e:
            logger.error(f"Failed to sync draft state: {e}")
            self._create_event("sync_error", {"error": str(e)})
            raise
            
    def _process_new_picks(self, session: YahooDraftSession, new_picks: List[Dict[str, Any]]):
        """Process new draft picks."""
        for pick in new_picks:
            # Create draft event
            event = YahooDraftEvent(
                draft_session_id=session.id,
                event_type="pick_made",
                pick_number=pick.get("pick"),
                round_number=pick.get("round"),
                team_key=pick.get("team_key"),
                player_key=pick.get("player_key"),
                player_name=self._extract_player_name(pick),
                event_data=pick
            )
            self.db.add(event)
            
            # Emit WebSocket event
            self._emit_pick_event(pick, session)
            
        self.db.commit()
        
    def _extract_player_name(self, pick: Dict[str, Any]) -> str:
        """Extract player name from pick data."""
        player_data = pick.get("player", {})
        if isinstance(player_data, dict):
            name = player_data.get("name", {})
            if isinstance(name, dict):
                return name.get("full", "Unknown Player")
            return str(name)
        return "Unknown Player"
        
    def _check_user_turn(self, session: YahooDraftSession):
        """Check if it's the user's turn to pick."""
        league = session.league
        picks_until_turn = session.get_picks_until_user_turn(league.num_teams)
        
        if picks_until_turn == 0:
            # It's user's turn!
            self._emit_user_turn_event(session)
        elif picks_until_turn <= 3:
            # Almost user's turn
            self._emit_almost_turn_event(session, picks_until_turn)
            
    def _emit_pick_event(self, pick: Dict[str, Any], session: YahooDraftSession):
        """Emit WebSocket event for new pick."""
        event_data = {
            "type": "pick_made",
            "session_id": session.id,
            "pick_number": pick.get("pick"),
            "round": pick.get("round"),
            "team_key": pick.get("team_key"),
            "player_name": self._extract_player_name(pick),
            "is_user_pick": pick.get("team_key") == session.user_team_key
        }
        
        ws_manager.send_draft_event(str(session.id), event_data['type'], event_data)
        
    def _emit_user_turn_event(self, session: YahooDraftSession):
        """Emit event when it's user's turn."""
        event_data = {
            "type": "user_on_clock",
            "session_id": session.id,
            "current_pick": session.current_pick,
            "current_round": session.current_round,
            "message": "It's your turn to pick!"
        }
        
        ws_manager.send_draft_event(str(session.id), event_data['type'], event_data)
        
        # Create event record
        self._create_event("user_on_clock", event_data)
        
    def _emit_almost_turn_event(self, session: YahooDraftSession, picks_away: int):
        """Emit event when user's turn is approaching."""
        event_data = {
            "type": "turn_approaching",
            "session_id": session.id,
            "picks_away": picks_away,
            "message": f"Your turn in {picks_away} picks"
        }
        
        ws_manager.send_draft_event(str(session.id), event_data['type'], event_data)
        
    def _emit_draft_completed_event(self):
        """Emit event when draft is completed."""
        event_data = {
            "type": "draft_completed",
            "session_id": self.session_id,
            "message": "Draft has been completed!"
        }
        
        ws_manager.send_draft_event(str(session.id), event_data['type'], event_data)
        
        # Create event record
        self._create_event("draft_completed", event_data)
        
    def _emit_error_event(self, error_message: str):
        """Emit error event."""
        event_data = {
            "type": "sync_error",
            "session_id": self.session_id,
            "error": error_message
        }
        
        ws_manager.send_draft_event(str(session.id), event_data['type'], event_data)
        
    def _create_event(self, event_type: str, event_data: Dict[str, Any]):
        """Create a draft event record."""
        try:
            event = YahooDraftEvent(
                draft_session_id=self.session_id,
                event_type=event_type,
                event_data=event_data
            )
            self.db.add(event)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            self.db.rollback()