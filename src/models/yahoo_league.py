"""Yahoo Fantasy League models."""

from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

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


class YahooDraftSession(Base):
    """Yahoo draft session for live draft tracking."""
    
    __tablename__ = "yahoo_draft_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("yahoo_leagues.id"), nullable=False)
    session_token = Column(String, unique=True, nullable=False, index=True)
    
    # Draft state
    draft_status = Column(String, default="predraft")  # predraft, drafting, completed
    current_pick = Column(Integer, default=1)
    current_round = Column(Integer, default=1)
    draft_order = Column(JSON)  # Team order for snake draft
    snake_draft = Column(Boolean, default=True)
    
    # User's position
    user_draft_position = Column(Integer)
    user_team_key = Column(String)
    
    # Draft picks made so far
    drafted_players = Column(JSON, default=list)  # List of {pick, round, team_key, player_key, player_name}
    
    # Sync settings
    live_sync_enabled = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    sync_interval_seconds = Column(Integer, default=10)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    league = relationship("YahooLeague")
    recommendations = relationship("YahooDraftRecommendation", back_populates="draft_session", cascade="all, delete-orphan")
    events = relationship("YahooDraftEvent", back_populates="draft_session", cascade="all, delete-orphan")
    
    def get_next_pick_number(self, current_pick: int, current_round: int, num_teams: int) -> int:
        """Calculate next pick number in snake draft."""
        if self.snake_draft:
            if current_round % 2 == 1:  # Odd round (1, 3, 5...)
                if current_pick % num_teams == 0:  # Last pick of round
                    return current_pick + 1
                else:
                    return current_pick + 1
            else:  # Even round (2, 4, 6...)
                if current_pick % num_teams == 1:  # First pick of round
                    return current_pick + 1
                else:
                    return current_pick + 1
        else:
            return current_pick + 1
    
    def get_picks_until_user_turn(self, num_teams: int) -> int:
        """Calculate how many picks until user's turn."""
        current_position = ((self.current_pick - 1) % num_teams) + 1
        
        if self.snake_draft and self.current_round % 2 == 0:
            # Even round - reverse order
            current_position = num_teams - current_position + 1
        
        if current_position < self.user_draft_position:
            return self.user_draft_position - current_position
        else:
            # User's turn passed in this round, calculate for next round
            if self.snake_draft:
                # In snake draft, position reverses each round
                if self.current_round % 2 == 1:
                    # Currently odd round, next will be even (reversed)
                    return (num_teams - current_position) + (num_teams - self.user_draft_position + 1)
                else:
                    # Currently even round, next will be odd (normal)
                    return (num_teams - current_position) + self.user_draft_position
            else:
                return num_teams - current_position + self.user_draft_position
    
    def __repr__(self):
        return f"<YahooDraftSession {self.id} - League {self.league_id}>"


class YahooDraftRecommendation(Base):
    """AI-generated draft recommendations for Yahoo drafts."""
    
    __tablename__ = "yahoo_draft_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    draft_session_id = Column(Integer, ForeignKey("yahoo_draft_sessions.id"), nullable=False)
    
    # Recommendation data
    recommended_players = Column(JSON)  # List of recommended players with analysis
    primary_recommendation = Column(JSON)  # Top recommended player
    
    # AI insights
    positional_needs = Column(JSON)  # Analysis of team needs by position
    value_picks = Column(JSON)  # Players providing best value at current pick
    sleepers = Column(JSON)  # Potential sleeper picks
    avoid_players = Column(JSON)  # Players to avoid with reasoning
    
    # Scoring and confidence
    confidence_score = Column(Float)  # 0-1 confidence in recommendations
    ai_insights = Column(String)  # Text explanation from AI
    
    # Context used for generation
    current_pick = Column(Integer)
    current_round = Column(Integer)
    team_roster = Column(JSON)  # Current roster state
    available_players = Column(JSON)  # Top available players snapshot
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    draft_session = relationship("YahooDraftSession", back_populates="recommendations")
    
    def __repr__(self):
        return f"<YahooDraftRecommendation {self.id} - Pick {self.current_pick}>"


class YahooDraftEvent(Base):
    """Track draft events for Yahoo drafts."""
    
    __tablename__ = "yahoo_draft_events"
    
    id = Column(Integer, primary_key=True, index=True)
    draft_session_id = Column(Integer, ForeignKey("yahoo_draft_sessions.id"), nullable=False)
    
    # Event details
    event_type = Column(String, nullable=False)  # pick_made, draft_started, draft_completed, sync_error
    event_data = Column(JSON)  # Event-specific data
    
    # Pick details (if event_type is pick_made)
    pick_number = Column(Integer)
    round_number = Column(Integer)
    team_key = Column(String)
    player_key = Column(String)
    player_name = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    draft_session = relationship("YahooDraftSession", back_populates="events")
    
    def __repr__(self):
        return f"<YahooDraftEvent {self.event_type} - {self.id}>"