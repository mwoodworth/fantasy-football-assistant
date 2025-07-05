"""
User model for authentication and user management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import bcrypt
from typing import Optional


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
    
    # Relationships
    fantasy_teams = relationship("FantasyTeam", back_populates="owner")
    trades = relationship("Trade", back_populates="user")
    waiver_claims = relationship("WaiverClaim", back_populates="user")

    def set_password(self, password: str) -> None:
        """Hash and set the user's password"""
        salt = bcrypt.gensalt()
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """Verify the user's password"""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.hashed_password.encode('utf-8')
        )

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"