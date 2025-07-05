"""
Draft Assistant service for fantasy football draft recommendations
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from ..models.player import Player
from ..models.fantasy import League, FantasyTeam, Roster
from .player import PlayerService
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class DraftAssistant:
    """Provides draft recommendations and analysis"""
    
    def __init__(self, db: Session, league: League):
        self.db = db
        self.league = league
        self.scoring_type = league.scoring_type
    
    def get_draft_recommendations(
        self, 
        fantasy_team_id: int, 
        pick_number: int, 
        round_number: int
    ) -> List[Dict[str, Any]]:
        """Get draft recommendations for a specific pick"""
        
        # Get current roster composition
        roster_needs = self._analyze_roster_needs(fantasy_team_id)
        
        # Get available players
        available_players = self._get_available_players()
        
        # Calculate draft values
        recommendations = []
        for player in available_players:
            value_data = self._calculate_draft_value(
                player, 
                pick_number, 
                round_number, 
                roster_needs
            )
            recommendations.append(value_data)
        
        # Sort by draft value and return top recommendations
        recommendations.sort(key=lambda x: x['draft_value'], reverse=True)
        
        return recommendations[:20]  # Top 20 recommendations
    
    def _analyze_roster_needs(self, fantasy_team_id: int) -> Dict[str, int]:
        """Analyze current roster and determine positional needs"""
        current_roster = self.db.query(Roster).filter(
            Roster.fantasy_team_id == fantasy_team_id,
            Roster.is_active == True
        ).all()
        
        # Count players by position
        position_counts = defaultdict(int)
        for roster_entry in current_roster:
            if roster_entry.player and roster_entry.player.position:
                position_counts[roster_entry.player.position] += 1
        
        # Calculate needs based on league settings
        needs = {
            'QB': max(0, self.league.starting_qb + 1 - position_counts['QB']),
            'RB': max(0, self.league.starting_rb + 2 - position_counts['RB']),
            'WR': max(0, self.league.starting_wr + 2 - position_counts['WR']), 
            'TE': max(0, self.league.starting_te + 1 - position_counts['TE']),
            'K': max(0, self.league.starting_k + 1 - position_counts['K']),
            'DEF': max(0, self.league.starting_def + 1 - position_counts['DEF'])
        }
        
        # Add flex considerations
        flex_spots = self.league.starting_flex
        skill_position_total = position_counts['RB'] + position_counts['WR'] + position_counts['TE']
        min_skill_needed = (self.league.starting_rb + self.league.starting_wr + 
                           self.league.starting_te + flex_spots)
        
        if skill_position_total < min_skill_needed:
            # Prioritize RB and WR for flex
            needs['RB'] = max(needs['RB'], 1)
            needs['WR'] = max(needs['WR'], 1)
        
        return needs
    
    def _get_available_players(self) -> List[Player]:
        """Get players not already drafted in the league"""
        # Get all drafted players in this league
        drafted_player_ids = self.db.query(Roster.player_id).filter(
            Roster.fantasy_team.has(league_id=self.league.id),
            Roster.is_active == True
        ).subquery()
        
        # Get available players
        available = self.db.query(Player).filter(
            Player.is_active == True,
            ~Player.id.in_(drafted_player_ids)
        ).all()
        
        return available
    
    def _calculate_draft_value(
        self, 
        player: Player, 
        pick_number: int, 
        round_number: int, 
        roster_needs: Dict[str, int]
    ) -> Dict[str, Any]:
        """Calculate draft value for a player at a specific pick"""
        
        # Base player value
        base_value = PlayerService.calculate_player_value(
            self.db, 
            player.id, 
            self.scoring_type
        )
        
        # Position need multiplier
        need_multiplier = self._get_need_multiplier(player.position, roster_needs, round_number)
        
        # Value over replacement (VOR)
        vor_value = self._calculate_vor(player, pick_number)
        
        # Positional scarcity adjustment
        scarcity_multiplier = self._get_scarcity_multiplier(player.position, round_number)
        
        # Calculate final draft value
        draft_value = (base_value + vor_value) * need_multiplier * scarcity_multiplier
        
        # Tier analysis
        tier = self._get_player_tier(player.position, base_value)
        
        return {
            'player': player,
            'draft_value': round(draft_value, 2),
            'base_value': round(base_value, 2),
            'vor_value': round(vor_value, 2),
            'need_multiplier': round(need_multiplier, 2),
            'scarcity_multiplier': round(scarcity_multiplier, 2),
            'tier': tier,
            'position_rank': self._get_position_rank(player),
            'recommendation_reason': self._get_recommendation_reason(
                player, need_multiplier, tier, round_number
            )
        }
    
    def _get_need_multiplier(self, position: str, roster_needs: Dict[str, int], round_number: int) -> float:
        """Calculate need multiplier based on roster composition"""
        need = roster_needs.get(position, 0)
        
        if need == 0:
            return 0.7  # Already filled
        elif need == 1:
            return 1.0  # Normal need
        elif need >= 2:
            return 1.3  # High need
        
        # Late round considerations
        if round_number > 10:
            if position in ['K', 'DEF']:
                return 1.2  # Draft K/DEF late
            else:
                return 0.9  # Prefer skill positions
        
        return 1.0
    
    def _calculate_vor(self, player: Player, pick_number: int) -> float:
        """Calculate Value Over Replacement"""
        # Get baseline replacement level player for position
        position_players = PlayerService.get_position_rankings(
            self.db, 
            player.position, 
            self.scoring_type, 
            100
        )
        
        if not position_players:
            return 0.0
        
        # Replacement level varies by position
        replacement_ranks = {
            'QB': 15,   # QB15
            'RB': 36,   # RB36 (3 per team)
            'WR': 48,   # WR48 (4 per team)
            'TE': 15,   # TE15
            'K': 15,    # K15
            'DEF': 15   # DEF15
        }
        
        replacement_rank = replacement_ranks.get(player.position, 24)
        
        if len(position_players) > replacement_rank:
            replacement_value = position_players[replacement_rank - 1]['value']
            player_value = PlayerService.calculate_player_value(
                self.db, 
                player.id, 
                self.scoring_type
            )
            return max(0, player_value - replacement_value)
        
        return 0.0
    
    def _get_scarcity_multiplier(self, position: str, round_number: int) -> float:
        """Get position scarcity multiplier based on draft round"""
        
        # Early round scarcity (rounds 1-6)
        if round_number <= 6:
            scarcity = {
                'RB': 1.2,   # RB scarcity early
                'WR': 1.0,   # Balanced
                'QB': 0.8,   # Wait on QB early
                'TE': 0.9,   # Some good options
                'K': 0.5,    # Don't draft early
                'DEF': 0.5   # Don't draft early
            }
        # Mid round (7-12)
        elif round_number <= 12:
            scarcity = {
                'RB': 1.1,
                'WR': 1.0,
                'QB': 1.0,
                'TE': 1.1,   # TE scarcity kicks in
                'K': 0.7,
                'DEF': 0.7
            }
        # Late round (13+)
        else:
            scarcity = {
                'RB': 1.0,
                'WR': 1.0,
                'QB': 1.0,
                'TE': 1.0,
                'K': 1.2,    # Time for K/DEF
                'DEF': 1.2
            }
        
        return scarcity.get(position, 1.0)
    
    def _get_player_tier(self, position: str, value: float) -> int:
        """Determine player tier within position"""
        # Get all players at position and their values
        position_rankings = PlayerService.get_position_rankings(
            self.db, 
            position, 
            self.scoring_type, 
            50
        )
        
        # Define tier breakpoints (approximate)
        if not position_rankings:
            return 5
        
        sorted_values = [p['value'] for p in position_rankings]
        
        if position == 'QB':
            tier_sizes = [3, 6, 6, 9, 26]  # QB tiers
        elif position in ['RB', 'WR']:
            tier_sizes = [6, 8, 10, 12, 14]  # RB/WR tiers
        elif position == 'TE':
            tier_sizes = [3, 5, 7, 10, 25]  # TE tiers
        else:
            tier_sizes = [5, 5, 5, 5, 30]  # K/DEF tiers
        
        # Find which tier the player falls into
        rank = 1
        for i, ranking in enumerate(position_rankings):
            if ranking['value'] <= value:
                rank = i + 1
                break
        
        cumulative = 0
        for tier, size in enumerate(tier_sizes, 1):
            cumulative += size
            if rank <= cumulative:
                return tier
        
        return len(tier_sizes)  # Lowest tier
    
    def _get_position_rank(self, player: Player) -> int:
        """Get player's rank within their position"""
        position_rankings = PlayerService.get_position_rankings(
            self.db, 
            player.position, 
            self.scoring_type, 
            100
        )
        
        for ranking in position_rankings:
            if ranking['player'].id == player.id:
                return ranking['rank']
        
        return 999  # Not ranked
    
    def _get_recommendation_reason(
        self, 
        player: Player, 
        need_multiplier: float, 
        tier: int, 
        round_number: int
    ) -> str:
        """Generate human-readable recommendation reason"""
        
        position = player.position
        reasons = []
        
        # Tier-based reasons
        if tier == 1:
            reasons.append(f"Elite {position}")
        elif tier == 2:
            reasons.append(f"Top-tier {position}")
        elif tier <= 3:
            reasons.append(f"Solid {position} option")
        
        # Need-based reasons
        if need_multiplier > 1.2:
            reasons.append(f"High team need at {position}")
        elif need_multiplier < 0.8:
            reasons.append(f"Position already filled")
        
        # Round-based reasons
        if round_number <= 3 and position in ['RB', 'WR']:
            reasons.append("Core position early")
        elif round_number > 10 and position in ['K', 'DEF']:
            reasons.append("Good time for K/DEF")
        elif round_number <= 6 and position == 'QB':
            reasons.append("Consider waiting on QB")
        
        # Value-based reasons
        vor = self._calculate_vor(player, round_number * 12)  # Approximate pick
        if vor > 50:
            reasons.append("Excellent value")
        elif vor > 25:
            reasons.append("Good value")
        
        return "; ".join(reasons) if reasons else f"Solid {position} pick"
    
    def get_draft_board(self, top_n: int = 200) -> List[Dict[str, Any]]:
        """Get overall draft board rankings"""
        all_positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']
        all_players = []
        
        for position in all_positions:
            position_rankings = PlayerService.get_position_rankings(
                self.db, 
                position, 
                self.scoring_type, 
                50
            )
            all_players.extend(position_rankings)
        
        # Sort by value and assign overall ranks
        all_players.sort(key=lambda x: x['value'], reverse=True)
        
        for i, player_data in enumerate(all_players[:top_n]):
            player_data['overall_rank'] = i + 1
        
        return all_players[:top_n]
    
    def analyze_draft_capital(self, fantasy_team_id: int) -> Dict[str, Any]:
        """Analyze how draft capital was spent"""
        roster = self.db.query(Roster).filter(
            Roster.fantasy_team_id == fantasy_team_id,
            Roster.is_active == True,
            Roster.draft_round.isnot(None)
        ).all()
        
        analysis = {
            'total_picks': len(roster),
            'position_breakdown': defaultdict(list),
            'round_breakdown': defaultdict(list),
            'value_analysis': {
                'total_value': 0,
                'average_value': 0,
                'best_pick': None,
                'worst_pick': None
            }
        }
        
        values = []
        for pick in roster:
            if pick.player:
                value = PlayerService.calculate_player_value(
                    self.db, 
                    pick.player.id, 
                    self.scoring_type
                )
                values.append((pick, value))
                
                analysis['position_breakdown'][pick.player.position].append({
                    'player': pick.player,
                    'round': pick.draft_round,
                    'pick': pick.draft_pick,
                    'value': value
                })
                
                analysis['round_breakdown'][pick.draft_round].append({
                    'player': pick.player,
                    'position': pick.player.position,
                    'value': value
                })
        
        if values:
            total_value = sum(v[1] for v in values)
            analysis['value_analysis']['total_value'] = round(total_value, 2)
            analysis['value_analysis']['average_value'] = round(total_value / len(values), 2)
            
            # Best and worst picks
            values.sort(key=lambda x: x[1], reverse=True)
            analysis['value_analysis']['best_pick'] = {
                'player': values[0][0].player,
                'value': values[0][1],
                'round': values[0][0].draft_round
            }
            analysis['value_analysis']['worst_pick'] = {
                'player': values[-1][0].player,
                'value': values[-1][1],
                'round': values[-1][0].draft_round
            }
        
        return analysis