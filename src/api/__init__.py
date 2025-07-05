"""
API endpoints for Fantasy Football Assistant
"""

from .auth import auth_router
from .users import users_router
from .players import players_router

__all__ = [
    "auth_router",
    "users_router", 
    "players_router"
]