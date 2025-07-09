# Live ESPN Draft Integration Plan

## Overview
This document outlines the implementation plan for connecting the Fantasy Football Assistant to live ESPN draft data with real-time updates.

## Current State
- Basic draft session creation and management
- Manual pick entry
- AI recommendations (currently using fallback data)
- ESPN API integration for league and team data
- Draft completion detection after the fact

## Implementation Plan

### 1. Backend Polling Service
Create a background service that polls ESPN API during active drafts:

#### Components Needed:
- **Draft Monitor Service** (`src/services/draft_monitor.py`)
  - Poll ESPN draft endpoint every 5-10 seconds during active drafts
  - Detect new picks automatically
  - Update draft session state in database
  - Emit events for WebSocket broadcasting

- **Background Task Queue**
  - Use Celery or FastAPI BackgroundTasks
  - Schedule periodic checks for active draft sessions
  - Handle rate limiting and backoff strategies

#### ESPN API Endpoints Required:
```javascript
// Get current draft state
GET /seasons/{season}/segments/0/leagues/{leagueId}?view=mDraftDetail

// Response includes:
{
  draftDetail: {
    drafted: boolean,
    inProgress: boolean,
    picks: [...],
    currentPickTeam: {
      teamId: number,
      pickNumber: number
    }
  }
}
```

### 2. WebSocket Implementation (Recommended)
Add real-time communication between backend and frontend:

#### Backend WebSocket Server
- Use Socket.IO or native WebSockets
- Create rooms for each draft session
- Emit events:
  - `draft:pick_made` - New pick detected
  - `draft:user_on_clock` - User's turn to pick
  - `draft:status_changed` - Draft started/paused/completed
  - `draft:recommendation_ready` - AI recommendation generated

#### Frontend WebSocket Client
- Connect to draft session room
- Subscribe to draft events
- Update UI in real-time
- Fallback to polling if WebSocket fails

### 3. Enhanced Draft Session Management

#### Database Schema Updates:
```python
# Add to DraftSession model
draft_status = Column(Enum('not_started', 'in_progress', 'paused', 'completed'))
current_pick_team_id = Column(Integer)  # Team currently picking
pick_deadline = Column(DateTime)  # When current pick expires
last_espn_sync = Column(DateTime)  # Last successful ESPN API call
sync_errors = Column(JSON)  # Track API errors

# Add new model for draft events
class DraftEvent(Base):
    __tablename__ = "draft_events"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("draft_sessions.id"))
    event_type = Column(String)  # pick_made, draft_started, etc.
    event_data = Column(JSON)
    created_at = Column(DateTime)
```

#### Key Functions:
- `sync_draft_state()` - Fetch latest from ESPN
- `process_new_picks()` - Handle newly detected picks
- `update_available_players()` - Remove drafted players
- `check_user_on_clock()` - Determine if it's user's turn

### 4. Improved Frontend Updates

#### React Components:
- **DraftLiveTracker** - Shows current pick, timer, on-clock team
- **DraftBoard** - Real-time grid of all picks
- **AvailablePlayersList** - Updates as players are drafted
- **DraftNotifications** - Toast notifications for important events

#### Features:
- Visual countdown timer for picks
- Audio alert when user is on the clock
- Highlight recent picks
- Show pick trends (runs on positions)
- Auto-scroll to latest activity

### 5. ESPN API Integration Enhancements

#### Robust Error Handling:
```python
class ESPNDraftMonitor:
    def __init__(self):
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 2,
            'rate_limit_window': 60,  # seconds
            'max_requests_per_window': 30
        }
    
    async def fetch_draft_state(self, league_id: int, season: int):
        """Fetch with retry and rate limiting"""
        # Implement exponential backoff
        # Track API calls per minute
        # Cache responses for 5 seconds
        # Handle 401/403 auth errors
```

#### Caching Strategy:
- Redis or in-memory cache for draft state
- Cache TTL: 5 seconds during active draft
- Longer TTL (5 minutes) for completed drafts
- Invalidate cache on pick detection

### 6. Implementation Phases

#### Phase 1: Basic Polling (1-2 days)
- [ ] Create draft monitor service
- [ ] Add polling for active sessions
- [ ] Update database on pick detection
- [ ] Basic frontend polling for updates

#### Phase 2: WebSocket Integration (2-3 days)
- [ ] Set up Socket.IO server
- [ ] Create draft session rooms
- [ ] Implement real-time events
- [ ] Update frontend to use WebSockets

#### Phase 3: Enhanced Features (2-3 days)
- [ ] Add pick timer and notifications
- [ ] Implement draft board visualization
- [ ] Add audio/visual alerts
- [ ] Create draft replay feature

#### Phase 4: Production Hardening (1-2 days)
- [ ] Add comprehensive error handling
- [ ] Implement rate limiting
- [ ] Add monitoring and logging
- [ ] Create fallback mechanisms

## Technical Considerations

### Rate Limiting
- ESPN API likely has rate limits
- Implement request pooling for multiple active drafts
- Use caching to minimize API calls
- Consider user-specific API keys

### Authentication
- ESPN cookies may expire during long drafts
- Implement cookie refresh mechanism
- Handle re-authentication gracefully
- Store encrypted cookies securely

### Scalability
- Design for multiple concurrent drafts
- Use connection pooling for database
- Implement horizontal scaling for WebSockets
- Consider message queue for reliability

### Testing Strategy
- Mock ESPN API responses for development
- Create draft simulation mode
- Test with various draft scenarios
- Load test with multiple concurrent users

## Future Enhancements
- Mobile app push notifications
- Integration with draft strategy guides
- Post-draft analysis and grades
- Trade suggestions based on draft results
- Keeper league draft support

## References
- ESPN Fantasy API (unofficial): https://github.com/cwendt94/espn-api
- Socket.IO docs: https://socket.io/docs/v4/
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
- Celery for Python: https://docs.celeryproject.org/