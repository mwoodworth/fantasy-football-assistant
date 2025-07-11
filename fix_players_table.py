#!/usr/bin/env python3
"""
Fix players table by adding missing columns.
"""

import sys
from pathlib import Path
from sqlalchemy import text

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import engine

def fix_players_table():
    """Add missing columns to players table"""
    
    with engine.connect() as conn:
        # Check which columns already exist
        result = conn.execute(text("PRAGMA table_info(players)"))
        existing_columns = {row[1] for row in result}
        
        print(f"Existing columns: {existing_columns}")
        
        # List of columns that should exist
        required_columns = [
            ("ownership_percentage", "FLOAT", "NULL"),
            ("start_percentage", "FLOAT", "NULL"),
            ("pro_team_id", "INTEGER", "NULL"),
            ("default_position_id", "INTEGER", "NULL"),
            ("draft_rank", "INTEGER", "NULL"),
            ("draft_average_pick", "FLOAT", "NULL"),
            ("projected_total_points", "FLOAT", "NULL"),
            ("rest_of_season_projection", "FLOAT", "NULL"),
            ("consistency_rating", "FLOAT", "NULL"),
            ("boom_percentage", "FLOAT", "NULL"),
            ("bust_percentage", "FLOAT", "NULL"),
            ("team_name", "VARCHAR(100)", "NULL"),
            ("team_abbreviation", "VARCHAR(10)", "NULL"),
        ]
        
        # Add missing columns
        for col_name, col_type, default_value in required_columns:
            if col_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE players ADD COLUMN {col_name} {col_type} DEFAULT {default_value}"
                    conn.execute(text(alter_sql))
                    conn.commit()
                    print(f"✅ Added column: {col_name}")
                except Exception as e:
                    print(f"❌ Error adding column {col_name}: {e}")
            else:
                print(f"✓ Column already exists: {col_name}")
        
        print("\n✅ Players table fixed!")

if __name__ == "__main__":
    fix_players_table()