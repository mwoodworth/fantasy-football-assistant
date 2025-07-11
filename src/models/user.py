"""
User model for authentication and user management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import bcrypt
import base64
import json
from typing import Optional, List, Dict


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    
    # Admin fields
    is_admin = Column(Boolean, default=False)
    is_superadmin = Column(Boolean, default=False)
    admin_notes = Column(Text)  # Internal notes about admin actions
    permissions = Column(Text)  # JSON string of granular permissions
    
    # Fantasy preferences
    favorite_team = Column(String(50))  # NFL team abbreviation
    default_league_size = Column(Integer, default=12)
    preferred_scoring = Column(String(20), default="standard")  # standard, ppr, half_ppr
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Profile info
    bio = Column(Text)
    avatar_url = Column(String(500))
    
    # OAuth tokens
    yahoo_oauth_token = Column(Text)  # Encrypted Yahoo OAuth token
    
    # Relationships
    fantasy_teams = relationship("FantasyTeam", back_populates="owner")
    trades = relationship("Trade", back_populates="user")
    waiver_claims = relationship("WaiverClaim", back_populates="user")
    espn_leagues = relationship("ESPNLeague", back_populates="user", cascade="all, delete-orphan")
    yahoo_leagues = relationship("YahooLeague", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Hash and set the user's password"""
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
        # Store as base64 string to safely preserve binary data
        self.hashed_password = base64.b64encode(hashed_bytes).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """Verify the user's password"""
        try:
            # Try to decode as base64 (new format)
            hashed_bytes = base64.b64decode(self.hashed_password.encode('utf-8'))
        except Exception:
            # Fallback for legacy UTF-8 encoded passwords (if any exist)
            hashed_bytes = self.hashed_password.encode('utf-8')
        
        return bcrypt.checkpw(password.encode('utf-8'), hashed_bytes)

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission"""
        if self.is_superadmin:
            return True
        
        if not self.is_admin:
            return False
            
        if not self.permissions:
            return False
            
        try:
            perms = json.loads(self.permissions)
            return permission in perms
        except (json.JSONDecodeError, TypeError):
            return False
    
    def get_permissions(self) -> List[str]:
        """Get list of user permissions"""
        if self.is_superadmin:
            # Superadmin has all permissions
            return ["*"]
            
        if not self.is_admin or not self.permissions:
            return []
            
        try:
            return json.loads(self.permissions)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_permissions(self, permissions: List[str]) -> None:
        """Set user permissions"""
        self.permissions = json.dumps(permissions)
    
    @property
    def role(self) -> str:
        """Get user's role"""
        if self.is_superadmin:
            return "superadmin"
        elif self.is_admin:
            return "admin"
        else:
            return "user"

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', role='{self.role}')>"