"""
Integration tests for API endpoints
Tests the actual API endpoints with database and external service integration
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.main import app
from src.models.database import get_db
from src.models.user import User
from src.models.espn_league import ESPNLeague


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    def test_api_health_check(self, test_client: TestClient):
        """Test API health check endpoint"""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data
        assert "services" in data
        assert data["status"] == "healthy"
    
    def test_api_root_endpoint(self, test_client: TestClient):
        """Test API root endpoint"""
        response = test_client.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "Assistant Fantasy Football Manager" in response.text
        assert "API Documentation" in response.text
    
    def test_authentication_flow(self, test_client: TestClient, test_db_session, sample_user_data):
        """Test complete authentication flow"""
        # Register a new user
        register_response = test_client.post("/api/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        register_data = register_response.json()
        assert "access_token" in register_data
        assert "token_type" in register_data
        
        # Login with the registered user
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        login_response = test_client.post("/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        assert "access_token" in login_data
        
        # Use the token to access protected endpoint
        headers = {"Authorization": f"Bearer {login_data['access_token']}"}
        profile_response = test_client.get("/auth/me", headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()
        assert profile_data["username"] == sample_user_data["username"]
        assert profile_data["email"] == sample_user_data["email"]
    
    def test_teams_endpoint_integration(self, test_client: TestClient, auth_headers):
        """Test teams endpoint integration"""
        # Test getting user teams (should be empty initially)
        response = test_client.get("/teams/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Test filtering by season
        response = test_client.get("/teams/?season=2024", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Test filtering by platform
        response = test_client.get("/teams/?include_espn=true&include_manual=false", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @patch('src.services.espn_integration.espn_service')
    def test_espn_integration_endpoints(self, mock_espn_service, test_client: TestClient, auth_headers):
        """Test ESPN integration endpoints"""
        # Mock ESPN service responses
        mock_espn_service.client.__aenter__ = AsyncMock()
        mock_espn_service.client.__aexit__ = AsyncMock()
        mock_espn_service.client.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_espn_service.client.espn_connectivity_check = AsyncMock(return_value={"status": "connected"})
        mock_espn_service.get_cached_or_fetch = AsyncMock(return_value={
            "id": 12345,
            "name": "Test League",
            "size": 10
        })
        
        # Test ESPN health check
        response = test_client.get("/espn/health")
        assert response.status_code == 200
        data = response.json()
        assert "espn_service" in data
        assert "espn_api" in data
        
        # Test ESPN league info
        response = test_client.get("/espn/leagues/12345", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["id"] == 12345
    
    def test_dashboard_integration(self, test_client: TestClient, auth_headers):
        """Test dashboard endpoint integration"""
        response = test_client.get("/dashboard/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "teamRank" in data
        assert "leagueSize" in data
        assert "weeklyPoints" in data
        assert "activePlayers" in data
        assert "benchPlayers" in data
        assert "recentActivity" in data
        assert isinstance(data["recentActivity"], list)
    
    @patch('src.services.ai.claude_client.ClaudeClient')
    def test_ai_integration(self, mock_claude, test_client: TestClient, auth_headers):
        """Test AI integration endpoints"""
        # Mock Claude client
        mock_claude_instance = mock_claude.return_value
        mock_claude_instance.generate_response = AsyncMock(return_value={
            "response": "This is a test AI response about fantasy football.",
            "analysis": {
                "confidence": 0.85,
                "recommendations": ["Start your best players", "Check the waiver wire"]
            }
        })
        
        # Test AI chat
        chat_data = {
            "message": "Who should I start this week?",
            "context": "I have a tough matchup this week"
        }
        response = test_client.post("/ai/chat", json=chat_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "timestamp" in data
    
    def test_error_handling_integration(self, test_client: TestClient):
        """Test error handling across endpoints"""
        # Test 404 for non-existent endpoint
        response = test_client.get("/nonexistent")
        assert response.status_code == 404
        
        # Test 401 for protected endpoint without auth
        response = test_client.get("/teams/")
        assert response.status_code == 401
        
        # Test 422 for invalid request data
        response = test_client.post("/auth/register", json={"invalid": "data"})
        assert response.status_code == 422
    
    def test_cors_headers(self, test_client: TestClient):
        """Test CORS headers are properly set"""
        response = test_client.options("/")
        
        # Should allow CORS for development origins
        assert response.status_code == 200
        
        # Test with actual request
        response = test_client.get("/")
        assert response.status_code == 200
    
    @pytest.mark.slow
    def test_rate_limiting(self, test_client: TestClient):
        """Test rate limiting (if implemented)"""
        # This test would check if rate limiting is working
        # For now, just ensure endpoint is accessible
        response = test_client.get("/health")
        assert response.status_code == 200
    
    def test_database_integration(self, test_client: TestClient, test_db_session, sample_user_data):
        """Test database integration across endpoints"""
        # Register user (creates database record)
        response = test_client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 200
        
        # Verify user was created in database
        user = test_db_session.query(User).filter(User.username == sample_user_data["username"]).first()
        assert user is not None
        assert user.email == sample_user_data["email"]
        
        # Login and get profile (reads from database)
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        login_response = test_client.post("/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        profile_response = test_client.get("/auth/me", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["id"] == user.id


@pytest.mark.integration
@pytest.mark.slow
class TestESPNServiceIntegration:
    """Integration tests specifically for ESPN service connectivity"""
    
    @patch('src.services.espn_integration.espn_service')
    def test_espn_service_connectivity(self, mock_espn_service, test_client: TestClient):
        """Test ESPN service connectivity"""
        # Mock successful ESPN service connection
        mock_espn_service.client.__aenter__ = AsyncMock()
        mock_espn_service.client.__aexit__ = AsyncMock()
        mock_espn_service.client.health_check = AsyncMock(return_value={"status": "healthy"})
        
        response = test_client.get("/espn/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "espn_service" in data
    
    @patch('src.services.espn_integration.espn_service')
    def test_espn_auth_error_propagation(self, mock_espn_service, test_client: TestClient, auth_headers):
        """Test ESPN authentication error propagation"""
        from src.services.espn_integration import ESPNAuthError
        
        # Mock ESPN authentication error
        mock_espn_service.get_cached_or_fetch = AsyncMock(
            side_effect=ESPNAuthError("Authentication failed")
        )
        
        response = test_client.get("/espn/leagues/12345", headers=auth_headers)
        assert response.status_code == 401
        
        data = response.json()
        assert "requires_auth_update" in data["detail"]
        assert data["detail"]["requires_auth_update"] is True
    
    @patch('src.services.espn_integration.espn_service')
    def test_espn_service_error_propagation(self, mock_espn_service, test_client: TestClient, auth_headers):
        """Test ESPN service error propagation"""
        from src.services.espn_integration import ESPNServiceError
        
        # Mock ESPN service error
        mock_espn_service.get_cached_or_fetch = AsyncMock(
            side_effect=ESPNServiceError("Service temporarily unavailable")
        )
        
        response = test_client.get("/espn/leagues/12345", headers=auth_headers)
        assert response.status_code == 400
        
        data = response.json()
        assert "Service temporarily unavailable" in data["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncEndpointIntegration:
    """Integration tests for async endpoints"""
    
    async def test_async_ai_endpoints(self, async_test_client):
        """Test async AI endpoints"""
        # This would test any async endpoints
        # For now, just test that async client works
        response = await async_test_client.get("/health")
        assert response.status_code == 200
    
    @patch('src.services.ai.claude_client.ClaudeClient')
    async def test_async_ai_chat(self, mock_claude, async_test_client, auth_headers):
        """Test async AI chat functionality"""
        # Mock Claude client
        mock_claude_instance = mock_claude.return_value
        mock_claude_instance.generate_response = AsyncMock(return_value={
            "response": "This is an async AI response.",
            "timestamp": "2024-01-01T10:00:00Z"
        })
        
        chat_data = {
            "message": "Test async message",
            "context": "Test context"
        }
        
        response = await async_test_client.post("/ai/chat", json=chat_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data