#!/usr/bin/env python3
"""
Script to seed the database with mock NFL data for testing
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import our modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from models.database import SessionLocal, create_tables
from utils.mock_data import seed_mock_data
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main function to seed mock data"""
    
    print("🏈 Fantasy Football Assistant - Mock Data Seeder")
    print("=" * 50)
    
    try:
        # Create database tables
        print("Creating database tables...")
        create_tables()
        print("✓ Database tables created")
        
        # Create database session
        db = SessionLocal()
        
        try:
            print("\nGenerating mock data...")
            results = seed_mock_data(db)
            
            print("\n✓ Mock data generation completed successfully!")
            print(f"✓ Created {len(results['teams'])} NFL teams")
            print(f"✓ Created {len(results['players'])} players")
            print(f"✓ Generated {len(results['stats'])} player stat records")
            print(f"✓ Created test league with {len(results['test_users'])} users")
            
            print("\n🎯 Test Login Credentials:")
            print("Email: test@example.com")
            print("Password: test_password_hash")
            
            print("\n🚀 You can now test all Phase 2 features!")
            print("- Draft Assistant: Get recommendations for your test league")
            print("- Lineup Optimizer: Optimize lineups with mock player data")
            print("- Waiver Wire Analyzer: Find trending players")
            print("- Trade Analyzer: Evaluate trade proposals")
            
        except Exception as e:
            logger.error(f"Error generating mock data: {e}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()