"""
End-to-End tests for critical user flows
Tests complete user journeys through the Fantasy Football Assistant
"""

import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.mark.e2e
class TestUserRegistrationFlow:
    """Test complete user registration and authentication flow"""
    
    def test_complete_user_registration_flow(self, test_client: TestClient):
        """Test the complete user registration and login flow"""
        # Step 1: Register a new user
        user_data = {
            "username": "e2e_testuser",
            "email": "e2e@test.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        register_response = test_client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        register_data = register_response.json()
        assert "access_token" in register_data
        assert register_data["token_type"] == "bearer"
        
        # Step 2: Login with the registered user
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        login_response = test_client.post("/api/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        login_result = login_response.json()
        assert "access_token" in login_result
        
        # Step 3: Access protected profile endpoint
        headers = {"Authorization": f"Bearer {login_result['access_token']}"}
        profile_response = test_client.get("/api/auth/me", headers=headers)
        assert profile_response.status_code == 200
        
        profile = profile_response.json()
        assert profile["username"] == user_data["username"]
        assert profile["email"] == user_data["email"]
        assert profile["first_name"] == user_data["first_name"]
        assert profile["last_name"] == user_data["last_name"]
        
        # Step 4: Try to register the same user again (should fail)
        duplicate_response = test_client.post("/api/auth/register", json=user_data)
        assert duplicate_response.status_code == 400
        
        # Step 5: Try invalid login (should fail)
        invalid_login = {
            "username": user_data["username"],
            "password": "wrongpassword"
        }
        invalid_response = test_client.post("/api/auth/login", data=invalid_login)
        assert invalid_response.status_code == 401


@pytest.mark.e2e
class TestDashboardFlow:
    """Test dashboard access and data retrieval flow"""
    
    def test_dashboard_access_flow(self, test_client: TestClient, auth_headers):
        """Test accessing dashboard and getting user data"""
        # Step 1: Access dashboard (should work with auth)
        dashboard_response = test_client.get("/api/dashboard/", headers=auth_headers)
        assert dashboard_response.status_code == 200
        
        dashboard_data = dashboard_response.json()
        assert "teamRank" in dashboard_data
        assert "leagueSize" in dashboard_data
        assert "weeklyPoints" in dashboard_data
        assert "recentActivity" in dashboard_data
        
        # Step 2: Verify fallback data for new user
        assert dashboard_data["teamRank"] == "--"
        assert dashboard_data["leagueSize"] == 0
        assert dashboard_data["weeklyPoints"] == "0"
        
        # Step 3: Check recent activity contains welcome message
        activity = dashboard_data["recentActivity"]
        assert len(activity) > 0
        assert any("Connect ESPN League" in item["title"] for item in activity)
    
    def test_dashboard_unauthorized_access(self, test_client: TestClient):
        """Test that dashboard requires authentication"""
        response = test_client.get("/api/dashboard/")
        assert response.status_code == 401


@pytest.mark.e2e
class TestTeamsManagementFlow:
    """Test teams listing and management flow"""
    
    def test_teams_listing_flow(self, test_client: TestClient, auth_headers):
        """Test listing and filtering teams"""
        # Step 1: Get all teams (should be empty for new user)
        teams_response = test_client.get("/api/teams/", headers=auth_headers)
        assert teams_response.status_code == 200
        assert isinstance(teams_response.json(), list)
        assert len(teams_response.json()) == 0
        
        # Step 2: Test filtering by season
        season_response = test_client.get("/api/teams/?season=2024", headers=auth_headers)
        assert season_response.status_code == 200
        assert isinstance(season_response.json(), list)
        
        # Step 3: Test filtering by platform
        espn_response = test_client.get("/api/teams/?include_espn=true&include_manual=false", headers=auth_headers)
        assert espn_response.status_code == 200
        assert isinstance(espn_response.json(), list)
        
        # Step 4: Test invalid team access
        invalid_team_response = test_client.get("/teams/nonexistent_team", headers=auth_headers)
        assert invalid_team_response.status_code == 400  # Invalid format
    
    def test_team_detail_error_handling(self, test_client: TestClient, auth_headers):
        """Test team detail error handling"""
        # Test valid format but non-existent team
        response = test_client.get("/teams/espn_999999", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.e2e
@patch('src.services.espn_integration.espn_service')
class TestESPNIntegrationFlow:
    """Test ESPN integration flow"""
    
    def test_espn_health_check_flow(self, mock_espn_service, test_client: TestClient):
        """Test ESPN service health check flow"""
        # Mock ESPN service
        mock_espn_service.client.__aenter__ = AsyncMock()
        mock_espn_service.client.__aexit__ = AsyncMock()
        mock_espn_service.client.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_espn_service.client.espn_connectivity_check = AsyncMock(return_value={"status": "connected"})
        
        # Step 1: Check ESPN service health
        health_response = test_client.get("/espn/health")
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert "espn_service" in health_data
        assert "espn_api" in health_data
    
    def test_espn_league_access_flow(self, mock_espn_service, test_client: TestClient, auth_headers):
        """Test accessing ESPN league data"""
        # Mock ESPN league data
        mock_league_data = {
            "id": 12345,
            "name": "Test League",
            "size": 10,
            "season": 2024,
            "teams": []
        }
        
        mock_espn_service.get_cached_or_fetch = AsyncMock(return_value=mock_league_data)
        
        # Step 1: Access league information
        league_response = test_client.get("/espn/leagues/12345", headers=auth_headers)
        assert league_response.status_code == 200
        
        league_data = league_response.json()
        assert league_data["success"] is True
        assert league_data["data"]["id"] == 12345
        assert league_data["data"]["name"] == "Test League"
        
        # Step 2: Access league teams
        mock_espn_service.get_cached_or_fetch = AsyncMock(return_value=[])
        teams_response = test_client.get("/espn/leagues/12345/teams", headers=auth_headers)
        assert teams_response.status_code == 200
        
        teams_data = teams_response.json()
        assert teams_data["success"] is True
        assert isinstance(teams_data["data"], list)
    
    def test_espn_authentication_error_flow(self, mock_espn_service, test_client: TestClient, auth_headers):
        """Test ESPN authentication error handling flow"""
        from src.services.espn_integration import ESPNAuthError
        
        # Mock ESPN authentication error
        mock_espn_service.get_cached_or_fetch = AsyncMock(
            side_effect=ESPNAuthError("Authentication failed")
        )
        
        # Step 1: Try to access league (should fail with auth error)
        response = test_client.get("/espn/leagues/12345", headers=auth_headers)
        assert response.status_code == 401
        
        error_data = response.json()
        assert "requires_auth_update" in error_data["detail"]
        assert error_data["detail"]["requires_auth_update"] is True


@pytest.mark.e2e
@patch('src.services.ai.claude_client.ClaudeClient')
class TestAIAssistantFlow:
    """Test AI assistant interaction flow"""
    
    def test_ai_chat_flow(self, mock_claude, test_client: TestClient, auth_headers):
        """Test complete AI chat interaction flow"""
        # Mock Claude client
        mock_claude_instance = mock_claude.return_value
        mock_claude_instance.generate_response = AsyncMock(return_value={
            "response": "Based on your lineup, I recommend starting Josh Allen at QB this week. He has a favorable matchup against a weak defense and has been consistently putting up solid numbers. For your RB slots, consider starting your top-ranked players based on projected points.",
            "analysis": {
                "confidence": 0.85,
                "recommendations": [
                    "Start Josh Allen at QB",
                    "Monitor injury reports before game time",
                    "Check weather conditions for outdoor games"
                ]
            },
            "timestamp": "2024-01-01T10:00:00Z"
        })
        
        # Step 1: Send initial chat message
        chat_data = {
            "message": "Who should I start this week at QB and RB?",
            "context": "I have a tough matchup and need to optimize my lineup"
        }
        
        chat_response = test_client.post("/ai/chat", json=chat_data, headers=auth_headers)
        assert chat_response.status_code == 200
        
        chat_result = chat_response.json()
        assert "response" in chat_result
        assert "timestamp" in chat_result
        assert "Josh Allen" in chat_result["response"]
        
        # Step 2: Send follow-up message
        followup_data = {
            "message": "What about my flex position?",
            "context": "Following up on previous lineup advice"
        }
        
        mock_claude_instance.generate_response = AsyncMock(return_value={
            "response": "For your flex position, I'd recommend looking at matchup advantages and recent performance trends. Consider a WR with a high target share against a weak secondary.",
            "analysis": {
                "confidence": 0.78,
                "recommendations": ["Target WRs with high target share", "Avoid players facing elite defenses"]
            },
            "timestamp": "2024-01-01T10:05:00Z"
        })
        
        followup_response = test_client.post("/ai/chat", json=followup_data, headers=auth_headers)
        assert followup_response.status_code == 200
        
        followup_result = followup_response.json()
        assert "response" in followup_result
        assert "flex position" in followup_result["response"]
    
    def test_ai_unauthorized_access(self, mock_claude, test_client: TestClient):
        """Test that AI endpoints require authentication"""
        chat_data = {
            "message": "Test message",
            "context": "Test context"
        }
        
        response = test_client.post("/ai/chat", json=chat_data)
        assert response.status_code == 401


@pytest.mark.e2e
class TestCompleteUserJourney:
    """Test complete user journey from registration to AI interaction"""
    
    @patch('src.services.espn_integration.espn_service')
    @patch('src.services.ai.claude_client.ClaudeClient')
    def test_complete_user_journey(self, mock_claude, mock_espn_service, test_client: TestClient):
        """Test complete user journey through the app"""
        # Step 1: Register new user
        user_data = {
            "username": "journey_user",
            "email": "journey@test.com",
            "password": "Journey123!",
            "first_name": "Journey",
            "last_name": "User"
        }
        
        register_response = test_client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Access dashboard (should show welcome state)
        dashboard_response = test_client.get("/dashboard/", headers=headers)
        assert dashboard_response.status_code == 200
        
        dashboard_data = dashboard_response.json()
        assert dashboard_data["teamRank"] == "--"
        assert dashboard_data["leagueSize"] == 0
        
        # Step 3: Check ESPN service health
        mock_espn_service.client.__aenter__ = AsyncMock()
        mock_espn_service.client.__aexit__ = AsyncMock()
        mock_espn_service.client.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_espn_service.client.espn_connectivity_check = AsyncMock(return_value={"status": "connected"})
        
        espn_health_response = test_client.get("/espn/health")
        assert espn_health_response.status_code == 200
        
        # Step 4: List teams (should be empty)
        teams_response = test_client.get("/teams/", headers=headers)
        assert teams_response.status_code == 200
        assert len(teams_response.json()) == 0
        
        # Step 5: Interact with AI assistant
        mock_claude_instance = mock_claude.return_value
        mock_claude_instance.generate_response = AsyncMock(return_value={
            "response": "Welcome to your Fantasy Football Assistant! I can help you with lineup decisions, waiver wire pickups, and trade analysis. To get started, you might want to connect your ESPN league.",
            "analysis": {
                "confidence": 0.9,
                "recommendations": ["Connect your ESPN league", "Set up your team preferences"]
            },
            "timestamp": "2024-01-01T10:00:00Z"
        })
        
        ai_chat_data = {
            "message": "Hi, I'm new to the app. How can you help me?",
            "context": "New user looking for guidance"
        }
        
        ai_response = test_client.post("/ai/chat", json=ai_chat_data, headers=headers)
        assert ai_response.status_code == 200
        
        ai_result = ai_response.json()
        assert "Welcome" in ai_result["response"]
        assert "ESPN league" in ai_result["response"]
        
        # Step 6: Access profile one more time to confirm everything works
        profile_response = test_client.get("/api/auth/me", headers=headers)
        assert profile_response.status_code == 200
        
        profile = profile_response.json()
        assert profile["username"] == user_data["username"]
        assert profile["email"] == user_data["email"]
    
    def test_error_recovery_flow(self, test_client: TestClient):
        """Test that users can recover from errors gracefully"""
        # Step 1: Try to access protected endpoint without auth
        response = test_client.get("/api/dashboard/")
        assert response.status_code == 401
        
        # Step 2: Register user to fix the auth issue
        user_data = {
            "username": "recovery_user",
            "email": "recovery@test.com",
            "password": "Recovery123!",
            "first_name": "Recovery",
            "last_name": "User"
        }
        
        register_response = test_client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Now access should work
        dashboard_response = test_client.get("/dashboard/", headers=headers)
        assert dashboard_response.status_code == 200
        
        # Step 4: Try invalid team ID (should get proper error)
        invalid_team_response = test_client.get("/teams/invalid_format", headers=headers)
        assert invalid_team_response.status_code == 400
        
        # Step 5: Valid teams endpoint should still work
        teams_response = test_client.get("/teams/", headers=headers)
        assert teams_response.status_code == 200