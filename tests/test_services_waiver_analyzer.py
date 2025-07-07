"""
Tests for Waiver Analyzer Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from src.services.waiver_analyzer import WaiverAnalyzer
from src.models.fantasy import League, FantasyTeam, Roster, WaiverClaim
from src.models.player import Player, PlayerStats


@pytest.fixture
def mock_league():
    """Create a mock league"""
    league = Mock(spec=League)
    league.id = 1
    league.name = "Test League"
    league.scoring_type = "standard"
    league.waiver_type = "priority"
    league.starting_qb = 1
    league.starting_rb = 2
    league.starting_wr = 2
    league.starting_te = 1
    league.starting_k = 1
    league.starting_def = 1
    league.current_season = 2024
    return league


@pytest.fixture
def mock_available_players():
    """Create mock available players"""
    players = []
    
    # QB
    qb = Mock(spec=Player)
    qb.id = 1
    qb.name = "Baker Mayfield"
    qb.position = "QB"
    qb.team = "TB"
    qb.is_active = True
    qb.injury_status = "Healthy"
    players.append(qb)
    
    # RB
    rb = Mock(spec=Player)
    rb.id = 2
    rb.name = "Gus Edwards"
    rb.position = "RB"
    rb.team = "LAC"
    rb.is_active = True
    rb.injury_status = "Healthy"
    players.append(rb)
    
    # WR
    wr = Mock(spec=Player)
    wr.id = 3
    wr.name = "Dontayvion Wicks"
    wr.position = "WR"
    wr.team = "GB"
    wr.is_active = True
    wr.injury_status = "Healthy"
    players.append(wr)
    
    # TE
    te = Mock(spec=Player)
    te.id = 4
    te.name = "Noah Fant"
    te.position = "TE"
    te.team = "SEA"
    te.is_active = True
    te.injury_status = "Healthy"
    players.append(te)
    
    return players


@pytest.fixture
def mock_roster_entries():
    """Create mock roster entries"""
    entries = []
    
    for i in range(10):
        entry = Mock(spec=Roster)
        entry.player = Mock(spec=Player)
        entry.player.id = 100 + i
        entry.player.position = ["QB", "RB", "RB", "WR", "WR", "TE", "K", "DEF", "RB", "WR"][i]
        entry.fantasy_team_id = 1
        entry.is_active = True
        entries.append(entry)
    
    return entries


@pytest.mark.services
class TestWaiverAnalyzer:
    """Test waiver wire analyzer functionality"""
    
    def test_initialization(self, test_db_session, mock_league):
        """Test waiver analyzer initialization"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        assert analyzer.db == test_db_session
        assert analyzer.league == mock_league
        assert analyzer.scoring_type == "standard"
        
    def test_get_waiver_recommendations_empty(self, test_db_session, mock_league):
        """Test waiver recommendations with no team"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        with patch.object(analyzer, '_get_available_players', return_value=[]):
            with patch.object(analyzer, '_analyze_team_needs', return_value={}):
                result = analyzer.get_waiver_recommendations(fantasy_team_id=999, week=1)
                assert result is not None
                assert isinstance(result, list)
    
    def test_get_available_players(self, test_db_session, mock_league, mock_available_players):
        """Test getting available players"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        with patch.object(test_db_session, 'query') as mock_query:
            # Mock subquery for rostered players
            mock_subquery = Mock()
            mock_query.return_value.filter.return_value.subquery.return_value = mock_subquery
            
            # Mock available players query
            mock_query.return_value.filter.return_value.all.return_value = mock_available_players
            
            players = analyzer._get_available_players()
            
            assert isinstance(players, list)
            assert len(players) == len(mock_available_players)
    
    def test_get_available_players_by_position(self, test_db_session, mock_league, mock_available_players):
        """Test getting available players filtered by position"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        # Filter for QB only
        qb_players = [p for p in mock_available_players if p.position == "QB"]
        
        with patch.object(test_db_session, 'query') as mock_query:
            mock_subquery = Mock()
            mock_query.return_value.filter.return_value.subquery.return_value = mock_subquery
            mock_query.return_value.filter.return_value.all.return_value = qb_players
            
            players = analyzer._get_available_players(position="QB")
            
            assert isinstance(players, list)
            assert all(p.position == "QB" for p in players)
    
    def test_analyze_team_needs(self, test_db_session, mock_league, mock_roster_entries):
        """Test analyzing team positional needs"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        with patch.object(test_db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = mock_roster_entries
            
            with patch('src.services.player.PlayerService.calculate_player_value', return_value=100.0):
                needs = analyzer._analyze_team_needs(fantasy_team_id=1)
                
                assert isinstance(needs, dict)
                # Should have analyzed different positions
                assert len(needs) > 0
    
    def test_get_min_players_needed(self, test_db_session, mock_league):
        """Test minimum players needed calculation"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        assert analyzer._get_min_players_needed("QB") == 2  # starting_qb + 1
        assert analyzer._get_min_players_needed("RB") == 3  # starting_rb + 1
        assert analyzer._get_min_players_needed("K") == 1   # starting_k
        assert analyzer._get_min_players_needed("DEF") == 1 # starting_def
    
    def test_get_position_average_value(self, test_db_session, mock_league):
        """Test position average value calculation"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        qb_avg = analyzer._get_position_average_value("QB")
        rb_avg = analyzer._get_position_average_value("RB")
        wr_avg = analyzer._get_position_average_value("WR")
        
        assert isinstance(qb_avg, (int, float))
        assert isinstance(rb_avg, (int, float))
        assert isinstance(wr_avg, (int, float))
        assert qb_avg > 0
        assert rb_avg > 0
        assert wr_avg > 0
    
    def test_analyze_pickup_value(self, test_db_session, mock_league, mock_available_players):
        """Test analyzing pickup value for a player"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        player = mock_available_players[0]  # QB
        team_needs = {
            "QB": {
                "need_level": "medium",
                "count": 1,
                "avg_value": 150.0
            }
        }
        
        with patch('src.services.player.PlayerService.calculate_player_value', return_value=120.0):
            with patch.object(analyzer, '_calculate_trending_factor', return_value=1.1):
                with patch.object(analyzer, '_calculate_opportunity_factor', return_value=1.0):
                    with patch.object(analyzer, '_calculate_schedule_factor', return_value=1.05):
                        with patch.object(analyzer, '_calculate_injury_replacement_factor', return_value=1.0):
                            with patch.object(analyzer, '_get_drop_candidate', return_value=None):
                                analysis = analyzer._analyze_pickup_value(player, team_needs, week=1)
                                
                                assert isinstance(analysis, dict)
                                assert 'player' in analysis
                                assert 'pickup_score' in analysis
                                assert 'player_value' in analysis
                                assert 'faab_bid' in analysis
                                assert 'reasoning' in analysis
    
    def test_get_need_multiplier(self, test_db_session, mock_league):
        """Test need level to multiplier conversion"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        assert analyzer._get_need_multiplier("high") == 1.5
        assert analyzer._get_need_multiplier("medium") == 1.2
        assert analyzer._get_need_multiplier("low") == 1.0
        assert analyzer._get_need_multiplier("unknown") == 1.0
    
    def test_calculate_trending_factor(self, test_db_session, mock_league):
        """Test trending factor calculation"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        # Mock recent stats
        mock_recent_stats = []
        for i in range(3):
            stat = Mock(spec=PlayerStats)
            stat.fantasy_points_standard = 15.0 + i
            stat.fantasy_points_ppr = 18.0 + i
            stat.fantasy_points_half_ppr = 16.5 + i
            mock_recent_stats.append(stat)
        
        # Mock season stats
        mock_season_stats = Mock()
        mock_season_stats.fantasy_points_standard = 120.0
        mock_season_stats.fantasy_points_ppr = 150.0
        mock_season_stats.fantasy_points_half_ppr = 135.0
        mock_season_stats.games_played = 10
        
        with patch('src.services.player.PlayerService.get_player_recent_stats', return_value=mock_recent_stats):
            with patch('src.services.player.PlayerService.get_player_season_stats', return_value=mock_season_stats):
                factor = analyzer._calculate_trending_factor(player_id=1)
                
                assert isinstance(factor, (int, float))
                assert factor > 0
    
    def test_calculate_trending_factor_no_stats(self, test_db_session, mock_league):
        """Test trending factor with no recent stats"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        with patch('src.services.player.PlayerService.get_player_recent_stats', return_value=[]):
            factor = analyzer._calculate_trending_factor(player_id=1)
            
            assert factor == 1.0
    
    def test_calculate_opportunity_factor(self, test_db_session, mock_league):
        """Test opportunity factor calculation"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        # Mock stats with opportunities
        mock_stats = []
        for i in range(3):
            stat = Mock(spec=PlayerStats)
            stat.rush_attempts = 10 + i
            stat.targets = 8 + i
            stat.pass_attempts = 0
            mock_stats.append(stat)
        
        with patch('src.services.player.PlayerService.get_player_recent_stats', return_value=mock_stats):
            factor = analyzer._calculate_opportunity_factor(player_id=1)
            
            assert isinstance(factor, (int, float))
            assert factor > 0
    
    def test_calculate_opportunity_factor_no_stats(self, test_db_session, mock_league):
        """Test opportunity factor with no stats"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        with patch('src.services.player.PlayerService.get_player_recent_stats', return_value=[]):
            factor = analyzer._calculate_opportunity_factor(player_id=1)
            
            assert factor == 1.0
    
    def test_calculate_schedule_factor(self, test_db_session, mock_league, mock_available_players):
        """Test schedule factor calculation"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        qb_player = next(p for p in mock_available_players if p.position == "QB")
        rb_player = next(p for p in mock_available_players if p.position == "RB")
        
        qb_factor = analyzer._calculate_schedule_factor(qb_player, week=1)
        rb_factor = analyzer._calculate_schedule_factor(rb_player, week=1)
        
        assert isinstance(qb_factor, (int, float))
        assert isinstance(rb_factor, (int, float))
        assert qb_factor > 0
        assert rb_factor > 0
    
    def test_calculate_injury_replacement_factor(self, test_db_session, mock_league, mock_available_players):
        """Test injury replacement factor calculation"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        player = mock_available_players[0]
        player.team = Mock()
        player.team.id = 1
        
        with patch.object(test_db_session, 'query') as mock_query:
            # Mock injured teammates count
            mock_query.return_value.filter.return_value.count.return_value = 1
            
            factor = analyzer._calculate_injury_replacement_factor(player)
            
            assert isinstance(factor, (int, float))
            assert factor >= 1.0
    
    def test_calculate_injury_replacement_factor_no_team(self, test_db_session, mock_league, mock_available_players):
        """Test injury replacement factor with no team"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        player = mock_available_players[0]
        player.team = None
        
        factor = analyzer._calculate_injury_replacement_factor(player)
        
        assert factor == 1.0
    
    def test_calculate_faab_bid(self, test_db_session, mock_league):
        """Test FAAB bid calculation"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        # Test different pickup scores and need levels
        high_score_high_need = analyzer._calculate_faab_bid(200, {'need_level': 'high'})
        low_score_low_need = analyzer._calculate_faab_bid(50, {'need_level': 'low'})
        
        assert isinstance(high_score_high_need, int)
        assert isinstance(low_score_low_need, int)
        assert high_score_high_need > low_score_low_need
        assert 1 <= high_score_high_need <= 75
        assert 1 <= low_score_low_need <= 75
    
    def test_get_drop_candidate(self, test_db_session, mock_league, mock_available_players):
        """Test drop candidate suggestion"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        pickup_player = mock_available_players[0]  # QB
        team_needs = {
            "QB": {
                "weakest_player": {
                    "player": Mock(spec=Player),
                    "value": 80.0
                }
            }
        }
        
        with patch('src.services.player.PlayerService.calculate_player_value', return_value=120.0):
            drop_candidate = analyzer._get_drop_candidate(pickup_player, team_needs)
            
            assert isinstance(drop_candidate, dict)
            assert 'player' in drop_candidate
            assert 'value_difference' in drop_candidate
    
    def test_get_drop_candidate_no_improvement(self, test_db_session, mock_league, mock_available_players):
        """Test drop candidate when pickup isn't an improvement"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        pickup_player = mock_available_players[0]
        team_needs = {
            "QB": {
                "weakest_player": {
                    "player": Mock(spec=Player),
                    "value": 150.0  # Higher than pickup value
                }
            }
        }
        
        with patch('src.services.player.PlayerService.calculate_player_value', return_value=120.0):
            drop_candidate = analyzer._get_drop_candidate(pickup_player, team_needs)
            
            assert drop_candidate is None
    
    def test_generate_pickup_reasoning(self, test_db_session, mock_league, mock_available_players):
        """Test pickup reasoning generation"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        player = mock_available_players[1]  # RB
        reasoning = analyzer._generate_pickup_reasoning(player, 1.4, 1.25, 1.15)
        
        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
    
    def test_get_trending_players(self, test_db_session, mock_league, mock_available_players):
        """Test getting trending players"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        with patch.object(analyzer, '_get_available_players', return_value=mock_available_players):
            with patch.object(analyzer, '_calculate_trending_factor', return_value=1.2):
                with patch.object(analyzer, '_get_recent_average', return_value=15.5):
                    with patch.object(analyzer, '_get_season_average', return_value=12.8):
                        trending = analyzer.get_trending_players(limit=5)
                        
                        assert isinstance(trending, list)
                        assert len(trending) <= 5
                        if trending:
                            assert 'player' in trending[0]
                            assert 'trending_factor' in trending[0]
    
    def test_get_recent_average(self, test_db_session, mock_league):
        """Test recent average calculation"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        mock_stats = []
        for i in range(3):
            stat = Mock(spec=PlayerStats)
            stat.fantasy_points_standard = 10.0 + i * 2
            mock_stats.append(stat)
        
        with patch('src.services.player.PlayerService.get_player_recent_stats', return_value=mock_stats):
            avg = analyzer._get_recent_average(player_id=1)
            
            assert isinstance(avg, float)
            assert avg > 0
    
    def test_get_recent_average_no_stats(self, test_db_session, mock_league):
        """Test recent average with no stats"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        with patch('src.services.player.PlayerService.get_player_recent_stats', return_value=[]):
            avg = analyzer._get_recent_average(player_id=1)
            
            assert avg == 0.0
    
    def test_get_season_average(self, test_db_session, mock_league):
        """Test season average calculation"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        mock_season_stats = Mock()
        mock_season_stats.fantasy_points_standard = 150.0
        mock_season_stats.games_played = 10
        
        with patch('src.services.player.PlayerService.get_player_season_stats', return_value=mock_season_stats):
            avg = analyzer._get_season_average(player_id=1)
            
            assert isinstance(avg, float)
            assert avg == 15.0  # 150.0 / 10
    
    def test_get_season_average_no_stats(self, test_db_session, mock_league):
        """Test season average with no stats"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        with patch('src.services.player.PlayerService.get_player_season_stats', return_value=None):
            avg = analyzer._get_season_average(player_id=1)
            
            assert avg == 0.0
    
    def test_analyze_waiver_claims(self, test_db_session, mock_league):
        """Test waiver claims analysis"""
        analyzer = WaiverAnalyzer(test_db_session, mock_league)
        
        # Mock waiver claims
        mock_claims = []
        for i in range(5):
            claim = Mock(spec=WaiverClaim)
            claim.player_to_add_id = 1 if i < 3 else 2  # 3 claims for player 1, 2 for player 2
            claim.faab_bid = 50 + i * 10
            claim.team = Mock()
            claim.claim_week = 1
            claim.status = "PENDING"
            mock_claims.append(claim)
        
        with patch.object(test_db_session, 'query') as mock_query:
            # Mock claims query
            mock_query.return_value.filter.return_value.all.return_value = mock_claims
            
            # Mock player queries
            mock_player = Mock(spec=Player)
            mock_player.id = 1
            mock_query.return_value.filter.return_value.first.return_value = mock_player
            
            analysis = analyzer.analyze_waiver_claims(week=1)
            
            assert isinstance(analysis, dict)
            assert 'total_claims' in analysis
            assert 'contested_players' in analysis
            assert 'uncontested_claims' in analysis
            assert 'highest_bids' in analysis
    
    def test_different_scoring_types(self, test_db_session):
        """Test analyzer with different scoring types"""
        # Test PPR
        ppr_league = Mock(spec=League)
        ppr_league.scoring_type = "ppr"
        ppr_league.starting_qb = 1
        ppr_league.starting_rb = 2
        ppr_league.starting_wr = 2
        ppr_league.starting_te = 1
        ppr_league.starting_k = 1
        ppr_league.starting_def = 1
        
        ppr_analyzer = WaiverAnalyzer(test_db_session, ppr_league)
        assert ppr_analyzer.scoring_type == "ppr"
        
        # Test Half PPR
        half_ppr_league = Mock(spec=League)
        half_ppr_league.scoring_type = "half_ppr"
        half_ppr_league.starting_qb = 1
        half_ppr_league.starting_rb = 2
        half_ppr_league.starting_wr = 2
        half_ppr_league.starting_te = 1
        half_ppr_league.starting_k = 1
        half_ppr_league.starting_def = 1
        
        half_ppr_analyzer = WaiverAnalyzer(test_db_session, half_ppr_league)
        assert half_ppr_analyzer.scoring_type == "half_ppr"