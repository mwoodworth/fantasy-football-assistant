#!/usr/bin/env python3
"""
Test ESPN league-specific player endpoint
"""

import asyncio
import httpx
import json

async def test_league_players():
    """Test the league-specific player endpoint"""
    
    url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leagues/730253008"
    
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-fantasy-filter": '{"players":{"filterSlotIds":null,"sortPercChanged":{"sortPriority":1,"sortAsc":true},"limit":25,"filterRanksForSlotIds":{"value":[0,2,4,6,17,16,8,9,10,12,13,24,11,14,15]},"filterStatsForTopScoringPeriodIds":{"value":2,"additionalValue":["002025","102025","002024","022025"]}}}',
        "x-fantasy-platform": "kona-PROD-9488cfa0d0fb59d75804777bfee76c2f161a89b1",
        "x-fantasy-source": "kona",
        "referer": "https://fantasy.espn.com/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    params = {
        "view": "kona_player_info"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            print(f"Status code: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we got player data
                if 'players' in data:
                    players = data['players']
                    print(f"\nTotal players returned: {len(players)}")
                    
                    # Show first few players
                    print("\nFirst 5 players:")
                    for i, player in enumerate(players[:5]):
                        print(f"\n{i+1}. Player ID: {player.get('id')}")
                        print(f"   Name: {player.get('fullName', 'N/A')}")
                        
                        # Player info
                        player_info = player.get('player', {})
                        if player_info:
                            print(f"   Position: {player_info.get('defaultPositionId', 'N/A')}")
                            print(f"   Team: {player_info.get('proTeamId', 'N/A')}")
                            print(f"   Ownership: {player_info.get('ownership', {}).get('percentOwned', 0):.1f}%")
                            print(f"   Percent Change: {player_info.get('ownership', {}).get('percentChange', 0):.2f}%")
                            
                            # Stats
                            stats = player_info.get('stats', [])
                            if stats:
                                print(f"   Stats entries: {len(stats)}")
                        
                        # Ratings if available
                        ratings = player.get('ratings', {})
                        if ratings:
                            print(f"   Ratings: {ratings}")
                    
                    # Analyze the structure
                    print("\n\nData structure analysis:")
                    print(f"Top-level keys: {list(data.keys())}")
                    
                    if players:
                        first_player = players[0]
                        print(f"\nPlayer object keys: {list(first_player.keys())}")
                        
                        if 'player' in first_player:
                            print(f"\nNested player object keys: {list(first_player['player'].keys())}")
                
                else:
                    print("\nNo 'players' key in response")
                    print(f"Response keys: {list(data.keys())}")
                    
                # Save full response for analysis
                with open('league_players_response.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("\nFull response saved to league_players_response.json")
                
            else:
                print(f"Error response: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_league_players())