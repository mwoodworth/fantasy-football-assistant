"""
ESPN League models for multi-league support with historical data
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from typing import Optional, Dict, Any, List
import json


class UserLeagueSettings(Base):
    """Admin-configurable settings for user league limits"""
    __tablename__ = "user_league_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    max_leagues_per_user = Column(Integer, default=5, nullable=False)
    allow_historical_access = Column(Boolean, default=True, nullable=False)
    historical_years_limit = Column(Integer, default=5, nullable=False)
    auto_archive_old_seasons = Column(Boolean, default=True, nullable=False)
    require_league_verification = Column(Boolean, default=False, nullable=False)
    
    # Admin tracking
    updated_by_admin = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    updated_by = relationship("User", foreign_keys=[updated_by_admin])

    def __repr__(self):
        return f"<UserLeagueSettings(max_leagues={self.max_leagues_per_user})>"


class ESPNLeague(Base):
    """Enhanced ESPN League model with multi-year tracking and historical support"""
    __tablename__ = "espn_leagues"
    
    # Primary identity
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    espn_league_id = Column(Integer, nullable=False, index=True)  # ESPN's league ID
    season = Column(Integer, nullable=False, index=True)  # Year (e.g., 2024)
    
    # League metadata
    league_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)  # Current season
    is_archived = Column(Boolean, default=False, nullable=False)  # Past seasons
    
    # Multi-year tracking
    league_group_id = Column(String(100), index=True)  # Links same league across years
    previous_season_id = Column(Integer, ForeignKey("espn_leagues.id"))
    
    # League configuration
    team_count = Column(Integer, default=10, nullable=False)
    roster_positions = Column(JSON)  # {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1, "BENCH": 6}
    bench_size = Column(Integer, default=6)
    ir_slots = Column(Integer, default=0)
    
    # Scoring system
    scoring_settings = Column(JSON, nullable=False)  # Complete ESPN scoring configuration
    scoring_type = Column(String(20), default="standard")  # "standard", "ppr", "half_ppr", "custom"
    
    # Draft settings
    draft_type = Column(String(20), default="snake")  # "snake", "linear", "auction"
    draft_date = Column(DateTime(timezone=True))
    draft_completed = Column(Boolean, default=False)
    user_draft_position = Column(Integer)  # User's draft position (1-based)
    draft_order = Column(JSON)  # Complete draft order
    
    # Privacy and access
    is_private = Column(Boolean, default=False, nullable=False)
    espn_s2 = Column(String(500))  # Encrypted ESPN session cookie
    swid = Column(String(100))     # Encrypted ESPN SWID
    
    # Sync configuration
    last_sync = Column(DateTime(timezone=True))
    sync_enabled = Column(Boolean, default=True, nullable=False)
    sync_frequency = Column(String(20), default="daily")  # "real-time", "hourly", "daily", "manual"
    sync_status = Column(String(20), default="pending")  # "active", "error", "pending", "disabled"
    sync_error_message = Column(Text)
    
    # League status
    season_started = Column(Boolean, default=False)
    season_completed = Column(Boolean, default=False)
    playoff_started = Column(Boolean, default=False)
    
    # User's team info
    user_team_id = Column(Integer)  # ESPN team ID for the user
    user_team_name = Column(String(100))
    user_team_abbreviation = Column(String(10))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    archived_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="espn_leagues")
    previous_season = relationship("ESPNLeague", remote_side=[id])
    draft_sessions = relationship("DraftSession", back_populates="league", cascade="all, delete-orphan")
    historical_data = relationship("LeagueHistoricalData", back_populates="league", cascade="all, delete-orphan")

    def get_scoring_multipliers(self) -> Dict[str, float]:
        """Extract scoring multipliers from ESPN settings"""
        if not self.scoring_settings:
            return {}
        
        # Common ESPN scoring categories
        multipliers = {}
        settings = self.scoring_settings
        
        # Passing stats
        multipliers['passing_yards'] = settings.get('16', {}).get('points', 0.04)  # Usually 1pt per 25 yards
        multipliers['passing_tds'] = settings.get('4', {}).get('points', 4.0)     # 4 or 6 points
        multipliers['passing_ints'] = settings.get('20', {}).get('points', -2.0)  # Usually -2
        
        # Rushing stats
        multipliers['rushing_yards'] = settings.get('17', {}).get('points', 0.1)  # 1pt per 10 yards
        multipliers['rushing_tds'] = settings.get('5', {}).get('points', 6.0)     # Usually 6 points
        
        # Receiving stats
        multipliers['receiving_yards'] = settings.get('18', {}).get('points', 0.1)  # 1pt per 10 yards
        multipliers['receiving_tds'] = settings.get('6', {}).get('points', 6.0)     # Usually 6 points
        multipliers['receptions'] = settings.get('53', {}).get('points', 0.0)       # PPR value
        
        return multipliers

    def is_ppr_league(self) -> bool:
        """Check if this is a PPR league"""
        multipliers = self.get_scoring_multipliers()
        reception_points = multipliers.get('receptions', 0)
        return reception_points >= 0.5

    def get_league_type_description(self) -> str:
        """Get human-readable league type"""
        multipliers = self.get_scoring_multipliers()
        reception_points = multipliers.get('receptions', 0)
        passing_td_points = multipliers.get('passing_tds', 4)
        
        # Determine PPR status
        if reception_points >= 1.0:
            ppr_type = "Full PPR"
        elif reception_points >= 0.5:
            ppr_type = "Half PPR"
        else:
            ppr_type = "Standard"
        
        # Check for superflex (6pt passing TDs usually indicate this)
        if passing_td_points >= 6:
            return f"{ppr_type} + 6pt Passing TDs"
        
        return ppr_type

    def __repr__(self):
        return f"<ESPNLeague(id={self.id}, name='{self.league_name}', season={self.season})>"


class DraftSession(Base):
    """Track live draft sessions and state"""
    __tablename__ = "draft_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("espn_leagues.id"), nullable=False)
    
    # Session identification
    session_token = Column(String(100), unique=True, index=True)
    espn_draft_id = Column(String(100))  # ESPN's draft identifier
    
    # Draft state
    current_pick = Column(Integer, default=1)
    current_round = Column(Integer, default=1)
    total_rounds = Column(Integer, nullable=False)
    total_picks = Column(Integer, nullable=False)
    user_pick_position = Column(Integer, nullable=False)  # 1-based position in draft order
    
    # Draft status
    is_active = Column(Boolean, default=True)
    is_live_synced = Column(Boolean, default=False)  # Syncing with ESPN live
    manual_mode = Column(Boolean, default=False)     # Fallback to manual entry
    draft_status = Column(String(20), default='not_started')  # not_started, in_progress, paused, completed
    current_pick_team_id = Column(Integer)  # Team currently on the clock
    pick_deadline = Column(DateTime(timezone=True))  # When current pick timer expires
    last_espn_sync = Column(DateTime(timezone=True))  # Last successful ESPN API sync
    sync_errors = Column(JSON, default=list)  # Track sync errors
    
    # Draft data
    drafted_players = Column(JSON, default=list)  # [{player_id, pick_number, team, round}]
    available_players = Column(JSON)  # Cached player pool with rankings
    user_roster = Column(JSON, default=list)  # User's current picks
    
    # AI state
    last_recommendation_time = Column(DateTime(timezone=True))
    recommendation_count = Column(Integer, default=0)
    
    # Session timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    league = relationship("ESPNLeague", back_populates="draft_sessions")
    recommendations = relationship("DraftRecommendation", back_populates="session", cascade="all, delete-orphan")
    events = relationship("DraftEvent", back_populates="session", cascade="all, delete-orphan")

    def get_next_pick_number(self) -> int:
        """Calculate user's next pick number"""
        if not self.is_active or self.completed_at:
            return 0
        
        # Snake draft logic
        current_round = self.current_round
        picks_per_round = self.league.team_count
        
        if current_round % 2 == 1:  # Odd rounds (1, 3, 5...)
            next_pick = ((current_round - 1) * picks_per_round) + self.user_pick_position
        else:  # Even rounds (2, 4, 6...)
            next_pick = ((current_round - 1) * picks_per_round) + (picks_per_round - self.user_pick_position + 1)
        
        return next_pick if next_pick <= self.total_picks else 0

    def get_picks_until_user_turn(self) -> int:
        """Calculate how many picks until user's turn"""
        next_pick = self.get_next_pick_number()
        if next_pick == 0:
            return 0
        return max(0, next_pick - self.current_pick)

    def __repr__(self):
        return f"<DraftSession(id={self.id}, league={self.league_id}, pick={self.current_pick})>"


