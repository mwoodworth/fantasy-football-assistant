# ESPN Fantasy Football Service

A Node.js microservice for integrating with ESPN Fantasy Football API, specifically designed to access private league data that requires ESPN authentication cookies.

## Overview

This service complements the main Python FastAPI backend by providing ESPN-specific functionality that works better with Node.js. ESPN's fantasy football API requires specific cookie authentication for private leagues, which is more reliably handled through Node.js.

## Features

- **League Information**: Get league details, settings, and standings
- **Team Management**: Access team rosters, stats, and matchup history
- **Player Data**: Fetch free agents, trending players, and player details
- **Draft Analysis**: Complete draft results, grades, and summary statistics
- **Caching**: In-memory caching to reduce ESPN API calls
- **Rate Limiting**: Configurable rate limiting to respect ESPN's API limits
- **Authentication**: API key-based authentication for secure access
- **Health Monitoring**: Comprehensive health checks and monitoring

## Quick Start

### Prerequisites

- Node.js 18.0.0 or higher
- npm or yarn
- ESPN league access (cookies for private leagues)

### Installation

```bash
# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### Configuration

Edit `.env` file with your settings:

```env
# Service Configuration
PORT=3001
NODE_ENV=development

# ESPN API Configuration
ESPN_COOKIE_S2=your_espn_s2_cookie_here
ESPN_COOKIE_SWID=your_espn_swid_cookie_here

# Security
API_KEY=your_secure_api_key_here
```

### Getting ESPN Cookies

To access private ESPN leagues, you need authentication cookies:

1. **Login to ESPN Fantasy**: Go to [ESPN Fantasy Football](https://fantasy.espn.com)
2. **Open Browser DevTools**: Press F12 or right-click → Inspect
3. **Go to Application/Storage Tab**: Look for Cookies
4. **Find ESPN Cookies**: Copy the values for:
   - `espn_s2` (long encrypted string)
   - `SWID` (shorter string with curly braces)

### Running the Service

```bash
# Development mode (with auto-reload)
npm run dev

# Production mode
npm start

# Run tests
npm test
```

The service will start on `http://localhost:3001`

## API Documentation

### Base URL
```
http://localhost:3001
```

### Authentication
Include your API key in requests:
```bash
curl -H "X-API-Key: your_api_key" http://localhost:3001/api/leagues/123456
```

### Endpoints

#### Health & Status
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with dependency checks
- `GET /health/espn` - ESPN API connectivity test
- `GET /health/cache` - Cache status and statistics

#### League Information
- `GET /api/leagues/:leagueId` - Get league details
- `GET /api/leagues/:leagueId/settings` - Get league settings
- `GET /api/leagues/:leagueId/teams` - Get all teams
- `GET /api/leagues/:leagueId/standings` - Get league standings
- `GET /api/leagues/:leagueId/scoreboard` - Get scoreboard
- `GET /api/leagues/:leagueId/free-agents` - Get available free agents

#### Team Management
- `GET /api/teams/:teamId/roster` - Get team roster
- `GET /api/teams/:teamId/stats` - Get team statistics
- `GET /api/teams/:teamId/matchups` - Get team matchup history
- `GET /api/teams/compare` - Compare two teams

#### Player Data
- `GET /api/players/free-agents` - Get available free agents
- `GET /api/players/trending` - Get trending players
- `GET /api/players/search` - Search players by name
- `GET /api/players/by-position/:position` - Get players by position

#### Draft Information
- `GET /api/draft/:leagueId` - Get draft results
- `GET /api/draft/:leagueId/picks` - Get draft picks (filterable)
- `GET /api/draft/:leagueId/grades` - Get draft grades by team
- `GET /api/draft/:leagueId/summary` - Get draft summary statistics

### Example Requests

```bash
# Get league information
curl -H "X-API-Key: your_key" \
  "http://localhost:3001/api/leagues/123456?season=2024"

# Get team roster
curl -H "X-API-Key: your_key" \
  "http://localhost:3001/api/teams/1/roster?leagueId=123456&week=8"

# Get free agents
curl -H "X-API-Key: your_key" \
  "http://localhost:3001/api/players/free-agents?leagueId=123456&position=RB&limit=20"

# Get draft results
curl -H "X-API-Key: your_key" \
  "http://localhost:3001/api/draft/123456/grades"
```

