"""
ESPN Team models for storing league team data and trade recommendations
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


class ESPNTeam(Base):
    """Store all teams in an ESPN league with roster data"""
    __tablename__ = "espn_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # League relationship
    espn_league_id = Column(Integer, ForeignKey("espn_leagues.id"), nullable=False, index=True)
    
    # ESPN team data
    espn_team_id = Column(Integer, nullable=False, index=True)  # ESPN's team ID
    team_name = Column(String(100), nullable=False)
    owner_name = Column(String(100))
    team_abbreviation = Column(String(10))
    
    # Team performance
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    points_for = Column(Float, default=0.0)
    points_against = Column(Float, default=0.0)
    
    # Current roster data (JSON)
    roster_data = Column(JSON)  # Complete roster with player details
    starting_lineup = Column(JSON)  # Current starting lineup
    bench_players = Column(JSON)  # Bench players
    
    # Roster analysis (calculated fields)
    position_strengths = Column(JSON)  # {"QB": "strong", "RB": "weak", ...}
    position_depth_scores = Column(JSON)  # {"QB": 0.8, "RB": 0.3, ...}
    tradeable_assets = Column(JSON)  # List of surplus players
    team_needs = Column(JSON)  # List of position needs
    
    # Team metadata
    is_active = Column(Boolean, default=True)
    is_user_team = Column(Boolean, default=False)  # True if this is the current user's team
    
    # Sync tracking
    last_synced = Column(DateTime(timezone=True), server_default=func.now())
    sync_status = Column(String(20), default="pending")  # "success", "error", "pending"
    sync_error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    league = relationship("ESPNLeague", backref="teams")
    trade_recommendations_as_target = relationship("TradeRecommendation", 
                                                  foreign_keys="TradeRecommendation.target_team_id",
                                                  back_populates="target_team")
    
    def get_roster_summary(self) -> Dict[str, Any]:
        """Get a summary of the team's roster"""
        if not self.roster_data:
            return {}
        
        roster = self.roster_data
        summary = {
            "total_players": len(roster),
            "starters": len([p for p in roster if p.get('status') == 'starter']),
            "bench": len([p for p in roster if p.get('status') != 'starter']),
            "positions": {}
        }
        
        # Count by position
        for player in roster:
            pos = player.get('position', 'UNKNOWN')
            summary["positions"][pos] = summary["positions"].get(pos, 0) + 1
        
        return summary
    
    def get_position_depth(self, position: str) -> int:
        """Get number of players at a specific position"""
        if not self.roster_data:
            return 0
        
        return len([p for p in self.roster_data if p.get('position') == position])
    
    def has_surplus_at_position(self, position: str, threshold: int = 3) -> bool:
        """Check if team has surplus at a position (more than threshold)"""
        return self.get_position_depth(position) > threshold
    
    def needs_help_at_position(self, position: str, minimum: int = 2) -> bool:
        """Check if team needs help at a position (less than minimum)"""
        return self.get_position_depth(position) < minimum
    
    def __repr__(self):
        return f"<ESPNTeam(id={self.id}, name='{self.team_name}', espn_id={self.espn_team_id})>"


class TradeRecommendation(Base):
    """Cache trade recommendations with expiration"""
    __tablename__ = "trade_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Source team (user's team)
    user_team_id = Column(Integer, ForeignKey("espn_teams.id"), nullable=False, index=True)
    
    # Target team and player
    target_team_id = Column(Integer, ForeignKey("espn_teams.id"), nullable=False, index=True)
    target_player_id = Column(Integer, nullable=False)  # ESPN player ID
    target_player_name = Column(String(100), nullable=False)
    target_player_position = Column(String(10), nullable=False)
    target_player_team = Column(String(10))  # NFL team
    
    # Trade package suggestion
    suggested_offer = Column(JSON, nullable=False)  # List of player objects to offer
    
    # Analysis
    rationale = Column(Text, nullable=False)  # Why this trade makes sense
    trade_value = Column(Integer, nullable=False)  # 0-100 score
    likelihood = Column(String(10), nullable=False)  # "high", "medium", "low"
    
    # Detailed analysis
    user_team_impact = Column(JSON)  # How this affects user's team
    target_team_impact = Column(JSON)  # How this affects target team
    position_analysis = Column(JSON)  # Position-specific reasoning
    
    # Cache management
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_expired = Column(Boolean, default=False, index=True)
    
    # User interaction
    user_viewed = Column(Boolean, default=False)
    user_interest_level = Column(String(10))  # "high", "medium", "low", "none"
    user_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user_team = relationship("ESPNTeam", foreign_keys=[user_team_id])
    target_team = relationship("ESPNTeam", foreign_keys=[target_team_id], back_populates="trade_recommendations_as_target")
    
    @classmethod
    def create_with_expiration(cls, days: int = 5, **kwargs):
        """Create a new recommendation with automatic expiration"""
        expires_at = datetime.utcnow() + timedelta(days=days)
        return cls(expires_at=expires_at, **kwargs)
    
    def is_valid(self) -> bool:
        """Check if recommendation is still valid (not expired)"""
        return datetime.utcnow() < self.expires_at and not self.is_expired
    
    def mark_expired(self):
        """Mark recommendation as expired"""
        self.is_expired = True
    
    def get_time_until_expiration(self) -> timedelta:
        """Get time remaining until expiration"""
        return self.expires_at - datetime.utcnow()
    
    def get_days_until_expiration(self) -> int:
        """Get days remaining until expiration"""
        delta = self.get_time_until_expiration()
        return max(0, delta.days)
    
    def to_api_response(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "player": {
                "id": self.target_player_id,
                "name": self.target_player_name,
                "position": self.target_player_position,
                "team": self.target_player_team,
                "points": 0.0,  # Could be populated from roster_data
                "projected_points": 0.0,
                "injury_status": "ACTIVE"
            },
            "team_id": f"espn_{self.target_team.espn_team_id}",
            "team_name": self.target_team.team_name,
            "trade_value": self.trade_value,
            "likelihood": self.likelihood,
            "suggested_offer": self.suggested_offer,
            "rationale": self.rationale,
            "expires_in_days": self.get_days_until_expiration()
        }
    
    def __repr__(self):
        return f"<TradeRecommendation(id={self.id}, target='{self.target_player_name}', value={self.trade_value})>"


class TeamSyncLog(Base):
    """Track team synchronization history and performance"""
    __tablename__ = "team_sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # League reference
    espn_league_id = Column(Integer, ForeignKey("espn_leagues.id"), nullable=False, index=True)
    
    # Sync details
    sync_type = Column(String(20), nullable=False)  # "manual", "scheduled", "triggered"
    status = Column(String(20), nullable=False)  # "success", "partial", "failed"
    
    # Metrics
    teams_processed = Column(Integer, default=0)
    teams_updated = Column(Integer, default=0)
    teams_failed = Column(Integer, default=0)
    total_duration_seconds = Column(Float)
    
    # Results
    sync_summary = Column(JSON)  # Detailed sync results
    error_details = Column(JSON)  # Any errors encountered
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    league = relationship("ESPNLeague", backref="sync_logs")
    
    def mark_completed(self, status: str = "success"):
        """Mark sync as completed"""
        self.completed_at = datetime.utcnow()
        self.status = status
        if self.started_at:
            self.total_duration_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def __repr__(self):
        return f"<TeamSyncLog(id={self.id}, league={self.espn_league_id}, status='{self.status}')>"