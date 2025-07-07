"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    favorite_team: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    favorite_team: Optional[str] = None
    default_league_size: Optional[int] = Field(None, ge=6, le=20)
    preferred_scoring: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_premium: bool
    default_league_size: int
    preferred_scoring: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Auth schemas  
class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Player schemas
class PlayerBase(BaseModel):
    name: str
    position: str
    jersey_number: Optional[int] = None
    height: Optional[str] = None
    weight: Optional[int] = None
    age: Optional[int] = None
    college: Optional[str] = None


class PlayerResponse(PlayerBase):
    id: int
    espn_id: Optional[int] = None
    team_name: Optional[str] = None
    team_abbreviation: Optional[str] = None
    is_active: bool
    injury_status: Optional[str] = None
    bye_week: Optional[int] = None
    
    class Config:
        from_attributes = True


class PlayerStatsResponse(BaseModel):
    id: int
    player_id: int
    season: int
    week: Optional[int] = None
    games_played: int
    
    # Passing stats
    pass_attempts: int
    pass_completions: int
    pass_yards: int
    pass_touchdowns: int
    interceptions: int
    
    # Rushing stats
    rush_attempts: int
    rush_yards: int
    rush_touchdowns: int
    
    # Receiving stats
    targets: int
    receptions: int
    receiving_yards: int
    receiving_touchdowns: int
    
    # Fantasy points
    fantasy_points_standard: float
    fantasy_points_ppr: float
    fantasy_points_half_ppr: float
    
    class Config:
        from_attributes = True


# Team schemas
class TeamResponse(BaseModel):
    id: int
    name: str
    abbreviation: str
    city: str
    conference: Optional[str] = None
    division: Optional[str] = None
    logo_url: Optional[str] = None
    
    class Config:
        from_attributes = True


# Fantasy schemas
class LeagueBase(BaseModel):
    name: str
    platform: Optional[str] = None
    team_count: int = Field(default=12, ge=6, le=20)
    scoring_type: str = Field(default="standard")


class LeagueCreate(LeagueBase):
    pass


class LeagueResponse(LeagueBase):
    id: int
    current_season: Optional[int] = None
    current_week: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Error schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None