# Dynamic Trade Targets Implementation Plan

## Overview
Replace hardcoded trade targets with dynamic system that:
1. Syncs and caches all ESPN league teams in database
2. Generates real trade recommendations based on actual team rosters and needs
3. Implements caching with 5-day refresh logic
4. Adds manual refresh button for users

## Phase 1: Database Models for League Teams & Trade Cache

### 1.1 Create New Models
- **`ESPNTeam`** model to store all teams in a league:
  - Fields: `id`, `espn_league_id`, `espn_team_id`, `team_name`, `owner_name`, `record`, `points_for`, `points_against`, `roster_data` (JSON), `last_synced`, `is_active`
  
- **`TradeRecommendation`** model to cache recommendations:
  - Fields: `id`, `user_team_id`, `target_player_id`, `target_team_id`, `suggested_offer` (JSON), `rationale`, `trade_value`, `likelihood`, `generated_at`, `expires_at`

### 1.2 Database Migration
- Create migration file for new tables
- Add relationships to existing `ESPNLeague` model

## Phase 2: ESPN Team Sync Service

### 2.1 Team Sync Implementation
- Create `sync_league_teams()` function in `espn_integration.py`:
  - Call `get_league_teams()` to fetch all teams
  - Call `get_team_roster()` for each team to get current rosters
  - Store team data and rosters in `ESPNTeam` table
  - Update sync timestamps

### 2.2 Automated Sync Triggers
- Add sync logic to existing league connection workflow
- Implement background sync task (daily/weekly)
- Add manual sync endpoint for user-triggered refresh

## Phase 3: Dynamic Trade Analysis Engine

### 3.1 Roster Analysis
- Create `analyze_team_needs()` function:
  - Evaluate roster strengths/weaknesses by position
  - Calculate position depth scores
  - Identify surplus players (tradeable assets)

### 3.2 Trade Opportunity Detection
- Create `find_trade_opportunities()` function:
  - Compare user team needs vs other teams' surplus
  - Match complementary needs (e.g., user needs RB, other team has RB surplus but needs WR)
  - Calculate fair trade value using position scarcity and player rankings

### 3.3 Recommendation Generation
- Create `generate_trade_recommendations()` function:
  - Use roster analysis to identify optimal trades
  - Generate realistic multi-player trade packages
  - Create rationale based on actual team needs
  - Score likelihood based on team circumstances

## Phase 4: Caching & Refresh Logic

### 4.1 Cache Management
- Implement 5-day expiration logic for recommendations
- Create `refresh_trade_recommendations()` function
- Add cache invalidation when rosters change

### 4.2 UI Integration
- Add "Refresh Recommendations" button to Trade Center
- Show last updated timestamp
- Display loading states during generation

## Phase 5: API Endpoint Updates

### 5.1 Update Trade Targets Endpoint
Replace current hardcoded logic in `/teams/{team_id}/trade-targets`:
```python
# New logic:
1. Check if cached recommendations exist and are valid (< 5 days old)
2. If cache invalid or missing:
   - Sync league teams if needed
   - Analyze team needs
   - Generate new recommendations
   - Cache results
3. Return cached recommendations
```

### 5.2 Add Manual Refresh Endpoint
- `POST /teams/{team_id}/trade-targets/refresh`
- Force regeneration of recommendations
- Return new recommendations immediately

## Phase 6: Frontend Integration

### 6.1 Teams Page Updates
- Add refresh button to Trade Center
- Show "Last updated: X days ago" 
- Display loading spinner during refresh
- Handle refresh API calls

### 6.2 Enhanced Trade Display
- Show real team names from synced data
- Display actual roster analysis context
- Add more detailed rationale based on real needs

## Implementation Files to Create/Modify

### New Files:
- `src/models/espn_team.py` - Team and recommendation models
- `src/services/team_sync.py` - Team synchronization logic  
- `src/services/trade_analyzer.py` - Trade analysis engine
- Database migration for new tables

### Modified Files:
- `src/api/teams.py` - Update trade targets endpoint
- `src/services/espn_integration.py` - Add team sync methods
- `frontend/src/pages/TeamsPage.tsx` - Add refresh functionality
- `frontend/src/services/teams.ts` - Add refresh API call

## Benefits of This Approach

1. **Real Data**: Uses actual league teams and rosters instead of mock data
2. **Intelligent Analysis**: Recommendations based on actual roster needs and team situations  
3. **Performance**: Caching reduces API calls and improves response times
4. **Freshness**: 5-day expiration ensures recommendations stay current
5. **User Control**: Manual refresh gives users control over when to update
6. **Scalable**: Can be extended to more sophisticated trade analysis algorithms

## Technical Considerations

- **ESPN API Rate Limits**: Implement proper rate limiting for team sync
- **Data Consistency**: Handle cases where ESPN data changes between syncs
- **Error Handling**: Graceful fallback to cached data if sync fails
- **Background Processing**: Consider async background tasks for large leagues
- **Memory Usage**: Efficient JSON storage for roster data

## Implementation Phases Timeline

### Phase 1: Database Foundation (Day 1)
- Create database models
- Generate migration files
- Test database schema

### Phase 2: ESPN Integration (Day 2-3)
- Implement team sync service
- Add API endpoints for syncing
- Test with real ESPN data

### Phase 3: Trade Analysis (Day 4-5)
- Build roster analysis engine
- Implement trade opportunity detection
- Create recommendation algorithms

### Phase 4: Caching & Performance (Day 6)
- Implement caching logic
- Add refresh mechanisms
- Optimize database queries

### Phase 5: API Updates (Day 7)
- Update existing endpoints
- Add new refresh endpoints
- Test API integration

### Phase 6: Frontend Integration (Day 8)
- Update UI components
- Add refresh functionality
- Test end-to-end workflow

## Success Criteria

✅ **Phase 1 Complete**: Database models created and tested  
✅ **Phase 2 Complete**: ESPN team data successfully synced and stored  
✅ **Phase 3 Complete**: Dynamic trade recommendations generated based on real data  
✅ **Phase 4 Complete**: Caching system working with 5-day expiration  
✅ **Phase 5 Complete**: API endpoints updated and tested  
✅ **Phase 6 Complete**: Frontend shows real trade recommendations with refresh capability  

## Future Enhancements

- **Advanced Analytics**: Include player trends, injury data, schedule analysis
- **Trade Value Calculator**: More sophisticated player valuation algorithms
- **Multi-Team Trades**: Support for 3+ team trade scenarios
- **Trade History**: Track success rate of past recommendations
- **Machine Learning**: Learn from user trade preferences and success patterns