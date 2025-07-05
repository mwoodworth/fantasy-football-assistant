# Mock Data System for Fantasy Football Assistant

This document describes the mock data system that enables testing of all Phase 2 features without requiring real NFL data or ESPN API integration.

## Overview

The mock data system generates realistic NFL data including:
- 32 NFL teams with proper divisions and conferences
- ~200 mock players across all positions (QB, RB, WR, TE, K, DEF)
- Weekly statistics for the current season
- A test fantasy league with 10 users
- Sample rosters for testing all features

## Quick Start

### 1. Generate Mock Data

```bash
# Using the CLI tool (recommended)
cd /home/mwoodworth/code/my-projects/fantasy-football-assistant
python src/cli/mock_data_cli.py seed

# Or using the script
python scripts/seed_mock_data.py
```

### 2. Start the Server

```bash
python -m src.main
```

### 3. Test the Features

```bash
# Test all Phase 2 features
python scripts/test_mock_features.py

# Or use the API directly
curl http://localhost:6001/api/mock-data/status
```

## Mock Data CLI Tool

The CLI tool provides comprehensive mock data management:

### Commands

```bash
# Seed database with mock data
python src/cli/mock_data_cli.py seed

# Show current database status
python src/cli/mock_data_cli.py status

# List players (with optional position filter)
python src/cli/mock_data_cli.py players --position QB --limit 10

# Show player statistics
python src/cli/mock_data_cli.py stats --week 8

# Clear all data
python src/cli/mock_data_cli.py clear

# Test database connection
python src/cli/mock_data_cli.py test-connection
```

### Example Output

```
🏈 Players - QB
============================================================
 1. Josh Allen        QB  BUF  156.7 pts
 2. Lamar Jackson     QB  BAL  142.3 pts
 3. Jalen Hurts       QB  PHI  138.9 pts
 4. Joe Burrow        QB  CIN  135.2 pts
 5. Justin Herbert    QB  LAC  132.1 pts
```

## Test Data Structure

### Test User Credentials
- **Email**: test@example.com
- **Username**: testuser
- **Password**: test_password_hash

### Generated Data
- **Teams**: All 32 NFL teams with proper divisions
- **Players**: Realistic distribution across positions
- **Stats**: 8 weeks of mock statistics
- **League**: 10-team PPR league
- **Rosters**: Sample roster for main test user

## Testing Phase 2 Features

### Draft Assistant
```python
from services.draft_assistant import DraftAssistant

# Get draft board
draft_board = draft_assistant.get_draft_board(50)

# Get recommendations for specific pick
recommendations = draft_assistant.get_draft_recommendations(
    team_id=1, pick_number=15, round_number=2
)
```

### Lineup Optimizer
```python
from services.lineup_optimizer import LineupOptimizer

# Optimize lineup
optimal_lineup = lineup_optimizer.optimize_lineup(
    team_id=1, week=8, locked_players=[], excluded_players=[]
)

# Get start/sit recommendations
start_sit = lineup_optimizer.get_start_sit_recommendations(
    team_id=1, week=8, position="RB"
)
```

### Waiver Wire Analyzer
```python
from services.waiver_analyzer import WaiverAnalyzer

# Get waiver recommendations
waiver_recs = waiver_analyzer.get_waiver_recommendations(
    team_id=1, week=8, position="WR", limit=10
)

# Get trending players
trending = waiver_analyzer.get_trending_players(limit=5)
```

### Trade Analyzer
```python
from services.trade_analyzer import TradeAnalyzer

# Evaluate trade
evaluation = trade_analyzer.evaluate_trade(
    team1_id=1, team1_sends=[player1_id], team1_receives=[player2_id],
    team2_id=2, team2_sends=[player2_id], team2_receives=[player1_id]
)

# Get trade targets
targets = trade_analyzer.suggest_trade_targets(
    team_id=1, position_needed="RB", max_players_to_send=2
)
```

## API Testing

### Authentication
```bash
# Register user
curl -X POST "http://localhost:6001/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newuser",
    "password": "password123",
    "first_name": "New",
    "last_name": "User"
  }'

# Login
curl -X POST "http://localhost:6001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test_password_hash"
  }'
```

### Player Data
```bash
# Get QB rankings
curl "http://localhost:6001/api/players/rankings/QB?scoring_type=ppr&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get player stats
curl "http://localhost:6001/api/players/1/stats?recent_weeks=4" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Fantasy Features
```bash
# Get draft board
curl "http://localhost:6001/api/fantasy/draft/1/board?top_n=100" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Optimize lineup
curl -X POST "http://localhost:6001/api/fantasy/lineup/optimize" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "fantasy_team_id": 1,
    "week": 8,
    "locked_players": [],
    "excluded_players": []
  }'
```

## Mock Data Details

### Player Generation
- **Realistic Names**: Position-appropriate player names
- **Team Assignment**: Random but balanced distribution
- **Physical Attributes**: Position-specific height, weight, age ranges
- **Injury Status**: Weighted random injury statuses
- **Bye Weeks**: Proper NFL bye week schedule

### Statistics Generation
- **Position-Specific Stats**: Realistic stat ranges for each position
- **Weekly Variance**: Natural week-to-week fluctuation
- **Injury Impact**: Injured players miss games realistically
- **Fantasy Scoring**: Proper calculation for standard, PPR, and half-PPR

### Fantasy Calculations
- **VOR (Value Over Replacement)**: Proper positional value calculations
- **Tier Analysis**: Players grouped into performance tiers
- **Consistency Metrics**: Variance analysis for reliability
- **Matchup Factors**: Simulated opponent strength

## Troubleshooting

### Database Issues
```bash
# Clear and regenerate data
python src/cli/mock_data_cli.py clear
python src/cli/mock_data_cli.py seed

# Check database status
python src/cli/mock_data_cli.py status
```

### Feature Testing
```bash
# Run comprehensive test suite
python scripts/test_mock_features.py

# Test specific service
python -c "
from src.models.database import SessionLocal
from src.services.draft_assistant import DraftAssistant
from src.models.fantasy import League

db = SessionLocal()
league = db.query(League).first()
assistant = DraftAssistant(db, league)
board = assistant.get_draft_board(10)
print(f'Draft board has {len(board)} players')
"
```

## Next Steps

While the mock data system provides comprehensive testing capabilities, the next phase involves:

1. **Node.js ESPN Service**: Create separate service for ESPN API integration
2. **Real Data Integration**: Replace mock data with live NFL statistics
3. **Data Synchronization**: Implement regular updates from ESPN
4. **Advanced Analytics**: Add more sophisticated player analysis

The mock data system ensures all Phase 2 features work correctly and provides a solid foundation for real data integration.