# ESPN Fantasy Football Integration

This document explains how to use the ESPN Fantasy Football authentication and data integration features.

## Quick Start

### 1. Start All Services
```bash
./start.sh
```

This will automatically:
- Set up Python virtual environment
- Install Python dependencies 
- Install Node.js ESPN service dependencies
- Start both Python FastAPI (port 6001) and Node.js ESPN service (port 3001)

### 2. Access the Application
- **Main App**: http://localhost:6001
- **API Docs**: http://localhost:6001/api/docs  
- **ESPN Login**: http://localhost:6001/static/espn-login.html
- **Health Check**: http://localhost:6001/health

## ESPN Authentication

### Option 1: Web Interface (Recommended)
1. Visit http://localhost:6001/static/espn-login.html
2. Enter your ESPN email and password
3. Click "Login to ESPN"
4. Copy the returned cookies to your `.env` file

### Option 2: API Endpoints

**Check Cookie Status:**
```bash
curl "http://localhost:6001/api/espn/auth/cookie-status"
```

**Login to ESPN:**
```bash
curl -X POST "http://localhost:6001/api/espn/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@espn.com", "password": "your-password"}'
```

**Validate Cookies:**
```bash
curl -X POST "http://localhost:6001/api/espn/auth/validate-cookies" \
  -H "Content-Type: application/json" \
  -d '{"espn_s2": "your-cookie", "swid": "your-swid"}'
```

## ESPN Data Endpoints

Once authenticated, you can access ESPN fantasy data:

```bash
# Get league information
curl -H "X-API-Key: your_secure_api_key_here" \
  "http://localhost:6001/api/espn/leagues/1870083331?season=2025"

# Get league teams
curl -H "X-API-Key: your_secure_api_key_here" \
  "http://localhost:6001/api/espn/leagues/1870083331/teams?season=2025"

# Search for players
curl -H "X-API-Key: your_secure_api_key_here" \
  "http://localhost:6001/api/espn/players/search?league_id=1870083331&name=mahomes"
```

## Configuration

### Environment Variables (.env)
```bash
# ESPN Service Configuration
ESPN_SERVICE_URL="http://localhost:3001"
ESPN_COOKIE_S2="your-espn-s2-cookie"
ESPN_COOKIE_SWID="your-swid-cookie"

# API Authentication
API_KEY="your_secure_api_key_here"
```

### ESPN Service (.env in espn-service/)
```bash
# ESPN API Configuration
ESPN_COOKIE_S2="your-espn-s2-cookie-value"
ESPN_COOKIE_SWID="{your-swid-cookie-value}"

# Security
API_KEY="your_secure_api_key_here"
```

## Architecture

The system consists of two services:

1. **Python FastAPI Service** (port 6001)
   - Main application API
   - User authentication
   - Database management  
   - Proxies requests to ESPN service

2. **Node.js ESPN Service** (port 3001)
   - ESPN API integration
   - Cookie-based authentication
   - Private league access
   - Data transformation

## Private League Access

To access private ESPN leagues, you need:

1. **ESPN Cookies**: Use the login endpoint to get `espn_s2` and `SWID` cookies
2. **League ID**: Found in your ESPN league URL
3. **Season**: The NFL season year (e.g., 2025)

## Troubleshooting

### ESPN Service Not Starting
- Ensure Node.js 18+ is installed: `node --version`
- Check for port conflicts: `lsof -i :3001`
- Review logs in the terminal output

### Authentication Issues
- Verify cookies are correctly set in `.env` files
- Test cookies with the validation endpoint
- Check if cookies have expired (re-login if needed)

### API Errors
- Verify API key is correctly configured
- Check service health: `curl http://localhost:6001/health`
- Review logs for detailed error messages

## Development

### Manual Service Management

**Start Python service only:**
```bash
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 6001 --reload
```

**Start ESPN service only:**
```bash
cd espn-service
npm run dev
```

**Stop all services:**
```bash
pkill -f "uvicorn.*main:app"
pkill -f "node.*espn-service"
```