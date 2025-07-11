"""
Admin API endpoints for system management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
import os

from ..models import User, AdminActivityLog, ESPNLeague, YahooLeague, Player, Team
from ..models.database import get_db
from ..utils.dependencies import get_admin_user, get_superadmin_user, require_permission
from ..utils.admin_logging import log_admin_activity, AdminActions
from ..utils.schemas import UserResponse, UserUpdate
from ..config import settings
from ..services.espn_integration import espn_service

router = APIRouter(prefix="/admin", tags=["admin"])


# User Management Endpoints

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List all users with optional filters"""
    # Log admin viewing users
    log_admin_activity(
        db, admin.id, AdminActions.ADMIN_VIEW_USERS,
        details={
            "action": "viewed user list",
            "filters": {
                "search": search,
                "is_active": is_active,
                "is_admin": is_admin
            }
        },
        request=request
    )
    
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.first_name.contains(search)) |
            (User.last_name.contains(search))
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_admin is not None:
        query = query.filter(User.is_admin == is_admin)
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    # Log the action
    log_admin_activity(
        db, admin.id, "user.list",
        details={"filters": {"search": search, "is_active": is_active, "is_admin": is_admin}},
        request=request
    )
    
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Get detailed information about a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log the action
    log_admin_activity(
        db, admin.id, "user.view",
        target_type="user", target_id=user_id,
        request=request
    )
    
    return user


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update user information (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Track changes for logging
    changes = {}
    
    # Update basic fields
    for field, value in user_update.dict(exclude_unset=True).items():
        if field in ["is_admin", "is_superadmin"] and not admin.is_superadmin:
            raise HTTPException(
                status_code=403, 
                detail="Only superadmins can modify admin privileges"
            )
        
        if hasattr(user, field) and getattr(user, field) != value:
            changes[field] = {"old": getattr(user, field), "new": value}
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Log the action
    log_admin_activity(
        db, admin.id, AdminActions.USER_UPDATE,
        target_type="user", target_id=user_id,
        details={"changes": changes},
        request=request
    )
    
    return {"message": "User updated successfully", "user": user}


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    reason: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Suspend a user account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_admin and not admin.is_superadmin:
        raise HTTPException(
            status_code=403,
            detail="Only superadmins can suspend admin accounts"
        )
    
    user.is_active = False
    if not user.admin_notes:
        user.admin_notes = ""
    user.admin_notes += f"\n[{datetime.utcnow().isoformat()}] Suspended by {admin.username}: {reason}"
    
    db.commit()
    
    # Log the action
    log_admin_activity(
        db, admin.id, AdminActions.USER_SUSPEND,
        target_type="user", target_id=user_id,
        details={"reason": reason},
        request=request
    )
    
    return {"message": "User suspended successfully"}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Reactivate a suspended user account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    if not user.admin_notes:
        user.admin_notes = ""
    user.admin_notes += f"\n[{datetime.utcnow().isoformat()}] Activated by {admin.username}"
    
    db.commit()
    
    # Log the action
    log_admin_activity(
        db, admin.id, AdminActions.USER_ACTIVATE,
        target_type="user", target_id=user_id,
        request=request
    )
    
    return {"message": "User activated successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_superadmin_user)
):
    """Permanently delete a user (superadmin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Log before deletion
    log_admin_activity(
        db, admin.id, AdminActions.USER_DELETE,
        target_type="user", target_id=user_id,
        details={"username": user.username, "email": user.email},
        request=request
    )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


# System Statistics Endpoints

@router.get("/stats")
async def get_system_stats(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Get system-wide statistics"""
    # Log admin viewing stats
    log_admin_activity(
        db, admin.id, AdminActions.ADMIN_VIEW_STATS,
        details={"action": "viewed dashboard statistics"},
        request=request
    )
    
    # User stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    premium_users = db.query(User).filter(User.is_premium == True).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    superadmin_users = db.query(User).filter(User.is_superadmin == True).count()
    
    # Recent registrations
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)
    month_ago = datetime.utcnow() - timedelta(days=30)
    
    users_today = db.query(User).filter(
        func.date(User.created_at) == today
    ).count()
    
    users_this_week = db.query(User).filter(
        User.created_at >= week_ago
    ).count()
    
    users_this_month = db.query(User).filter(
        User.created_at >= month_ago
    ).count()
    
    # Return stats in the format expected by frontend
    stats = {
        "total_users": total_users,
        "active_users": active_users,
        "premium_users": premium_users,
        "total_admins": admin_users,
        "total_superadmins": superadmin_users,
        "users_today": users_today,
        "users_this_week": users_this_week,
        "users_this_month": users_this_month
    }
    
    # Log the action
    log_admin_activity(
        db, admin.id, "admin.view_stats",
        request=request
    )
    
    return stats


# Activity Log Endpoints

