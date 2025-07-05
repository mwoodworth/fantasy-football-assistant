"""
Trade Analyzer service for evaluating fantasy football trades
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from ..models.player import Player
from ..models.fantasy import League, FantasyTeam, Roster, Trade
from .player import PlayerService
import logging
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class TradeAnalyzer:
    """Analyzes and evaluates fantasy football trades"""
    
    def __init__(self, db: Session, league: League):
        self.db = db
        self.league = league
        self.scoring_type = league.scoring_type
    
    def evaluate_trade(
        self,
        team1_id: int,
        team1_sends: List[int],  # Player IDs
        team1_receives: List[int],  # Player IDs
        team2_id: int,
        team2_sends: List[int],  # Player IDs  
        team2_receives: List[int],  # Player IDs
        week: int = None
    ) -> Dict[str, Any]:
        """Evaluate a proposed trade between two teams"""
        
        # Validate that sends/receives match up
        if team1_sends != team2_receives or team2_sends != team1_receives:
            return {'error': 'Trade player lists do not match'}
        
        # Get team rosters and analyze
        team1_analysis = self._analyze_team_trade_impact(
            team1_id, team1_sends, team1_receives, week
        )
        team2_analysis = self._analyze_team_trade_impact(
            team2_id, team2_sends, team2_receives, week
        )
        
        # Calculate overall trade fairness
        fairness_analysis = self._calculate_trade_fairness(
            team1_analysis, team2_analysis
        )
        
        # Generate trade recommendation
        recommendation = self._generate_trade_recommendation(
            team1_analysis, team2_analysis, fairness_analysis
        )
        
        return {
            'team1_analysis': team1_analysis,
            'team2_analysis': team2_analysis,
            'fairness_analysis': fairness_analysis,
            'recommendation': recommendation,
            'trade_grade': self._calculate_trade_grade(fairness_analysis),
            'key_factors': self._identify_key_factors(team1_analysis, team2_analysis)
        }
    
    def _analyze_team_trade_impact(
        self,
        team_id: int,
        sends: List[int],
        receives: List[int],
        week: int = None
    ) -> Dict[str, Any]:
        """Analyze trade impact for one team"""
        
        # Get current roster
        current_roster = self._get_team_roster(team_id)
        
        # Calculate current team strength
        current_strength = self._calculate_roster_strength(current_roster)
        
        # Calculate post-trade roster
        post_trade_roster = self._simulate_post_trade_roster(
            current_roster, sends, receives
        )
        post_trade_strength = self._calculate_roster_strength(post_trade_roster)
        
        # Analyze players being traded
        sent_players_analysis = [
            self._analyze_player_trade_value(pid, 'sent') for pid in sends
        ]
        received_players_analysis = [
            self._analyze_player_trade_value(pid, 'received') for pid in receives
        ]
        
        # Calculate value exchange
        sent_value = sum(p['trade_value'] for p in sent_players_analysis)
        received_value = sum(p['trade_value'] for p in received_players_analysis)
        
        # Analyze positional impact
        positional_impact = self._analyze_positional_impact(
            current_roster, sends, receives
        )
        
        # Calculate team needs fulfillment
        needs_analysis = self._analyze_needs_fulfillment(
            team_id, sends, receives
        )
        
        return {
            'team_id': team_id,
            'current_strength': current_strength,
            'post_trade_strength': post_trade_strength,
            'strength_change': round(post_trade_strength - current_strength, 2),
            'sent_players': sent_players_analysis,
            'received_players': received_players_analysis,
            'sent_value': round(sent_value, 2),
            'received_value': round(received_value, 2),
            'value_change': round(received_value - sent_value, 2),
            'positional_impact': positional_impact,
            'needs_analysis': needs_analysis,
            'trade_impact_score': self._calculate_trade_impact_score(
                post_trade_strength - current_strength,
                received_value - sent_value,
                needs_analysis
            )
        }
    
    def _get_team_roster(self, team_id: int) -> List[Player]:
        """Get current roster for a team"""
        roster_entries = self.db.query(Roster).filter(
            Roster.fantasy_team_id == team_id,
            Roster.is_active == True
        ).all()
        
        return [entry.player for entry in roster_entries if entry.player]
    
    def _calculate_roster_strength(self, roster: List[Player]) -> float:
        """Calculate overall roster strength score"""
        if not roster:
            return 0.0
        
        total_value = 0
        for player in roster:
            player_value = PlayerService.calculate_player_value(
                self.db,
                player.id,
                self.scoring_type
            )
            total_value += player_value
        
        return round(total_value, 2)
    
    def _simulate_post_trade_roster(
        self,
        current_roster: List[Player],
        sends: List[int],
        receives: List[int]
    ) -> List[Player]:
        """Simulate roster after trade"""
        
        # Remove sent players
        post_trade = [p for p in current_roster if p.id not in sends]
        
        # Add received players
        for player_id in receives:
            player = self.db.query(Player).filter(Player.id == player_id).first()
            if player:
                post_trade.append(player)
        
        return post_trade
    
    def _analyze_player_trade_value(self, player_id: int, direction: str) -> Dict[str, Any]:
        """Analyze individual player's trade value"""
        
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return {'error': 'Player not found'}
        
        base_value = PlayerService.calculate_player_value(
            self.db,
            player.id,
            self.scoring_type
        )
        
        # Get position rank
        position_rankings = PlayerService.get_position_rankings(
            self.db,
            player.position,
            self.scoring_type,
            100
        )
        
        position_rank = 999
        for i, ranking in enumerate(position_rankings):
            if ranking['player'].id == player.id:
                position_rank = i + 1
                break
        
        # Calculate trade value modifiers
        age_factor = self._get_age_factor(player.age)
        injury_factor = self._get_injury_factor(player.injury_status)
        schedule_factor = self._get_schedule_factor(player)
        consistency_factor = self._get_consistency_factor(player.id)
        
        trade_value = base_value * age_factor * injury_factor * schedule_factor * consistency_factor
        
        return {
            'player': player,
            'base_value': round(base_value, 2),
            'trade_value': round(trade_value, 2),
            'position_rank': position_rank,
            'direction': direction,
            'age_factor': round(age_factor, 2),
            'injury_factor': round(injury_factor, 2),
            'schedule_factor': round(schedule_factor, 2),
            'consistency_factor': round(consistency_factor, 2),
            'value_tier': self._get_value_tier(position_rank, player.position)
        }
    
    def _get_age_factor(self, age: Optional[int]) -> float:
        """Get age-based value modifier"""
        if not age:
            return 1.0
        
        if age <= 25:
            return 1.1  # Young player premium
        elif age <= 28:
            return 1.0  # Prime age
        elif age <= 31:
            return 0.95  # Slight decline
        else:
            return 0.85  # Aging concerns
    
    def _get_injury_factor(self, injury_status: str) -> float:
        """Get injury-based value modifier"""
        factors = {
            'Healthy': 1.0,
            'Probable': 0.98,
            'Questionable': 0.9,
            'Doubtful': 0.75,
            'Out': 0.6,
            'IR': 0.3
        }
        return factors.get(injury_status, 1.0)
    
    def _get_schedule_factor(self, player: Player) -> float:
        """Get schedule strength factor"""
        # This would analyze remaining schedule difficulty
        # For now, return neutral
        return 1.0
    
    def _get_consistency_factor(self, player_id: int) -> float:
        """Calculate player consistency factor"""
        recent_stats = PlayerService.get_player_recent_stats(self.db, player_id, 6)
        
        if len(recent_stats) < 3:
            return 1.0
        
        # Calculate coefficient of variation
        points = []
        for stat in recent_stats:
            points.append(getattr(stat, f'fantasy_points_{self.scoring_type}'))
        
        if points:
            mean = sum(points) / len(points)
            if mean == 0:
                return 0.9
            
            variance = sum((p - mean) ** 2 for p in points) / len(points)
            std_dev = variance ** 0.5
            cv = std_dev / mean  # Coefficient of variation
            
            # Convert to consistency factor (lower CV = more consistent = higher factor)
            if cv < 0.3:
                return 1.1  # Very consistent
            elif cv < 0.5:
                return 1.05  # Consistent
            elif cv < 0.8:
                return 1.0  # Average
            else:
                return 0.9  # Inconsistent
        
        return 1.0
    
    def _get_value_tier(self, position_rank: int, position: str) -> str:
        """Get value tier based on position rank"""
        if position == 'QB':
            tiers = [(3, 'Elite'), (8, 'QB1'), (15, 'Low QB1'), (24, 'QB2')]
        elif position in ['RB', 'WR']:
            tiers = [(6, 'Elite'), (12, 'RB1/WR1'), (24, 'RB2/WR2'), (36, 'RB3/WR3')]
        elif position == 'TE':
            tiers = [(3, 'Elite'), (8, 'TE1'), (15, 'Low TE1'), (24, 'TE2')]
        else:
            tiers = [(5, 'Top 5'), (12, 'Startable'), (20, 'Streamer')]
        
        for threshold, tier in tiers:
            if position_rank <= threshold:
                return tier
        
        return 'Deep League'
    
    def _analyze_positional_impact(
        self,
        current_roster: List[Player],
        sends: List[int],
        receives: List[int]
    ) -> Dict[str, Any]:
        """Analyze how trade affects positional strength"""
        
        # Count positions before and after
        position_counts_before = defaultdict(int)
        position_counts_after = defaultdict(int)
        
        for player in current_roster:
            if player.id not in sends:
                position_counts_after[player.position] += 1
            position_counts_before[player.position] += 1
        
        # Add received players
        for player_id in receives:
            player = self.db.query(Player).filter(Player.id == player_id).first()
            if player:
                position_counts_after[player.position] += 1
        
        # Analyze changes
        position_changes = {}
        for position in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
            before = position_counts_before[position]
            after = position_counts_after[position]
            
            if before != after:
                position_changes[position] = {
                    'before': before,
                    'after': after,
                    'change': after - before,
                    'impact': self._assess_positional_change_impact(
                        position, before, after
                    )
                }
        
        return position_changes
    
    def _assess_positional_change_impact(
        self,
        position: str,
        before: int,
        after: int
    ) -> str:
        """Assess impact of positional changes"""
        
        min_needed = {
            'QB': 2,
            'RB': 4,
            'WR': 4,
            'TE': 2,
            'K': 1,
            'DEF': 1
        }.get(position, 2)
        
        if after < min_needed:
            return 'Concerning - Below minimum'
        elif before < min_needed and after >= min_needed:
            return 'Positive - Reaches minimum'
        elif after > before:
            return 'Positive - Added depth'
        elif after < before:
            return 'Negative - Lost depth'
        else:
            return 'Neutral'
    
    def _analyze_needs_fulfillment(
        self,
        team_id: int,
        sends: List[int],
        receives: List[int]
    ) -> Dict[str, Any]:
        """Analyze how well trade addresses team needs"""
        
        # This would analyze team weaknesses and see if trade addresses them
        # For now, provide basic analysis
        
        received_positions = []
        sent_positions = []
        
        for player_id in receives:
            player = self.db.query(Player).filter(Player.id == player_id).first()
            if player:
                received_positions.append(player.position)
        
        for player_id in sends:
            player = self.db.query(Player).filter(Player.id == player_id).first()
            if player:
                sent_positions.append(player.position)
        
        return {
            'positions_acquired': received_positions,
            'positions_traded_away': sent_positions,
            'addresses_needs': len(set(received_positions)) > len(set(sent_positions)),
            'depth_impact': len(received_positions) - len(sent_positions)
        }
    
    def _calculate_trade_impact_score(
        self,
        strength_change: float,
        value_change: float,
        needs_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall trade impact score for a team"""
        
        base_score = (strength_change * 0.4) + (value_change * 0.4)
        
        # Needs bonus
        if needs_analysis.get('addresses_needs', False):
            base_score += 10
        
        # Depth penalty/bonus
        depth_impact = needs_analysis.get('depth_impact', 0)
        if depth_impact < 0:
            base_score += abs(depth_impact) * 5  # Bonus for consolidating
        
        return round(base_score, 2)
    
    def _calculate_trade_fairness(
        self,
        team1_analysis: Dict[str, Any],
        team2_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall trade fairness"""
        
        team1_value = team1_analysis['received_value']
        team2_value = team2_analysis['received_value']
        
        total_value = team1_value + team2_value
        if total_value == 0:
            return {'fairness_score': 50, 'winner': 'Even'}
        
        team1_percentage = (team1_value / total_value) * 100
        team2_percentage = (team2_value / total_value) * 100
        
        # Calculate fairness score (closer to 50-50 = more fair)
        fairness_score = 100 - abs(50 - team1_percentage)
        
        # Determine winner
        if abs(team1_percentage - team2_percentage) < 10:
            winner = 'Even'
        elif team1_percentage > team2_percentage:
            winner = f'Team {team1_analysis["team_id"]}'
        else:
            winner = f'Team {team2_analysis["team_id"]}'
        
        return {
            'fairness_score': round(fairness_score, 1),
            'team1_value_percentage': round(team1_percentage, 1),
            'team2_value_percentage': round(team2_percentage, 1),
            'winner': winner,
            'value_gap': round(abs(team1_value - team2_value), 2)
        }
    
    def _generate_trade_recommendation(
        self,
        team1_analysis: Dict[str, Any],
        team2_analysis: Dict[str, Any],
        fairness_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate trade recommendation and reasoning"""
        
        fairness_score = fairness_analysis['fairness_score']
        
        if fairness_score >= 80:
            recommendation = 'Accept'
            reasoning = 'Fair trade that benefits both teams'
        elif fairness_score >= 60:
            recommendation = 'Consider'
            reasoning = 'Decent trade with minor value discrepancy'
        else:
            recommendation = 'Reject'
            reasoning = 'Unfair trade with significant value gap'
        
        # Add specific reasoning based on analysis
        factors = []
        
        if team1_analysis['needs_analysis'].get('addresses_needs'):
            factors.append('Addresses team needs')
        
        if abs(team1_analysis['strength_change']) > 20:
            if team1_analysis['strength_change'] > 0:
                factors.append('Improves roster strength')
            else:
                factors.append('Weakens roster strength')
        
        if fairness_analysis['value_gap'] > 50:
            factors.append('Large value discrepancy')
        
        if factors:
            reasoning += '. ' + '; '.join(factors)
        
        return {
            'recommendation': recommendation,
            'reasoning': reasoning,
            'confidence': min(100, fairness_score + 20)
        }
    
    def _calculate_trade_grade(self, fairness_analysis: Dict[str, Any]) -> str:
        """Calculate letter grade for trade fairness"""
        score = fairness_analysis['fairness_score']
        
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        elif score >= 40:
            return 'D'
        else:
            return 'F'
    
    def _identify_key_factors(
        self,
        team1_analysis: Dict[str, Any],
        team2_analysis: Dict[str, Any]
    ) -> List[str]:
        """Identify key factors affecting the trade"""
        
        factors = []
        
        # Value discrepancy
        value_diff = abs(team1_analysis['value_change'] - team2_analysis['value_change'])
        if value_diff > 30:
            factors.append('Significant value imbalance')
        
        # Positional impacts
        if team1_analysis['positional_impact'] or team2_analysis['positional_impact']:
            factors.append('Major positional reshuffling')
        
        # Injury concerns
        all_players = (team1_analysis['sent_players'] + team1_analysis['received_players'] +
                      team2_analysis['sent_players'] + team2_analysis['received_players'])
        
        injured_players = [p for p in all_players 
                          if p['player'].injury_status not in ['Healthy', None]]
        if injured_players:
            factors.append('Injury risk considerations')
        
        # Star player involved
        elite_players = [p for p in all_players if p.get('value_tier') == 'Elite']
        if elite_players:
            factors.append('Elite player involved')
        
        return factors
    
    def suggest_trade_targets(
        self,
        team_id: int,
        position_needed: str,
        max_players_to_send: int = 2
    ) -> List[Dict[str, Any]]:
        """Suggest potential trade targets for a team"""
        
        # Get team's roster
        team_roster = self._get_team_roster(team_id)
        
        # Get all other teams' rosters
        other_teams = self.db.query(FantasyTeam).filter(
            FantasyTeam.league_id == self.league.id,
            FantasyTeam.id != team_id
        ).all()
        
        suggestions = []
        
        for other_team in other_teams:
            other_roster = self._get_team_roster(other_team.id)
            
            # Find players at needed position
            available_targets = [
                p for p in other_roster 
                if p.position == position_needed
            ]
            
            for target in available_targets:
                # Find potential trade packages
                trade_packages = self._generate_trade_packages(
                    team_roster, [target], max_players_to_send
                )
                
                for package in trade_packages:
                    # Evaluate trade
                    evaluation = self.evaluate_trade(
                        team_id, package, [target.id],
                        other_team.id, [target.id], package
                    )
                    
                    if evaluation.get('fairness_analysis', {}).get('fairness_score', 0) >= 60:
                        suggestions.append({
                            'target_player': target,
                            'target_team': other_team,
                            'trade_package': [
                                self.db.query(Player).filter(Player.id == pid).first()
                                for pid in package
                            ],
                            'fairness_score': evaluation['fairness_analysis']['fairness_score'],
                            'recommendation': evaluation['recommendation']
                        })
        
        # Sort by fairness score
        suggestions.sort(key=lambda x: x['fairness_score'], reverse=True)
        
        return suggestions[:10]  # Top 10 suggestions
    
    def _generate_trade_packages(
        self,
        roster: List[Player],
        targets: List[Player],
        max_players: int
    ) -> List[List[int]]:
        """Generate potential trade packages"""
        
        from itertools import combinations
        
        packages = []
        
        # Single player trades
        for player in roster:
            if player.position != 'K' and player.position != 'DEF':  # Avoid kickers/defenses
                packages.append([player.id])
        
        # Two player combinations if allowed
        if max_players >= 2:
            skill_players = [p for p in roster if p.position in ['QB', 'RB', 'WR', 'TE']]
            for combo in combinations(skill_players, 2):
                packages.append([p.id for p in combo])
        
        return packages