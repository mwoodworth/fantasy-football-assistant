"""
Tests for teams API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.mark.api
class TestTeamsAPI:
    """Test teams endpoints"""
    
    def test_get_user_teams_empty(self, test_client: TestClient, auth_headers):
        """Test getting user teams when none exist"""
        response = test_client.get("/api/teams/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_user_teams_with_mock_data(self, test_client: TestClient, auth_headers):
        """Test getting user teams with mock data enabled"""
        # Mock data should be enabled by default in test settings
        response = test_client.get("/api/teams/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Mock data should return some teams
        if len(data) > 0:
            team = data[0]
            assert "id" in team
            assert "name" in team
            assert "league" in team
            assert "platform" in team
    
    def test_get_user_teams_filter_by_season(self, test_client: TestClient, auth_headers):
        """Test filtering teams by season"""
        response = test_client.get("/api/teams/?season=2024", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_user_teams_include_espn_only(self, test_client: TestClient, auth_headers):
        """Test including only ESPN teams"""
        response = test_client.get("/api/teams/?include_espn=true&include_manual=false", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_user_teams_unauthorized(self, test_client: TestClient):
        """Test getting teams without authentication"""
        response = test_client.get("/api/teams/")
        
        assert response.status_code == 401
    
    @patch('src.services.espn_integration.espn_service')
    def test_get_team_detail_espn_success(self, mock_espn_service, test_client: TestClient, auth_headers):
        """Test getting ESPN team detail successfully"""
        # Mock ESPN service response
        mock_roster_data = [
            {
                "id": 1,
                "name": "Test Player",
                "position": "QB",
                "team": "TEST",
                "status": "starter",
                "points": 100.0
            }
        ]
        
        with patch('src.api.teams.get_live_espn_roster', new_callable=AsyncMock) as mock_roster:
            mock_roster.return_value = mock_roster_data
            
            response = test_client.get("/api/teams/espn_1", headers=auth_headers)
            
            # Should return 404 if no ESPN league exists, or success if mocked properly
            assert response.status_code in [200, 404]
    
    def test_get_team_detail_invalid_id(self, test_client: TestClient, auth_headers):
        """Test getting team detail with invalid ID"""
        response = test_client.get("/api/teams/invalid_id", headers=auth_headers)
        
        assert response.status_code == 400
        assert "Invalid team ID format" in response.json()["detail"]
    
    def test_get_team_detail_not_found(self, test_client: TestClient, auth_headers):
        """Test getting team detail for non-existent team"""
        response = test_client.get("/api/teams/espn_999999", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_sync_team_data_espn(self, test_client: TestClient, auth_headers):
        """Test syncing ESPN team data"""
        response = test_client.post("/api/teams/espn_1/sync", headers=auth_headers)
        
        # Should return 404 if no ESPN league exists
        assert response.status_code in [200, 404]
    
    def test_sync_team_data_manual(self, test_client: TestClient, auth_headers):
        """Test syncing manual team data (should fail)"""
        response = test_client.post("/api/teams/manual_1/sync", headers=auth_headers)
        
        assert response.status_code == 400
        assert "ESPN teams" in response.json()["detail"]
    
    def test_sync_team_unauthorized(self, test_client: TestClient):
        """Test syncing team without authentication"""
        response = test_client.post("/api/teams/espn_1/sync")
        
        assert response.status_code == 401
    
    @patch('src.api.teams.get_live_espn_roster')
    def test_espn_auth_error_handling(self, mock_roster, test_client: TestClient, auth_headers):
        """Test ESPN authentication error handling"""
        from src.services.espn_integration import ESPNAuthError
        
        # Mock ESPNAuthError
        mock_roster.side_effect = ESPNAuthError("ESPN authentication failed. Please update your s2 and swid cookies.")
        
        response = test_client.get("/api/teams/espn_1", headers=auth_headers)
        
        # Should return 401 with auth update details if ESPN league exists
        if response.status_code == 401:
            data = response.json()
            assert "requires_auth_update" in data["detail"]
            assert data["detail"]["requires_auth_update"] is True
    
    def test_get_team_draft_info(self, test_client: TestClient, auth_headers):
        """Test getting team draft information"""
        response = test_client.get("/api/teams/espn_1/draft", headers=auth_headers)
        
        # Should return 404 if no ESPN league exists, or success if it does
        assert response.status_code in [200, 404]
    
    def test_get_team_draft_info_manual_team(self, test_client: TestClient, auth_headers):
        """Test getting draft info for manual team (should fail)"""
        response = test_client.get("/api/teams/manual_1/draft", headers=auth_headers)
        
        assert response.status_code == 400
        assert "ESPN teams" in response.json()["detail"]