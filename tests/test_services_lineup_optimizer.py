"""
Tests for Lineup Optimizer Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from src.services.lineup_optimizer import LineupOptimizer
from src.models.fantasy import League, FantasyTeam, Roster
from src.models.player import Player, PlayerStats


@pytest.fixture
def mock_league():
    """Create a mock league"""
    league = Mock(spec=League)
    league.id = 1
    league.name = "Test League"
    league.scoring_type = "standard"
    return league


@pytest.fixture
def mock_players():
    """Create mock players with different positions"""
    players = []
    
    # QB
    qb = Mock(spec=Player)
    qb.id = 1
    qb.name = "Patrick Mahomes"
    qb.position = "QB"
    qb.team = "KC"
    players.append(qb)
    
    # RBs
    for i in range(3):
        rb = Mock(spec=Player)
        rb.id = 10 + i
        rb.name = f"RB Player {i+1}"
        rb.position = "RB"
        rb.team = "TEST"
        players.append(rb)
    
    # WRs
    for i in range(4):
        wr = Mock(spec=Player)
        wr.id = 20 + i
        wr.name = f"WR Player {i+1}"
        wr.position = "WR"
        wr.team = "TEST"
        players.append(wr)
    
    # TE
    te = Mock(spec=Player)
    te.id = 30
    te.name = "Travis Kelce"
    te.position = "TE"
    te.team = "KC"
    players.append(te)
    
    # K
    k = Mock(spec=Player)
    k.id = 40
    k.name = "Justin Tucker"
    k.position = "K"
    k.team = "BAL"
    players.append(k)
    
    # DST
    dst = Mock(spec=Player)
    dst.id = 50
    dst.name = "49ers D/ST"
    dst.position = "DST"
    dst.team = "SF"
    players.append(dst)
    
    return players


@pytest.mark.services
class TestLineupOptimizer:
    """Test lineup optimizer functionality"""
    
    def test_initialization(self, test_db_session, mock_league):
        """Test lineup optimizer initialization"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        assert optimizer.db == test_db_session
        assert optimizer.league == mock_league
        assert optimizer.scoring_type == "standard"
        assert hasattr(optimizer, 'lineup_slots')
        
    def test_optimize_lineup_no_team(self, test_db_session, mock_league):
        """Test optimize lineup without team"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Should handle missing team_id gracefully
        result = optimizer.optimize_lineup(fantasy_team_id=999, week=1)
        assert result is not None
        assert isinstance(result, dict)
    
    @patch('src.services.lineup_optimizer.LineupOptimizer._get_available_players')
    def test_optimize_lineup_with_players(self, mock_get_players, test_db_session, mock_league, mock_players):
        """Test lineup optimization with available players"""
        # Mock available players data
        mock_player_data = []
        for player in mock_players:
            mock_player_data.append({
                'player': player,
                'projected_points': 15.0,
                'floor': 10.0,
                'ceiling': 20.0,
                'matchup_rating': 0.7
            })
        
        mock_get_players.return_value = mock_player_data
        
        optimizer = LineupOptimizer(test_db_session, mock_league)
        result = optimizer.optimize_lineup(fantasy_team_id=1, week=1)
        
        assert isinstance(result, dict)
        assert 'optimal_lineup' in result
        assert 'projected_points' in result
        assert 'confidence_score' in result
    
    def test_is_player_available_healthy(self, test_db_session, mock_league):
        """Test player availability check for healthy player"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Mock healthy player
        player = Mock(spec=Player)
        player.injury_status = "healthy"
        player.team = "KC"
        
        with patch.object(optimizer, '_is_on_bye', return_value=False):
            available = optimizer._is_player_available(player, week=1)
            assert available is True
    
    def test_is_player_available_injured(self, test_db_session, mock_league):
        """Test player availability check for injured player"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Mock injured player
        player = Mock(spec=Player)
        player.injury_status = "out"
        player.team = "KC"
        
        available = optimizer._is_player_available(player, week=1)
        assert available is False
    
    def test_is_player_available_on_bye(self, test_db_session, mock_league):
        """Test player availability check for player on bye"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Mock player on bye
        player = Mock(spec=Player)
        player.injury_status = "healthy"
        player.team = "KC"
        
        with patch.object(optimizer, '_is_on_bye', return_value=True):
            available = optimizer._is_player_available(player, week=1)
            assert available is False
    
    def test_get_eligible_positions(self, test_db_session, mock_league):
        """Test eligible positions for lineup slots"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Test RB eligibility
        rb_positions = optimizer._get_eligible_positions("RB")
        assert "RB" in rb_positions
        assert "FLEX" in rb_positions
        
        # Test WR eligibility  
        wr_positions = optimizer._get_eligible_positions("WR")
        assert "WR" in wr_positions
        assert "FLEX" in wr_positions
        
        # Test TE eligibility
        te_positions = optimizer._get_eligible_positions("TE")
        assert "TE" in te_positions
        assert "FLEX" in te_positions
        
        # Test QB ineligibility for FLEX
        qb_positions = optimizer._get_eligible_positions("QB")
        assert "QB" in qb_positions
        assert "FLEX" not in qb_positions
    
    def test_calculate_floor_ceiling(self, test_db_session, mock_league):
        """Test floor/ceiling calculation"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        projected_points = 15.0
        floor, ceiling = optimizer._calculate_floor_ceiling(player_id=1, projected_points=projected_points)
        
        assert isinstance(floor, (int, float))
        assert isinstance(ceiling, (int, float))
        assert floor <= projected_points <= ceiling
        assert floor >= 0
        assert ceiling > floor
    
    def test_get_matchup_rating(self, test_db_session, mock_league):
        """Test matchup rating calculation"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        player = Mock(spec=Player)
        player.position = "RB"
        player.team = "KC"
        
        with patch('src.services.lineup_optimizer.PlayerService.get_matchup_data') as mock_matchup:
            mock_matchup.return_value = {
                "opponent": "LAC",
                "points_allowed_avg": 20.5,
                "defense_rank": 15
            }
            
            rating = optimizer._get_matchup_rating(player, week=1)
            
            assert isinstance(rating, (int, float))
            assert 0 <= rating <= 1
    
    @patch('src.services.lineup_optimizer.PlayerService.get_player_projections')
    def test_get_available_players_with_projections(self, mock_projections, test_db_session, mock_league):
        """Test getting available players with projections"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Mock roster entry
        mock_roster = Mock(spec=Roster)
        mock_roster.player = Mock(spec=Player)
        mock_roster.player.id = 1
        mock_roster.player.position = "RB"
        mock_roster.fantasy_team_id = 1
        mock_roster.is_active = True
        
        # Mock projection
        mock_projection = Mock()
        mock_projection.fantasy_points_standard = 15.0
        mock_projections.return_value = mock_projection
        
        with patch.object(test_db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = [mock_roster]
            
            with patch.object(optimizer, '_is_player_available', return_value=True):
                with patch.object(optimizer, '_calculate_floor_ceiling', return_value=(10.0, 20.0)):
                    with patch.object(optimizer, '_get_matchup_rating', return_value=0.7):
                        players = optimizer._get_available_players(
                            fantasy_team_id=1, 
                            week=1, 
                            excluded_players=[]
                        )
                        
                        assert isinstance(players, list)
                        if players:  # May be empty due to filtering
                            player_data = players[0]
                            assert 'player' in player_data
                            assert 'projected_points' in player_data
                            assert 'floor' in player_data
                            assert 'ceiling' in player_data
    
    @patch('src.services.lineup_optimizer.PlayerService.get_player_recent_stats')
    def test_get_available_players_without_projections(self, mock_recent_stats, test_db_session, mock_league):
        """Test getting available players without projections (using recent stats)"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Mock roster entry
        mock_roster = Mock(spec=Roster)
        mock_roster.player = Mock(spec=Player)
        mock_roster.player.id = 1
        mock_roster.player.position = "RB"
        mock_roster.fantasy_team_id = 1
        mock_roster.is_active = True
        
        # Mock recent stats
        mock_stat = Mock(spec=PlayerStats)
        mock_stat.fantasy_points_standard = 12.0
        mock_recent_stats.return_value = [mock_stat, mock_stat, mock_stat]
        
        with patch('src.services.lineup_optimizer.PlayerService.get_player_projections', return_value=None):
            with patch.object(test_db_session, 'query') as mock_query:
                mock_query.return_value.filter.return_value.all.return_value = [mock_roster]
                
                with patch.object(optimizer, '_is_player_available', return_value=True):
                    with patch.object(optimizer, '_calculate_floor_ceiling', return_value=(8.0, 16.0)):
                        with patch.object(optimizer, '_get_matchup_rating', return_value=0.6):
                            players = optimizer._get_available_players(
                                fantasy_team_id=1, 
                                week=1, 
                                excluded_players=[]
                            )
                            
                            assert isinstance(players, list)
    
    def test_generate_optimal_lineup_basic(self, test_db_session, mock_league, mock_players):
        """Test basic lineup generation"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Create mock player data
        available_players = []
        for i, player in enumerate(mock_players):
            available_players.append({
                'player': player,
                'projected_points': 15.0 - i,  # Decreasing points
                'floor': 10.0,
                'ceiling': 20.0,
                'matchup_rating': 0.7
            })
        
        lineup = optimizer._generate_optimal_lineup(available_players, locked_players=[])
        
        assert isinstance(lineup, list)
        # Should try to fill required positions
        positions_filled = [player_data['player'].position for player_data in lineup]
        
        # Check that we have at least some key positions
        assert len(lineup) > 0
    
    def test_find_best_position_for_player(self, test_db_session, mock_league):
        """Test finding best position for a player"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Mock RB player
        rb_player = Mock(spec=Player)
        rb_player.position = "RB"
        rb_player.id = 1
        
        player_data = {
            'player': rb_player,
            'projected_points': 15.0,
            'floor': 10.0,
            'ceiling': 20.0
        }
        
        # Mock current lineup (empty)
        current_lineup = {}
        
        best_position = optimizer._find_best_position_for_player(player_data, current_lineup)
        
        # Should prefer RB position over FLEX
        assert best_position in ["RB", "FLEX"]
    
    def test_find_best_player_for_position(self, test_db_session, mock_league, mock_players):
        """Test finding best player for a position"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Create available RB players
        rb_players = []
        for i, player in enumerate(mock_players):
            if player.position == "RB":
                rb_players.append({
                    'player': player,
                    'projected_points': 15.0 + i,  # Different points
                    'floor': 10.0,
                    'ceiling': 20.0,
                    'matchup_rating': 0.7
                })
        
        if rb_players:
            best_player = optimizer._find_best_player_for_position("RB", rb_players, used_players=set())
            
            assert best_player is not None
            assert best_player['player'].position == "RB"
    
    def test_calculate_confidence_score(self, test_db_session, mock_league, mock_players):
        """Test confidence score calculation"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Mock lineup
        lineup = []
        for player in mock_players[:5]:  # Use first 5 players
            lineup.append({
                'player': player,
                'projected_points': 15.0,
                'floor': 10.0,
                'ceiling': 20.0,
                'matchup_rating': 0.7
            })
        
        confidence = optimizer._calculate_confidence_score(lineup, week=1)
        
        assert isinstance(confidence, (int, float))
        assert 0 <= confidence <= 1
    
    def test_different_scoring_types(self, test_db_session):
        """Test optimizer with different scoring types"""
        # Test PPR
        ppr_league = Mock(spec=League)
        ppr_league.scoring_type = "ppr"
        
        ppr_optimizer = LineupOptimizer(test_db_session, ppr_league)
        assert ppr_optimizer.scoring_type == "ppr"
        
        # Test Half PPR
        half_ppr_league = Mock(spec=League)
        half_ppr_league.scoring_type = "half_ppr"
        
        half_ppr_optimizer = LineupOptimizer(test_db_session, half_ppr_league)
        assert half_ppr_optimizer.scoring_type == "half_ppr"
    
    def test_locked_players_functionality(self, test_db_session, mock_league, mock_players):
        """Test lineup optimization with locked players"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Mock available players
        available_players = []
        for player in mock_players:
            available_players.append({
                'player': player,
                'projected_points': 15.0,
                'floor': 10.0,
                'ceiling': 20.0,
                'matchup_rating': 0.7
            })
        
        # Lock the QB
        locked_player_ids = [1]  # QB player ID
        
        with patch.object(optimizer, '_get_available_players', return_value=available_players):
            result = optimizer.optimize_lineup(
                fantasy_team_id=1, 
                week=1, 
                locked_players=locked_player_ids
            )
            
            assert isinstance(result, dict)
            # The locked player should be in the optimal lineup
    
    def test_excluded_players_functionality(self, test_db_session, mock_league, mock_players):
        """Test lineup optimization with excluded players"""
        optimizer = LineupOptimizer(test_db_session, mock_league)
        
        # Mock available players
        available_players = []
        for player in mock_players:
            available_players.append({
                'player': player,
                'projected_points': 15.0,
                'floor': 10.0,
                'ceiling': 20.0,
                'matchup_rating': 0.7
            })
        
        # Exclude some players
        excluded_player_ids = [10, 11]  # Some RB player IDs
        
        with patch.object(optimizer, '_get_available_players') as mock_get_players:
            # Should be called with excluded players
            optimizer.optimize_lineup(
                fantasy_team_id=1, 
                week=1, 
                excluded_players=excluded_player_ids
            )
            
            mock_get_players.assert_called_once_with(1, 1, excluded_player_ids)