class DraftRecommendation(Base):
    """Store AI-generated draft recommendations"""
    __tablename__ = "draft_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("draft_sessions.id"), nullable=False)
    pick_number = Column(Integer, nullable=False)
    round_number = Column(Integer, nullable=False)
    
    # Recommendation data
    recommended_players = Column(JSON, nullable=False)  # [{player_id, name, position, score, reasoning}]
    primary_recommendation = Column(JSON)  # Top recommendation with detailed analysis
    
    # AI analysis
    strategy_reasoning = Column(Text)  # Overall draft strategy explanation
    positional_analysis = Column(JSON)  # Position-specific needs and priorities
    tier_analysis = Column(JSON)  # Tier breaks and value analysis
    future_pick_strategy = Column(Text)  # Strategy for upcoming picks
    
    # Recommendation metadata
    confidence_score = Column(Float, default=0.0)  # 0.0 to 1.0
    recommendation_type = Column(String(50))  # "best_available", "positional_need", "value_pick", etc.
    
    # Context used in recommendation
    available_player_count = Column(Integer)
    user_roster_positions = Column(JSON)  # Current roster construction
    scoring_adjustments_applied = Column(JSON)  # How league scoring affected rankings
    ai_insights = Column(JSON)  # Key insights from AI analysis
    next_pick_strategy = Column(Text)  # Strategy for next picks
    
    # Timing
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    user_viewed = Column(Boolean, default=False)
    user_followed = Column(Boolean)  # Did user pick recommended player?
    
    # Relationships
    session = relationship("DraftSession", back_populates="recommendations")

    def __repr__(self):
        return f"<DraftRecommendation(id={self.id}, pick={self.pick_number}, confidence={self.confidence_score})>"


