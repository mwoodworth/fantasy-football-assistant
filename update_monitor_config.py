#!/usr/bin/env python3
"""
Update monitoring configuration to reduce log noise.
"""

import os

# Set environment variable to reduce monitoring frequency
def update_config():
    """Update configuration settings"""
    
    # Create or update .env file with monitoring settings
    env_file = "/home/mwoodworth/code/my-projects/fantasy-football-assistant/.env"
    
    new_settings = [
        "# Monitoring Settings",
        "DRAFT_MONITOR_INTERVAL=60  # Check every 60 seconds instead of 5",
        "LIVE_MONITOR_INTERVAL=300  # Check every 5 minutes instead of 30 seconds",
        "DISABLE_ESPN_SYNC_LOGS=true  # Reduce ESPN sync logging",
        "LOG_LEVEL=WARNING  # Reduce log verbosity",
    ]
    
    # Read existing .env if it exists
    existing_lines = []
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            existing_lines = f.readlines()
    
    # Add new settings if not already present
    settings_to_add = []
    for setting in new_settings:
        if not any(setting.split('=')[0] in line for line in existing_lines if '=' in setting):
            settings_to_add.append(setting + '\n')
    
    if settings_to_add:
        with open(env_file, 'a') as f:
            f.write('\n# Added by update_monitor_config.py\n')
            f.writelines(settings_to_add)
        print(f"✅ Added {len(settings_to_add)} new configuration settings to .env")
    else:
        print("ℹ️  All configuration settings already present")
    
    # Also update the services directly if they're running
    print("\n📝 Configuration Summary:")
    print("   - Draft monitor will check every 60 seconds")
    print("   - Live monitor will check every 5 minutes")
    print("   - ESPN sync logs will be reduced")
    print("   - Overall log level set to WARNING")
    print("\n⚠️  Restart the FastAPI server for changes to take effect")

if __name__ == "__main__":
    update_config()