### Response Format

All successful responses follow this format:
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "leagueId": 123456,
    "timestamp": "2024-01-05T12:00:00.000Z"
  }
}
```

Error responses:
```json
{
  "error": "Error description",
  "status": 400,
  "timestamp": "2024-01-05T12:00:00.000Z",
  "path": "/api/leagues/123456"
}
```

## Integration with Python Service

This Node.js service is designed to work alongside the main Python FastAPI backend:

### Architecture
```
Frontend/CLI → Python FastAPI (Port 6001) ⟷ Node.js ESPN Service (Port 3001) → ESPN API
```

### Python Integration Example
```python
import httpx

class ESPNService:
    def __init__(self):
        self.base_url = "http://localhost:3001"
        self.api_key = os.getenv("ESPN_SERVICE_API_KEY")
    
    async def get_league_data(self, league_id: int):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/leagues/{league_id}",
                headers={"X-API-Key": self.api_key}
            )
            return response.json()
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PORT` | Service port | 3001 | No |
| `NODE_ENV` | Environment | development | No |
| `ESPN_COOKIE_S2` | ESPN S2 cookie | - | Yes* |
| `ESPN_COOKIE_SWID` | ESPN SWID cookie | - | Yes* |
| `API_KEY` | Service API key | - | Yes** |
| `RATE_LIMIT_WINDOW_MS` | Rate limit window | 900000 | No |
| `RATE_LIMIT_MAX_REQUESTS` | Max requests per window | 100 | No |
| `CACHE_TTL_MINUTES` | Cache TTL | 15 | No |
| `ENABLE_CACHING` | Enable caching | true | No |

\* Required for private league access  
\** Required for production, optional in development

### Rate Limiting

Default rate limits:
- **Window**: 15 minutes
- **Requests**: 100 per window per IP
- **Headers**: Standard rate limit headers included

### Caching

- **Type**: In-memory cache
- **TTL**: 15 minutes (configurable)
- **Cleanup**: Automatic every 5 minutes
- **Cache Keys**: Based on method, URL, and query parameters

## Development

### Project Structure
```
espn-service/
├── src/
│   ├── routes/          # API route handlers
│   ├── middleware/      # Express middleware
│   ├── utils/          # Utilities and ESPN client
│   └── server.js       # Main server file
├── logs/               # Log files
├── package.json        # Dependencies and scripts
└── README.md          # This file
```

### Adding New Endpoints

1. **Create route handler** in `src/routes/`
2. **Add validation** using Joi schemas
3. **Update server.js** to include the new route
4. **Add tests** (when test framework is set up)
5. **Update documentation**

### ESPN API Notes

- **Rate Limits**: ESPN has undocumented rate limits
- **Authentication**: Private leagues require valid cookies
- **Data Structure**: ESPN's data structure can be complex and nested
- **Caching**: Recommended to cache responses to reduce API calls

### Troubleshooting

#### Common Issues

**401 Unauthorized**
- Check ESPN cookies are valid and not expired
- Ensure league is accessible with provided credentials

**404 Not Found**
- Verify league ID is correct
- Check if league exists for the specified season

**503 Service Unavailable**
- ESPN API may be down or experiencing issues
- Check `/health/espn` endpoint for connectivity

#### Debugging

Enable debug logging:
```bash
LOG_LEVEL=debug npm run dev
```

Check health endpoints:
```bash
curl http://localhost:3001/health/detailed
```

## Contributing

1. Follow existing code style and patterns
2. Add appropriate error handling
3. Include input validation
4. Update documentation
5. Test with real ESPN data when possible

## License

MIT License - see LICENSE file for details

## Support

For issues related to:
- **ESPN API changes**: Check ESPN's fantasy football documentation
- **Service bugs**: Create an issue in the repository  
- **Integration**: Refer to the main Python service documentation