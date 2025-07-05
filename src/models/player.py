"""
Player and team models for NFL data
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from typing import Optional


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # "Dallas Cowboys"
    abbreviation = Column(String(10), unique=True, nullable=False)  # "DAL"
    city = Column(String(100))  # "Dallas"
    conference = Column(String(10))  # "NFC" or "AFC"
    division = Column(String(20))  # "NFC East"
    
    # Team colors and branding
    primary_color = Column(String(7))  # Hex color
    secondary_color = Column(String(7))
    logo_url = Column(String(500))
    
    # Stadium info
    stadium_name = Column(String(100))
    stadium_city = Column(String(100))
    stadium_state = Column(String(50))
    
    # Relationships
    players = relationship("Player", back_populates="team")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', abbr='{self.abbreviation}')>"


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    espn_id = Column(Integer, unique=True, index=True)  # ESPN player ID
    name = Column(String(100), nullable=False)
    position = Column(String(10), nullable=False)  # QB, RB, WR, TE, K, DEF
    jersey_number = Column(Integer)
    
    # Team relationship
    team_id = Column(Integer, ForeignKey("teams.id"))
    team = relationship("Team", back_populates="players")
    
    # Physical attributes
    height = Column(String(10))  # "6'2""
    weight = Column(Integer)  # pounds
    age = Column(Integer)
    college = Column(String(100))
    years_pro = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True)
    injury_status = Column(String(50))  # "Healthy", "Questionable", "Doubtful", "Out", "IR"
    injury_description = Column(Text)
    
    # Fantasy relevance
    fantasy_positions = Column(String(50))  # "QB", "RB,WR", etc.
    bye_week = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    stats = relationship("PlayerStats", back_populates="player")
    roster_entries = relationship("Roster", back_populates="player")
    
    @property
    def display_name(self) -> str:
        """Get formatted display name"""
        team_abbr = self.team.abbreviation if self.team else "FA"
        return f"{self.name} ({team_abbr} - {self.position})"
    
    @property
    def is_skill_position(self) -> bool:
        """Check if player is a skill position (QB, RB, WR, TE)"""
        return self.position in ["QB", "RB", "WR", "TE"]
    
    def __repr__(self):
        return f"<Player(id={self.id}, name='{self.name}', position='{self.position}')>"


class PlayerStats(Base):
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    # Time period
    season = Column(Integer, nullable=False)  # 2024
    week = Column(Integer)  # 1-18, None for season totals
    game_date = Column(DateTime)
    
    # Basic stats
    games_played = Column(Integer, default=0)
    games_started = Column(Integer, default=0)
    
    # Passing stats
    pass_attempts = Column(Integer, default=0)
    pass_completions = Column(Integer, default=0)
    pass_yards = Column(Integer, default=0)
    pass_touchdowns = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)
    
    # Rushing stats
    rush_attempts = Column(Integer, default=0)
    rush_yards = Column(Integer, default=0)
    rush_touchdowns = Column(Integer, default=0)
    
    # Receiving stats
    targets = Column(Integer, default=0)
    receptions = Column(Integer, default=0)
    receiving_yards = Column(Integer, default=0)
    receiving_touchdowns = Column(Integer, default=0)
    
    # Kicking stats
    field_goals_made = Column(Integer, default=0)
    field_goals_attempted = Column(Integer, default=0)
    extra_points_made = Column(Integer, default=0)
    extra_points_attempted = Column(Integer, default=0)
    
    # Defense stats (for DEF position)
    sacks = Column(Float, default=0)
    interceptions_def = Column(Integer, default=0)
    fumbles_recovered = Column(Integer, default=0)
    touchdowns_def = Column(Integer, default=0)
    safety = Column(Integer, default=0)
    points_allowed = Column(Integer, default=0)
    yards_allowed = Column(Integer, default=0)
    
    # Fantasy points
    fantasy_points_standard = Column(Float, default=0)
    fantasy_points_ppr = Column(Float, default=0)
    fantasy_points_half_ppr = Column(Float, default=0)
    
    # Projections (for future weeks)
    is_projection = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    player = relationship("Player", back_populates="stats")
    
    @property
    def completion_percentage(self) -> Optional[float]:
        """Calculate completion percentage"""
        if self.pass_attempts > 0:
            return round((self.pass_completions / self.pass_attempts) * 100, 1)
        return None
    
    @property
    def yards_per_carry(self) -> Optional[float]:
        """Calculate yards per carry"""
        if self.rush_attempts > 0:
            return round(self.rush_yards / self.rush_attempts, 1)
        return None
    
    @property
    def field_goal_percentage(self) -> Optional[float]:
        """Calculate field goal percentage"""
        if self.field_goals_attempted > 0:
            return round((self.field_goals_made / self.field_goals_attempted) * 100, 1)
        return None
    
    def __repr__(self):
        period = f"Week {self.week}" if self.week else "Season"
        return f"<PlayerStats(player_id={self.player_id}, {self.season} {period})>"