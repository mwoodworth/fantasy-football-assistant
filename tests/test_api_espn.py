"""
Tests for ESPN API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.mark.api
@pytest.mark.espn
class TestESPNAPI:
    """Test ESPN integration endpoints"""
    
    def test_health_check(self, test_client: TestClient):
        """Test ESPN service health check"""
        with patch('src.services.espn_integration.ESPNServiceClient') as mock_client_class:
            # Create a mock client instance
            mock_client = AsyncMock()
            mock_client.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_client.espn_connectivity_check = AsyncMock(return_value={"status": "connected"})
            
            # Make the client class return our mock instance
            mock_client_class.return_value = mock_client
            
            response = test_client.get("/api/espn/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "espn_service" in data
            assert "espn_api" in data
    
    def test_validate_espn_cookies(self, test_client: TestClient):
        """Test ESPN cookie validation"""
        cookie_data = {
            "espn_s2": "test_s2_cookie",
            "swid": "test_swid_cookie"
        }
        
        with patch('src.services.espn_integration.espn_service') as mock_service:
            # Create a mock client that supports async context manager
            mock_client = AsyncMock()
            mock_client.validate_espn_cookies = AsyncMock(return_value={"valid": True})
            
            # Make the client property return our mock
            mock_service.client = mock_client
            
            response = test_client.post("/api/espn/auth/validate-cookies", json=cookie_data)
            
            assert response.status_code == 200
    
    def test_get_cookie_status(self, test_client: TestClient):
        """Test getting ESPN cookie status"""
        with patch('src.services.espn_integration.espn_service') as mock_service:
            mock_service.client.__aenter__ = AsyncMock()
            mock_service.client.__aexit__ = AsyncMock()
            mock_service.client.get_cookie_status = AsyncMock(return_value={"configured": False})
            
            response = test_client.get("/api/espn/auth/cookie-status")
            
            assert response.status_code == 200
    
    def test_get_league_info(self, test_client: TestClient, auth_headers):
        """Test getting ESPN league information"""
        with patch('src.services.espn_integration.espn_service') as mock_service:
            mock_service.get_cached_or_fetch = AsyncMock(return_value={
                "id": 12345,
                "name": "Test League",
                "size": 10
            })
            
            response = test_client.get("/api/espn/leagues/12345", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
    
    def test_get_league_teams(self, test_client: TestClient, auth_headers):
        """Test getting ESPN league teams"""
        with patch('src.services.espn_integration.espn_service') as mock_service:
            mock_service.get_cached_or_fetch = AsyncMock(return_value=[
                {"id": 1, "name": "Team 1"},
                {"id": 2, "name": "Team 2"}
            ])
            
            response = test_client.get("/api/api/espn/leagues/12345/teams", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2
    
    def test_get_free_agents(self, test_client: TestClient, auth_headers):
        """Test getting ESPN free agents"""
        with patch('src.services.espn_integration.espn_service') as mock_service:
            mock_service.get_cached_or_fetch = AsyncMock(return_value=[
                {"id": 1, "name": "Free Agent 1", "position": "QB"},
                {"id": 2, "name": "Free Agent 2", "position": "RB"}
            ])
            
            response = test_client.get("/api/api/espn/leagues/12345/free-agents", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2
    
    def test_get_team_roster(self, test_client: TestClient, auth_headers):
        """Test getting ESPN team roster"""
        with patch('src.services.espn_integration.espn_service') as mock_service:
            mock_service.get_cached_or_fetch = AsyncMock(return_value={
                "entries": [
                    {"player": {"id": 1, "name": "Player 1", "position": "QB"}},
                    {"player": {"id": 2, "name": "Player 2", "position": "RB"}}
                ]
            })
            
            response = test_client.get("/api/espn/teams/1/roster?league_id=12345", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_search_players(self, test_client: TestClient, auth_headers):
        """Test searching ESPN players"""
        with patch('src.services.espn_integration.espn_service') as mock_service:
            mock_service.get_cached_or_fetch = AsyncMock(return_value=[
                {"id": 1, "name": "Josh Allen", "position": "QB"},
                {"id": 2, "name": "Christian McCaffrey", "position": "RB"}
            ])
            
            response = test_client.get("/api/espn/players/search?league_id=12345&name=josh", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2
    
    def test_clear_espn_cache(self, test_client: TestClient, auth_headers):
        """Test clearing ESPN cache"""
        with patch('src.services.espn_integration.espn_service') as mock_service:
            mock_service.clear_cache = AsyncMock()
            
            response = test_client.delete("/api/espn/cache", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_espn_service_error_handling(self, test_client: TestClient, auth_headers):
        """Test ESPN service error handling"""
        from src.services.espn_integration import ESPNServiceError
        
        with patch('src.services.espn_integration.espn_service') as mock_service:
            mock_service.get_cached_or_fetch = AsyncMock(side_effect=ESPNServiceError("ESPN API error"))
            
            response = test_client.get("/api/espn/leagues/12345", headers=auth_headers)
            
            assert response.status_code == 400
            assert "ESPN API error" in response.json()["detail"]
    
    def test_espn_auth_error_handling(self, test_client: TestClient, auth_headers):
        """Test ESPN authentication error handling"""
        from src.services.espn_integration import ESPNAuthError
        
        with patch('src.services.espn_integration.espn_service') as mock_service:
            mock_service.get_cached_or_fetch = AsyncMock(side_effect=ESPNAuthError("Authentication failed"))
            
            response = test_client.get("/api/espn/leagues/12345", headers=auth_headers)
            
            assert response.status_code == 401
            data = response.json()
            assert data["detail"]["requires_auth_update"] is True
    
    def test_unauthorized_access(self, test_client: TestClient):
        """Test accessing ESPN endpoints without authentication"""
        response = test_client.get("/api/espn/leagues/12345")
        
        assert response.status_code == 401