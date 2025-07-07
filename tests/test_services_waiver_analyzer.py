"""
Tests for Waiver Analyzer Service
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from src.services.waiver_analyzer import WaiverAnalyzer
from src.models.fantasy import League


@pytest.fixture
def mock_league():
    """Create a mock league"""
    league = Mock(spec=League)
    league.id = 1
    league.name = "Test League"
    league.scoring_type = "standard"
    league.waiver_type = "priority"
    return league


@pytest.mark.services
class TestWaiverAnalyzer:
    """Test waiver wire analyzer functionality"""
    
    def test_initialization(self, test_db_session, mock_league):
        """Test waiver analyzer initialization"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        assert analyzer.db == test_db_session
        assert analyzer.league == mock_league
        
    def test_get_waiver_recommendations_empty(self, test_db_session, mock_league):
        """Test waiver recommendations with no team"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        # Should handle missing team gracefully
        result = analyzer.get_waiver_recommendations(fantasy_team_id=999, week=1)
        assert result is not None