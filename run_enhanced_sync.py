#!/usr/bin/env python3
"""
Standalone script to run enhanced player sync
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append('.')

# Set environment variables
os.environ['DATABASE_URL'] = 'sqlite:///./fantasy_football.db'

from src.models.database import SessionLocal, create_tables
# Import directly to avoid circular imports
from src.services.player_sync import PlayerSyncService

async def run_enhanced_sync():
    print('🚀 Starting enhanced player sync with historical data...')
    print('This will collect all available player data from ESPN including historical stats.\n')
    
    # Create tables if they don't exist
    print('📋 Creating database tables...')
    create_tables()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Run enhanced sync with historical data
        print('🔄 Fetching players from ESPN...')
        result = await PlayerSyncService.sync_all_players(
            db, 
            force=True, 
            include_historical=True
        )
        
        print('\n' + '='*50)
        print('📊 ENHANCED SYNC RESULTS')
        print('='*50)
        print(f'📥 Total players fetched: {result["total_fetched"]}')
        print(f'🆕 New players added: {result["synced_count"]}')
        print(f'🔄 Players updated: {result["updated_count"]}')
        print(f'📈 Historical stats synced: {result["stats_synced"]}')
        print(f'❌ Errors encountered: {len(result["errors"])}')
        
        if result['errors']:
            print('\n🚨 Error Details (first 5):')
            for i, error in enumerate(result['errors'][:5], 1):
                print(f'  {i}. {error}')
        
        print('\n✅ Enhanced sync completed successfully!')
        print(f'💾 Database now contains comprehensive player data with historical stats.')
        
    except Exception as e:
        print(f'\n❌ Error during enhanced sync: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(run_enhanced_sync())