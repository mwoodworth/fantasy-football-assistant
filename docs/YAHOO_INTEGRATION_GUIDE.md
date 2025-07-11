# Yahoo Fantasy Integration Guide

This guide explains how to set up and use the Yahoo Fantasy integration in the Fantasy Football Assistant.

## Prerequisites

Before you can use Yahoo Fantasy integration, you need to:

1. **Create a Yahoo App**
   - Go to [Yahoo Developer Network](https://developer.yahoo.com/apps/)
   - Click "Create an App"
   - Fill in the application details:
     - Application Name: "Fantasy Football Assistant" (or your preferred name)
     - Application Type: "Web Application"
     - Redirect URI: `http://localhost:8000/api/yahoo/auth/callback` (for local development)
     - API Permissions: Select "Fantasy Sports" and choose "Read" permission
   - After creation, you'll receive a Client ID and Client Secret

2. **Configure Environment Variables**
   Add the following to your `.env` file:
   ```env
   YAHOO_CLIENT_ID=your_client_id_here
   YAHOO_CLIENT_SECRET=your_client_secret_here
   YAHOO_REDIRECT_URI=http://localhost:8000/api/yahoo/auth/callback
   ```

## Features

The Yahoo Fantasy integration provides:

### League Management
- Import all your Yahoo fantasy football leagues
- View league settings, scoring, and rosters
- Track league standings and transactions
- Sync league data for offline analysis

### Team Tracking
- Monitor all teams in your leagues
- View detailed roster information
- Track team performance metrics
- Identify waiver wire opportunities

### Player Data
- Search players across Yahoo's database
- View ownership percentages and trends
- Get injury reports and status updates
- Compare players across platforms (Yahoo vs ESPN)

### Cross-Platform Analysis
- Unified player data across Yahoo and ESPN
- Standardized scoring projections
- Combined waiver wire recommendations
- Platform-agnostic trade analysis

## User Flow

1. **Initial Connection**
   - Navigate to "Yahoo Leagues" in the sidebar
   - Click "Connect Yahoo Account"
   - You'll be redirected to Yahoo to authorize the app
   - After authorization, you'll be redirected back to the app

2. **League Import**
   - Your Yahoo leagues will automatically load
   - Click on any league to view details
   - Use the "Sync" button to update league data

3. **Data Integration**
   - Yahoo player data is automatically mapped to standard format
   - Players are matched with ESPN data when available
   - Combined analysis available in Teams and AI Assistant pages

## API Endpoints

### Authentication
- `GET /api/yahoo/auth/url` - Get OAuth authorization URL
- `GET /api/yahoo/auth/callback` - Handle OAuth callback
- `GET /api/yahoo/auth/status` - Check authentication status
- `POST /api/yahoo/auth/disconnect` - Disconnect Yahoo account

### Leagues
- `GET /api/yahoo/leagues` - Get all user leagues
- `GET /api/yahoo/leagues/{league_key}` - Get league details
- `GET /api/yahoo/leagues/{league_key}/teams` - Get league teams
- `POST /api/yahoo/leagues/{league_key}/sync` - Sync league data

### Teams & Players
- `GET /api/yahoo/teams/{team_key}/roster` - Get team roster
- `GET /api/yahoo/leagues/{league_key}/players/search` - Search players
- `GET /api/yahoo/leagues/{league_key}/free-agents` - Get available players

### Transactions & Draft
- `GET /api/yahoo/leagues/{league_key}/transactions` - Get league transactions
- `GET /api/yahoo/leagues/{league_key}/draft` - Get draft results

## Data Mapping

Yahoo player data is mapped to our standard format:

```typescript
{
  player_id: yahoo_player_key,
  name: full_name,
  position: primary_position,
  team: editorial_team_abbr,
  ownership: {
    percentage_owned: percent_owned,
    change: ownership_delta
  },
  points: {
    total: season_total,
    average: points_per_game
  },
  source: 'yahoo'
}
```

## Security Considerations

- OAuth tokens are encrypted before storage
- Tokens are automatically refreshed when expired
- Only read permissions are requested
- No changes are made to Yahoo leagues
- Users can disconnect at any time

## Troubleshooting

### Common Issues

1. **"Not authenticated with Yahoo" error**
   - Ensure you've connected your Yahoo account
   - Check if your token has expired
   - Try disconnecting and reconnecting

2. **Empty league list**
   - Verify you have active leagues for the current season
   - Check that your app has Fantasy Sports permissions
   - Ensure you're logged into the correct Yahoo account

3. **Sync failures**
   - Check your internet connection
   - Verify Yahoo's API is accessible
   - Review server logs for specific error messages

### Rate Limiting

Yahoo enforces rate limits on their API:
- 20,000 requests per hour per app
- Some endpoints have lower limits
- The app implements caching to minimize requests

## Development Notes

### Adding New Features

When extending Yahoo integration:

1. Update the `YahooFantasyClient` for new API calls
2. Add corresponding methods to `YahooIntegrationService`
3. Create new API endpoints in `src/api/yahoo.py`
4. Update frontend services and components
5. Add appropriate error handling and caching

### Testing

To test Yahoo integration:
1. Use a test Yahoo account with sample leagues
2. Mock API responses for unit tests
3. Test OAuth flow with different scenarios
4. Verify data mapping accuracy
5. Check error handling for API failures