"""
Tests for Auth Service
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from jose import jwt
from fastapi import HTTPException

from src.services.auth import AuthService
from src.models.user import User
from src.config import settings


@pytest.mark.services
class TestAuthService:
    """Test authentication service functionality"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "1"}
        token = AuthService.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        decoded = jwt.decode(token, settings.secret_key, algorithms=[AuthService.ALGORITHM])
        assert decoded["sub"] == "1"
        assert "exp" in decoded
    
    def test_create_access_token_with_expiry(self):
        """Test access token with custom expiry"""
        data = {"sub": "1"}
        expires_delta = timedelta(minutes=15)
        token = AuthService.create_access_token(data, expires_delta)
        
        decoded = jwt.decode(token, settings.secret_key, algorithms=[AuthService.ALGORITHM])
        exp_time = datetime.fromtimestamp(decoded["exp"])
        
        # Check expiry is approximately 15 minutes from now
        time_diff = exp_time - datetime.utcnow()
        assert 14 <= time_diff.total_seconds() / 60 <= 16
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "1"}
        token = AuthService.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        decoded = jwt.decode(token, settings.secret_key, algorithms=[AuthService.ALGORITHM])
        assert decoded["sub"] == "1"
        assert "exp" in decoded
    
    def test_verify_token_valid(self):
        """Test verifying valid token"""
        token = AuthService.create_access_token({"sub": "1"})
        payload = AuthService.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "1"
    
    def test_verify_token_invalid(self):
        """Test verifying invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.verify_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail
    
    def test_verify_token_expired(self):
        """Test verifying expired token"""
        # Create token that expires immediately
        token = AuthService.create_access_token(
            {"sub": "1"}, 
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.verify_token(token)
        
        assert exc_info.value.status_code == 401
    
    def test_authenticate_user_success(self, test_db_session):
        """Test successful user authentication"""
        # Create a test user
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        # Mock password verification
        with patch.object(user, 'verify_password', return_value=True):
            result = AuthService.authenticate_user(
                test_db_session, 
                "test@example.com", 
                "password"
            )
            
            assert result == user
            assert user.last_login is not None
    
    def test_authenticate_user_by_username(self, test_db_session):
        """Test authentication by username"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        with patch.object(user, 'verify_password', return_value=True):
            result = AuthService.authenticate_user(
                test_db_session, 
                "testuser", 
                "password",
                by_email=False
            )
            
            assert result == user
    
    def test_authenticate_user_wrong_password(self, test_db_session):
        """Test authentication with wrong password"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        with patch.object(user, 'verify_password', return_value=False):
            result = AuthService.authenticate_user(
                test_db_session, 
                "test@example.com", 
                "wrongpassword"
            )
            
            assert result is None
    
    def test_authenticate_user_not_found(self, test_db_session):
        """Test authentication with non-existent user"""
        result = AuthService.authenticate_user(
            test_db_session, 
            "nonexistent@example.com", 
            "password"
        )
        
        assert result is None
    
    def test_get_user_from_token(self, test_db_session):
        """Test getting user from token"""
        # Create a test user
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        # Create token with user ID
        token = AuthService.create_access_token({"sub": str(user.id)})
        
        # Get user from token
        retrieved_user = AuthService.get_user_from_token(token, test_db_session)
        
        assert retrieved_user.id == user.id
        assert retrieved_user.username == user.username
    
    def test_get_user_from_token_invalid(self, test_db_session):
        """Test getting user from invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.get_user_from_token("invalid.token", test_db_session)
        
        assert exc_info.value.status_code == 401
    
    def test_get_user_from_token_no_sub(self, test_db_session):
        """Test getting user from token without sub claim"""
        # Create token without sub
        token = AuthService.create_access_token({"foo": "bar"})
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.get_user_from_token(token, test_db_session)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail
    
    def test_get_user_from_token_user_not_found(self, test_db_session):
        """Test getting non-existent user from token"""
        # Create token with non-existent user ID
        token = AuthService.create_access_token({"sub": "999999"})
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.get_user_from_token(token, test_db_session)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail
    
    def test_create_user_tokens(self):
        """Test creating user tokens"""
        user = Mock(spec=User)
        user.id = 1
        
        tokens = AuthService.create_user_tokens(user)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        
        # Verify tokens are valid
        access_payload = jwt.decode(
            tokens["access_token"], 
            settings.secret_key, 
            algorithms=[AuthService.ALGORITHM]
        )
        assert access_payload["sub"] == "1"
        
        refresh_payload = jwt.decode(
            tokens["refresh_token"], 
            settings.secret_key, 
            algorithms=[AuthService.ALGORITHM]
        )
        assert refresh_payload["sub"] == "1"