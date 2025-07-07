"""
Tests for User Service
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from src.services.user import UserService
from src.models.user import User


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
    
    def test_create_user_success(self, test_db_session, sample_user_data):
        """Test successful user creation"""
        user = UserService.create_user(
            test_db_session,
            **sample_user_data
        )
        
        assert isinstance(user, User)
        assert user.username == sample_user_data["username"]
        assert user.email == sample_user_data["email"]
        assert user.first_name == sample_user_data["first_name"]
        assert user.last_name == sample_user_data["last_name"]
        assert user.hashed_password != sample_user_data["password"]  # Should be hashed
        assert user.is_active is True
    
    def test_create_user_duplicate_username(self, test_db_session, sample_user_data):
        """Test creating user with duplicate username"""
        # Create first user
        UserService.create_user(test_db_session, **sample_user_data)
        
        # Try to create another with same username
        with pytest.raises(HTTPException) as exc_info:
            UserService.create_user(test_db_session, **sample_user_data)
        
        assert exc_info.value.status_code == 400
        assert "Username already taken" in exc_info.value.detail
    
    def test_create_user_duplicate_email(self, test_db_session, sample_user_data):
        """Test creating user with duplicate email"""
        # Create first user
        UserService.create_user(test_db_session, **sample_user_data)
        
        # Try to create another with same email but different username
        sample_user_data["username"] = "anotheruser"
        with pytest.raises(HTTPException) as exc_info:
            UserService.create_user(test_db_session, **sample_user_data)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail
    
    def test_get_user_by_username(self, test_db_session, sample_user_data):
        """Test getting user by username"""
        created_user = UserService.create_user(test_db_session, **sample_user_data)
        
        found_user = UserService.get_user_by_username(
            test_db_session,
            sample_user_data["username"]
        )
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.username == sample_user_data["username"]
    
    def test_get_user_by_username_not_found(self, test_db_session):
        """Test getting non-existent user by username"""
        user = UserService.get_user_by_username(test_db_session, "nonexistent")
        assert user is None
    
    def test_get_user_by_email(self, test_db_session, sample_user_data):
        """Test getting user by email"""
        created_user = UserService.create_user(test_db_session, **sample_user_data)
        
        found_user = UserService.get_user_by_email(
            test_db_session,
            sample_user_data["email"]
        )
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == sample_user_data["email"]
    
    def test_get_user_by_email_not_found(self, test_db_session):
        """Test getting non-existent user by email"""
        user = UserService.get_user_by_email(test_db_session, "nonexistent@test.com")
        assert user is None
    
    def test_get_user_by_id(self, test_db_session, sample_user_data):
        """Test getting user by ID"""
        created_user = UserService.create_user(test_db_session, **sample_user_data)
        
        found_user = UserService.get_user_by_id(test_db_session, created_user.id)
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.username == sample_user_data["username"]
    
    def test_get_user_by_id_not_found(self, test_db_session):
        """Test getting non-existent user by ID"""
        user = UserService.get_user_by_id(test_db_session, 99999)
        assert user is None
    
    def test_update_user(self, test_db_session, sample_user_data):
        """Test updating user information"""
        user = UserService.create_user(test_db_session, **sample_user_data)
        
        updated_user = UserService.update_user(
            test_db_session,
            user,
            first_name="Updated",
            last_name="Name"
        )
        
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.email == sample_user_data["email"]  # Unchanged
    
    def test_change_password(self, test_db_session, sample_user_data):
        """Test changing user password"""
        user = UserService.create_user(test_db_session, **sample_user_data)
        old_hash = user.hashed_password
        
        updated_user = UserService.change_password(
            test_db_session,
            user,
            "NewSecurePass123!"
        )
        
        assert updated_user.hashed_password != old_hash
        assert updated_user.verify_password("NewSecurePass123!")
    
    def test_activate_user(self, test_db_session, sample_user_data):
        """Test activating user"""
        user = UserService.create_user(test_db_session, **sample_user_data)
        
        # First deactivate
        deactivated = UserService.deactivate_user(test_db_session, user)
        assert deactivated.is_active is False
        
        # Then activate
        activated = UserService.activate_user(test_db_session, user)
        assert activated.is_active is True
    
    def test_deactivate_user(self, test_db_session, sample_user_data):
        """Test deactivating user"""
        user = UserService.create_user(test_db_session, **sample_user_data)
        
        deactivated = UserService.deactivate_user(test_db_session, user)
        assert deactivated.is_active is False
    
    def test_get_all_users(self, test_db_session):
        """Test getting all users"""
        # Create multiple users
        for i in range(5):
            UserService.create_user(
                test_db_session,
                username=f"user{i}",
                email=f"user{i}@test.com",
                password="password123"
            )
        
        users = UserService.get_all_users(test_db_session)
        assert len(users) >= 5
    
    def test_get_all_users_pagination(self, test_db_session):
        """Test getting users with pagination"""
        # Create multiple users
        for i in range(10):
            UserService.create_user(
                test_db_session,
                username=f"paguser{i}",
                email=f"paguser{i}@test.com",
                password="password123"
            )
        
        # Get first page
        page1 = UserService.get_all_users(test_db_session, skip=0, limit=5)
        assert len(page1) == 5
        
        # Get second page
        page2 = UserService.get_all_users(test_db_session, skip=5, limit=5)
        assert len(page2) >= 5
        
        # Ensure different users
        page1_ids = {u.id for u in page1}
        page2_ids = {u.id for u in page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    def test_search_users(self, test_db_session):
        """Test searching users"""
        # Create test users
        UserService.create_user(
            test_db_session,
            username="johndoe",
            email="john@test.com",
            password="password123",
            first_name="John",
            last_name="Doe"
        )
        
        UserService.create_user(
            test_db_session,
            username="janedoe",
            email="jane@test.com",
            password="password123",
            first_name="Jane",
            last_name="Doe"
        )
        
        # Search by last name
        results = UserService.search_users(test_db_session, "doe")
        assert len(results) >= 2
        
        # Search by first name
        results = UserService.search_users(test_db_session, "john")
        assert len(results) >= 1
        assert results[0].username == "johndoe"