class LeagueHistoricalData(Base):
    """Store historical performance and analysis data"""
    __tablename__ = "league_historical_data"
    
    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("espn_leagues.id"), nullable=False)
    season = Column(Integer, nullable=False, index=True)
    
    # Season results
    final_standings = Column(JSON)  # Complete league standings
    playoff_results = Column(JSON)  # Playoff bracket and results
    user_final_rank = Column(Integer)
    user_record = Column(String(20))  # "12-2-0" format
    user_points_for = Column(Float)
    user_points_against = Column(Float)
    
    # Draft analysis
    draft_results = Column(JSON)  # All picks with season outcomes
    user_draft_grade = Column(String(10))  # A+, A, B+, B, C+, C, D+, D, F
    user_draft_position = Column(Integer)
    best_pick = Column(JSON)  # User's best draft pick analysis
    worst_pick = Column(JSON)  # User's worst draft pick analysis
    draft_value_score = Column(Float)  # Overall draft performance score
    
    # Season performance metrics
    highest_weekly_score = Column(Float)
    lowest_weekly_score = Column(Float)
    average_weekly_score = Column(Float)
    consistency_score = Column(Float)  # Standard deviation of weekly scores
    
    # League comparative stats
    league_average_score = Column(Float)
    user_vs_league_performance = Column(Float)  # % above/below league average
    weeks_as_highest_scorer = Column(Integer)
    weeks_as_lowest_scorer = Column(Integer)
    
    # Transaction history
    trades_made = Column(JSON)  # All trades with success analysis
    trade_success_rate = Column(Float)  # % of successful trades
    waiver_claims = Column(JSON)  # Successful waiver claims
    waiver_success_rate = Column(Float)
    free_agent_pickups = Column(JSON)  # FA pickups and their impact
    
    # Positional performance
    qb_performance = Column(JSON)  # QB stats and ranking
    rb_performance = Column(JSON)  # RB stats and ranking
    wr_performance = Column(JSON)  # WR stats and ranking
    te_performance = Column(JSON)  # TE stats and ranking
    k_performance = Column(JSON)   # Kicker stats and ranking
    def_performance = Column(JSON) # Defense stats and ranking
    
    # Advanced analytics
    optimal_lineup_percentage = Column(Float)  # % of weeks with optimal lineup
    bench_points_percentage = Column(Float)   # % of total points on bench
    injury_impact_score = Column(Float)       # How injuries affected season
    streaming_success_rate = Column(Float)    # Success rate for streamed positions
    
    # Year-over-year comparisons
    improvement_from_previous = Column(Float)  # Change in performance
    draft_strategy_evolution = Column(JSON)    # How strategy changed
    
    # Data quality and completeness
    data_completeness = Column(Float, default=1.0)  # 0.0 to 1.0
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    calculation_version = Column(String(20), default="1.0")  # For tracking analysis updates
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    league = relationship("ESPNLeague", back_populates="historical_data")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of historical performance"""
        return {
            "season": self.season,
            "final_rank": self.user_final_rank,
            "record": self.user_record,
            "points_for": self.user_points_for,
            "draft_grade": self.user_draft_grade,
            "vs_league_avg": self.user_vs_league_performance,
            "consistency": self.consistency_score,
            "trade_success": self.trade_success_rate,
            "waiver_success": self.waiver_success_rate
        }

    def __repr__(self):
        return f"<LeagueHistoricalData(league={self.league_id}, season={self.season}, rank={self.user_final_rank})>"


class DraftEvent(Base):
    """Track draft events for real-time updates and history"""
    __tablename__ = "draft_events"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("draft_sessions.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # pick_made, draft_started, draft_paused, etc.
    event_data = Column(JSON)  # Event-specific data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("DraftSession", back_populates="events")
    
    def __repr__(self):
        return f"<DraftEvent(id={self.id}, type={self.event_type}, session={self.session_id})>"