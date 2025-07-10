#!/usr/bin/env python3
"""
Test ESPN league API with multiple views
"""

import asyncio
import httpx
import json

async def test_league_views():
    """Test the league endpoint with multiple views"""
    
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
        "x-fantasy-filter": '{"players":{}}',
        "x-fantasy-platform": "kona-PROD-9488cfa0d0fb59d75804777bfee76c2f161a89b1",
        "x-fantasy-source": "kona",
        "referer": "https://fantasy.espn.com/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    # Test with multiple views
    params = {
        "view": ["mSettings", "mTeam", "modular", "mNav"]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                print("\n=== RESPONSE STRUCTURE ===")
                print(f"Top-level keys: {list(data.keys())}")
                
                # Analyze settings
                if 'settings' in data:
                    settings = data['settings']
                    print(f"\nSettings keys: {list(settings.keys())}")
                    
                    if 'rosterSettings' in settings:
                        roster = settings['rosterSettings']
                        print(f"\nRoster positions:")
                        if 'lineupSlotCounts' in roster:
                            for slot_id, count in roster['lineupSlotCounts'].items():
                                print(f"  Slot {slot_id}: {count} positions")
                    
                    if 'scoringSettings' in settings:
                        scoring = settings['scoringSettings']
                        print(f"\nScoring type: {scoring.get('scoringType', 'Unknown')}")
                        print(f"Points per reception: {scoring.get('receivingSettings', {}).get('receivingReception', 0)}")
                
                # Analyze teams
                if 'teams' in data:
                    teams = data['teams']
                    print(f"\n\nTotal teams: {len(teams)}")
                    for i, team in enumerate(teams[:3]):
                        print(f"\nTeam {i+1}:")
                        print(f"  ID: {team.get('id')}")
                        print(f"  Name: {team.get('name', 'Unnamed')}")
                        print(f"  Abbreviation: {team.get('abbrev', 'N/A')}")
                        print(f"  Owner: {team.get('owners', ['No owner'])[0]}")
                        
                        # Check roster
                        if 'roster' in team:
                            roster = team['roster']
                            print(f"  Roster entries: {len(roster.get('entries', []))}")
                
                # Analyze members (users)
                if 'members' in data:
                    members = data['members']
                    print(f"\n\nLeague members: {len(members)}")
                    for member in members[:3]:
                        print(f"  - {member.get('displayName', 'Unknown')} (ID: {member.get('id')})")
                
                # Analyze status
                if 'status' in data:
                    status = data['status']
                    print(f"\n\nLeague Status:")
                    print(f"  Current matchup period: {status.get('currentMatchupPeriod')}")
                    print(f"  Is active: {status.get('isActive')}")
                    print(f"  Latest scoring period: {status.get('latestScoringPeriod')}")
                
                # Save full response
                with open('league_views_response.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("\n\nFull response saved to league_views_response.json")
                
            else:
                print(f"Error response: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_league_views())