"""
Tests for Auth Service
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from jose import jwt

from src.services.auth import AuthService
from src.models.user import User
from src.config import settings


@pytest.fixture
def auth_service():
    """Create auth service instance"""
    return AuthService()


@pytest.fixture
def mock_user():
    """Create a mock user"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.mark.services
class TestAuthService:
    """Test authentication service functionality"""
    
    def test_create_access_token(self, auth_service):
        """Test access token creation"""
        data = {"sub": "testuser"}
        token = auth_service.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert decoded["sub"] == "testuser"
        assert "exp" in decoded
    
    def test_create_access_token_with_expiry(self, auth_service):
        """Test access token with custom expiry"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)
        token = auth_service.create_access_token(data, expires_delta)
        
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp_time = datetime.fromtimestamp(decoded["exp"])
        
        # Check expiry is approximately 15 minutes from now
        time_diff = exp_time - datetime.utcnow()
        assert 14 <= time_diff.total_seconds() / 60 <= 16
    
    def test_verify_password(self, auth_service):
        """Test password verification"""
        plain_password = "testpassword123"
        hashed = auth_service.get_password_hash(plain_password)
        
        assert auth_service.verify_password(plain_password, hashed) is True
        assert auth_service.verify_password("wrongpassword", hashed) is False
    
    def test_get_password_hash(self, auth_service):
        """Test password hashing"""
        password = "testpassword123"
        hashed1 = auth_service.get_password_hash(password)
        hashed2 = auth_service.get_password_hash(password)
        
        # Same password should produce different hashes (due to salt)
        assert hashed1 != hashed2
        
        # But both should verify correctly
        assert auth_service.verify_password(password, hashed1) is True
        assert auth_service.verify_password(password, hashed2) is True
    
    def test_authenticate_user_success(self, auth_service, test_db_session, mock_user):
        """Test successful user authentication"""
        password = "testpassword123"
        mock_user.hashed_password = auth_service.get_password_hash(password)
        
        with patch.object(test_db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_user
            
            result = auth_service.authenticate_user(test_db_session, "testuser", password)
            
            assert result == mock_user
    
    def test_authenticate_user_wrong_password(self, auth_service, test_db_session, mock_user):
        """Test authentication with wrong password"""
        mock_user.hashed_password = auth_service.get_password_hash("correctpassword")
        
        with patch.object(test_db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_user
            
            result = auth_service.authenticate_user(test_db_session, "testuser", "wrongpassword")
            
            assert result is False
    
    def test_authenticate_user_not_found(self, auth_service, test_db_session):
        """Test authentication with non-existent user"""
        with patch.object(test_db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            
            result = auth_service.authenticate_user(test_db_session, "nonexistent", "password")
            
            assert result is False
    
    def test_decode_token_valid(self, auth_service):
        """Test decoding valid token"""
        token = auth_service.create_access_token({"sub": "testuser"})
        decoded = auth_service.decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "testuser"
    
    def test_decode_token_invalid(self, auth_service):
        """Test decoding invalid token"""
        decoded = auth_service.decode_token("invalid.token.here")
        
        assert decoded is None
    
    def test_decode_token_expired(self, auth_service):
        """Test decoding expired token"""
        # Create token that expires immediately
        token = auth_service.create_access_token(
            {"sub": "testuser"}, 
            expires_delta=timedelta(seconds=-1)
        )
        
        decoded = auth_service.decode_token(token)
        assert decoded is None