#!/usr/bin/env python3
"""Create Yahoo draft-related tables"""

import sqlite3
import sys

def create_yahoo_draft_tables():
    try:
        # Connect to the database
        conn = sqlite3.connect('fantasy_football.db')
        cursor = conn.cursor()
        
        # Create yahoo_draft_sessions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_draft_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            league_id INTEGER NOT NULL,
            session_token VARCHAR UNIQUE NOT NULL,
            draft_status VARCHAR DEFAULT 'predraft',
            current_pick INTEGER DEFAULT 1,
            current_round INTEGER DEFAULT 1,
            draft_order TEXT,
            snake_draft BOOLEAN DEFAULT 1,
            user_draft_position INTEGER,
            user_team_key VARCHAR,
            drafted_players TEXT,
            live_sync_enabled BOOLEAN DEFAULT 1,
            last_sync TIMESTAMP,
            sync_interval_seconds INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (league_id) REFERENCES yahoo_leagues (id)
        )
        """)
        
        # Create yahoo_draft_recommendations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_draft_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_session_id INTEGER NOT NULL,
            recommended_players TEXT,
            primary_recommendation TEXT,
            positional_needs TEXT,
            value_picks TEXT,
            sleepers TEXT,
            avoid_players TEXT,
            confidence_score REAL,
            ai_insights TEXT,
            current_pick INTEGER,
            current_round INTEGER,
            team_roster TEXT,
            available_players TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (draft_session_id) REFERENCES yahoo_draft_sessions (id)
        )
        """)
        
        # Create yahoo_draft_events table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_draft_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_session_id INTEGER NOT NULL,
            event_type VARCHAR NOT NULL,
            event_data TEXT,
            pick_number INTEGER,
            round_number INTEGER,
            team_key VARCHAR,
            player_key VARCHAR,
            player_name VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (draft_session_id) REFERENCES yahoo_draft_sessions (id)
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_yahoo_draft_sessions_user_id ON yahoo_draft_sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_yahoo_draft_sessions_league_id ON yahoo_draft_sessions(league_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_yahoo_draft_sessions_token ON yahoo_draft_sessions(session_token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_yahoo_draft_recommendations_session ON yahoo_draft_recommendations(draft_session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_yahoo_draft_events_session ON yahoo_draft_events(draft_session_id)")
        
        conn.commit()
        print("Successfully created Yahoo draft tables")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_yahoo_draft_tables()