"""
Configuration settings for Fantasy Football Assistant
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # App info
    app_name: str = "Fantasy Football Assistant"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./fantasy_football.db"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    
    # External APIs
    anthropic_api_key: str = ""
    espn_api_key: str = ""
    
    # ESPN Service Integration (Node.js microservice)
    espn_service_url: str = "http://localhost:3001"
    espn_service_api_key: str = ""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 6001
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Cache settings
    cache_expire_time: int = 3600  # 1 hour
    
    # Fantasy football settings
    current_nfl_season: int = 2024
    default_league_size: int = 12
    
    # Development/Testing settings
    use_mock_data: bool = False
    
    # Monitoring settings
    draft_monitor_interval: int = 60  # seconds
    live_monitor_interval: int = 300  # seconds
    disable_espn_sync_logs: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()