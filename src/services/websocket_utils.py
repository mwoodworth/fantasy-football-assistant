"""WebSocket utility functions for Yahoo draft integration."""

import logging
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manager for WebSocket communications in synchronous contexts."""
    
    @staticmethod
    def send_draft_event(draft_session_id: str, event_type: str, data: Dict[str, Any]):
        """Send draft event through WebSocket (synchronous wrapper)."""
        try:
            from .websocket_server import sio
            
            # Create event data - flatten the structure
            event_data = {
                **data,
                'session_id': draft_session_id
            }
            
            # Use asyncio to run the async emit in sync context
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                # Schedule the coroutine to run in the existing loop
                asyncio.create_task(
                    sio.emit('draft_update', event_data, room=f"draft_{draft_session_id}")
                )
            else:
                # Run the coroutine in the loop
                loop.run_until_complete(
                    sio.emit('draft_update', event_data, room=f"draft_{draft_session_id}")
                )
                
            logger.info(f"Sent {event_type} event for draft session {draft_session_id}")
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket event: {e}")
            # Don't crash the draft monitor if WebSocket fails
    
    @staticmethod
    def send_user_notification(user_id: str, event_type: str, data: Dict[str, Any]):
        """Send notification to specific user."""
        try:
            from .websocket_server import emit_to_user
            
            # Use asyncio to run the async function
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                asyncio.create_task(emit_to_user(str(user_id), event_type, data))
            else:
                loop.run_until_complete(emit_to_user(str(user_id), event_type, data))
                
            logger.info(f"Sent {event_type} notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send user notification: {e}")

# Global instance for easy access
ws_manager = WebSocketManager()