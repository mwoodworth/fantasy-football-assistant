"""
Fantasy football models for leagues, teams, and transactions
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from typing import Optional, Dict, Any
from enum import Enum


class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    platform = Column(String(20))  # "ESPN", "Yahoo", "Sleeper", "Manual"
    external_id = Column(String(50))  # Platform-specific league ID
    
    # League settings
    team_count = Column(Integer, default=12)
    scoring_type = Column(String(20), default="standard")  # standard, ppr, half_ppr
    playoff_teams = Column(Integer, default=6)
    regular_season_weeks = Column(Integer, default=14)
    
    # Roster settings
    roster_size = Column(Integer, default=16)
    starting_qb = Column(Integer, default=1)
    starting_rb = Column(Integer, default=2)
    starting_wr = Column(Integer, default=2)
    starting_te = Column(Integer, default=1)
    starting_flex = Column(Integer, default=1)
    starting_k = Column(Integer, default=1)
    starting_def = Column(Integer, default=1)
    bench_spots = Column(Integer, default=6)
    ir_spots = Column(Integer, default=1)
    
    # League rules
    waiver_type = Column(String(20), default="FAAB")  # FAAB, Rolling, Reverse
    trade_deadline_week = Column(Integer, default=12)
    playoff_seeding = Column(String(20), default="record")  # record, points
    
    # Season info
    current_season = Column(Integer)
    current_week = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    fantasy_teams = relationship("FantasyTeam", back_populates="league")
    trades = relationship("Trade", back_populates="league")
    waiver_claims = relationship("WaiverClaim", back_populates="league")
    
    def __repr__(self):
        return f"<League(id={self.id}, name='{self.name}', teams={self.team_count})>"


class FantasyTeam(Base):
    __tablename__ = "fantasy_teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    
    # Relationships
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    league = relationship("League", back_populates="fantasy_teams")
    owner = relationship("User", back_populates="fantasy_teams")
    
    # Team settings
    logo_url = Column(String(500))
    motto = Column(String(200))
    
    # FAAB budget (if applicable)
    faab_budget = Column(Integer, default=100)
    faab_spent = Column(Integer, default=0)
    
    # Current season record
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    points_for = Column(Float, default=0)
    points_against = Column(Float, default=0)
    
    # Playoff info
    playoff_seed = Column(Integer)
    made_playoffs = Column(Boolean, default=False)
    championship_winner = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    roster = relationship("Roster", back_populates="fantasy_team")
    trades = relationship("Trade", back_populates="team")
    waiver_claims = relationship("WaiverClaim", back_populates="team")
    
    @property
    def win_percentage(self) -> float:
        """Calculate win percentage"""
        total_games = self.wins + self.losses + self.ties
        if total_games == 0:
            return 0.0
        return round(self.wins / total_games, 3)
    
    @property
    def remaining_faab(self) -> int:
        """Calculate remaining FAAB budget"""
        return self.faab_budget - self.faab_spent
    
    def __repr__(self):
        return f"<FantasyTeam(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"


class Roster(Base):
    __tablename__ = "roster"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    fantasy_team_id = Column(Integer, ForeignKey("fantasy_teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    fantasy_team = relationship("FantasyTeam", back_populates="roster")
    player = relationship("Player", back_populates="roster_entries")
    
    # Roster slot info
    slot_type = Column(String(20))  # "QB", "RB", "WR", "TE", "FLEX", "K", "DEF", "BENCH", "IR"
    acquisition_type = Column(String(20))  # "DRAFT", "WAIVER", "TRADE", "FREE_AGENT"
    acquisition_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Draft info (if applicable)
    draft_round = Column(Integer)
    draft_pick = Column(Integer)
    draft_cost = Column(Integer)  # for auction drafts
    
    # Transaction info
    waiver_priority = Column(Integer)
    faab_cost = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True)  # False if dropped
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Roster(team_id={self.fantasy_team_id}, player_id={self.player_id}, slot='{self.slot_type}')>"


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who initiated
    team_id = Column(Integer, ForeignKey("fantasy_teams.id"), nullable=False)  # Team involved
    
    league = relationship("League", back_populates="trades")
    user = relationship("User", back_populates="trades")
    team = relationship("FantasyTeam", back_populates="trades")
    
    # Trade details
    trade_partner_id = Column(Integer, ForeignKey("fantasy_teams.id"), nullable=False)
    
    # JSON fields for flexibility
    players_sent = Column(JSON)  # List of player IDs
    players_received = Column(JSON)  # List of player IDs
    draft_picks_sent = Column(JSON)  # List of draft pick objects
    draft_picks_received = Column(JSON)  # List of draft pick objects
    faab_sent = Column(Integer, default=0)
    faab_received = Column(Integer, default=0)
    
    # Trade status
    status = Column(String(20), default="PENDING")  # PENDING, ACCEPTED, REJECTED, EXPIRED
    proposed_date = Column(DateTime(timezone=True), server_default=func.now())
    executed_date = Column(DateTime(timezone=True))
    expiration_date = Column(DateTime(timezone=True))
    
    # Analysis
    trade_value_sent = Column(Float)  # AI-calculated trade value
    trade_value_received = Column(Float)
    fairness_score = Column(Float)  # 0-100 score
    
    # Notes
    proposal_note = Column(Text)
    rejection_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @property
    def is_fair_trade(self) -> bool:
        """Determine if trade is fair based on analysis"""
        if self.fairness_score is None:
            return True  # No analysis yet
        return self.fairness_score >= 40  # Within 60-40 value range
    
    def __repr__(self):
        return f"<Trade(id={self.id}, status='{self.status}', teams={self.team_id}->{self.trade_partner_id})>"


class WaiverClaim(Base):
    __tablename__ = "waiver_claims"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("fantasy_teams.id"), nullable=False)
    
    league = relationship("League", back_populates="waiver_claims")
    user = relationship("User", back_populates="waiver_claims")
    team = relationship("FantasyTeam", back_populates="waiver_claims")
    
    # Claim details
    player_to_add_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    player_to_drop_id = Column(Integer, ForeignKey("players.id"))  # Optional for IR moves
    
    # Waiver info
    waiver_priority = Column(Integer)
    faab_bid = Column(Integer, default=0)
    claim_week = Column(Integer, nullable=False)
    
    # Status
    status = Column(String(20), default="PENDING")  # PENDING, SUCCESSFUL, FAILED, CANCELLED
    processed_date = Column(DateTime(timezone=True))
    failure_reason = Column(String(100))  # "Outbid", "Higher Priority", "Roster Full"
    
    # AI analysis
    recommendation_score = Column(Float)  # 0-100 AI recommendation score
    analysis_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<WaiverClaim(id={self.id}, status='{self.status}', player_id={self.player_to_add_id})>"