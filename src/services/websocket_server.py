"""
WebSocket server for real-time draft updates using Socket.IO
"""

import socketio
import logging
from typing import Optional, Dict, Any, Set
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Configure appropriately for production
    logger=True,
    engineio_logger=False
)

# Store active connections and draft sessions
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[str]] = {}  # draft_session_id -> set of socket_ids
        self.user_sessions: Dict[str, str] = {}  # socket_id -> user_id
        self.draft_sessions: Dict[str, str] = {}  # socket_id -> draft_session_id
    
    def add_connection(self, socket_id: str, user_id: str, draft_session_id: str):
        """Add a new connection to a draft session"""
        # Track user session
        self.user_sessions[socket_id] = user_id
        self.draft_sessions[socket_id] = draft_session_id
        
        # Add to draft session
        if draft_session_id not in self.active_connections:
            self.active_connections[draft_session_id] = set()
        self.active_connections[draft_session_id].add(socket_id)
        
        logger.info(f"User {user_id} connected to draft session {draft_session_id}")
    
    def remove_connection(self, socket_id: str):
        """Remove a connection"""
        user_id = self.user_sessions.pop(socket_id, None)
        draft_session_id = self.draft_sessions.pop(socket_id, None)
        
        if draft_session_id and draft_session_id in self.active_connections:
            self.active_connections[draft_session_id].discard(socket_id)
            if not self.active_connections[draft_session_id]:
                del self.active_connections[draft_session_id]
        
        logger.info(f"User {user_id} disconnected from draft session {draft_session_id}")
    
    def get_session_connections(self, draft_session_id: str) -> Set[str]:
        """Get all connections for a draft session"""
        return self.active_connections.get(draft_session_id, set())

connection_manager = ConnectionManager()

# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    """Handle new client connection"""
    logger.info(f"Client connected: {sid}")
    await sio.emit('connected', {'message': 'Connected to draft server'}, to=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    connection_manager.remove_connection(sid)
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def join_draft_session(sid, data):
    """Join a draft session room"""
    try:
        user_id = data.get('user_id')
        draft_session_id = data.get('draft_session_id')
        
        if not user_id or not draft_session_id:
            await sio.emit('error', {'message': 'Missing user_id or draft_session_id'}, to=sid)
            return
        
        # Join Socket.IO room
        await sio.enter_room(sid, f"draft_{draft_session_id}")
        
        # Track connection
        connection_manager.add_connection(sid, str(user_id), str(draft_session_id))
        
        # Notify user
        await sio.emit('joined_draft', {
            'draft_session_id': draft_session_id,
            'message': f'Joined draft session {draft_session_id}'
        }, to=sid)
        
        # Notify others in the draft
        await sio.emit('user_joined', {
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"draft_{draft_session_id}", skip_sid=sid)
        
    except Exception as e:
        logger.error(f"Error joining draft session: {e}")
        await sio.emit('error', {'message': str(e)}, to=sid)

@sio.event
async def leave_draft_session(sid, data):
    """Leave a draft session room"""
    try:
        draft_session_id = data.get('draft_session_id')
        
        if draft_session_id:
            await sio.leave_room(sid, f"draft_{draft_session_id}")
            
        connection_manager.remove_connection(sid)
        
        await sio.emit('left_draft', {
            'message': 'Left draft session'
        }, to=sid)
        
    except Exception as e:
        logger.error(f"Error leaving draft session: {e}")
        await sio.emit('error', {'message': str(e)}, to=sid)

# Server-side event emitters (called by draft monitor)
async def emit_draft_update(draft_session_id: str, update_type: str, data: Dict[str, Any]):
    """Emit draft update to all connected clients in a session"""
    room = f"draft_{draft_session_id}"
    
    event_data = {
        'type': update_type,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    await sio.emit('draft_update', event_data, room=room)
    logger.info(f"Emitted {update_type} to draft session {draft_session_id}")

async def emit_pick_made(draft_session_id: str, pick_data: Dict[str, Any]):
    """Emit when a new pick is made"""
    await emit_draft_update(draft_session_id, 'pick_made', pick_data)

async def emit_user_on_clock(draft_session_id: str, user_id: str, pick_deadline: Optional[str] = None):
    """Emit when it's a user's turn to pick"""
    data = {
        'user_id': user_id,
        'pick_deadline': pick_deadline
    }
    await emit_draft_update(draft_session_id, 'user_on_clock', data)

async def emit_draft_status_change(draft_session_id: str, status: str):
    """Emit when draft status changes (paused, resumed, completed)"""
    await emit_draft_update(draft_session_id, 'status_change', {'status': status})

async def emit_sync_error(draft_session_id: str, error_message: str):
    """Emit when there's a sync error"""
    await emit_draft_update(draft_session_id, 'sync_error', {'error': error_message})

# Create ASGI app
def create_socket_app():
    """Create Socket.IO ASGI app"""
    return socketio.ASGIApp(sio, other_asgi_app=None)

# Export for use in other modules
__all__ = [
    'sio',
    'create_socket_app',
    'emit_pick_made',
    'emit_user_on_clock',
    'emit_draft_status_change',
    'emit_sync_error',
    'connection_manager'
]