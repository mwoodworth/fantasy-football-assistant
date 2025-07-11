#!/usr/bin/env python3
"""
Script to fix missing columns in draft_sessions table
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment or use default
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./fantasy_football.db')

def fix_draft_sessions_table():
    """Add missing columns to draft_sessions table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if columns exist first
        result = conn.execute(text("PRAGMA table_info(draft_sessions)"))
        existing_columns = [row[1] for row in result]
        
        columns_to_add = [
            ('draft_status', 'VARCHAR(50)', 'pending'),
            ('current_pick_team_id', 'INTEGER', None),
            ('pick_deadline', 'DATETIME', None),
            ('last_espn_sync', 'DATETIME', None),
            ('sync_errors', 'TEXT', None),
        ]
        
        for column_name, column_type, default_value in columns_to_add:
            if column_name not in existing_columns:
                print(f"Adding column {column_name}...")
                if default_value is not None:
                    query = f"ALTER TABLE draft_sessions ADD COLUMN {column_name} {column_type} DEFAULT '{default_value}'"
                else:
                    query = f"ALTER TABLE draft_sessions ADD COLUMN {column_name} {column_type}"
                conn.execute(text(query))
                conn.commit()
                print(f"✓ Added {column_name}")
            else:
                print(f"✓ Column {column_name} already exists")
        
        print("\nDraft sessions table structure updated successfully!")

if __name__ == "__main__":
    try:
        fix_draft_sessions_table()
    except Exception as e:
        print(f"Error fixing draft sessions table: {e}")
        sys.exit(1)