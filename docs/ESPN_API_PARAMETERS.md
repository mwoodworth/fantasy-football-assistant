# ESPN Fantasy Football API Parameters Documentation

## Base URL Structure
```
https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/{segment}/leagues/{leagueId}
```

### Path Parameters
- `season`: The year of the fantasy season (e.g., 2025)
- `segment`: Always 0 for regular season
- `leagueId`: The ESPN league ID (e.g., 730253008)

## Query Parameters - Views

The `view` parameter determines what data is included in the response. Multiple views can be combined in a single request.

### League & Settings Views
- **`mSettings`**: League settings including:
  - `acquisitionSettings`: Waiver/FA settings (acquisition type, budget, process days)
  - `draftSettings`: Draft configuration (date, type, pick order)
  - `rosterSettings`: Roster positions and lineup slot counts
  - `scoringSettings`: Scoring system (H2H, points, categories) and point values per stat
  - `scheduleSettings`: Number of regular season weeks, playoff weeks
  - `tradeSettings`: Trade deadline, review period, veto settings
  
- **`mTeam`**: Team information including:
  - Basic info: team ID, name, abbreviation, logo
  - Owner information and IDs
  - Record: wins, losses, ties, points for/against
  - Playoff seed and final standing
  - Current roster (requires roster view)
  
- **`modular`**: Provides structured league data
  - Navigation elements
  - Current period information
  - League metadata
  
- **`mNav`**: Navigation data including:
  - Current week/period
  - Season dates
  - League navigation options

### Player Views
- **`kona_player_info`**: Detailed player information with ownership and trending data
- **`players_wl`**: Player waiver list view

### Draft Views
- **`mDraftDetail`**: Detailed draft information including all picks
- **`mLiveScoring`**: Live scoring data for current matchups
- **`mMatchup`**: Matchup details for specific weeks

### Transaction Views
- **`mTransactions2`**: Recent transactions (adds, drops, trades)
- **`mPendingTransactions`**: Pending trades and waiver claims

### Standings & Stats Views
- **`mStandings`**: League standings
- **`mSchedule`**: Full season schedule
- **`mRoster`**: Detailed roster information
- **`mMatchupScore`**: Scoring details for matchups

## Headers

### Required Headers
```javascript
{
  "accept": "application/json",
  "x-fantasy-platform": "kona-PROD-{buildHash}",
  "x-fantasy-source": "kona"
}
```

### Optional Headers
- **`x-fantasy-filter`**: JSON string for filtering results
- **`cache-control`**: Cache control directives
- **`referer`**: https://fantasy.espn.com/

## X-Fantasy-Filter Parameter

The `x-fantasy-filter` header accepts a JSON string with various filtering options:

### Player Filters
```json
{
  "players": {
    "limit": 50,                    // Number of players to return
    "offset": 0,                    // Pagination offset
    "sortPercOwned": {              // Sort by ownership percentage
      "sortAsc": false,
      "sortPriority": 1
    },
    "sortPercChanged": {            // Sort by ownership change
      "sortAsc": false,
      "sortPriority": 1
    },
    "filterSlotIds": {              // Filter by roster slot
      "value": [0, 2, 4, 6, 17, 16]  // QB, RB, WR, TE, K, D/ST
    },
    "filterStatus": {               // Filter by player status
      "value": ["FREEAGENT", "WAIVERS", "ONTEAM"]
    },
    "filterProTeamIds": {           // Filter by NFL team
      "value": [1, 2, 3]           // Team IDs
    },
    "filterRanksForSlotIds": {      // Rankings filter
      "value": [0, 2, 4, 6, 17, 16]
    },
    "filterStatsForTopScoringPeriodIds": {  // Stats filter
      "value": 2,
      "additionalValue": ["002025", "102025", "002024", "022025"]
    }
  }
}
```

### Common Slot IDs
- 0: QB
- 2: RB
- 4: WR
- 6: TE
- 7: FLEX
- 16: D/ST
- 17: K
- 20: Bench
- 21: IR

### Common Pro Team IDs
```
0: Free Agent
1: ATL, 2: BUF, 3: CHI, 4: CIN, 5: CLE
6: DAL, 7: DEN, 8: DET, 9: GB, 10: TEN
11: IND, 12: KC, 13: LV, 14: LAR, 15: MIA
16: MIN, 17: NE, 18: NO, 19: NYG, 20: NYJ
21: PHI, 22: ARI, 23: PIT, 24: LAC, 25: SF
26: SEA, 27: TB, 28: WSH, 29: CAR, 30: JAX
33: BAL, 34: HOU
```

## Response Headers

ESPN includes useful metadata in response headers:

- **`X-Fantasy-Filter-Player-Count`**: Total number of players matching filter
- **`X-Fantasy-Server-Time`**: Server timestamp
- **`X-Fantasy-Role`**: User's role in the league
- **`etag`**: For caching

## Example API Calls

### Get League Info with Settings and Teams
```javascript
fetch("https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leagues/730253008?view=mSettings&view=mTeam&view=modular&view=mNav", {
  headers: {
    "accept": "application/json",
    "x-fantasy-platform": "kona-PROD-{hash}",
    "x-fantasy-source": "kona"
  }
});
```

