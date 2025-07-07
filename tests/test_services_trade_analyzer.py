"""
Tests for Trade Analyzer Service
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from src.services.trade_analyzer import TradeAnalyzer
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
class TestTradeAnalyzer:
    """Test trade analyzer functionality"""
    
    def test_initialization(self, test_db_session, mock_league):
        """Test trade analyzer initialization"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        assert analyzer.db == test_db_session
        assert analyzer.league == mock_league
        
    def test_evaluate_trade_empty(self, test_db_session, mock_league):
        """Test evaluate trade with empty parameters"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        # Should handle empty trade gracefully
        result = analyzer.evaluate_trade(
            team1_id=1,
            team1_sends=[],
            team1_receives=[],
            team2_id=2,
            team2_sends=[],
            team2_receives=[]
        )
        assert result is not None