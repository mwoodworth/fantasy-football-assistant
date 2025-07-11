#!/usr/bin/env python3
"""
Clean up log files and reset services.
"""

import os
import subprocess
import time
from pathlib import Path

def clean_logs():
    """Clean up various log files"""
    log_files = [
        "/home/mwoodworth/code/my-projects/fantasy-football-assistant/espn-service/logs/error.log",
        "/home/mwoodworth/code/my-projects/fantasy-football-assistant/espn-service/logs/combined.log",
        "/home/mwoodworth/code/my-projects/fantasy-football-assistant/espn-service/espn.log",
        "/home/mwoodworth/code/my-projects/fantasy-football-assistant/espn-service/espn-service.log",
    ]
    
    print("🧹 Cleaning up log files...")
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                # Truncate the file instead of deleting it
                with open(log_file, 'w') as f:
                    f.write("")
                print(f"✅ Cleaned: {log_file}")
            except Exception as e:
                print(f"❌ Failed to clean {log_file}: {e}")
        else:
            print(f"⏭️  Skipped (not found): {log_file}")

def restart_espn_service():
    """Restart the ESPN service"""
    print("\n🔄 Restarting ESPN service...")
    
    # Kill existing ESPN service processes
    try:
        subprocess.run(["pkill", "-f", "node.*espn-service"], check=False)
        time.sleep(2)
        print("✅ Stopped existing ESPN service processes")
    except Exception as e:
        print(f"⚠️  Error stopping ESPN service: {e}")
    
    # The main.py startup will handle starting the ESPN service
    print("ℹ️  ESPN service will be started by the main application")

def update_live_monitor_config():
    """Update live monitor configuration to reduce log noise"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from src.models.database import SessionLocal
        from src.models.espn_league import ESPNLeague
        
        db = SessionLocal()
        try:
            # Reduce monitoring frequency for all leagues
            leagues = db.query(ESPNLeague).all()
            for league in leagues:
                if league.sync_frequency_minutes < 30:
                    league.sync_frequency_minutes = 30  # Check every 30 minutes instead
                    print(f"✅ Updated league {league.league_id} sync frequency to 30 minutes")
            
            db.commit()
            
        except Exception as e:
            print(f"❌ Error updating league configs: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Failed to update configs: {e}")

def main():
    """Run all cleanup tasks"""
    print("🚀 Starting server cleanup and optimization...\n")
    
    # 1. Clean log files
    clean_logs()
    
    # 2. Update monitoring config
    print("\n⚙️  Updating monitoring configuration...")
    update_live_monitor_config()
    
    # 3. Restart ESPN service
    restart_espn_service()
    
    print("\n✨ Cleanup complete! The server should now run with cleaner logs.")
    print("ℹ️  Note: Restart the FastAPI server to apply all changes.")

if __name__ == "__main__":
    main()