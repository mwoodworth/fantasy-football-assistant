"""
Waiver Wire Analyzer service for fantasy football pickup recommendations
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from ..models.player import Player, PlayerStats
from ..models.fantasy import League, FantasyTeam, Roster, WaiverClaim
from .player import PlayerService
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class WaiverAnalyzer:
    """Analyzes waiver wire for pickup recommendations"""
    
    def __init__(self, db: Session, league: League):
        self.db = db
        self.league = league
        self.scoring_type = league.scoring_type
    
    def get_waiver_recommendations(
        self,
        fantasy_team_id: int,
        week: int,
        position: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get top waiver wire pickup recommendations"""
        
        # Get available players (not on any roster)
        available_players = self._get_available_players(position)
        
        # Analyze team needs
        team_needs = self._analyze_team_needs(fantasy_team_id)
        
        recommendations = []
        
        for player in available_players:
            analysis = self._analyze_pickup_value(player, team_needs, week)
            if analysis['pickup_score'] > 0:
                recommendations.append(analysis)
        
        # Sort by pickup score
        recommendations.sort(key=lambda x: x['pickup_score'], reverse=True)
        
        return recommendations[:limit]
    
    def _get_available_players(self, position: str = None) -> List[Player]:
        """Get players available on waivers (not on any roster)"""
        
        # Get all rostered players in the league
        rostered_player_ids = self.db.query(Roster.player_id).filter(
            Roster.fantasy_team.has(league_id=self.league.id),
            Roster.is_active == True
        ).subquery()
        
        # Get available players
        query = self.db.query(Player).filter(
            Player.is_active == True,
            ~Player.id.in_(rostered_player_ids)
        )
        
        if position:
            query = query.filter(Player.position == position)
        
        return query.all()
    
    def _analyze_team_needs(self, fantasy_team_id: int) -> Dict[str, Any]:
        """Analyze team's positional needs and weaknesses"""
        
        current_roster = self.db.query(Roster).filter(
            Roster.fantasy_team_id == fantasy_team_id,
            Roster.is_active == True
        ).all()
        
        position_analysis = defaultdict(lambda: {
            'count': 0,
            'avg_value': 0,
            'weakest_player': None,
            'need_level': 'low'
        })
        
        # Analyze current roster
        for roster_entry in current_roster:
            if roster_entry.player:
                player = roster_entry.player
                position = player.position
                
                player_value = PlayerService.calculate_player_value(
                    self.db, 
                    player.id, 
                    self.scoring_type
                )
                
                position_analysis[position]['count'] += 1
                position_analysis[position]['avg_value'] += player_value
                
                # Track weakest player for potential drops
                if (position_analysis[position]['weakest_player'] is None or 
                    player_value < position_analysis[position]['weakest_player']['value']):
                    position_analysis[position]['weakest_player'] = {
                        'player': player,
                        'value': player_value
                    }
        
        # Calculate averages and need levels
        for position, data in position_analysis.items():
            if data['count'] > 0:
                data['avg_value'] = data['avg_value'] / data['count']
                
                # Determine need level based on roster construction
                min_needed = self._get_min_players_needed(position)
                if data['count'] < min_needed:
                    data['need_level'] = 'high'
                elif data['count'] == min_needed:
                    data['need_level'] = 'medium'
                elif data['avg_value'] < self._get_position_average_value(position):
                    data['need_level'] = 'medium'
                else:
                    data['need_level'] = 'low'
        
        return dict(position_analysis)
    
    def _get_min_players_needed(self, position: str) -> int:
        """Get minimum players needed at each position"""
        minimums = {
            'QB': self.league.starting_qb + 1,
            'RB': self.league.starting_rb + 1,
            'WR': self.league.starting_wr + 1,
            'TE': self.league.starting_te + 1,
            'K': self.league.starting_k,
            'DEF': self.league.starting_def
        }
        return minimums.get(position, 1)
    
    def _get_position_average_value(self, position: str) -> float:
        """Get league average value for position"""
        # This would normally calculate from all league rosters
        # For now, return default values
        defaults = {
            'QB': 180,
            'RB': 150,
            'WR': 140,
            'TE': 120,
            'K': 80,
            'DEF': 90
        }
        return defaults.get(position, 100)
    
    def _analyze_pickup_value(
        self,
        player: Player,
        team_needs: Dict[str, Any],
        week: int
    ) -> Dict[str, Any]:
        """Analyze the pickup value of a specific player"""
        
        # Base player value
        player_value = PlayerService.calculate_player_value(
            self.db, 
            player.id, 
            self.scoring_type
        )
        
        # Position need multiplier
        position_need = team_needs.get(player.position, {})
        need_multiplier = self._get_need_multiplier(position_need.get('need_level', 'low'))
        
        # Trending factor (recent performance vs season)
        trending_factor = self._calculate_trending_factor(player.id)
        
        # Opportunity factor (target share, snap count trends)
        opportunity_factor = self._calculate_opportunity_factor(player.id)
        
        # Schedule factor (upcoming matchups)
        schedule_factor = self._calculate_schedule_factor(player, week)
        
        # Injury replacement factor
        injury_factor = self._calculate_injury_replacement_factor(player)
        
        # Calculate overall pickup score
        pickup_score = (
            player_value * 
            need_multiplier * 
            trending_factor * 
            opportunity_factor * 
            schedule_factor * 
            injury_factor
        )
        
        # Recommended FAAB bid
        faab_bid = self._calculate_faab_bid(pickup_score, position_need)
        
        # Drop recommendation
        drop_candidate = self._get_drop_candidate(player, team_needs)
        
        return {
            'player': player,
            'pickup_score': round(pickup_score, 2),
            'player_value': round(player_value, 2),
            'need_multiplier': round(need_multiplier, 2),
            'trending_factor': round(trending_factor, 2),
            'opportunity_factor': round(opportunity_factor, 2),
            'schedule_factor': round(schedule_factor, 2),
            'injury_factor': round(injury_factor, 2),
            'faab_bid': faab_bid,
            'drop_candidate': drop_candidate,
            'reasoning': self._generate_pickup_reasoning(
                player, need_multiplier, trending_factor, opportunity_factor
            )
        }
    
    def _get_need_multiplier(self, need_level: str) -> float:
        """Convert need level to multiplier"""
        multipliers = {
            'high': 1.5,
            'medium': 1.2,
            'low': 1.0
        }
        return multipliers.get(need_level, 1.0)
    
    def _calculate_trending_factor(self, player_id: int) -> float:
        """Calculate if player is trending up or down"""
        
        # Get recent vs early season performance
        recent_stats = PlayerService.get_player_recent_stats(self.db, player_id, 3)
        
        if not recent_stats:
            return 1.0
        
        # Calculate recent average
        recent_avg = 0
        for stat in recent_stats:
            if self.scoring_type == 'ppr':
                recent_avg += stat.fantasy_points_ppr
            elif self.scoring_type == 'half_ppr':
                recent_avg += stat.fantasy_points_half_ppr
            else:
                recent_avg += stat.fantasy_points_standard
        
        recent_avg = recent_avg / len(recent_stats)
        
        # Get season average for comparison
        season_stats = PlayerService.get_player_season_stats(
            self.db, 
            player_id, 
            self.league.current_season or 2024
        )
        
        if season_stats:
            if self.scoring_type == 'ppr':
                season_avg = season_stats.fantasy_points_ppr / max(1, season_stats.games_played)
            elif self.scoring_type == 'half_ppr':
                season_avg = season_stats.fantasy_points_half_ppr / max(1, season_stats.games_played)
            else:
                season_avg = season_stats.fantasy_points_standard / max(1, season_stats.games_played)
            
            if season_avg > 0:
                trend_ratio = recent_avg / season_avg
                
                if trend_ratio > 1.5:
                    return 1.3  # Hot streak
                elif trend_ratio > 1.2:
                    return 1.15  # Trending up
                elif trend_ratio < 0.7:
                    return 0.8   # Trending down
                elif trend_ratio < 0.5:
                    return 0.6   # Cold streak
        
        return 1.0  # Stable
    
    def _calculate_opportunity_factor(self, player_id: int) -> float:
        """Calculate opportunity trends (targets, carries, snaps)"""
        
        # This would analyze target share, snap count, red zone usage
        # For now, return a default based on recent usage trends
        
        recent_stats = PlayerService.get_player_recent_stats(self.db, player_id, 3)
        if not recent_stats:
            return 1.0
        
        # Simple opportunity score based on touches/targets
        total_opportunities = 0
        for stat in recent_stats:
            opportunities = (
                stat.rush_attempts + 
                stat.targets + 
                (stat.pass_attempts if stat.pass_attempts > 0 else 0)
            )
            total_opportunities += opportunities
        
        avg_opportunities = total_opportunities / len(recent_stats)
        
        # Convert to factor
        if avg_opportunities >= 15:
            return 1.2  # High opportunity
        elif avg_opportunities >= 10:
            return 1.1  # Good opportunity
        elif avg_opportunities >= 5:
            return 1.0  # Average opportunity
        else:
            return 0.9  # Low opportunity
    
    def _calculate_schedule_factor(self, player: Player, week: int) -> float:
        """Calculate upcoming schedule difficulty"""
        
        # This would analyze opponent defensive rankings
        # For now, return a default factor
        
        # Check for favorable matchups based on position
        if player.position in ['RB', 'WR']:
            return 1.1  # Slight boost for skill positions
        elif player.position == 'QB':
            return 1.05
        else:
            return 1.0
    
    def _calculate_injury_replacement_factor(self, player: Player) -> float:
        """Factor in if player is replacing an injured starter"""
        
        # This would check if a higher-ranked player at the position is injured
        # For now, check injury status of team players
        
        if player.team:
            # Check if any teammates at same position are injured
            injured_teammates = self.db.query(Player).filter(
                Player.team_id == player.team.id,
                Player.position == player.position,
                Player.injury_status.in_(['Out', 'IR', 'Doubtful'])
            ).count()
            
            if injured_teammates > 0:
                return 1.3  # Likely replacement
        
        return 1.0
    
    def _calculate_faab_bid(self, pickup_score: float, position_need: Dict[str, Any]) -> int:
        """Calculate recommended FAAB bid percentage"""
        
        # Base bid on pickup score
        base_bid = min(50, max(1, int(pickup_score / 10)))
        
        # Adjust for need
        need_level = position_need.get('need_level', 'low')
        if need_level == 'high':
            base_bid = int(base_bid * 1.5)
        elif need_level == 'medium':
            base_bid = int(base_bid * 1.2)
        
        # Cap at reasonable maximums
        return min(75, max(1, base_bid))
    
    def _get_drop_candidate(
        self,
        pickup_player: Player,
        team_needs: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Suggest a player to drop for the pickup"""
        
        position_data = team_needs.get(pickup_player.position, {})
        weakest_player = position_data.get('weakest_player')
        
        if weakest_player:
            pickup_value = PlayerService.calculate_player_value(
                self.db,
                pickup_player.id,
                self.scoring_type
            )
            
            if pickup_value > weakest_player['value']:
                return {
                    'player': weakest_player['player'],
                    'value_difference': round(pickup_value - weakest_player['value'], 2)
                }
        
        return None
    
    def _generate_pickup_reasoning(
        self,
        player: Player,
        need_multiplier: float,
        trending_factor: float,
        opportunity_factor: float
    ) -> str:
        """Generate human-readable reasoning for pickup"""
        
        reasons = []
        
        # Position-based reasons
        if player.position in ['RB', 'WR']:
            reasons.append(f"Skill position depth")
        
        # Need-based reasons
        if need_multiplier > 1.3:
            reasons.append("High team need")
        elif need_multiplier > 1.1:
            reasons.append("Addresses positional need")
        
        # Performance-based reasons
        if trending_factor > 1.2:
            reasons.append("Strong recent performance")
        elif trending_factor > 1.1:
            reasons.append("Trending upward")
        elif trending_factor < 0.8:
            reasons.append("Recent struggles")
        
        # Opportunity-based reasons
        if opportunity_factor > 1.1:
            reasons.append("Increased opportunity")
        elif opportunity_factor < 0.95:
            reasons.append("Limited touches")
        
        # Injury status
        if player.injury_status == 'Questionable':
            reasons.append("Monitor injury status")
        
        return "; ".join(reasons) if reasons else f"Solid {player.position} option"
    
    def get_trending_players(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get players trending up in performance"""
        
        available_players = self._get_available_players()
        trending = []
        
        for player in available_players:
            trending_factor = self._calculate_trending_factor(player.id)
            
            if trending_factor > 1.1:  # Only include players trending up
                trending.append({
                    'player': player,
                    'trending_factor': round(trending_factor, 2),
                    'recent_avg': self._get_recent_average(player.id),
                    'season_avg': self._get_season_average(player.id)
                })
        
        # Sort by trending factor
        trending.sort(key=lambda x: x['trending_factor'], reverse=True)
        
        return trending[:limit]
    
    def _get_recent_average(self, player_id: int) -> float:
        """Get player's recent average fantasy points"""
        recent_stats = PlayerService.get_player_recent_stats(self.db, player_id, 3)
        
        if not recent_stats:
            return 0.0
        
        total = sum(
            getattr(stat, f'fantasy_points_{self.scoring_type}')
            for stat in recent_stats
        )
        
        return round(total / len(recent_stats), 2)
    
    def _get_season_average(self, player_id: int) -> float:
        """Get player's season average fantasy points per game"""
        season_stats = PlayerService.get_player_season_stats(
            self.db,
            player_id,
            self.league.current_season or 2024
        )
        
        if not season_stats or season_stats.games_played == 0:
            return 0.0
        
        total_points = getattr(season_stats, f'fantasy_points_{self.scoring_type}')
        return round(total_points / season_stats.games_played, 2)
    
    def analyze_waiver_claims(self, week: int) -> Dict[str, Any]:
        """Analyze waiver claim competition for the week"""
        
        claims = self.db.query(WaiverClaim).filter(
            WaiverClaim.league.has(id=self.league.id),
            WaiverClaim.claim_week == week,
            WaiverClaim.status == 'PENDING'
        ).all()
        
        # Group claims by player
        player_claims = defaultdict(list)
        for claim in claims:
            player_claims[claim.player_to_add_id].append(claim)
        
        analysis = {
            'total_claims': len(claims),
            'contested_players': [],
            'uncontested_claims': [],
            'highest_bids': []
        }
        
        for player_id, player_claims_list in player_claims.items():
            player = self.db.query(Player).filter(Player.id == player_id).first()
            
            if len(player_claims_list) > 1:
                # Contested player
                max_bid = max(claim.faab_bid for claim in player_claims_list)
                analysis['contested_players'].append({
                    'player': player,
                    'num_claims': len(player_claims_list),
                    'highest_bid': max_bid,
                    'competition_level': 'High' if len(player_claims_list) > 3 else 'Medium'
                })
            else:
                # Uncontested
                analysis['uncontested_claims'].append({
                    'player': player,
                    'bid': player_claims_list[0].faab_bid
                })
            
            # Track highest bids
            for claim in player_claims_list:
                analysis['highest_bids'].append({
                    'player': player,
                    'team': claim.team,
                    'bid': claim.faab_bid
                })
        
        # Sort highest bids
        analysis['highest_bids'].sort(key=lambda x: x['bid'], reverse=True)
        analysis['highest_bids'] = analysis['highest_bids'][:10]
        
        return analysis