### Get Trending Players
```javascript
fetch("https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leagues/730253008?view=kona_player_info", {
  headers: {
    "accept": "application/json",
    "x-fantasy-filter": '{"players":{"limit":25,"sortPercChanged":{"sortPriority":1,"sortAsc":false}}}',
    "x-fantasy-platform": "kona-PROD-{hash}",
    "x-fantasy-source": "kona"
  }
});
```

### Get Available Players by Position
```javascript
fetch("https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leagues/730253008?view=kona_player_info", {
  headers: {
    "accept": "application/json",
    "x-fantasy-filter": '{"players":{"filterSlotIds":{"value":[2]},"filterStatus":{"value":["FREEAGENT"]},"limit":50}}',
    "x-fantasy-platform": "kona-PROD-{hash}",
    "x-fantasy-source": "kona"
  }
});
```

## Additional Views and Endpoints

### Season-Level Views
- **`kona_game_state`**: Global season information including:
  - Current scoring period
  - League creation settings
  - Client feature flags (ESPN_PLUS_ENABLED, IBM_TRADE_ASSISTANT, etc.)
  - Draft schedule settings and available times
  - Season dates and matchup overrides
  - Notification settings

### Player Card Views
- **`kona_playercard`**: Enhanced player data including:
  - Detailed stats with variance calculations
  - Draft rankings by rank type (STANDARD, PPR)
  - Injury details with expected return dates
  - Historical performance data
  - Ownership trends and auction values

## HTTP Methods Support

The ESPN API supports multiple HTTP methods:
- **GET**: Retrieve data (primary method)
- **POST**: Create new entries (requires authentication)
- **PUT**: Update existing entries (requires authentication)
- **DELETE**: Remove entries (requires authentication)
- **OPTIONS**: Check API capabilities and CORS settings

## CORS Configuration

The API has permissive CORS settings:
- `access-control-allow-origin: *` - Accepts requests from any origin
- `access-control-allow-credentials: true` - Supports authenticated requests
- `access-control-max-age: 600` - Preflight responses cached for 10 minutes

## ESPN Free Agency Recommendations API

ESPN provides AI-powered free agency recommendations through authenticated endpoints. This feature can enhance our fantasy assistant with ESPN's own recommendation engine.

### Endpoint Structure
```
GET /apis/v3/games/ffl/seasons/{season}/segments/{segment}/leagues/{leagueId}/teams/{teamId}/recommendations
```

### Parameters
- `recommendationTypeId`: Type of recommendation (e.g., "FREEAGENCY")
- `view`: Data view (e.g., "recommend")

### Authentication Requirements
- **ESPN_S2 Cookie**: Session authentication token
- **SWID Cookie**: User identifier
- **Team Ownership**: User must own or have access to the specified team

### Implementation Strategy

#### Phase 1: Authentication Setup
1. **Cookie Collection**: Implement ESPN login flow to collect session cookies
2. **Session Management**: Store and refresh ESPN_S2 and SWID tokens securely
3. **Team Verification**: Validate user access to specific teams

#### Phase 2: API Integration
```python
async def get_espn_recommendations(
    league_id: int, 
    team_id: int, 
    espn_s2: str, 
    swid: str,
    recommendation_type: str = "FREEAGENCY"
):
    headers = {
        "Cookie": f"ESPN_S2={espn_s2}; SWID={swid}",
        "x-fantasy-platform": "kona-PROD-{hash}",
        "x-fantasy-source": "kona"
    }
    
    params = {
        "recommendationTypeId": recommendation_type,
        "view": "recommend"
    }
    
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leagues/{league_id}/teams/{team_id}/recommendations"
    
    # Make authenticated request
    response = await client.get(url, headers=headers, params=params)
    return response.json()
```

#### Phase 3: Data Processing
- **Recommendation Parsing**: Extract player suggestions and reasoning
- **Integration**: Combine with our AI recommendations for enhanced insights
- **Comparison**: Show both ESPN and our AI recommendations side-by-side

#### Phase 4: User Experience
- **Authentication Flow**: Secure ESPN login within our app
- **Recommendation Dashboard**: Display ESPN recommendations alongside our analysis
- **Hybrid Recommendations**: Merge ESPN data with our ML models

### Security Considerations
- Store ESPN cookies securely (encrypted)
- Implement token refresh mechanisms
- Respect ESPN's terms of service and rate limits
- Never log or expose user credentials

### Benefits
- **Official ESPN Insights**: Access ESPN's proprietary recommendation algorithms
- **Enhanced Accuracy**: Combine multiple data sources for better recommendations
- **User Trust**: Leverage ESPN's established fantasy expertise
- **Competitive Advantage**: Offer unique insights not available elsewhere

## Notes

1. **Authentication**: Private leagues require ESPN_S2 and SWID cookies
2. **Rate Limiting**: ESPN may rate limit requests, implement appropriate delays
3. **Data Freshness**: Player ownership data updates periodically (not real-time)
4. **Platform Hash**: The platform hash in headers changes with ESPN updates
5. **Feature Flags**: The `kona_game_state` view reveals active ESPN features and experiments
6. **Write Operations**: POST/PUT/DELETE methods are available but require proper authentication and permissions
7. **Recommendations**: ESPN's free agency recommendations require team ownership authentication