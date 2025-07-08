#!/usr/bin/env python3
"""Get live roster for michael's Magnificent Team"""

import sys
sys.path.append('.')

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.espn_league import ESPNLeague
from src.config import settings
from src.api.teams import get_live_espn_roster, get_mock_espn_roster
import json

async def main():
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Get the league info for League 730253008
    league_id = 730253008
    league = db.query(ESPNLeague).filter(
        ESPNLeague.espn_league_id == league_id
    ).first()

    if not league:
        print(f"League {league_id} not found in database")
        return

    print(f"Team: {league.user_team_name}")
    print(f"League: {league.league_name} (ID: {league.espn_league_id})")
    print(f"ESPN Team ID: {league.user_team_id}")
    print(f"Season: {league.season}")
    print(f"Scoring: {league.scoring_type}")
    print("=" * 60)

    # Check if cookies are available
    has_cookies = bool(league.espn_s2 and league.swid)
    print(f"ESPN Cookies Available: {has_cookies}")
    
    if has_cookies:
        print(f"ESPN S2 Cookie: {'*' * (len(league.espn_s2) - 10)}...{league.espn_s2[-10:]}")
        print(f"SWID Cookie: {'*' * (len(league.swid) - 6)}...{league.swid[-6:]}")
    else:
        print("ESPN Cookies: Not set - will use mock data")
    
    print("\n" + "=" * 60)

    # Try to get live roster data
    try:
        if has_cookies:
            print("🔄 Fetching LIVE roster from ESPN...")
            roster = await get_live_espn_roster(
                league.espn_league_id,
                league.user_team_id,
                league.season,
                league.espn_s2,
                league.swid
            )
            print("✅ Successfully fetched live roster from ESPN!")
            roster_type = "LIVE ESPN DATA"
        else:
            print("⚠️  No ESPN cookies found, using mock roster data...")
            roster = get_mock_espn_roster(league.scoring_type or "PPR")
            roster_type = "MOCK DATA (for testing)"
    except Exception as e:
        print(f"❌ Error fetching live roster: {e}")
        print("🔄 Falling back to mock roster data...")
        roster = get_mock_espn_roster(league.scoring_type or "PPR")
        roster_type = "MOCK DATA (fallback)"

    # Display roster
    print(f"\n🏈 ROSTER - {roster_type}")
    print(f"📊 Total Players: {len(roster)}")
    print("=" * 80)
    
    # Separate starters and bench
    starters = [p for p in roster if p.get('status') == 'starter']
    bench = [p for p in roster if p.get('status') != 'starter']
    
    print(f"\n🔥 STARTING LINEUP ({len(starters)} players):")
    print("-" * 80)
    for player in starters:
        injury_status = player.get('injury_status', 'ACTIVE')
        status_emoji = "🚑" if injury_status not in ['ACTIVE', 'Healthy'] else "✅"
        
        print(f"{status_emoji} {player['name']:<22} {player['position']:>3} {player['team']:>3} │ "
              f"Points: {player.get('points', 0):>6.1f} │ "
              f"Proj: {player.get('projected_points', 0):>5.1f} │ "
              f"{injury_status}")
    
    print(f"\n🪑 BENCH ({len(bench)} players):")
    print("-" * 80)
    for player in bench:
        injury_status = player.get('injury_status', 'ACTIVE')
        status_emoji = "🚑" if injury_status not in ['ACTIVE', 'Healthy'] else "📋"
        
        print(f"{status_emoji} {player['name']:<22} {player['position']:>3} {player['team']:>3} │ "
              f"Points: {player.get('points', 0):>6.1f} │ "
              f"Proj: {player.get('projected_points', 0):>5.1f} │ "
              f"{injury_status}")
    
    # Calculate totals
    total_points = sum(p.get('points', 0) for p in roster)
    total_projected = sum(p.get('projected_points', 0) for p in roster)
    starter_points = sum(p.get('points', 0) for p in starters)
    
    print("\n" + "=" * 80)
    print(f"📈 TEAM TOTALS:")
    print(f"   Total Season Points: {total_points:>8.1f}")
    print(f"   Starting Lineup:     {starter_points:>8.1f}")
    print(f"   Total Projected:     {total_projected:>8.1f}")
    
    print(f"\n📋 ROSTER BREAKDOWN:")
    positions = {}
    for player in roster:
        pos = player['position']
        if pos not in positions:
            positions[pos] = 0
        positions[pos] += 1
    
    for pos, count in sorted(positions.items()):
        print(f"   {pos}: {count} players")
    
    db.close()

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())