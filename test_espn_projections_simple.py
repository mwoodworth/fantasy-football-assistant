#!/usr/bin/env python3
"""
Simple test of ESPN projection endpoints without complex imports
"""

import asyncio
import httpx
import json

async def test_espn_projections():
    print('🎯 Testing ESPN 2025 Projection Data')
    print('=' * 50)
    
    # The league endpoint that includes projections
    url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leagues/730253008"
    
    headers = {
        "accept": "application/json",
        "x-fantasy-platform": "kona-PROD-9488cfa0d0fb59d75804777bfee76c2f161a89b1",
        "x-fantasy-source": "kona",
        "referer": "https://fantasy.espn.com/"
    }
    
    params = {
        "scoringPeriodId": 1,
        "view": "kona_player_info"
    }
    
    # Use the exact filter from your working example
    filter_obj = {
        "players": {
            "filterStatus": {"value": ["FREEAGENT", "WAIVERS"]},
            "filterSlotIds": {"value": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 23, 24]},
            "filterRanksForScoringPeriodIds": {"value": [1]},
            "limit": 50,
            "offset": 0,
            "sortAppliedStatTotal": {"sortAsc": False, "sortPriority": 1, "value": "102025"},
            "sortDraftRanks": {"sortPriority": 100, "sortAsc": True, "value": "STANDARD"},
            "filterRanksForRankTypes": {"value": ["PPR"]},
            "filterRanksForSlotIds": {"value": [0, 2, 4, 6, 17, 16, 8, 9, 10, 12, 13, 24, 11, 14, 15]},
            "filterStatsForTopScoringPeriodIds": {"value": 2, "additionalValue": ["002025", "102025", "002024", "1120251", "022025"]}
        }
    }
    headers["x-fantasy-filter"] = json.dumps(filter_obj)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "players" not in data:
                print("❌ No players found in response")
                return
            
            print(f"✅ Found {len(data['players'])} players")
            print()
            
            # Process each player
            projection_count = 0
            for player_entry in data['players']:
                player = player_entry.get('player', {})
                name = player.get('fullName', 'Unknown')
                position = player.get('defaultPositionId', 0)
                
                # Position mapping
                pos_map = {0: "QB", 2: "RB", 4: "WR", 6: "TE"}
                pos_name = pos_map.get(position, f"Pos{position}")
                
                # Look for 2025 projections in stats
                stats = player.get('stats', [])
                season_projection = None
                week1_projection = None
                
                for stat in stats:
                    if stat.get('seasonId') == 2025 and stat.get('statSourceId') == 1:
                        applied_total = stat.get('appliedTotal', 0)
                        if stat.get('scoringPeriodId') == 0:  # Season projection
                            season_projection = applied_total
                        elif stat.get('scoringPeriodId') == 1:  # Week 1 projection
                            week1_projection = applied_total
                
                if season_projection and season_projection > 0:
                    print(f"🏈 {name} ({pos_name})")
                    print(f"    2025 Season: {season_projection:.1f} points")
                    if week1_projection and week1_projection > 0:
                        print(f"    Week 1: {week1_projection:.1f} points")
                    print()
                    projection_count += 1
            
            print(f"📊 Found projections for {projection_count} players")
            
            if projection_count == 0:
                print("⚠️  No 2025 projections found - checking data structure...")
                # Debug: show first player's structure
                if data['players']:
                    first_player = data['players'][0]['player']
                    print(f"Sample player: {first_player.get('fullName', 'Unknown')}")
                    print(f"Stats count: {len(first_player.get('stats', []))}")
                    
                    for i, stat in enumerate(first_player.get('stats', [])[:3]):
                        print(f"  Stat {i}: season={stat.get('seasonId')}, "
                              f"period={stat.get('scoringPeriodId')}, "
                              f"source={stat.get('statSourceId')}, "
                              f"total={stat.get('appliedTotal', 0)}")
                              
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    asyncio.run(test_espn_projections())