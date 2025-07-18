"""
API endpoints for Fantasy Football Assistant
"""

from .auth import router as auth_router
from .players import router as players_router
from .fantasy import router as fantasy_router
from .espn import router as espn_router
from .espn_enhanced import router as espn_enhanced_router
from .espn_players_enhanced import router as espn_players_enhanced_router
from .ai import router as ai_router
from .dashboard import router as dashboard_router
from .teams import router as teams_router
from .yahoo import router as yahoo_router
from .yahoo_draft import router as yahoo_draft_router
from .admin import router as admin_router
from .user_settings import router as user_settings_router

__all__ = [
    "auth_router",
    "players_router", 
    "fantasy_router",
    "espn_router",
    "espn_enhanced_router",
    "espn_players_enhanced_router",
    "ai_router",
    "dashboard_router",
    "teams_router",
    "yahoo_router",
    "yahoo_draft_router",
    "admin_router",
    "user_settings_router"
]