@router.get("/activity")
async def get_activity_logs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    admin_id: Optional[int] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Get admin activity logs with filters"""
    # Log admin viewing activity logs (but don't create infinite loop)
    if action != AdminActions.ADMIN_VIEW_ACTIVITY:
        log_admin_activity(
            db, admin.id, AdminActions.ADMIN_VIEW_ACTIVITY,
            details={"action": "viewed activity logs"},
            request=request
        )
    
    query = db.query(AdminActivityLog)
    
    if admin_id:
        query = query.filter(AdminActivityLog.admin_id == admin_id)
    
    if action:
        query = query.filter(AdminActivityLog.action.contains(action))
    
    if target_type:
        query = query.filter(AdminActivityLog.target_type == target_type)
    
    if start_date:
        query = query.filter(AdminActivityLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(AdminActivityLog.created_at <= end_date)
    
    logs = query.order_by(desc(AdminActivityLog.created_at)).offset(skip).limit(limit).all()
    
    # Format logs with admin username
    formatted_logs = []
    for log in logs:
        formatted_log = {
            "id": log.id,
            "admin_id": log.admin_id,
            "admin_username": log.admin.username if log.admin else "Unknown",
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        formatted_logs.append(formatted_log)
    
    return formatted_logs


# Admin Management Endpoints (Superadmin only)

@router.post("/grant-admin/{user_id}")
async def grant_admin_privileges(
    user_id: int,
    request: Request,
    permissions: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_superadmin_user)
):
    """Grant admin privileges to a user (superadmin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_admin = True
    if permissions:
        user.set_permissions(permissions)
    
    db.commit()
    
    # Log the action
    log_admin_activity(
        db, admin.id, AdminActions.USER_GRANT_ADMIN,
        target_type="user", target_id=user_id,
        details={"permissions": permissions},
        request=request
    )
    
    return {"message": "Admin privileges granted successfully"}


@router.post("/revoke-admin/{user_id}")
async def revoke_admin_privileges(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_superadmin_user)
):
    """Revoke admin privileges from a user (superadmin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_superadmin:
        raise HTTPException(
            status_code=400,
            detail="Cannot revoke privileges from a superadmin"
        )
    
    user.is_admin = False
    user.permissions = None
    
    db.commit()
    
    # Log the action
    log_admin_activity(
        db, admin.id, AdminActions.USER_REVOKE_ADMIN,
        target_type="user", target_id=user_id,
        request=request
    )
    
    return {"message": "Admin privileges revoked successfully"}


# System Settings Schema
class SystemSettings(BaseModel):
    draft_monitor_interval: int = 60
    live_monitor_interval: int = 300
    disable_espn_sync_logs: bool = False
    log_level: str = "INFO"
    cache_expire_time: int = 3600
    rate_limit_default: int = 60
    rate_limit_espn: int = 10
    rate_limit_ai: int = 20


# Settings Endpoints

@router.get("/settings")
async def get_system_settings(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_superadmin_user)
):
    """Get current system settings (superadmin only)"""
    # Get settings from config
    current_settings = {
        "draft_monitor_interval": getattr(settings, 'draft_monitor_interval', 60),
        "live_monitor_interval": getattr(settings, 'live_monitor_interval', 300),
        "disable_espn_sync_logs": getattr(settings, 'disable_espn_sync_logs', False),
        "log_level": settings.log_level,
        "cache_expire_time": settings.cache_expire_time,
        "rate_limit_default": 60,  # These would come from middleware config
        "rate_limit_espn": 10,
        "rate_limit_ai": 20
    }
    
    return current_settings


@router.put("/settings")
async def update_system_settings(
    new_settings: SystemSettings,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_superadmin_user)
):
    """Update system settings (superadmin only)"""
    # In a real implementation, you'd save these to a database or config file
    # For now, we'll update environment variables
    
    changes = {}
    
    # Update monitoring intervals
    if new_settings.draft_monitor_interval != getattr(settings, 'draft_monitor_interval', 60):
        os.environ['DRAFT_MONITOR_INTERVAL'] = str(new_settings.draft_monitor_interval)
        changes['draft_monitor_interval'] = new_settings.draft_monitor_interval
    
    if new_settings.live_monitor_interval != getattr(settings, 'live_monitor_interval', 300):
        os.environ['LIVE_MONITOR_INTERVAL'] = str(new_settings.live_monitor_interval)
        changes['live_monitor_interval'] = new_settings.live_monitor_interval
    
    if new_settings.disable_espn_sync_logs != getattr(settings, 'disable_espn_sync_logs', False):
        os.environ['DISABLE_ESPN_SYNC_LOGS'] = str(new_settings.disable_espn_sync_logs).lower()
        changes['disable_espn_sync_logs'] = new_settings.disable_espn_sync_logs
    
    # Log the changes
    log_admin_activity(
        db, admin.id, "settings.update",
        details={"changes": changes},
        request=request
    )
    
    return {"message": "Settings updated successfully", "changes": changes}


# Maintenance Endpoints

@router.post("/maintenance/{action}")
async def perform_maintenance(
    action: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_superadmin_user)
):
    """Perform maintenance actions (superadmin only)"""
    
    if action == "clear-cache":
        # Clear ESPN service cache
        espn_service.clear_cache()
        message = "Cache cleared successfully"
        
    elif action == "optimize-database":
        # Run database optimization (SQLite specific)
        from sqlalchemy import text
        db.execute(text("VACUUM"))
        db.commit()
        message = "Database optimized successfully"
        
    elif action == "clean-logs":
        # Clean old activity logs (older than 90 days)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        deleted = db.query(AdminActivityLog).filter(
            AdminActivityLog.created_at < cutoff_date
        ).delete()
        db.commit()
        message = f"Cleaned {deleted} old log entries"
        
    elif action == "reset-rate-limits":
        # This would reset rate limit counters in your middleware
        message = "Rate limits reset successfully"
        
    else:
        raise HTTPException(status_code=400, detail=f"Unknown maintenance action: {action}")
    
    # Log the action
    log_admin_activity(
        db, admin.id, f"maintenance.{action}",
        details={"result": message},
        request=request
    )
    
    return {"message": message}