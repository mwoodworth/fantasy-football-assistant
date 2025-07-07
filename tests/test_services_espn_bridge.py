"""
Tests for ESPN Bridge Service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from src.services.espn_bridge import ESPNBridgeService
from src.models.espn_league import ESPNLeague
from src.models.user import User


@pytest.mark.unit
@pytest.mark.espn
class TestESPNBridgeService:
    """Test ESPN Bridge Service functionality"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def espn_bridge_service(self, mock_db_session):
        """Create ESPN Bridge Service instance"""
        return ESPNBridgeService(mock_db_session)
    
    @pytest.fixture
    def sample_espn_league(self):
        """Sample ESPN league for testing"""
        league = Mock(spec=ESPNLeague)
        league.id = 1
        league.espn_league_id = 12345
        league.season = 2024
        league.league_name = "Test League"
        league.user_team_id = 1
        league.user_team_name = "Test Team"
        league.team_count = 10
        league.scoring_type = "PPR"
        league.draft_completed = True
        league.is_active = True
        league.is_archived = False
        league.espn_s2 = "test_s2"
        league.swid = "test_swid"
        league.roster_positions = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1, "BENCH": 6}
        return league
    
    def test_get_fallback_dashboard_data(self, espn_bridge_service):
        """Test getting fallback dashboard data when no ESPN leagues exist"""
        result = espn_bridge_service._get_fallback_dashboard_data()
        
        assert result.teamRank == "--"
        assert result.leagueSize == 0
        assert result.weeklyPoints == "0"
        assert result.activePlayers == "0"
        assert result.benchPlayers == 0
        assert len(result.recentActivity) == 1
        assert result.recentActivity[0].title == "Connect ESPN League"
    
    def test_calculate_team_rank(self, espn_bridge_service, sample_espn_league):
        """Test team rank calculation"""
        result = espn_bridge_service._calculate_team_rank(sample_espn_league)
        
        # Should return "--" for pre-season
        assert result == "--"
    
    def test_get_weekly_points(self, espn_bridge_service, sample_espn_league):
        """Test getting weekly points"""
        result = espn_bridge_service._get_weekly_points(sample_espn_league)
        
        assert isinstance(result, str)
        assert "." in result  # Should be a decimal number
    
    def test_count_active_players(self, espn_bridge_service, sample_espn_league):
        """Test counting active players"""
        result = espn_bridge_service._count_active_players(sample_espn_league)
        
        assert isinstance(result, int)
        assert result > 0
    
    def test_count_bench_players(self, espn_bridge_service, sample_espn_league):
        """Test counting bench players"""
        result = espn_bridge_service._count_bench_players(sample_espn_league)
        
        assert result == 6  # Based on roster_positions
    
    def test_get_team_record_preseason(self, espn_bridge_service, sample_espn_league):
        """Test getting team record in pre-season"""
        result = espn_bridge_service._get_team_record(sample_espn_league)
        
        assert result == "0-0"
    
    def test_get_team_points_preseason(self, espn_bridge_service, sample_espn_league):
        """Test getting team points in pre-season"""
        result = espn_bridge_service._get_team_points(sample_espn_league)
        
        assert result == 0.0
    
    def test_is_in_playoffs_preseason(self, espn_bridge_service, sample_espn_league):
        """Test playoff status in pre-season"""
        result = espn_bridge_service._is_in_playoffs(sample_espn_league)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_real_team_stats_success(self, espn_bridge_service, sample_espn_league):
        """Test getting real team stats from ESPN service successfully"""
        mock_stats = {
            "success": True,
            "data": {
                "record": {"wins": 8, "losses": 5, "ties": 0},
                "standings": {"pointsFor": 1234.5, "rank": 3}
            }
        }
        
        with patch('src.services.espn_bridge.espn_service') as mock_service:
            mock_service.client.__aenter__ = AsyncMock()
            mock_service.client.__aexit__ = AsyncMock()
            mock_service.client.get_team_stats = AsyncMock(return_value=mock_stats)
            
            record, points, rank, playoffs = await espn_bridge_service._get_real_team_stats(sample_espn_league)
            
            assert record == "8-5"
            assert points == 1234.5
            assert rank == "3rd"
            assert playoffs is True  # Rank 3 should make playoffs
    
    @pytest.mark.asyncio
    async def test_get_real_team_stats_failure(self, espn_bridge_service, sample_espn_league):
        """Test getting real team stats when ESPN service fails"""
        with patch('src.services.espn_bridge.espn_service') as mock_service:
            mock_service.client.__aenter__ = AsyncMock()
            mock_service.client.__aexit__ = AsyncMock()
            mock_service.client.get_team_stats = AsyncMock(side_effect=Exception("ESPN error"))
            
            record, points, rank, playoffs = await espn_bridge_service._get_real_team_stats(sample_espn_league)
            
            # Should fall back to mock data
            assert record == "0-0"
            assert points == 0.0
            assert rank == "--"
            assert playoffs is False
    
    @pytest.mark.asyncio
    async def test_get_user_teams_data_no_leagues(self, espn_bridge_service, mock_db_session):
        """Test getting user teams data when no leagues exist"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = await espn_bridge_service.get_user_teams_data(1)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_user_teams_data_with_leagues(self, espn_bridge_service, mock_db_session, sample_espn_league):
        """Test getting user teams data with ESPN leagues"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = [sample_espn_league]
        
        with patch.object(espn_bridge_service, '_get_real_team_stats') as mock_stats:
            mock_stats.return_value = ("8-5", 1234.5, "3rd", True)
            
            result = await espn_bridge_service.get_user_teams_data(1)
            
            assert len(result) == 1
            team_data = result[0]
            assert team_data['id'] == "espn_1"
            assert team_data['name'] == "Test Team"
            assert team_data['league'] == "Test League"
            assert team_data['platform'] == "ESPN"
            assert team_data['record'] == "8-5"
            assert team_data['points'] == 1234.5
            assert team_data['rank'] == "3rd"
            assert team_data['playoffs'] is True
    
    def test_get_ai_context_for_user(self, espn_bridge_service, mock_db_session, sample_espn_league):
        """Test generating AI context from user's ESPN leagues"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = [sample_espn_league]
        
        result = espn_bridge_service.get_ai_context_for_user(1)
        
        assert result["active_leagues_count"] == 1
        assert len(result["user_leagues"]) == 1
        assert result["user_leagues"][0]["league_name"] == "Test League"
        assert result["user_leagues"][0]["platform"] == "ESPN"
        assert result["user_leagues"][0]["scoring_type"] == "PPR"
        assert "PPR" in result["primary_scoring_types"]
        assert result["has_active_drafts"] is False  # Draft is completed
    
    def test_generate_recent_activity_with_active_draft(self, espn_bridge_service):
        """Test generating recent activity with active draft"""
        league = Mock(spec=ESPNLeague)
        league.league_name = "Test League"
        league.draft_completed = False
        
        result = espn_bridge_service._generate_recent_activity([league])
        
        assert len(result) >= 1
        assert any(activity.title == "Draft in Progress" for activity in result)
        assert any(activity.priority == "high" for activity in result)
    
    def test_generate_recent_activity_completed_draft(self, espn_bridge_service):
        """Test generating recent activity with completed draft"""
        league = Mock(spec=ESPNLeague)
        league.league_name = "Test League"
        league.draft_completed = True
        
        result = espn_bridge_service._generate_recent_activity([league])
        
        assert len(result) >= 1
        assert any("ESPN League Update" in activity.title for activity in result)
        assert len(result) <= 5  # Should limit to 5 activities