#!/usr/bin/env python3
"""Add Yahoo OAuth token column to users table"""

import sqlite3
import sys

def add_yahoo_column():
    try:
        # Connect to the database
        conn = sqlite3.connect('fantasy_football.db')
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'yahoo_oauth_token' not in columns:
            # Add the column
            cursor.execute("ALTER TABLE users ADD COLUMN yahoo_oauth_token TEXT")
            conn.commit()
            print("Successfully added yahoo_oauth_token column to users table")
        else:
            print("yahoo_oauth_token column already exists")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_yahoo_column()