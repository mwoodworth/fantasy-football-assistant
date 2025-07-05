"""
ESPN API client for fetching NFL and fantasy football data
"""

import requests
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from ..config import settings

logger = logging.getLogger(__name__)


class ESPNClient:
    """ESPN API client for NFL and fantasy data"""
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    FANTASY_URL = "https://fantasy.espn.com/apis/v3/games/ffl"
    
    def __init__(self):
        self.session = None
        self.current_season = settings.current_nfl_season
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_nfl_teams(self) -> List[Dict[str, Any]]:
        """Get all NFL teams"""
        try:
            session = await self._get_session()
            url = f"{self.BASE_URL}/teams"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    teams = []
                    
                    for team in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                        team_data = team.get('team', {})
                        teams.append({
                            'id': team_data.get('id'),
                            'name': team_data.get('displayName'),
                            'abbreviation': team_data.get('abbreviation'),
                            'city': team_data.get('location'),
                            'conference': team_data.get('conference', {}).get('name'),
                            'division': team_data.get('conference', {}).get('groups', [{}])[0].get('name'),
                            'logo_url': team_data.get('logos', [{}])[0].get('href'),
                            'primary_color': team_data.get('color'),
                            'stadium_name': team_data.get('venue', {}).get('fullName'),
                            'stadium_city': team_data.get('venue', {}).get('address', {}).get('city'),
                            'stadium_state': team_data.get('venue', {}).get('address', {}).get('state')
                        })
                    
                    logger.info(f"Fetched {len(teams)} NFL teams from ESPN")
                    return teams
                else:
                    logger.error(f"Failed to fetch teams: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching NFL teams: {e}")
            return []
    
    async def get_player_stats(self, season: int = None, week: int = None) -> List[Dict[str, Any]]:
        """Get player statistics for a given season/week"""
        if season is None:
            season = self.current_season
            
        try:
            session = await self._get_session()
            
            # Build URL based on whether week is specified
            if week:
                url = f"{self.BASE_URL}/seasons/{season}/types/2/weeks/{week}/athletes"
            else:
                url = f"{self.BASE_URL}/seasons/{season}/athletes"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    players = []
                    
                    for athlete in data.get('athletes', []):
                        player_data = self._parse_player_data(athlete, season, week)
                        if player_data:
                            players.append(player_data)
                    
                    logger.info(f"Fetched {len(players)} player stats for {season}")
                    return players
                else:
                    logger.error(f"Failed to fetch player stats: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching player stats: {e}")
            return []
    
    def _parse_player_data(self, athlete: Dict[str, Any], season: int, week: Optional[int]) -> Optional[Dict[str, Any]]:
        """Parse ESPN athlete data into our player format"""
        try:
            # Basic player info
            player_info = {
                'espn_id': athlete.get('id'),
                'name': athlete.get('displayName'),
                'position': athlete.get('position', {}).get('abbreviation'),
                'jersey_number': athlete.get('jersey'),
                'height': athlete.get('displayHeight'),
                'weight': athlete.get('weight'),
                'age': athlete.get('age'),
                'college': athlete.get('college', {}).get('name'),
                'team_id': athlete.get('team', {}).get('id'),
                'team_name': athlete.get('team', {}).get('displayName'),
                'team_abbreviation': athlete.get('team', {}).get('abbreviation'),
                'is_active': athlete.get('active', True),
                'injury_status': athlete.get('injuries', [{}])[0].get('status') if athlete.get('injuries') else 'Healthy'
            }
            
            # Parse statistics if available
            stats = athlete.get('statistics', [])
            if stats:
                player_info['stats'] = self._parse_player_stats(stats[0], season, week)
            
            return player_info
            
        except Exception as e:
            logger.warning(f"Error parsing player data for {athlete.get('displayName', 'Unknown')}: {e}")
            return None
    
    def _parse_player_stats(self, stats: Dict[str, Any], season: int, week: Optional[int]) -> Dict[str, Any]:
        """Parse ESPN statistics into our stats format"""
        stat_data = {
            'season': season,
            'week': week,
            'games_played': 0,
            'games_started': 0,
            
            # Passing stats
            'pass_attempts': 0,
            'pass_completions': 0,
            'pass_yards': 0,
            'pass_touchdowns': 0,
            'interceptions': 0,
            
            # Rushing stats
            'rush_attempts': 0,
            'rush_yards': 0,
            'rush_touchdowns': 0,
            
            # Receiving stats
            'targets': 0,
            'receptions': 0,
            'receiving_yards': 0,
            'receiving_touchdowns': 0,
            
            # Kicking stats
            'field_goals_made': 0,
            'field_goals_attempted': 0,
            'extra_points_made': 0,
            'extra_points_attempted': 0,
            
            # Fantasy points (calculated)
            'fantasy_points_standard': 0,
            'fantasy_points_ppr': 0,
            'fantasy_points_half_ppr': 0
        }
        
        # Map ESPN stat names to our field names
        stat_mapping = {
            'passingAttempts': 'pass_attempts',
            'passingCompletions': 'pass_completions',
            'passingYards': 'pass_yards',
            'passingTouchdowns': 'pass_touchdowns',
            'interceptions': 'interceptions',
            'rushingAttempts': 'rush_attempts',
            'rushingYards': 'rush_yards',
            'rushingTouchdowns': 'rush_touchdowns',
            'receivingTargets': 'targets',
            'receivingReceptions': 'receptions',
            'receivingYards': 'receiving_yards',
            'receivingTouchdowns': 'receiving_touchdowns',
            'fieldGoalsMade': 'field_goals_made',
            'fieldGoalsAttempted': 'field_goals_attempted',
            'extraPointsMade': 'extra_points_made',
            'extraPointsAttempted': 'extra_points_attempted'
        }
        
        # Extract stats from ESPN format
        for stat_category in stats.get('stats', []):
            for stat_name, stat_value in stat_category.items():
                if stat_name in stat_mapping:
                    stat_data[stat_mapping[stat_name]] = float(stat_value) if stat_value else 0
        
        # Calculate fantasy points
        stat_data['fantasy_points_standard'] = self._calculate_fantasy_points(stat_data, 'standard')
        stat_data['fantasy_points_ppr'] = self._calculate_fantasy_points(stat_data, 'ppr')
        stat_data['fantasy_points_half_ppr'] = self._calculate_fantasy_points(stat_data, 'half_ppr')
        
        return stat_data
    
    def _calculate_fantasy_points(self, stats: Dict[str, Any], scoring_type: str) -> float:
        """Calculate fantasy points based on scoring system"""
        points = 0.0
        
        # Passing points (1 point per 25 yards, 4 points per TD, -2 per INT)
        points += (stats['pass_yards'] / 25) * 1
        points += stats['pass_touchdowns'] * 4
        points += stats['interceptions'] * -2
        
        # Rushing points (1 point per 10 yards, 6 points per TD)
        points += (stats['rush_yards'] / 10) * 1
        points += stats['rush_touchdowns'] * 6
        
        # Receiving points (1 point per 10 yards, 6 points per TD)
        points += (stats['receiving_yards'] / 10) * 1
        points += stats['receiving_touchdowns'] * 6
        
        # PPR bonus
        if scoring_type == 'ppr':
            points += stats['receptions'] * 1
        elif scoring_type == 'half_ppr':
            points += stats['receptions'] * 0.5
        
        # Kicking points
        points += stats['field_goals_made'] * 3
        points += stats['extra_points_made'] * 1
        
        return round(points, 2)
    
    async def get_current_week(self) -> int:
        """Get the current NFL week"""
        try:
            session = await self._get_session()
            url = f"{self.BASE_URL}/scoreboard"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    current_week = data.get('week', {}).get('number', 1)
                    logger.info(f"Current NFL week: {current_week}")
                    return current_week
                else:
                    logger.warning("Failed to fetch current week, defaulting to 1")
                    return 1
                    
        except Exception as e:
            logger.error(f"Error fetching current week: {e}")
            return 1


# Singleton instance
espn_client = ESPNClient()