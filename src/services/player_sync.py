"""
Enhanced player synchronization service for ESPN data with full stats collection
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import httpx

from ..models.player import Player, PlayerStats
from ..api.espn_players_enhanced import fetch_all_players_from_espn, get_position_name, get_team_name

logger = logging.getLogger(__name__)


class PlayerSyncService:
    """Enhanced service for syncing comprehensive player data from ESPN"""
    
    # ESPN stat ID mappings
    STAT_MAPPINGS = {
        # Passing
        "0": "pass_attempts",
        "1": "pass_completions", 
        "3": "pass_yards",
        "4": "pass_touchdowns",
        "20": "interceptions",
        
        # Rushing
        "23": "rush_attempts",
        "24": "rush_yards", 
        "25": "rush_touchdowns",
        
        # Receiving
        "53": "targets",
        "58": "receptions",
        "42": "receiving_yards",
        "43": "receiving_touchdowns",
        
        # Kicking
        "74": "field_goals_made",
        "75": "field_goals_attempted",
        "77": "extra_points_made",
        "78": "extra_points_attempted",
        
        # Defense
        "99": "sacks",
        "95": "interceptions_def",
        "96": "fumbles_recovered",
        "98": "touchdowns_def",
        "97": "safety",
        "120": "points_allowed",
        "121": "yards_allowed"
    }
    
    @staticmethod
    async def fetch_enhanced_player_data(player_id: int, include_stats: bool = True, league_id: int = 730253008) -> Dict[str, Any]:
        """Fetch comprehensive player data including projections from league endpoint"""
        # Use the league endpoint which includes projections
        url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leagues/{league_id}"
        
        headers = {
            "accept": "application/json",
            "x-fantasy-platform": "kona-PROD-9488cfa0d0fb59d75804777bfee76c2f161a89b1",
            "x-fantasy-source": "kona",
            "referer": "https://fantasy.espn.com/"
        }
        
        params = {
            "scoringPeriodId": 1,
            "view": "kona_player_info"
        }
        
        # Filter for specific player with projection data
        filter_obj = {
            "players": {
                "filterIds": {"value": [player_id]},
                "limit": 1,
                "filterStatsForTopScoringPeriodIds": {
                    "value": 2,
                    "additionalValue": ["002025", "102025", "002024", "1120251", "022025"]
                }
            }
        }
        headers["x-fantasy-filter"] = str(filter_obj).replace("'", '"')
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data and "players" in data and len(data["players"]) > 0:
                    return data["players"][0]["player"]
                return {}
                
            except Exception as e:
                logger.error(f"Error fetching enhanced data for player {player_id}: {e}")
                return {}
    
    @staticmethod
    async def sync_all_players(db: Session, force: bool = False, include_historical: bool = True) -> Dict[str, Any]:
        """Sync all players from ESPN to local database with enhanced data collection"""
        try:
            logger.info("Starting enhanced player sync from ESPN")
            
            # Fetch all players from ESPN
            espn_players = await fetch_all_players_from_espn(force_refresh=force)
            logger.info(f"Fetched {len(espn_players)} players from ESPN")
            
            sync_result = {
                "total_fetched": len(espn_players),
                "synced_count": 0,
                "updated_count": 0,
                "stats_synced": 0,
                "errors": []
            }
            
            # Process players in batches
            batch_size = 50  # Smaller batches for enhanced data
            for i in range(0, len(espn_players), batch_size):
                batch = espn_players[i:i + batch_size]
                
                for espn_player in batch:
                    try:
                        # Skip players without names
                        player_name = espn_player.get("fullName")
                        if not player_name:
                            continue
                        
                        # Process enhanced player data
                        player_sync_result = await PlayerSyncService._sync_single_player(
                            db, espn_player, include_historical
                        )
                        
                        if player_sync_result["success"]:
                            if player_sync_result["is_new"]:
                                sync_result["synced_count"] += 1
                            else:
                                sync_result["updated_count"] += 1
                            
                            if player_sync_result["stats_count"] > 0:
                                sync_result["stats_synced"] += player_sync_result["stats_count"]
                        else:
                            sync_result["errors"].append(player_sync_result["error"])
                    
                    except Exception as e:
                        error_msg = f"Error syncing player {espn_player.get('fullName', 'Unknown')}: {str(e)}"
                        logger.error(error_msg)
                        sync_result["errors"].append(error_msg)
                
                # Commit batch
                db.commit()
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(espn_players) + batch_size - 1)//batch_size}")
            
            logger.info(f"Enhanced player sync completed: {sync_result['synced_count']} new, {sync_result['updated_count']} updated, {sync_result['stats_synced']} stats")
            return sync_result
            
        except Exception as e:
            logger.error(f"Failed to sync players: {e}")
            db.rollback()
            return {
                "total_fetched": 0,
                "synced_count": 0,
                "updated_count": 0,
                "stats_synced": 0,
                "errors": [str(e)]
            }
    
    @staticmethod
    async def _sync_single_player(db: Session, espn_player: Dict[str, Any], include_historical: bool = True) -> Dict[str, Any]:
        """Sync a single player with all available data"""
        result = {
            "success": False,
            "is_new": False,
            "stats_count": 0,
            "error": None
        }
        
        try:
            player_id = espn_player.get("id")
            player_name = espn_player.get("fullName")
            
            # Check if player exists
            existing_player = db.query(Player).filter(Player.espn_id == player_id).first()
            
            # Prepare comprehensive player data
            ownership_data = espn_player.get("ownership", {})
            injury_data = espn_player.get("injuryDetails", {})
            
            player_data = {
                "espn_id": player_id,
                "name": player_name,
                "position": get_position_name(espn_player.get("defaultPositionId", 0)),
                "team_name": get_team_name(espn_player.get("proTeamId", 0)),
                "team_abbreviation": get_team_name(espn_player.get("proTeamId", 0)),
                "jersey_number": int(espn_player.get("jersey")) if espn_player.get("jersey", "").isdigit() else None,
                
                # Status and activity
                "is_active": espn_player.get("active", True),
                "injury_status": espn_player.get("injuryStatus"),
                "injury_description": injury_data.get("type"),
                
                # ESPN ownership data
                "ownership_percentage": ownership_data.get("percentOwned", 0),
                "start_percentage": ownership_data.get("percentStarted", 0),
                "draft_average_pick": ownership_data.get("averageDraftPosition"),
                
                # ESPN IDs
                "pro_team_id": espn_player.get("proTeamId", 0),
                "default_position_id": espn_player.get("defaultPositionId", 0),
                
                # Draft rankings if available
                "draft_rank": None  # Will be populated from draftRanksByRankType if available
            }
            
            # Extract draft rankings
            draft_ranks = espn_player.get("draftRanksByRankType", {})
            if "STANDARD" in draft_ranks:
                player_data["draft_rank"] = draft_ranks["STANDARD"].get("rank")
            
            # Create or update player
            if existing_player:
                for key, value in player_data.items():
                    if value is not None:  # Only update non-null values
                        setattr(existing_player, key, value)
                player = existing_player
                result["is_new"] = False
            else:
                player = Player(**player_data)
                db.add(player)
                db.flush()  # Get the ID
                result["is_new"] = True
            
            # Sync historical stats if requested
            if include_historical:
                stats_count = await PlayerSyncService._sync_player_stats(
                    db, player, espn_player.get("stats", [])
                )
                result["stats_count"] = stats_count
            
            result["success"] = True
            return result
            
        except Exception as e:
            result["error"] = f"Error syncing player {espn_player.get('fullName', 'Unknown')}: {str(e)}"
            logger.error(result["error"])
            return result
    
    @staticmethod
    async def _sync_player_stats(db: Session, player: Player, stats_data: List[Dict[str, Any]]) -> int:
        """Sync all available stats including projections for a player"""
        stats_synced = 0
        
        try:
            for stat_entry in stats_data:
                season = stat_entry.get("seasonId")
                scoring_period = stat_entry.get("scoringPeriodId", 0)
                stat_source = stat_entry.get("statSourceId", 0)
                split_type = stat_entry.get("statSplitTypeId", 0)
                stats = stat_entry.get("stats", {})
                applied_total = stat_entry.get("appliedTotal", 0)
                
                if not season:
                    continue
                
                # Determine if this is weekly or season stats/projections
                week = scoring_period if scoring_period > 0 else None
                
                # Determine if this is a projection (statSourceId: 1) or actual (statSourceId: 0)
                is_projection = (stat_source == 1)
                
                # Check if stats already exist
                existing_stats = db.query(PlayerStats).filter(
                    PlayerStats.player_id == player.id,
                    PlayerStats.season == season,
                    PlayerStats.week == week,
                    PlayerStats.is_projection == is_projection
                ).first()
                
                # Parse ESPN stats into our format
                parsed_stats = PlayerSyncService._parse_espn_stats(stats)
                
                # Determine fantasy points based on scoring system
                fantasy_points = applied_total if applied_total > 0 else 0
                
                stat_data = {
                    "player_id": player.id,
                    "season": season,
                    "week": week,
                    "is_projection": is_projection,
                    "fantasy_points_standard": fantasy_points,
                    "fantasy_points_ppr": fantasy_points,  # ESPN likely uses league settings
                    **parsed_stats
                }
                
                if existing_stats:
                    # Update existing stats
                    for key, value in stat_data.items():
                        if hasattr(existing_stats, key) and value is not None:
                            setattr(existing_stats, key, value)
                else:
                    # Create new stats entry
                    new_stats = PlayerStats(**stat_data)
                    db.add(new_stats)
                    stats_synced += 1
                
                # Update player's season projection if this is a season projection
                if is_projection and week is None and season == 2025:
                    player.projected_total_points = fantasy_points
            
            return stats_synced
            
        except Exception as e:
            logger.error(f"Error syncing stats for player {player.name}: {e}")
            return 0
    
    @staticmethod
    def _parse_espn_stats(espn_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ESPN stats format into our database format"""
        parsed = {}
        
        for espn_stat_id, value in espn_stats.items():
            if espn_stat_id in PlayerSyncService.STAT_MAPPINGS:
                field_name = PlayerSyncService.STAT_MAPPINGS[espn_stat_id]
                
                # Convert to appropriate type
                if isinstance(value, (int, float)):
                    parsed[field_name] = value
                elif isinstance(value, str) and value.replace('.', '').isdigit():
                    parsed[field_name] = float(value) if '.' in value else int(value)
        
        return parsed
    
    @staticmethod
    async def sync_league_players(db: Session, league_id: int, espn_league_id: int, 
                                 season: int = 2025, force: bool = False, include_historical: bool = True) -> Dict[str, Any]:
        """Sync players for a specific league with enhanced data collection"""
        # For now, just sync all players with enhanced data
        # In the future, this could be optimized to only sync players in the league
        return await PlayerSyncService.sync_all_players(db, force, include_historical)
    
    @staticmethod
    async def sync_historical_stats_only(db: Session, limit_players: int = None) -> Dict[str, Any]:
        """One-time sync of historical stats for existing players"""
        try:
            logger.info("Starting historical stats sync for existing players")
            
            # Get existing players without many stats
            query = db.query(Player).filter(Player.espn_id.isnot(None))
            if limit_players:
                query = query.limit(limit_players)
            
            players = query.all()
            logger.info(f"Found {len(players)} players to sync historical stats")
            
            sync_result = {
                "players_processed": 0,
                "total_stats_synced": 0,
                "errors": []
            }
            
            for player in players:
                try:
                    # Fetch enhanced data for this player
                    enhanced_data = await PlayerSyncService.fetch_enhanced_player_data(
                        player.espn_id, include_stats=True
                    )
                    
                    if enhanced_data and "stats" in enhanced_data:
                        stats_count = await PlayerSyncService._sync_player_stats(
                            db, player, enhanced_data["stats"]
                        )
                        sync_result["total_stats_synced"] += stats_count
                        
                        # Update player with any new info
                        if "ownership" in enhanced_data:
                            ownership = enhanced_data["ownership"]
                            player.ownership_percentage = ownership.get("percentOwned", player.ownership_percentage)
                            player.start_percentage = ownership.get("percentStarted", player.start_percentage)
                        
                        if "injuryStatus" in enhanced_data:
                            player.injury_status = enhanced_data["injuryStatus"]
                    
                    sync_result["players_processed"] += 1
                    
                    # Commit every 10 players
                    if sync_result["players_processed"] % 10 == 0:
                        db.commit()
                        logger.info(f"Processed {sync_result['players_processed']}/{len(players)} players")
                
                except Exception as e:
                    error_msg = f"Error syncing historical stats for {player.name}: {str(e)}"
                    logger.error(error_msg)
                    sync_result["errors"].append(error_msg)
            
            # Final commit
            db.commit()
            
            logger.info(f"Historical stats sync completed: {sync_result['players_processed']} players, {sync_result['total_stats_synced']} stats")
            return sync_result
            
        except Exception as e:
            logger.error(f"Failed to sync historical stats: {e}")
            db.rollback()
            return {
                "players_processed": 0,
                "total_stats_synced": 0,
                "errors": [str(e)]
            }
    
    @staticmethod
    def sync_player_stats(db: Session, player_id: int, stats_data: Dict[str, Any]) -> bool:
        """Legacy method - use _sync_player_stats instead"""
        logger.warning("sync_player_stats is deprecated, use enhanced sync methods")
        return True


# Export service instance
player_sync_service = PlayerSyncService()