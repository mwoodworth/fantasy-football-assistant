#!/usr/bin/env python3
"""
Temporarily disable the draft monitor service to reduce log noise.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import SessionLocal
from src.models.espn_league import DraftSession

def disable_active_draft_sessions():
    """Mark all draft sessions as inactive to stop monitoring"""
    
    db = SessionLocal()
    try:
        # Find all active draft sessions
        active_sessions = db.query(DraftSession).filter(
            DraftSession.is_active == True
        ).all()
        
        if not active_sessions:
            print("No active draft sessions found.")
            return
        
        print(f"Found {len(active_sessions)} active draft session(s)")
        
        # Deactivate them
        for session in active_sessions:
            session.is_active = False
            session.is_live_synced = False
            print(f"✅ Deactivated draft session {session.id} for league {session.league_id}")
        
        db.commit()
        print("\n✅ All draft sessions deactivated. Draft monitor will stop checking.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    disable_active_draft_sessions()