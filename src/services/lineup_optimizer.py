"""
Lineup Optimizer service for weekly fantasy football lineup decisions
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.orm import Session
from ..models.player import Player, PlayerStats
from ..models.fantasy import League, FantasyTeam, Roster
from .player import PlayerService
import logging
from itertools import combinations
from collections import defaultdict

logger = logging.getLogger(__name__)


class LineupOptimizer:
    """Optimizes fantasy football lineups for maximum projected points"""
    
    def __init__(self, db: Session, league: League):
        self.db = db
        self.league = league
        self.scoring_type = league.scoring_type
        
        # Lineup requirements
        self.lineup_slots = {
            'QB': league.starting_qb,
            'RB': league.starting_rb, 
            'WR': league.starting_wr,
            'TE': league.starting_te,
            'FLEX': league.starting_flex,  # RB/WR/TE eligible
            'K': league.starting_k,
            'DEF': league.starting_def
        }
    
    def optimize_lineup(
        self, 
        fantasy_team_id: int, 
        week: int,
        locked_players: List[int] = None,
        excluded_players: List[int] = None
    ) -> Dict[str, Any]:
        """Optimize lineup for maximum projected points"""
        
        if locked_players is None:
            locked_players = []
        if excluded_players is None:
            excluded_players = []
        
        # Get team roster
        available_players = self._get_available_players(fantasy_team_id, week, excluded_players)
        
        if not available_players:
            return {'error': 'No available players found'}
        
        # Generate optimal lineup
        optimal_lineup = self._generate_optimal_lineup(
            available_players, 
            locked_players,
            week
        )
        
        # Calculate lineup analysis
        analysis = self._analyze_lineup(optimal_lineup, available_players, week)
        
        return {
            'lineup': optimal_lineup,
            'analysis': analysis,
            'total_projected_points': sum(p['projected_points'] for p in optimal_lineup.values()),
            'confidence_score': self._calculate_confidence_score(optimal_lineup, week)
        }
    
    def _get_available_players(
        self, 
        fantasy_team_id: int, 
        week: int,
        excluded_players: List[int]
    ) -> List[Dict[str, Any]]:
        """Get all available players on the roster for the week"""
        
        roster_players = self.db.query(Roster).filter(
            Roster.fantasy_team_id == fantasy_team_id,
            Roster.is_active == True
        ).all()
        
        available = []
        
        for roster_entry in roster_players:
            player = roster_entry.player
            if not player or player.id in excluded_players:
                continue
            
            # Check if player is available (not on bye, not injured out)
            if not self._is_player_available(player, week):
                continue
            
            # Get projections for the week
            projection = PlayerService.get_player_projections(self.db, player.id, week)
            projected_points = 0
            
            if projection:
                if self.scoring_type == 'ppr':
                    projected_points = projection.fantasy_points_ppr
                elif self.scoring_type == 'half_ppr':
                    projected_points = projection.fantasy_points_half_ppr
                else:
                    projected_points = projection.fantasy_points_standard
            else:
                # Use season average if no weekly projection
                recent_stats = PlayerService.get_player_recent_stats(self.db, player.id, 4)
                if recent_stats:
                    avg_points = sum(
                        getattr(stat, f'fantasy_points_{self.scoring_type}') 
                        for stat in recent_stats
                    ) / len(recent_stats)
                    projected_points = avg_points
            
            # Calculate floor/ceiling
            floor, ceiling = self._calculate_floor_ceiling(player.id, projected_points)
            
            available.append({
                'player': player,
                'projected_points': round(projected_points, 2),
                'floor': round(floor, 2),
                'ceiling': round(ceiling, 2),
                'positions': self._get_eligible_positions(player.position),
                'matchup_rating': self._get_matchup_rating(player, week),
                'injury_risk': self._get_injury_risk(player),
                'recent_form': self._get_recent_form(player.id)
            })
        
        return available
    
    def _is_player_available(self, player: Player, week: int) -> bool:
        """Check if player is available to play in the given week"""
        
        # Check bye week
        if player.bye_week == week:
            return False
        
        # Check injury status
        if player.injury_status in ['Out', 'IR', 'PUP', 'Suspended']:
            return False
        
        return True
    
    def _get_eligible_positions(self, position: str) -> List[str]:
        """Get all positions a player is eligible for"""
        positions = [position]
        
        # FLEX eligibility
        if position in ['RB', 'WR', 'TE']:
            positions.append('FLEX')
        
        return positions
    
    def _generate_optimal_lineup(
        self,
        available_players: List[Dict[str, Any]],
        locked_players: List[int],
        week: int
    ) -> Dict[str, Dict[str, Any]]:
        """Generate the optimal lineup using a greedy algorithm with constraints"""
        
        lineup = {}
        used_players = set()
        
        # First, place locked players
        for player_data in available_players:
            if player_data['player'].id in locked_players:
                best_position = self._find_best_position_for_player(
                    player_data, lineup, used_players
                )
                if best_position:
                    lineup[best_position] = player_data
                    used_players.add(player_data['player'].id)
        
        # Fill remaining positions by priority
        position_priority = ['QB', 'RB', 'WR', 'TE', 'FLEX', 'K', 'DEF']
        
        for position in position_priority:
            slots_needed = self.lineup_slots.get(position, 0)
            current_slots = len([k for k in lineup.keys() if k.startswith(position)])
            
            while current_slots < slots_needed:
                best_player = self._find_best_player_for_position(
                    position, available_players, used_players
                )
                
                if best_player:
                    slot_name = f"{position}{current_slots + 1}" if slots_needed > 1 else position
                    lineup[slot_name] = best_player
                    used_players.add(best_player['player'].id)
                    current_slots += 1
                else:
                    break  # No more players available for this position
        
        return lineup
    
    def _find_best_position_for_player(
        self,
        player_data: Dict[str, Any],
        current_lineup: Dict[str, Dict[str, Any]],
        used_players: Set[int]
    ) -> Optional[str]:
        """Find the best available position for a locked player"""
        
        eligible_positions = player_data['positions']
        
        for position in eligible_positions:
            slots_needed = self.lineup_slots.get(position, 0)
            current_slots = len([k for k in current_lineup.keys() if k.startswith(position)])
            
            if current_slots < slots_needed:
                slot_name = f"{position}{current_slots + 1}" if slots_needed > 1 else position
                return slot_name
        
        return None
    
    def _find_best_player_for_position(
        self,
        position: str,
        available_players: List[Dict[str, Any]],
        used_players: Set[int]
    ) -> Optional[Dict[str, Any]]:
        """Find the best available player for a position"""
        
        eligible_players = [
            p for p in available_players
            if position in p['positions'] and p['player'].id not in used_players
        ]
        
        if not eligible_players:
            return None
        
        # Sort by projected points (with tiebreakers)
        eligible_players.sort(
            key=lambda p: (
                p['projected_points'],
                p['ceiling'],
                -p['injury_risk'],
                p['matchup_rating']
            ),
            reverse=True
        )
        
        return eligible_players[0]
    
    def _calculate_floor_ceiling(self, player_id: int, projected_points: float) -> Tuple[float, float]:
        """Calculate player's floor and ceiling for the week"""
        
        # Get recent performance variance
        recent_stats = PlayerService.get_player_recent_stats(self.db, player_id, 6)
        
        if not recent_stats:
            # Default variance if no recent data
            floor = projected_points * 0.6
            ceiling = projected_points * 1.8
            return floor, ceiling
        
        # Calculate variance from recent games
        points = []
        for stat in recent_stats:
            if self.scoring_type == 'ppr':
                points.append(stat.fantasy_points_ppr)
            elif self.scoring_type == 'half_ppr':
                points.append(stat.fantasy_points_half_ppr)
            else:
                points.append(stat.fantasy_points_standard)
        
        if points:
            avg = sum(points) / len(points)
            variance = sum((p - avg) ** 2 for p in points) / len(points)
            std_dev = variance ** 0.5
            
            # Floor = projected - 1.5 * std_dev, but at least 40% of projection
            floor = max(projected_points * 0.4, projected_points - (1.5 * std_dev))
            # Ceiling = projected + 2 * std_dev, but at most 3x projection
            ceiling = min(projected_points * 3.0, projected_points + (2 * std_dev))
        else:
            floor = projected_points * 0.6
            ceiling = projected_points * 1.8
        
        return floor, ceiling
    
    def _get_matchup_rating(self, player: Player, week: int) -> float:
        """Get matchup rating for the player (1-10 scale)"""
        # This would normally analyze opponent defense rankings
        # For now, return a default rating based on position
        
        base_ratings = {
            'QB': 6.0,
            'RB': 6.5, 
            'WR': 6.0,
            'TE': 5.5,
            'K': 5.0,
            'DEF': 5.0
        }
        
        base_rating = base_ratings.get(player.position, 5.0)
        
        # Adjust for injury status
        if player.injury_status == 'Questionable':
            base_rating -= 1.0
        elif player.injury_status == 'Doubtful':
            base_rating -= 2.0
        
        return max(1.0, min(10.0, base_rating))
    
    def _get_injury_risk(self, player: Player) -> float:
        """Get injury risk rating (0-10 scale, higher = more risk)"""
        risk_ratings = {
            'Healthy': 2.0,
            'Probable': 3.0,
            'Questionable': 6.0,
            'Doubtful': 8.0,
            'Out': 10.0,
            'IR': 10.0
        }
        
        return risk_ratings.get(player.injury_status, 2.0)
    
    def _get_recent_form(self, player_id: int) -> float:
        """Get recent form rating (1-10 scale)"""
        recent_stats = PlayerService.get_player_recent_stats(self.db, player_id, 3)
        
        if not recent_stats:
            return 5.0
        
        # Calculate average fantasy points from recent games
        total_points = 0
        for stat in recent_stats:
            if self.scoring_type == 'ppr':
                total_points += stat.fantasy_points_ppr
            elif self.scoring_type == 'half_ppr':
                total_points += stat.fantasy_points_half_ppr
            else:
                total_points += stat.fantasy_points_standard
        
        avg_points = total_points / len(recent_stats)
        
        # Convert to 1-10 scale (roughly)
        if avg_points >= 20:
            return 9.0
        elif avg_points >= 15:
            return 7.5
        elif avg_points >= 10:
            return 6.0
        elif avg_points >= 5:
            return 4.0
        else:
            return 2.0
    
    def _analyze_lineup(
        self,
        lineup: Dict[str, Dict[str, Any]],
        available_players: List[Dict[str, Any]],
        week: int
    ) -> Dict[str, Any]:
        """Analyze the optimized lineup"""
        
        if not lineup:
            return {}
        
        total_projected = sum(p['projected_points'] for p in lineup.values())
        total_floor = sum(p['floor'] for p in lineup.values())
        total_ceiling = sum(p['ceiling'] for p in lineup.values())
        
        # Calculate bench strength
        bench_players = [
            p for p in available_players 
            if p['player'].id not in [lineup_p['player'].id for lineup_p in lineup.values()]
        ]
        
        bench_strength = sum(p['projected_points'] for p in bench_players[:5]) / 5 if bench_players else 0
        
        # Position analysis
        position_strength = {}
        for position in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
            position_players = [p for k, p in lineup.items() if k.startswith(position)]
            if position_players:
                avg_points = sum(p['projected_points'] for p in position_players) / len(position_players)
                position_strength[position] = round(avg_points, 2)
        
        # Risk assessment
        injury_risk_players = [
            p['player'].name for p in lineup.values() 
            if p['injury_risk'] > 5
        ]
        
        return {
            'total_projected': round(total_projected, 2),
            'total_floor': round(total_floor, 2),
            'total_ceiling': round(total_ceiling, 2),
            'bench_strength': round(bench_strength, 2),
            'position_strength': position_strength,
            'injury_risk_players': injury_risk_players,
            'lineup_variance': round(total_ceiling - total_floor, 2),
            'upside_potential': round(total_ceiling - total_projected, 2)
        }
    
    def _calculate_confidence_score(self, lineup: Dict[str, Dict[str, Any]], week: int) -> float:
        """Calculate confidence score for the lineup (1-100)"""
        
        if not lineup:
            return 0.0
        
        factors = []
        
        # Injury factor (lower injury risk = higher confidence)
        avg_injury_risk = sum(p['injury_risk'] for p in lineup.values()) / len(lineup)
        injury_factor = max(0, 100 - (avg_injury_risk * 10))
        factors.append(injury_factor)
        
        # Projection reliability (higher recent form = higher confidence)
        avg_form = sum(p['recent_form'] for p in lineup.values()) / len(lineup)
        form_factor = avg_form * 10
        factors.append(form_factor)
        
        # Matchup factor
        avg_matchup = sum(p['matchup_rating'] for p in lineup.values()) / len(lineup)
        matchup_factor = avg_matchup * 10
        factors.append(matchup_factor)
        
        # Variance factor (lower variance = higher confidence)
        total_projected = sum(p['projected_points'] for p in lineup.values())
        total_floor = sum(p['floor'] for p in lineup.values())
        variance_ratio = total_floor / total_projected if total_projected > 0 else 0
        variance_factor = variance_ratio * 100
        factors.append(variance_factor)
        
        # Calculate weighted average
        confidence = sum(factors) / len(factors)
        
        return round(min(100, max(0, confidence)), 1)
    
    def get_start_sit_recommendations(
        self,
        fantasy_team_id: int,
        week: int,
        position: str = None
    ) -> List[Dict[str, Any]]:
        """Get start/sit recommendations for close decisions"""
        
        available_players = self._get_available_players(fantasy_team_id, week, [])
        
        if position:
            available_players = [
                p for p in available_players 
                if p['player'].position == position
            ]
        
        # Find close decisions (players with similar projected points)
        recommendations = []
        
        for i, player1 in enumerate(available_players):
            for player2 in available_players[i+1:]:
                if player1['player'].position == player2['player'].position:
                    point_diff = abs(player1['projected_points'] - player2['projected_points'])
                    
                    # Consider it a close decision if within 3 points
                    if point_diff <= 3.0:
                        recommendation = self._compare_players(player1, player2, week)
                        recommendations.append(recommendation)
        
        # Sort by point differential (closest decisions first)
        recommendations.sort(key=lambda x: x['point_differential'])
        
        return recommendations[:10]  # Top 10 closest decisions
    
    def _compare_players(
        self,
        player1: Dict[str, Any],
        player2: Dict[str, Any],
        week: int
    ) -> Dict[str, Any]:
        """Compare two players and provide start/sit recommendation"""
        
        factors = {
            'projected_points': 0.4,
            'ceiling': 0.2,
            'matchup_rating': 0.2,
            'recent_form': 0.1,
            'injury_risk': -0.1  # Negative because lower is better
        }
        
        score1 = sum(
            player1[factor] * weight for factor, weight in factors.items()
        )
        score2 = sum(
            player2[factor] * weight for factor, weight in factors.items()
        )
        
        if score1 > score2:
            recommended = player1
            alternative = player2
        else:
            recommended = player2
            alternative = player1
        
        # Generate reasoning
        reasons = []
        if recommended['projected_points'] > alternative['projected_points']:
            reasons.append(f"Higher projection ({recommended['projected_points']:.1f} vs {alternative['projected_points']:.1f})")
        if recommended['matchup_rating'] > alternative['matchup_rating']:
            reasons.append("Better matchup")
        if recommended['recent_form'] > alternative['recent_form']:
            reasons.append("Better recent form")
        if recommended['injury_risk'] < alternative['injury_risk']:
            reasons.append("Lower injury risk")
        
        return {
            'recommended_player': recommended['player'],
            'alternative_player': alternative['player'],
            'point_differential': abs(player1['projected_points'] - player2['projected_points']),
            'confidence': min(100, abs(score1 - score2) * 50),
            'reasoning': "; ".join(reasons) if reasons else "Very close decision"
        }