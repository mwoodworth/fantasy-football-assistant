"""
Admin activity logging utilities
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request

from ..models import AdminActivityLog


def log_admin_activity(
    db: Session,
    admin_id: int,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> AdminActivityLog:
    """
    Log an admin activity to the database
    
    Args:
        db: Database session
        admin_id: ID of the admin performing the action
        action: Action being performed (e.g., "user.update", "user.delete")
        target_type: Type of entity being acted upon
        target_id: ID of the entity being acted upon
        details: Additional details about the action
        request: FastAPI request object for IP and user agent
        
    Returns:
        Created AdminActivityLog instance
    """
    log_entry = AdminActivityLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details) if details else None,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    
    return log_entry


# Common admin actions
class AdminActions:
    # User management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_SUSPEND = "user.suspend"
    USER_ACTIVATE = "user.activate"
    USER_RESET_PASSWORD = "user.reset_password"
    USER_GRANT_ADMIN = "user.grant_admin"
    USER_REVOKE_ADMIN = "user.revoke_admin"
    
    # League management
    LEAGUE_UPDATE = "league.update"
    LEAGUE_DELETE = "league.delete"
    LEAGUE_SYNC = "league.sync"
    
    # System management
    SYSTEM_CONFIG_UPDATE = "system.config_update"
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_BROADCAST = "system.broadcast"
    
    # Content moderation
    CONTENT_DELETE = "content.delete"
    CONTENT_MODERATE = "content.moderate"
    
    # Admin activities
    ADMIN_LOGIN = "admin.login"
    ADMIN_VIEW_STATS = "admin.view_stats"
    ADMIN_VIEW_USERS = "admin.view_users"
    ADMIN_VIEW_ACTIVITY = "admin.view_activity"
    ADMIN_VIEW_SETTINGS = "admin.view_settings"
    ADMIN_UPDATE_SETTINGS = "admin.update_settings"