"""
Tests for Lineup Optimizer Service
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from src.services.lineup_optimizer import LineupOptimizer
from src.models.fantasy import League


@pytest.fixture
def mock_league():
    """Create a mock league"""
    league = Mock(spec=League)
    league.id = 1
    league.name = "Test League"
    league.scoring_type = "standard"
    return league


@pytest.mark.services
class TestLineupOptimizer:
    """Test lineup optimizer functionality"""
    
    def test_initialization(self, test_db_session, mock_league):
        """Test lineup optimizer initialization"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        assert optimizer.db == test_db_session
        assert optimizer.league == mock_league
        assert optimizer.scoring_type == "standard"
        
    def test_optimize_lineup_no_team(self, test_db_session, mock_league):
        """Test optimize lineup without team"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Should handle missing team_id gracefully
        result = optimizer.optimize_lineup(team_id=999, week=1)
        assert result is not None