"""Yahoo Fantasy League models."""

from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from src.core.database import Base

class YahooLeague(Base):
    """Yahoo Fantasy League model."""
    
    __tablename__ = "yahoo_leagues"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_key = Column(String, unique=True, nullable=False, index=True)
    league_id = Column(String, nullable=False)
    game_key = Column(String, nullable=False)  # e.g., "423" for NFL 2024
    
    # League details
    name = Column(String, nullable=False)
    season = Column(Integer, nullable=False)
    num_teams = Column(Integer, nullable=False)
    scoring_type = Column(String)  # "head" for H2H, "points" for points league
    league_type = Column(String)  # "private", "public", "pro"
    draft_status = Column(String)  # "predraft", "drafting", "postdraft"
    current_week = Column(Integer)
    
    # Settings
    settings = Column(JSON)  # Full league settings
    scoring_settings = Column(JSON)  # Scoring configuration
    roster_positions = Column(JSON)  # Roster requirements
    
    # User's team in this league
    user_team_key = Column(String)
    user_team_name = Column(String)
    user_team_rank = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="yahoo_leagues")
    teams = relationship("YahooTeam", back_populates="league", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<YahooLeague {self.name} ({self.league_key})>"


class YahooTeam(Base):
    """Yahoo Fantasy Team model."""
    
    __tablename__ = "yahoo_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("yahoo_leagues.id"), nullable=False)
    team_key = Column(String, unique=True, nullable=False, index=True)
    team_id = Column(Integer, nullable=False)
    
    # Team details
    name = Column(String, nullable=False)
    manager_name = Column(String)
    logo_url = Column(String)
    
    # Performance
    rank = Column(Integer)
    points_for = Column(Float)
    points_against = Column(Float)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    
    # Waiver/FAAB info
    waiver_priority = Column(Integer)
    faab_balance = Column(Float)
    number_of_moves = Column(Integer, default=0)
    number_of_trades = Column(Integer, default=0)
    
    # Ownership
    is_owned_by_current_login = Column(Boolean, default=False)
    
    # Roster
    roster = Column(JSON)  # Current roster snapshot
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    league = relationship("YahooLeague", back_populates="teams")
    
    def __repr__(self):
        return f"<YahooTeam {self.name} ({self.team_key})>"


class YahooPlayer(Base):
    """Yahoo player data cache."""
    
    __tablename__ = "yahoo_players"
    
    id = Column(Integer, primary_key=True, index=True)
    player_key = Column(String, unique=True, nullable=False, index=True)
    player_id = Column(Integer, nullable=False)
    
    # Player info
    name_full = Column(String, nullable=False, index=True)
    name_first = Column(String)
    name_last = Column(String)
    editorial_team_abbr = Column(String)  # NFL team abbreviation
    uniform_number = Column(Integer)
    
    # Position info
    position_type = Column(String)  # "O" for offense, "D" for defense
    primary_position = Column(String)
    eligible_positions = Column(JSON)  # List of eligible positions
    
    # Status
    status = Column(String)  # "A" for active
    injury_note = Column(String)
    
    # Stats and projections (season totals)
    season_points = Column(Float)
    projected_season_points = Column(Float)
    percent_owned = Column(Float)
    
    # Additional data
    bye_week = Column(Integer)
    image_url = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced = Column(DateTime)
    
    def __repr__(self):
        return f"<YahooPlayer {self.name_full} ({self.player_key})>"