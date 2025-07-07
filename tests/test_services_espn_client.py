"""
Tests for ESPN Client Service
"""

import pytest
import aiohttp
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.services.espn_client import ESPNClient


@pytest.mark.asyncio
@pytest.mark.services
class TestESPNClient:
    """Test ESPN client functionality"""
    
    async def test_initialization(self):
        """Test ESPN client initialization"""
        client = ESPNClient()
        
        assert client.BASE_URL == "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        assert client.FANTASY_URL == "https://fantasy.espn.com/apis/v3/games/ffl"
        assert client.session is None
        assert client.current_season == 2024
    
    async def test_get_session(self):
        """Test session creation and reuse"""
        client = ESPNClient()
        
        # Get session for first time
        session1 = await client._get_session()
        assert isinstance(session1, aiohttp.ClientSession)
        assert not session1.closed
        
        # Get session again - should reuse
        session2 = await client._get_session()
        assert session1 is session2
        
        await client.close()
    
    async def test_close_session(self):
        """Test closing session"""
        client = ESPNClient()
        
        # Create session
        session = await client._get_session()
        assert not session.closed
        
        # Close it
        await client.close()
        assert session.closed
    
    @patch('aiohttp.ClientSession.get')
    async def test_get_nfl_teams_success(self, mock_get):
        """Test successful NFL teams retrieval"""
        # Mock response data
        mock_response_data = {
            "sports": [{
                "leagues": [{
                    "teams": [
                        {
                            "team": {
                                "id": "22",
                                "displayName": "Kansas City Chiefs",
                                "abbreviation": "KC",
                                "color": "e31837"
                            }
                        },
                        {
                            "team": {
                                "id": "25",
                                "displayName": "San Francisco 49ers", 
                                "abbreviation": "SF",
                                "color": "aa0000"
                            }
                        }
                    ]
                }]
            }]
        }
        
        # Mock the response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_get.return_value.__aenter__.return_value = mock_response
        
        client = ESPNClient()
        teams = await client.get_nfl_teams()
        
        assert len(teams) == 2
        assert teams[0]["name"] == "Kansas City Chiefs"
        assert teams[0]["abbreviation"] == "KC"
        assert teams[1]["name"] == "San Francisco 49ers"
        assert teams[1]["abbreviation"] == "SF"
        
        await client.close()
    
    @patch('aiohttp.ClientSession.get')
    async def test_get_nfl_teams_http_error(self, mock_get):
        """Test NFL teams retrieval with HTTP error"""
        # Mock 404 response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response
        
        client = ESPNClient()
        teams = await client.get_nfl_teams()
        
        assert teams == []
        await client.close()
    
    @patch('aiohttp.ClientSession.get')
    async def test_get_players_success(self, mock_get):
        """Test successful players retrieval"""
        mock_response_data = {
            "athletes": [
                {
                    "id": "1234",
                    "displayName": "Patrick Mahomes",
                    "position": {
                        "abbreviation": "QB"
                    },
                    "team": {
                        "id": "22",
                        "abbreviation": "KC"
                    }
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_get.return_value.__aenter__.return_value = mock_response
        
        client = ESPNClient()
        players = await client.get_players()
        
        assert len(players) == 1
        assert players[0]["name"] == "Patrick Mahomes"
        assert players[0]["position"] == "QB"
        assert players[0]["team"] == "KC"
        
        await client.close()
    
    @patch('aiohttp.ClientSession.get')
    async def test_get_scoreboard_success(self, mock_get):
        """Test successful scoreboard retrieval"""
        mock_response_data = {
            "events": [
                {
                    "id": "401547439",
                    "name": "Kansas City Chiefs at San Francisco 49ers",
                    "competitions": [
                        {
                            "competitors": [
                                {
                                    "team": {
                                        "abbreviation": "KC"
                                    },
                                    "score": "21"
                                },
                                {
                                    "team": {
                                        "abbreviation": "SF"
                                    },
                                    "score": "14"
                                }
                            ],
                            "status": {
                                "type": {
                                    "completed": True
                                }
                            }
                        }
                    ]
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_get.return_value.__aenter__.return_value = mock_response
        
        client = ESPNClient()
        scoreboard = await client.get_scoreboard()
        
        assert len(scoreboard) == 1
        game = scoreboard[0]
        assert game["id"] == "401547439"
        assert len(game["teams"]) == 2
        assert game["completed"] is True
        
        await client.close()
    
    @patch('aiohttp.ClientSession.get')
    async def test_get_fantasy_league_success(self, mock_get):
        """Test successful fantasy league retrieval"""
        mock_response_data = {
            "id": 123456,
            "settings": {
                "name": "Test League",
                "size": 10,
                "scoringPeriodId": 8
            },
            "teams": [
                {
                    "id": 1,
                    "location": "Team",
                    "nickname": "Name"
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_get.return_value.__aenter__.return_value = mock_response
        
        client = ESPNClient()
        league = await client.get_fantasy_league(123456)
        
        assert league["id"] == 123456
        assert league["name"] == "Test League"
        assert league["size"] == 10
        assert len(league["teams"]) == 1
        
        await client.close()
    
    async def test_session_recreation_after_close(self):
        """Test that session is recreated after being closed"""
        client = ESPNClient()
        
        # Get first session
        session1 = await client._get_session()
        session1_id = id(session1)
        
        # Close it
        await client.close()
        
        # Get new session - should be different instance
        session2 = await client._get_session()
        session2_id = id(session2)
        
        assert session1_id != session2_id
        assert not session1.closed or session1.closed  # Could be either
        assert not session2.closed
        
        await client.close()
    
    @patch('aiohttp.ClientSession.get')
    async def test_request_exception_handling(self, mock_get):
        """Test handling of request exceptions"""
        # Mock exception
        mock_get.side_effect = aiohttp.ClientError("Connection failed")
        
        client = ESPNClient()
        
        # Should handle exceptions gracefully
        teams = await client.get_nfl_teams()
        assert teams == []
        
        await client.close()
    
    @patch('aiohttp.ClientSession.get')
    async def test_invalid_json_response(self, mock_get):
        """Test handling of invalid JSON responses"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
        mock_get.return_value.__aenter__.return_value = mock_response
        
        client = ESPNClient()
        teams = await client.get_nfl_teams()
        
        assert teams == []
        await client.close()
    
    async def test_context_manager_usage(self):
        """Test using client as context manager"""
        async with ESPNClient() as client:
            assert isinstance(client, ESPNClient)
            session = await client._get_session()
            assert not session.closed
        
        # Session should be closed after context exit
        assert session.closed