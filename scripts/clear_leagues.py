#!/usr/bin/env python3
"""
Script to clear all ESPN leagues from the database for testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database import DATABASE_URL, SessionLocal
from src.models.espn_league import ESPNLeague, DraftSession, DraftRecommendation, LeagueHistoricalData

def clear_all_leagues():
    """Clear all ESPN leagues and related data from the database"""
    db = SessionLocal()
    
    try:
        # Get counts before deletion
        league_count = db.query(ESPNLeague).count()
        session_count = db.query(DraftSession).count()
        
        print(f"Found {league_count} leagues to delete")
        print(f"Found {session_count} draft sessions to delete")
        
        # Delete in order to respect foreign key constraints
        # First delete draft recommendations
        rec_count = db.query(DraftRecommendation).count()
        db.query(DraftRecommendation).delete()
        print(f"Deleted {rec_count} draft recommendations")
        
        # Delete draft sessions
        db.query(DraftSession).delete()
        print(f"Deleted {session_count} draft sessions")
        
        # Delete historical data
        hist_count = db.query(LeagueHistoricalData).count()
        db.query(LeagueHistoricalData).delete()
        print(f"Deleted {hist_count} historical data records")
        
        # Finally delete all leagues
        db.query(ESPNLeague).delete()
        print(f"Deleted {league_count} leagues")
        
        db.commit()
        print("\nAll ESPN leagues and related data have been cleared!")
        
    except Exception as e:
        print(f"Error clearing leagues: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    response = input("Are you sure you want to delete ALL ESPN leagues? (yes/no): ")
    if response.lower() == 'yes':
        clear_all_leagues()
    else:
        print("Cancelled")