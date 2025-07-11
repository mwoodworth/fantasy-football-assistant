#!/usr/bin/env python3
"""
Create an admin user for the Fantasy Football Assistant application.

Usage:
    python3 create_admin.py
"""

import os
import sys
import getpass
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import SessionLocal, engine
from src.models.user import User
from src.models import Base
from src.auth import get_password_hash
from sqlalchemy import select

def create_admin():
    """Create an admin user interactively."""
    print("=== Fantasy Football Assistant - Create Admin User ===\n")
    
    # Get user input
    email = input("Enter admin email: ").strip()
    if not email:
        print("Error: Email is required")
        return
    
    username = input("Enter admin username: ").strip()
    if not username:
        print("Error: Username is required")
        return
    
    first_name = input("Enter first name (optional): ").strip() or None
    last_name = input("Enter last name (optional): ").strip() or None
    
    # Get password with confirmation
    while True:
        password = getpass.getpass("Enter password: ")
        if len(password) < 8:
            print("Error: Password must be at least 8 characters long")
            continue
            
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("Error: Passwords do not match")
            continue
            
        break
    
    # Ask for admin type
    is_superadmin = False
    admin_type = input("\nCreate as superadmin? (y/N): ").strip().lower()
    if admin_type == 'y':
        is_superadmin = True
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                print(f"\nError: User with email '{email}' already exists")
            else:
                print(f"\nError: User with username '{username}' already exists")
            return
        
        # Create new admin user
        new_user = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_admin=True,
            is_superadmin=is_superadmin,
            is_premium=True  # Admins get premium features
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"\n✅ Admin user created successfully!")
        print(f"   Email: {new_user.email}")
        print(f"   Username: {new_user.username}")
        print(f"   Type: {'Superadmin' if is_superadmin else 'Admin'}")
        print(f"   User ID: {new_user.id}")
        
    except Exception as e:
        print(f"\nError creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def list_admins():
    """List all existing admin users."""
    db = SessionLocal()
    
    try:
        admins = db.query(User).filter(
            (User.is_admin == True) | (User.is_superadmin == True)
        ).all()
        
        if not admins:
            print("\nNo admin users found.")
            return
        
        print(f"\n=== Admin Users ({len(admins)}) ===\n")
        for admin in admins:
            admin_type = "Superadmin" if admin.is_superadmin else "Admin"
            status = "Active" if admin.is_active else "Suspended"
            print(f"ID: {admin.id}")
            print(f"  Email: {admin.email}")
            print(f"  Username: {admin.username}")
            print(f"  Name: {admin.first_name or ''} {admin.last_name or ''}")
            print(f"  Type: {admin_type}")
            print(f"  Status: {status}")
            print(f"  Created: {admin.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
    except Exception as e:
        print(f"\nError listing admins: {e}")
    finally:
        db.close()

def main():
    """Main entry point."""
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_admins()
    else:
        create_admin()

if __name__ == "__main__":
    main()