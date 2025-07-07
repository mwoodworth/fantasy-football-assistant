"""
Tests for User Service
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError

from src.services.user import UserService
from src.models.user import User


@pytest.fixture
def user_service(test_db_session):
    """Create user service instance"""
    return UserService(test_db_session)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "newuser",
        "email": "newuser@test.com",
        "password": "SecurePass123!",
        "first_name": "New",
        "last_name": "User"
    }


@pytest.mark.services
class TestUserService:
    """Test user service functionality"""
    
    def test_create_user_success(self, user_service, sample_user_data):
        """Test successful user creation"""
        user = user_service.create_user(**sample_user_data)
        
        assert isinstance(user, User)
        assert user.username == sample_user_data["username"]
        assert user.email == sample_user_data["email"]
        assert user.first_name == sample_user_data["first_name"]
        assert user.last_name == sample_user_data["last_name"]
        assert user.hashed_password != sample_user_data["password"]  # Should be hashed
        assert user.is_active is True
    
    def test_create_user_duplicate_username(self, user_service, sample_user_data):
        """Test creating user with duplicate username"""
        # Create first user
        user_service.create_user(**sample_user_data)
        
        # Try to create another with same username
        with pytest.raises(ValueError, match="Username already exists"):
            user_service.create_user(**sample_user_data)
    
    def test_create_user_duplicate_email(self, user_service, sample_user_data):
        """Test creating user with duplicate email"""
        # Create first user
        user_service.create_user(**sample_user_data)
        
        # Try to create another with same email but different username
        sample_user_data["username"] = "anotheruser"
        with pytest.raises(ValueError, match="Email already exists"):
            user_service.create_user(**sample_user_data)
    
    def test_get_user_by_username(self, user_service, sample_user_data):
        """Test getting user by username"""
        created_user = user_service.create_user(**sample_user_data)
        
        found_user = user_service.get_user_by_username(sample_user_data["username"])
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.username == sample_user_data["username"]
    
    def test_get_user_by_username_not_found(self, user_service):
        """Test getting non-existent user by username"""
        user = user_service.get_user_by_username("nonexistent")
        assert user is None
    
    def test_get_user_by_email(self, user_service, sample_user_data):
        """Test getting user by email"""
        created_user = user_service.create_user(**sample_user_data)
        
        found_user = user_service.get_user_by_email(sample_user_data["email"])
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == sample_user_data["email"]
    
    def test_get_user_by_email_not_found(self, user_service):
        """Test getting non-existent user by email"""
        user = user_service.get_user_by_email("nonexistent@test.com")
        assert user is None
    
    def test_get_user_by_id(self, user_service, sample_user_data):
        """Test getting user by ID"""
        created_user = user_service.create_user(**sample_user_data)
        
        found_user = user_service.get_user_by_id(created_user.id)
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.username == sample_user_data["username"]
    
    def test_get_user_by_id_not_found(self, user_service):
        """Test getting non-existent user by ID"""
        user = user_service.get_user_by_id(99999)
        assert user is None
    
    def test_update_user(self, user_service, sample_user_data):
        """Test updating user information"""
        user = user_service.create_user(**sample_user_data)
        
        updated = user_service.update_user(
            user.id,
            first_name="Updated",
            last_name="Name"
        )
        
        assert updated is True
        
        # Verify changes
        updated_user = user_service.get_user_by_id(user.id)
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.email == sample_user_data["email"]  # Unchanged
    
    def test_update_user_not_found(self, user_service):
        """Test updating non-existent user"""
        updated = user_service.update_user(99999, first_name="Test")
        assert updated is False
    
    def test_delete_user(self, user_service, sample_user_data):
        """Test deleting user"""
        user = user_service.create_user(**sample_user_data)
        user_id = user.id
        
        deleted = user_service.delete_user(user_id)
        assert deleted is True
        
        # Verify user is gone
        found_user = user_service.get_user_by_id(user_id)
        assert found_user is None
    
    def test_delete_user_not_found(self, user_service):
        """Test deleting non-existent user"""
        deleted = user_service.delete_user(99999)
        assert deleted is False
    
    def test_activate_user(self, user_service, sample_user_data):
        """Test activating user"""
        user = user_service.create_user(**sample_user_data)
        user.is_active = False
        user_service.db.commit()
        
        activated = user_service.activate_user(user.id)
        assert activated is True
        
        # Verify user is active
        updated_user = user_service.get_user_by_id(user.id)
        assert updated_user.is_active is True
    
    def test_deactivate_user(self, user_service, sample_user_data):
        """Test deactivating user"""
        user = user_service.create_user(**sample_user_data)
        
        deactivated = user_service.deactivate_user(user.id)
        assert deactivated is True
        
        # Verify user is inactive
        updated_user = user_service.get_user_by_id(user.id)
        assert updated_user.is_active is False