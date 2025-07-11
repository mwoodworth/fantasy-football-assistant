#!/usr/bin/env python3
"""Create Yahoo Fantasy tables"""

import sqlite3
import sys

def create_yahoo_tables():
    try:
        # Connect to the database
        conn = sqlite3.connect('fantasy_football.db')
        cursor = conn.cursor()
        
        # Create yahoo_leagues table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_leagues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            league_key VARCHAR UNIQUE NOT NULL,
            league_id VARCHAR NOT NULL,
            game_key VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            season INTEGER NOT NULL,
            num_teams INTEGER NOT NULL,
            scoring_type VARCHAR,
            league_type VARCHAR,
            draft_status VARCHAR,
            current_week INTEGER,
            settings TEXT,
            scoring_settings TEXT,
            roster_positions TEXT,
            user_team_key VARCHAR,
            user_team_name VARCHAR,
            user_team_rank INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_synced TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # Create yahoo_teams table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER NOT NULL,
            team_key VARCHAR UNIQUE NOT NULL,
            team_id INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            manager_name VARCHAR,
            logo_url VARCHAR,
            rank INTEGER,
            points_for REAL,
            points_against REAL,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            ties INTEGER DEFAULT 0,
            waiver_priority INTEGER,
            faab_balance REAL,
            number_of_moves INTEGER DEFAULT 0,
            number_of_trades INTEGER DEFAULT 0,
            is_owned_by_current_login BOOLEAN DEFAULT 0,
            roster TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (league_id) REFERENCES yahoo_leagues (id)
        )
        """)
        
        # Create yahoo_players table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_key VARCHAR UNIQUE NOT NULL,
            player_id INTEGER NOT NULL,
            name_full VARCHAR NOT NULL,
            name_first VARCHAR,
            name_last VARCHAR,
            editorial_team_abbr VARCHAR,
            uniform_number INTEGER,
            position_type VARCHAR,
            primary_position VARCHAR,
            eligible_positions TEXT,
            status VARCHAR,
            injury_note VARCHAR,
            season_points REAL,
            projected_season_points REAL,
            percent_owned REAL,
            bye_week INTEGER,
            image_url VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_synced TIMESTAMP
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_yahoo_leagues_user_id ON yahoo_leagues(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_yahoo_teams_league_id ON yahoo_teams(league_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_yahoo_players_name ON yahoo_players(name_full)")
        
        conn.commit()
        print("Successfully created Yahoo Fantasy tables")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_yahoo_tables()