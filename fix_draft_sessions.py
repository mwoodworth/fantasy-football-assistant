#!/usr/bin/env python3
"""
Fix draft_sessions table by adding missing columns.
"""

import sys
from pathlib import Path
from sqlalchemy import text

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import engine

def fix_draft_sessions_table():
    """Add missing columns to draft_sessions table"""
    
    with engine.connect() as conn:
        # Check which columns already exist
        result = conn.execute(text("PRAGMA table_info(draft_sessions)"))
        existing_columns = {row[1] for row in result}
        
        print(f"Existing columns: {existing_columns}")
        
        # List of columns that should exist (based on the model)
        required_columns = [
            ("draft_status", "VARCHAR(20)", "'not_started'"),
            ("current_pick_team_id", "INTEGER", "NULL"),
            ("pick_deadline", "DATETIME", "NULL"),
            ("last_espn_sync", "DATETIME", "NULL"),
            ("sync_errors", "JSON", "'[]'"),
            ("is_live_synced", "BOOLEAN", "0"),
            ("manual_mode", "BOOLEAN", "0"),
        ]
        
        # Add missing columns
        for col_name, col_type, default_value in required_columns:
            if col_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE draft_sessions ADD COLUMN {col_name} {col_type} DEFAULT {default_value}"
                    conn.execute(text(alter_sql))
                    conn.commit()
                    print(f"✅ Added column: {col_name}")
                except Exception as e:
                    print(f"❌ Error adding column {col_name}: {e}")
            else:
                print(f"✓ Column already exists: {col_name}")
        
        print("\n✅ Draft sessions table fixed!")

if __name__ == "__main__":
    fix_draft_sessions_table()