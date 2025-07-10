"""
Player service for player data management and analysis
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from ..models.player import Player, PlayerStats, Team
from ..models.fantasy import League
import logging

logger = logging.getLogger(__name__)


class PlayerService:
    """Handle player-related operations and analysis"""
    
    @staticmethod
    def get_players_by_position(db: Session, position: str, limit: int = 50) -> List[Player]:
        """Get players by position"""
        return db.query(Player).filter(
            Player.position == position,
            Player.is_active == True
        ).limit(limit).all()
    
    @staticmethod
    def get_available_players(db: Session, league_id: int, position: str = None) -> List[Player]:
        """Get players not on any roster in the league"""
        # This would normally check against roster table
        # For now, return all active players
        query = db.query(Player).filter(Player.is_active == True)
        
        if position:
            query = query.filter(Player.position == position)
        
        return query.all()
    
    @staticmethod
    def search_players(db: Session, query: str, limit: int = 20) -> List[Player]:
        """Search players by name or team"""
        search_term = f"%{query}%"
        return db.query(Player).filter(
            or_(
                Player.name.ilike(search_term),
                Player.team.has(Team.name.ilike(search_term)),
                Player.team.has(Team.abbreviation.ilike(search_term))
            )
        ).filter(Player.is_active == True).limit(limit).all()
    
    @staticmethod
    def get_player_projections(db: Session, player_id: int, week: int = None) -> Optional[PlayerStats]:
        """Get player projections for a specific week or season"""
        query = db.query(PlayerStats).filter(
            PlayerStats.player_id == player_id,
            PlayerStats.is_projection == True
        )
        
        if week:
            query = query.filter(PlayerStats.week == week)
        else:
            query = query.filter(PlayerStats.week.is_(None))  # Season projections
        
        return query.first()
    
    @staticmethod
    def get_player_season_stats(db: Session, player_id: int, season: int) -> Optional[PlayerStats]:
        """Get player's season stats"""
        return db.query(PlayerStats).filter(
            PlayerStats.player_id == player_id,
            PlayerStats.season == season,
            PlayerStats.week.is_(None),  # Season totals
            PlayerStats.is_projection == False
        ).first()
    
    @staticmethod
    def get_player_recent_stats(db: Session, player_id: int, weeks: int = 4) -> List[PlayerStats]:
        """Get player's recent weekly stats"""
        return db.query(PlayerStats).filter(
            PlayerStats.player_id == player_id,
            PlayerStats.week.isnot(None),
            PlayerStats.is_projection == False
        ).order_by(PlayerStats.week.desc()).limit(weeks).all()
    
    @staticmethod
    def calculate_player_value(db: Session, player_id: int, scoring_type: str = 'standard') -> float:
        """Calculate player's fantasy value based on projections and recent performance"""
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return 0.0
        
        # Get season projections
        projections = PlayerService.get_player_projections(db, player_id)
        if not projections:
            return 0.0
        
        # Base value from projections
        if scoring_type == 'ppr':
            base_value = projections.fantasy_points_ppr
        elif scoring_type == 'half_ppr':
            base_value = projections.fantasy_points_half_ppr
        else:
            base_value = projections.fantasy_points_standard
        
        # Adjust based on position scarcity
        position_multiplier = PlayerService._get_position_multiplier(player.position)
        
        # Adjust based on recent performance trend
        recent_stats = PlayerService.get_player_recent_stats(db, player_id, 4)
        trend_multiplier = PlayerService._calculate_trend_multiplier(recent_stats, scoring_type)
        
        # Adjust for injury status
        injury_multiplier = PlayerService._get_injury_multiplier(player.injury_status)
        
        final_value = base_value * position_multiplier * trend_multiplier * injury_multiplier
        
        return round(final_value, 2)
    
    @staticmethod
    def _get_position_multiplier(position: str) -> float:
        """Get position scarcity multiplier"""
        multipliers = {
            'QB': 0.9,   # Lower scarcity, many viable options
            'RB': 1.2,   # High scarcity, limited supply
            'WR': 1.0,   # Balanced
            'TE': 1.1,   # Moderate scarcity
            'K': 0.8,    # Low importance
            'DEF': 0.8   # Low importance
        }
        return multipliers.get(position, 1.0)
    
    @staticmethod
    def _calculate_trend_multiplier(recent_stats: List[PlayerStats], scoring_type: str) -> float:
        """Calculate performance trend multiplier"""
        if not recent_stats or len(recent_stats) < 2:
            return 1.0
        
        # Get fantasy points for each week
        points = []
        for stat in recent_stats:
            if scoring_type == 'ppr':
                points.append(stat.fantasy_points_ppr)
            elif scoring_type == 'half_ppr':
                points.append(stat.fantasy_points_half_ppr)
            else:
                points.append(stat.fantasy_points_standard)
        
        # Calculate trend (simple linear regression slope)
        n = len(points)
        if n < 2:
            return 1.0
        
        x_sum = sum(range(n))
        y_sum = sum(points)
        xy_sum = sum(i * points[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        if n * x2_sum - x_sum * x_sum == 0:
            return 1.0
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        # Convert slope to multiplier (trending up = higher value)
        if slope > 2:
            return 1.1  # Strong upward trend
        elif slope > 0:
            return 1.05  # Mild upward trend
        elif slope > -2:
            return 0.95  # Mild downward trend
        else:
            return 0.9   # Strong downward trend
    
    @staticmethod
    def _get_injury_multiplier(injury_status: str) -> float:
        """Get injury status multiplier"""
        multipliers = {
            'Healthy': 1.0,
            'Probable': 0.95,
            'Questionable': 0.85,
            'Doubtful': 0.7,
            'Out': 0.5,
            'IR': 0.2,
            'PUP': 0.1
        }
        return multipliers.get(injury_status, 1.0)
    
    @staticmethod
    def get_position_rankings(db: Session, position: str, scoring_type: str = 'standard', limit: int = 50) -> List[Dict[str, Any]]:
        """Get player rankings for a specific position"""
        players = PlayerService.get_players_by_position(db, position, limit * 2)  # Get more to filter
        
        rankings = []
        for player in players:
            value = PlayerService.calculate_player_value(db, player.id, scoring_type)
            rankings.append({
                'player': player,
                'value': value,
                'rank': 0  # Will be set after sorting
            })
        
        # Sort by value and assign ranks
        rankings.sort(key=lambda x: x['value'], reverse=True)
        for i, ranking in enumerate(rankings[:limit]):
            ranking['rank'] = i + 1
        
        return rankings[:limit]
    
    @staticmethod
    def get_bye_week_players(db: Session, week: int) -> List[Player]:
        """Get players on bye for a specific week"""
        return db.query(Player).filter(
            Player.bye_week == week,
            Player.is_active == True
        ).all()
    
    @staticmethod
    def get_injury_report(db: Session) -> List[Player]:
        """Get current injury report"""
        return db.query(Player).filter(
            Player.injury_status.notin_(['Healthy', None]),
            Player.is_active == True
        ).all()
    
    @staticmethod
    def sync_espn_player(db: Session, espn_player_data: Dict[str, Any]) -> Player:
        """Sync ESPN player data to local database"""
        espn_id = espn_player_data.get('id')
        
        # Check if player already exists
        player = db.query(Player).filter(Player.espn_id == espn_id).first()
        
        if not player:
            # Create new player
            player = Player(
                espn_id=espn_id,
                name=espn_player_data.get('fullName'),
                position=espn_player_data.get('defaultPositionId'),
                jersey_number=espn_player_data.get('jersey'),
                height=espn_player_data.get('height'),
                weight=espn_player_data.get('weight'),
                age=espn_player_data.get('age'),
                college=espn_player_data.get('college'),
                is_active=espn_player_data.get('active', True)
            )
            
            # Set team if available
            if espn_player_data.get('proTeamId'):
                team = db.query(Team).filter(Team.espn_id == espn_player_data['proTeamId']).first()
                if team:
                    player.team_id = team.id
                    player.team_name = team.name
                    player.team_abbreviation = team.abbreviation
            
            db.add(player)
            logger.info(f"Created new player: {player.name}")
        else:
            # Update existing player
            player.name = espn_player_data.get('fullName', player.name)
            player.position = espn_player_data.get('defaultPositionId', player.position)
            player.jersey_number = espn_player_data.get('jersey', player.jersey_number)
            player.height = espn_player_data.get('height', player.height)
            player.weight = espn_player_data.get('weight', player.weight)
            player.age = espn_player_data.get('age', player.age)
            player.college = espn_player_data.get('college', player.college)
            player.is_active = espn_player_data.get('active', player.is_active)
            
            # Update team if changed
            if espn_player_data.get('proTeamId'):
                team = db.query(Team).filter(Team.espn_id == espn_player_data['proTeamId']).first()
                if team and team.id != player.team_id:
                    player.team_id = team.id
                    player.team_name = team.name
                    player.team_abbreviation = team.abbreviation
            
            logger.info(f"Updated player: {player.name}")
        
        # Update injury status if available
        if espn_player_data.get('injuryStatus'):
            player.injury_status = espn_player_data['injuryStatus']
        
        # Update bye week if available
        if espn_player_data.get('byeWeek'):
            player.bye_week = espn_player_data['byeWeek']
        
        db.commit()
        db.refresh(player)
        
        return player