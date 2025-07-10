#!/usr/bin/env python3
"""
Test script to verify ESPN projection data collection
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append('.')

# Set environment variables
os.environ['DATABASE_URL'] = 'sqlite:///./fantasy_football.db'

from src.services.player_sync import PlayerSyncService

async def test_projection_sync():
    print('🎯 Testing ESPN 2025 Projection Data Collection')
    print('='*60)
    
    # Test Trevor Lawrence (id from your example)
    test_players = [
        {"name": "Trevor Lawrence", "id": 4362887},  # QB
        {"name": "Josh Allen", "id": 3917792},      # QB
        {"name": "Christian McCaffrey", "id": 3045147}  # RB
    ]
    
    for test_player in test_players:
        print(f'\n🔍 Testing {test_player["name"]} (ID: {test_player["id"]})')
        
        try:
            # Fetch enhanced data with projections
            player_data = await PlayerSyncService.fetch_enhanced_player_data(
                test_player["id"], 
                include_stats=True
            )
            
            if player_data and "stats" in player_data:
                print(f'✅ Found player data: {player_data.get("fullName", "Unknown")}')
                
                # Look for 2025 projections
                season_projections = []
                week_projections = []
                
                for stat in player_data["stats"]:
                    if stat.get("seasonId") == 2025:
                        applied_total = stat.get("appliedTotal", 0)
                        scoring_period = stat.get("scoringPeriodId", 0)
                        stat_source = stat.get("statSourceId", 0)
                        
                        if stat_source == 1:  # Projections
                            if scoring_period == 0:  # Season projection
                                season_projections.append({
                                    "id": stat.get("id"),
                                    "points": applied_total,
                                    "type": "Season Total"
                                })
                            elif scoring_period > 0:  # Weekly projection
                                week_projections.append({
                                    "id": stat.get("id"),
                                    "week": scoring_period,
                                    "points": applied_total,
                                    "type": f"Week {scoring_period}"
                                })
                
                if season_projections:
                    print(f'📊 Season Projections Found:')
                    for proj in season_projections:
                        print(f'    {proj["type"]}: {proj["points"]:.1f} points (ID: {proj["id"]})')
                
                if week_projections:
                    print(f'📅 Weekly Projections Found:')
                    for proj in week_projections[:3]:  # Show first 3 weeks
                        print(f'    {proj["type"]}: {proj["points"]:.1f} points (ID: {proj["id"]})')
                
                if not season_projections and not week_projections:
                    print('⚠️  No 2025 projections found')
                    
            else:
                print(f'❌ No player data found for {test_player["name"]}')
                
        except Exception as e:
            print(f'❌ Error testing {test_player["name"]}: {e}')
    
    print('\n' + '='*60)
    print('🎯 Projection Test Complete!')

if __name__ == '__main__':
    asyncio.run(test_projection_sync())