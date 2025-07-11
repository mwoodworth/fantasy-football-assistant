#!/usr/bin/env python3
"""
Fix teams table by adding missing columns.
"""

import sys
from pathlib import Path
from sqlalchemy import text

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import engine

def fix_teams_table():
    """Add missing columns to teams table"""
    
    with engine.connect() as conn:
        # Check which columns already exist
        result = conn.execute(text("PRAGMA table_info(teams)"))
        existing_columns = {row[1] for row in result}
        
        print(f"Existing columns: {existing_columns}")
        
        # List of columns that should exist
        required_columns = [
            ("espn_id", "INTEGER", "NULL"),
            ("abbreviation", "VARCHAR(10)", "NULL"),
            ("city", "VARCHAR(100)", "NULL"),
            ("conference", "VARCHAR(20)", "NULL"),
            ("division", "VARCHAR(20)", "NULL"),
            ("primary_color", "VARCHAR(7)", "NULL"),
            ("secondary_color", "VARCHAR(7)", "NULL"),
            ("logo_url", "VARCHAR(500)", "NULL"),
            ("stadium_name", "VARCHAR(200)", "NULL"),
            ("stadium_city", "VARCHAR(100)", "NULL"),
            ("stadium_state", "VARCHAR(50)", "NULL"),
        ]
        
        # Add missing columns
        for col_name, col_type, default_value in required_columns:
            if col_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE teams ADD COLUMN {col_name} {col_type} DEFAULT {default_value}"
                    conn.execute(text(alter_sql))
                    conn.commit()
                    print(f"✅ Added column: {col_name}")
                except Exception as e:
                    print(f"❌ Error adding column {col_name}: {e}")
            else:
                print(f"✓ Column already exists: {col_name}")
        
        print("\n✅ Teams table fixed!")

if __name__ == "__main__":
    fix_teams_table()