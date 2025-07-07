"""
Tests for authentication API endpoints
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.auth
class TestAuthAPI:
    """Test authentication endpoints"""
    
    def test_register_user_success(self, test_client: TestClient, sample_user_data):
        """Test successful user registration"""
        response = test_client.post("/api/auth/register", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    def test_register_duplicate_username(self, test_client: TestClient, sample_user_data):
        """Test registration with duplicate username fails"""
        # Register first user
        response = test_client.post("/api/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        # Try to register same username
        response = test_client.post("/api/auth/register", json=sample_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, test_client: TestClient, sample_user_data):
        """Test registration with invalid email fails"""
        sample_user_data["email"] = "invalid-email"
        response = test_client.post("/api/auth/register", json=sample_user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_login_success(self, test_client: TestClient, sample_user_data):
        """Test successful login"""
        # Register user first
        test_client.post("/api/auth/register", json=sample_user_data)
        
        # Login
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        response = test_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, test_client: TestClient, sample_user_data):
        """Test login with invalid credentials fails"""
        # Register user first
        test_client.post("/api/auth/register", json=sample_user_data)
        
        # Try login with wrong password
        login_data = {
            "username": sample_user_data["username"],
            "password": "wrongpassword"
        }
        response = test_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, test_client: TestClient):
        """Test login with non-existent user fails"""
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }
        response = test_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
    
    def test_refresh_token(self, test_client: TestClient, sample_user_data):
        """Test token refresh functionality"""
        # Register and login
        test_client.post("/api/auth/register", json=sample_user_data)
        
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        login_response = test_client.post("/api/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        refresh_data = {"refresh_token": refresh_token}
        response = test_client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_logout(self, test_client: TestClient, auth_headers):
        """Test logout functionality"""
        response = test_client.post("/api/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()
    
    def test_protected_endpoint_without_auth(self, test_client: TestClient):
        """Test accessing protected endpoint without authentication"""
        response = test_client.get("/api/auth/me")
        
        assert response.status_code == 403
    
    def test_protected_endpoint_with_auth(self, test_client: TestClient, auth_headers):
        """Test accessing protected endpoint with valid authentication"""
        response = test_client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
    
    def test_invalid_token(self, test_client: TestClient):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = test_client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == 401