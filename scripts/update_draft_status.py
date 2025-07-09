#!/usr/bin/env python3
"""
Script to update draft status for existing leagues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import SessionLocal
from src.models.espn_league import ESPNLeague

def update_league_draft_status(league_id, draft_completed=True):
    """Update a specific league's draft status"""
    db = SessionLocal()
    try:
        league = db.query(ESPNLeague).filter(ESPNLeague.id == league_id).first()
        if league:
            league.draft_completed = draft_completed
            db.commit()
            print(f"Updated league {league_id} ({league.league_name}) draft_completed to {draft_completed}")
        else:
            print(f"League {league_id} not found")
    except Exception as e:
        print(f"Error updating league: {e}")
        db.rollback()
    finally:
        db.close()

def list_leagues():
    """List all leagues and their draft status"""
    db = SessionLocal()
    try:
        leagues = db.query(ESPNLeague).all()
        print("\nCurrent leagues:")
        print("-" * 60)
        for league in leagues:
            print(f"ID: {league.id} | ESPN ID: {league.espn_league_id} | Name: {league.league_name}")
            print(f"   Draft Completed: {league.draft_completed} | Archived: {league.is_archived}")
            print("-" * 60)
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_leagues()
        elif sys.argv[1] == "update" and len(sys.argv) >= 3:
            league_id = int(sys.argv[2])
            draft_completed = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else True
            update_league_draft_status(league_id, draft_completed)
        else:
            print("Usage:")
            print("  python scripts/update_draft_status.py list")
            print("  python scripts/update_draft_status.py update <league_id> [true|false]")
    else:
        # Default action - list leagues
        list_leagues()