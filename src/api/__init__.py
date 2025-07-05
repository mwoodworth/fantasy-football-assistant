"""
API endpoints for Fantasy Football Assistant
"""

from .auth import router as auth_router
from .players import router as players_router
from .fantasy import router as fantasy_router

__all__ = [
    "auth_router",
    "players_router", 
    "fantasy_router"
]