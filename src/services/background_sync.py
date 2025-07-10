"""
Background sync service for periodic data updates with rate limiting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from ..models.database import get_db
from ..models.fantasy import ESPNLeague
from ..models.player import Player
from .espn_integration import ESPNDataService, ESPNServiceError
from .player import PlayerService
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 30, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[float] = []
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        
        # Check if we need to wait
        if len(self.calls) >= self.max_calls:
            # Calculate how long to wait
            oldest_call = min(self.calls)
            wait_time = self.time_window - (now - oldest_call) + 1
            
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
                
                # Clean up old calls again after waiting
                now = time.time()
                self.calls = [call_time for call_time in self.calls 
                             if now - call_time < self.time_window]
        
        # Record this call
        self.calls.append(now)


class BackgroundSyncService:
    """Service for background synchronization of player and league data"""
    
    def __init__(self):
        self.espn_service = ESPNDataService()
        self.rate_limiter = RateLimiter(max_calls=30, time_window=60)
        self.is_running = False
        self._sync_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background sync service"""
        if self.is_running:
            logger.warning("Background sync already running")
            return
        
        self.is_running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("Background sync service started")
    
    async def stop(self):
        """Stop the background sync service"""
        self.is_running = False
        
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None
        
        logger.info("Background sync service stopped")
    
    async def _sync_loop(self):
        """Main sync loop that runs periodically"""
        while self.is_running:
            try:
                # Sync data
                await self._sync_all_data()
                
                # Wait before next sync (30 minutes)
                await asyncio.sleep(1800)
                
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                # Wait 5 minutes before retrying on error
                await asyncio.sleep(300)
    
    async def _sync_all_data(self):
        """Sync all league and player data"""
        logger.info("Starting background sync of all data")
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get all active ESPN leagues
            leagues = db.query(ESPNLeague).filter(
                ESPNLeague.is_active == True,
                ESPNLeague.is_archived == False
            ).all()
            
            for league in leagues:
                try:
                    await self._sync_league_data(db, league)
                except Exception as e:
                    logger.error(f"Error syncing league {league.id}: {e}")
            
            # Sync trending players
            await self._sync_trending_players(db)
            
            db.commit()
            logger.info("Background sync completed successfully")
            
        except Exception as e:
            logger.error(f"Error in background sync: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _sync_league_data(self, db: Session, league: ESPNLeague):
        """Sync data for a specific league"""
        logger.info(f"Syncing data for league {league.league_name} (ID: {league.id})")
        
        # Rate limit check
        await self.rate_limiter.wait_if_needed()
        
        try:
            # Get league info
            league_data = await self.espn_service.get_league_info(
                league.espn_id, 
                league.season
            )
            
            # Update league details if changed
            if league_data:
                league.team_count = league_data.get('team_count', league.team_count)
                league.draft_date = league_data.get('draft_date', league.draft_date)
                league.draft_completed = league_data.get('draft_completed', league.draft_completed)
            
            # Sync league players
            await self._sync_league_players(db, league)
            
            # Update sync timestamp
            league.last_sync_at = datetime.utcnow()
            league.sync_status = 'success'
            
        except ESPNServiceError as e:
            logger.error(f"ESPN service error for league {league.id}: {e}")
            league.sync_status = 'error'
            league.sync_error = str(e)
    
    async def _sync_league_players(self, db: Session, league: ESPNLeague):
        """Sync all players in a league"""
        logger.info(f"Syncing players for league {league.id}")
        
        # Rate limit check
        await self.rate_limiter.wait_if_needed()
        
        try:
            # Get all players in the league
            result = await self.espn_service.sync_league_players(
                league.espn_id,
                league.season,
                force=False
            )
            
            logger.info(f"Synced {result.get('synced_count', 0)} players for league {league.id}")
            
        except Exception as e:
            logger.error(f"Error syncing players for league {league.id}: {e}")
    
    async def _sync_trending_players(self, db: Session):
        """Sync trending players data"""
        logger.info("Syncing trending players")
        
        try:
            # Rate limit check
            await self.rate_limiter.wait_if_needed()
            
            # Get trending adds
            trending_adds = await self.espn_service.get_trending_players(
                trend_type='add',
                hours=24,
                limit=50
            )
            
            # Rate limit check
            await self.rate_limiter.wait_if_needed()
            
            # Get trending drops
            trending_drops = await self.espn_service.get_trending_players(
                trend_type='drop',
                hours=24,
                limit=50
            )
            
            # Process trending data
            all_trending = trending_adds.get('players', []) + trending_drops.get('players', [])
            
            for player_data in all_trending:
                try:
                    # Sync player to database
                    PlayerService.sync_espn_player(db, player_data)
                except Exception as e:
                    logger.error(f"Error syncing trending player {player_data.get('id')}: {e}")
            
            logger.info(f"Synced {len(all_trending)} trending players")
            
        except Exception as e:
            logger.error(f"Error syncing trending players: {e}")
    
    async def sync_player_by_id(self, player_id: int) -> Dict[str, Any]:
        """Sync a specific player by ESPN ID"""
        logger.info(f"Syncing player {player_id}")
        
        # Rate limit check
        await self.rate_limiter.wait_if_needed()
        
        db = next(get_db())
        
        try:
            # Get player details from ESPN
            player_data = await self.espn_service.get_player_details(player_id)
            
            if not player_data:
                return {
                    'success': False,
                    'error': 'Player not found'
                }
            
            # Sync to database
            player = PlayerService.sync_espn_player(db, player_data)
            db.commit()
            
            return {
                'success': True,
                'player_id': player.id,
                'player_name': player.name
            }
            
        except Exception as e:
            logger.error(f"Error syncing player {player_id}: {e}")
            db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            db.close()


# Global instance
background_sync = BackgroundSyncService()