#!/usr/bin/env python3
"""
Reset the database to a fresh state with all tables created.
This is useful for development when migrations are broken.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    print("🔄 Fantasy Football Assistant - Database Reset Tool")
    print("=" * 50)
    
    # Check if database exists
    db_path = Path("fantasy_football.db")
    if db_path.exists():
        response = input("\n⚠️  Database file exists. Delete and recreate? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled.")
            return
        
        # Remove existing database
        print(f"\n🗑️  Removing existing database: {db_path}")
        db_path.unlink()
        print("✅ Database removed successfully")
    
    # Create new database with all tables
    print("\n📊 Creating fresh database with all tables...")
    try:
        from src.models.database import engine, Base
        # Import all models to ensure their tables are registered with Base
        from src.models import (
            User, Player, PlayerStats, Team, League, FantasyTeam,
            Roster, Trade, WaiverClaim, ESPNLeague, DraftSession,
            DraftRecommendation, DraftEvent, LeagueHistoricalData, 
            UserLeagueSettings, ESPNTeam, TradeRecommendation, TeamSyncLog
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Set alembic version to latest
        print("\n🔧 Setting alembic version to latest migration...")
        from sqlalchemy import create_engine, text
        
        engine = create_engine('sqlite:///fantasy_football.db')
        with engine.connect() as conn:
            # Create alembic version table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            '''))
            
            # Clear any existing versions
            conn.execute(text('DELETE FROM alembic_version'))
            
            # Insert the latest version
            conn.execute(text("INSERT INTO alembic_version VALUES ('006_add_draft_session_fields')"))
            conn.commit()
        
        print("✅ Alembic version set to latest!")
        
        # Verify tables were created
        print("\n📋 Verifying database tables...")
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            'users', 'players', 'teams', 'leagues', 'fantasy_teams',
            'roster', 'trades', 'waiver_claims', 'player_stats',
            'espn_leagues', 'espn_teams', 'draft_sessions', 'draft_events',
            'draft_recommendations', 'trade_recommendations', 'team_sync_logs',
            'league_historical_data', 'user_league_settings', 'alembic_version'
        ]
        
        print(f"\n📊 Found {len(tables)} tables:")
        for table in sorted(tables):
            status = "✅" if table in expected_tables else "❓"
            print(f"  {status} {table}")
        
        missing_tables = set(expected_tables) - set(tables)
        if missing_tables:
            print(f"\n⚠️  Warning: Missing expected tables: {', '.join(missing_tables)}")
        else:
            print("\n✅ All expected tables are present!")
        
        # Check draft_sessions columns
        print("\n🔍 Checking draft_sessions table columns...")
        columns = inspector.get_columns('draft_sessions')
        column_names = [col['name'] for col in columns]
        
        required_columns = [
            'draft_status', 'current_pick_team_id', 'pick_deadline',
            'last_espn_sync', 'sync_errors', 'available_players',
            'last_recommendation_time', 'recommendation_count'
        ]
        
        missing_columns = set(required_columns) - set(column_names)
        if missing_columns:
            print(f"⚠️  Missing columns in draft_sessions: {', '.join(missing_columns)}")
            print("   These columns may need to be added manually.")
        else:
            print("✅ All required draft_sessions columns are present!")
        
        print("\n🎉 Database reset completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Start the application: python3 scripts/start_with_websockets.py")
        print("   2. Register a new user or use test credentials")
        print("   3. The draft monitor errors should now be resolved")
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\n💡 Make sure you're running this from the project root with the virtual environment activated:")
        print("   source venv/bin/activate")
        print("   python3 scripts/reset_database.py")
        return 1
    except Exception as e:
        print(f"\n❌ Error creating database: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())