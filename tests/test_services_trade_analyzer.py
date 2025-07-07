"""
Tests for Trade Analyzer Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from src.services.trade_analyzer import TradeAnalyzer
from src.models.fantasy import League, FantasyTeam, Roster
from src.models.player import Player


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
    """Create mock players for trades"""
    players = {}
    
    # Team 1 players (giving away)
    players['rb1'] = Mock(spec=Player)
    players['rb1'].id = 1
    players['rb1'].name = "Christian McCaffrey"
    players['rb1'].position = "RB"
    players['rb1'].team = "SF"
    
    players['wr1'] = Mock(spec=Player)
    players['wr1'].id = 2
    players['wr1'].name = "Tyreek Hill"
    players['wr1'].position = "WR"
    players['wr1'].team = "MIA"
    
    # Team 2 players (giving away)
    players['qb1'] = Mock(spec=Player)
    players['qb1'].id = 10
    players['qb1'].name = "Josh Allen"
    players['qb1'].position = "QB"
    players['qb1'].team = "BUF"
    
    players['te1'] = Mock(spec=Player)
    players['te1'].id = 11
    players['te1'].name = "Travis Kelce"
    players['te1'].position = "TE"
    players['te1'].team = "KC"
    
    return players


@pytest.fixture
def mock_roster():
    """Create mock roster data"""
    roster = []
    
    for i in range(16):  # Standard roster size
        roster_entry = Mock(spec=Roster)
        roster_entry.player = Mock(spec=Player)
        roster_entry.player.id = i + 100
        roster_entry.player.position = ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "K", "DST"][i % 9]
        roster_entry.is_active = True
        roster.append(roster_entry)
    
    return roster


@pytest.mark.services
class TestTradeAnalyzer:
    """Test trade analyzer functionality"""
    
    def test_initialization(self, test_db_session, mock_league):
        """Test trade analyzer initialization"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        assert analyzer.db == test_db_session
        assert analyzer.league == mock_league
        assert analyzer.scoring_type == "standard"
        
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
        assert isinstance(result, dict)
    
    @patch('src.services.trade_analyzer.TradeAnalyzer._get_team_roster')
    @patch('src.services.trade_analyzer.TradeAnalyzer._analyze_player_trade_value')
    def test_evaluate_trade_basic(self, mock_player_value, mock_get_roster, 
                                 test_db_session, mock_league, mock_players, mock_roster):
        """Test basic trade evaluation"""
        # Setup mocks
        mock_get_roster.return_value = mock_roster
        mock_player_value.return_value = {
            'trade_value': 75.0,
            'position_scarcity': 0.7,
            'recent_performance': 15.2,
            'injury_risk': 0.2
        }
        
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        with patch.object(analyzer, '_calculate_roster_strength', return_value=85.0):
            with patch.object(analyzer, '_analyze_positional_impact', return_value={'RB': -1, 'QB': 1}):
                with patch.object(analyzer, '_analyze_needs_fulfillment', return_value={'score': 0.8}):
                    with patch.object(analyzer, '_calculate_trade_fairness', return_value={'fairness_score': 0.9}):
                        result = analyzer.evaluate_trade(
                            team1_id=1,
                            team1_sends=[1],  # McCaffrey
                            team1_receives=[10],  # Allen
                            team2_id=2,
                            team2_sends=[10],  # Allen
                            team2_receives=[1]   # McCaffrey
                        )
                        
                        assert isinstance(result, dict)
                        assert 'team1_analysis' in result
                        assert 'team2_analysis' in result
                        assert 'fairness_analysis' in result
                        assert 'recommendation' in result
    
    def test_get_team_roster(self, test_db_session, mock_league, mock_roster):
        """Test getting team roster"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        with patch.object(test_db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = mock_roster
            
            roster = analyzer._get_team_roster(team_id=1)
            
            assert isinstance(roster, list)
            assert len(roster) == len(mock_roster)
    
    def test_calculate_roster_strength(self, test_db_session, mock_league, mock_roster):
        """Test roster strength calculation"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        with patch('src.services.player.PlayerService.calculate_player_value', return_value=70.0):
            strength = analyzer._calculate_roster_strength(mock_roster)
            
            assert isinstance(strength, (int, float))
            assert strength > 0
    
    def test_analyze_player_trade_value(self, test_db_session, mock_league, mock_players):
        """Test individual player trade value analysis"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        with patch.object(test_db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_players['rb1']
            
            with patch('src.services.player.PlayerService.calculate_player_value', return_value=85.0):
                with patch('src.services.player.PlayerService.get_position_rankings', return_value=[]):
                    with patch('src.services.player.PlayerService.get_player_recent_stats', return_value=[]):
                        # Ensure mock player has necessary attributes
                        mock_players['rb1'].age = 25
                        mock_players['rb1'].injury_status = "Healthy"
                        
                        value_analysis = analyzer._analyze_player_trade_value(
                            player_id=1, 
                            direction='sent'
                        )
                        
                        assert isinstance(value_analysis, dict)
                        assert 'trade_value' in value_analysis
                        assert 'player' in value_analysis
    
    def test_analyze_player_trade_value_detailed(self, test_db_session, mock_league):
        """Test detailed player trade value analysis"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        player = Mock(spec=Player)
        player.position = "RB"
        player.team = "SF"
        
        # Mock various factors that contribute to trade value
        with patch('src.services.player.PlayerService.calculate_player_value', return_value=85.0) as mock_value:
            with patch('src.services.player.PlayerService.get_position_rankings', return_value=[{'player': player}]) as mock_rankings:
                with patch.object(test_db_session, 'query') as mock_query:
                    mock_query.return_value.filter.return_value.first.return_value = player
                    
                    result = analyzer._analyze_player_trade_value(1, 'sent')
                    
                    assert isinstance(result, dict)
                    assert 'player' in result
                    assert 'trade_value' in result
    
    def test_get_value_tier(self, test_db_session, mock_league):
        """Test value tier calculation"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        # Test different positions and ranks
        tier = analyzer._get_value_tier(5, "RB")
        assert isinstance(tier, str)
        
        tier_qb = analyzer._get_value_tier(2, "QB")
        assert tier_qb == "Elite"
    
    def test_get_consistency_factor(self, test_db_session, mock_league):
        """Test consistency factor calculation"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        player_id = 1
        
        # Mock recent stats
        mock_stats = []
        for i in range(6):  # Last 6 weeks
            stat = Mock()
            stat.fantasy_points_standard = 15.0 + i
            mock_stats.append(stat)
        
        with patch('src.services.player.PlayerService.get_player_recent_stats') as mock_recent:
            mock_recent.return_value = mock_stats
            
            factor = analyzer._get_consistency_factor(player_id)
            
            assert isinstance(factor, (int, float))
            assert factor > 0
    
    def test_get_injury_factor(self, test_db_session, mock_league):
        """Test injury factor calculation"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        # Test healthy player
        factor = analyzer._get_injury_factor("Healthy")
        assert factor == 1.0
        
        # Test injured player
        factor_out = analyzer._get_injury_factor("Out")
        assert factor_out == 0.6
    
    def test_simulate_post_trade_roster(self, test_db_session, mock_league, mock_roster):
        """Test post-trade roster simulation"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        # Players to send and receive
        sends = [1, 2]
        receives = [10, 11]
        
        with patch.object(test_db_session, 'query') as mock_query:
            # Mock players being received
            mock_query.return_value.filter.return_value.all.return_value = [
                Mock(spec=Player, id=10), Mock(spec=Player, id=11)
            ]
            
            post_roster = analyzer._simulate_post_trade_roster(mock_roster, sends, receives)
            
            assert isinstance(post_roster, list)
            # Should have same size as original roster (players swapped)
    
    def test_analyze_positional_impact(self, test_db_session, mock_league, mock_roster):
        """Test positional impact analysis"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        sends = [1]  # Sending RB
        receives = [10]  # Receiving QB
        
        with patch.object(test_db_session, 'query') as mock_query:
            # Mock player queries
            mock_query.return_value.filter.return_value.first.side_effect = [
                Mock(spec=Player, position="RB"),  # Sent player
                Mock(spec=Player, position="QB")   # Received player
            ]
            
            impact = analyzer._analyze_positional_impact(mock_roster, sends, receives)
            
            assert isinstance(impact, dict)
            # Should show position changes
            assert "RB" in impact or "QB" in impact
    
    def test_analyze_needs_fulfillment(self, test_db_session, mock_league):
        """Test needs fulfillment analysis"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        team_id = 1
        sends = [1]  # Sending RB
        receives = [10]  # Receiving QB
        
        with patch.object(analyzer, '_get_team_positional_needs') as mock_needs:
            mock_needs.return_value = {"QB": 0.9, "RB": 0.3}  # High QB need, low RB need
            
            with patch.object(test_db_session, 'query') as mock_query:
                mock_query.return_value.filter.return_value.first.side_effect = [
                    Mock(spec=Player, position="RB"),
                    Mock(spec=Player, position="QB")
                ]
                
                fulfillment = analyzer._analyze_needs_fulfillment(team_id, sends, receives)
                
                assert isinstance(fulfillment, dict)
                assert 'score' in fulfillment
                assert isinstance(fulfillment['score'], (int, float))
    
    def test_calculate_trade_fairness(self, test_db_session, mock_league):
        """Test trade fairness calculation"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        team1_analysis = {
            'received_value': 80.0,
            'team_id': 1
        }
        
        team2_analysis = {
            'received_value': 75.0,
            'team_id': 2
        }
        
        fairness = analyzer._calculate_trade_fairness(team1_analysis, team2_analysis)
        
        assert isinstance(fairness, dict)
        assert 'fairness_score' in fairness
        assert 'winner' in fairness
    
    def test_calculate_trade_grade(self, test_db_session, mock_league):
        """Test trade grade calculation"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        # High fairness should result in good grade
        high_fairness = {'fairness_score': 0.9, 'balance_rating': 'even'}
        grade_high = analyzer._calculate_trade_grade(high_fairness)
        
        # Low fairness should result in poor grade
        low_fairness = {'fairness_score': 0.3, 'balance_rating': 'lopsided'}
        grade_low = analyzer._calculate_trade_grade(low_fairness)
        
        assert grade_high in ['A', 'B', 'C', 'D', 'F']
        assert grade_low in ['A', 'B', 'C', 'D', 'F']
        # High fairness should get better grade than low fairness
    
    def test_identify_key_factors(self, test_db_session, mock_league):
        """Test key factors identification"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        team1_analysis = {
            'positional_impact': {'RB': -1, 'QB': 1},
            'needs_fulfillment': {'score': 0.8},
            'strength_change': 3.0
        }
        
        team2_analysis = {
            'positional_impact': {'RB': 1, 'QB': -1},
            'needs_fulfillment': {'score': 0.6},
            'strength_change': -2.0
        }
        
        factors = analyzer._identify_key_factors(team1_analysis, team2_analysis)
        
        assert isinstance(factors, list)
        assert len(factors) > 0
        assert all(isinstance(factor, str) for factor in factors)
    
    def test_get_age_factor(self, test_db_session, mock_league):
        """Test age factor calculation"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        # Test young player
        young_factor = analyzer._get_age_factor(24)
        assert young_factor == 1.1
        
        # Test prime age
        prime_factor = analyzer._get_age_factor(27)
        assert prime_factor == 1.0
        
        # Test older player
        old_factor = analyzer._get_age_factor(32)
        assert old_factor == 0.85
    
    def test_generate_trade_recommendation(self, test_db_session, mock_league):
        """Test trade recommendation generation"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        team1_analysis = {'strength_change': 3.0, 'needs_analysis': {'addresses_needs': True}}
        team2_analysis = {'strength_change': -1.0, 'needs_analysis': {'addresses_needs': False}}
        fairness_analysis = {'fairness_score': 85.0, 'value_gap': 10.0}
        
        recommendation = analyzer._generate_trade_recommendation(
            team1_analysis, team2_analysis, fairness_analysis
        )
        
        assert isinstance(recommendation, dict)
        assert 'recommendation' in recommendation
        assert 'reasoning' in recommendation
    
    def test_different_scoring_types(self, test_db_session):
        """Test analyzer with different scoring types"""
        # Test PPR
        ppr_league = Mock(spec=League)
        ppr_league.scoring_type = "ppr"
        
        ppr_analyzer = TradeAnalyzer(test_db_session, ppr_league)
        assert ppr_analyzer.scoring_type == "ppr"
        
        # Test Half PPR
        half_ppr_league = Mock(spec=League)
        half_ppr_league.scoring_type = "half_ppr"
        
        half_ppr_analyzer = TradeAnalyzer(test_db_session, half_ppr_league)
        assert half_ppr_analyzer.scoring_type == "half_ppr"
    
    def test_multi_player_trade_evaluation(self, test_db_session, mock_league, mock_players):
        """Test evaluation of multi-player trades"""
        analyzer = TradeAnalyzer(test_db_session, mock_league)
        
        # 2-for-2 trade
        with patch.object(analyzer, '_get_team_roster', return_value=[]):
            with patch.object(analyzer, '_analyze_player_trade_value') as mock_value:
                mock_value.return_value = {
                    'trade_value': 70.0,
                    'position_scarcity': 0.6,
                    'recent_performance': 14.0,
                    'injury_risk': 0.3
                }
                
                with patch.object(analyzer, '_calculate_roster_strength', return_value=80.0):
                    with patch.object(analyzer, '_analyze_positional_impact', return_value={}):
                        with patch.object(analyzer, '_analyze_needs_fulfillment', return_value={'score': 0.7}):
                            with patch.object(analyzer, '_calculate_trade_fairness', return_value={'fairness_score': 0.8}):
                                result = analyzer.evaluate_trade(
                                    team1_id=1,
                                    team1_sends=[1, 2],  # McCaffrey + Hill
                                    team1_receives=[10, 11],  # Allen + Kelce
                                    team2_id=2,
                                    team2_sends=[10, 11],  # Allen + Kelce
                                    team2_receives=[1, 2]   # McCaffrey + Hill
                                )
                                
                                assert isinstance(result, dict)
                                assert 'team1_analysis' in result
                                assert 'team2_analysis' in result