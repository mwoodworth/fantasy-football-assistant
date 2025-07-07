"""
Pytest configuration and fixtures for Fantasy Football Assistant tests
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.models.database import Base, get_db
from src.main import app
from src.config import Settings


@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing"""
    return Settings(
        database_url="sqlite:///:memory:",
        secret_key="test-secret-key-for-testing-only",
        debug=True,
        use_mock_data=True
    )


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine for each test"""
    engine = create_engine(
        "sqlite:///:memory:", 
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session for each test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session, test_settings):
    """Create a test client with dependency overrides"""
    
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Override settings
    app.state.settings = test_settings
    
    with TestClient(app) as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_test_client(test_db_session, test_settings):
    """Create an async test client for async tests"""
    
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    app.state.settings = test_settings
    
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
def sample_league_data():
    """Sample league data for testing"""
    return {
        "name": "Test League",
        "platform": "ESPN",
        "external_id": "12345",
        "team_count": 10,
        "scoring_type": "PPR",
        "current_season": 2024
    }


@pytest.fixture
def sample_espn_league_data():
    """Sample ESPN league data for testing"""
    return {
        "espn_league_id": 1870083331,
        "season": 2025,
        "league_name": "Test ESPN League",
        "espn_s2": "test_s2_cookie",
        "swid": "test_swid_cookie"
    }


@pytest.fixture
def auth_headers(test_client, sample_user_data):
    """Get authorization headers for authenticated requests"""
    # Create user
    response = test_client.post("/auth/register", json=sample_user_data)
    assert response.status_code == 201
    
    # Login
    login_data = {
        "username": sample_user_data["username"],
        "password": sample_user_data["password"]
    }
    response = test_client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
async def async_test_client():
    """Create async test client for testing async endpoints"""
    from httpx import AsyncClient
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_espn_response():
    """Mock ESPN API response data"""
    return {
        "teams": [
            {
                "id": 1,
                "name": "Test Team",
                "owner": "Test Owner",
                "roster": []
            }
        ],
        "league": {
            "id": 1870083331,
            "name": "Test League",
            "size": 10,
            "scoringType": "PPR"
        }
    }


# Test markers for organization
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "espn: mark test as ESPN service test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication test"
    )