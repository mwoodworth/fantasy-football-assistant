#!/usr/bin/env python3
"""Add admin fields to users table and create admin activity log table"""

import sqlite3
import sys
from datetime import datetime

def add_admin_fields():
    try:
        # Connect to the database
        conn = sqlite3.connect('fantasy_football.db')
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add admin fields to users table if they don't exist
        if 'is_admin' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            print("Added is_admin column")
        
        if 'is_superadmin' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_superadmin BOOLEAN DEFAULT 0")
            print("Added is_superadmin column")
            
        if 'admin_notes' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN admin_notes TEXT")
            print("Added admin_notes column")
            
        if 'permissions' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT")
            print("Added permissions column")
        
        # Create admin activity log table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action VARCHAR NOT NULL,
            target_type VARCHAR,
            target_id INTEGER,
            details TEXT,
            ip_address VARCHAR,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users (id)
        )
        """)
        print("Created admin_activity_logs table")
        
        # Create indexes for performance
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_activity_logs_admin_id 
        ON admin_activity_logs(admin_id)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_activity_logs_created_at 
        ON admin_activity_logs(created_at)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_is_admin 
        ON users(is_admin)
        """)
        
        print("Created indexes")
        
        conn.commit()
        print("Successfully added admin fields and created admin tables")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_admin_fields()