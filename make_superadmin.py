#!/usr/bin/env python3
"""
Make an existing user a superadmin.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import SessionLocal
from src.models.user import User

def make_superadmin(email: str):
    """Make an existing user a superadmin."""
    db = SessionLocal()
    
    try:
        # Find the user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"Error: User with email '{email}' not found")
            return False
        
        # Update user to be superadmin
        user.is_admin = True
        user.is_superadmin = True
        user.is_premium = True  # Superadmins get premium features
        
        db.commit()
        db.refresh(user)
        
        print(f"✅ Successfully made {user.username} ({user.email}) a superadmin!")
        print(f"   User ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Status: {'Active' if user.is_active else 'Inactive'}")
        
        return True
        
    except Exception as e:
        print(f"Error updating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    email = "mwoodworth33@gmail.com"
    make_superadmin(email)