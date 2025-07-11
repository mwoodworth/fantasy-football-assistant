"""
Admin API endpoints for system management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..models import User, AdminActivityLog, ESPNLeague, YahooLeague, Player, Team
from ..models.database import get_db
from ..utils.dependencies import get_admin_user, get_superadmin_user, require_permission
from ..utils.admin_logging import log_admin_activity, AdminActions
from ..utils.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/api/admin", tags=["admin"])


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
    # User stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    
    # Recent registrations (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_signups = db.query(User).filter(User.created_at >= week_ago).count()
    
    # League stats
    espn_leagues = db.query(ESPNLeague).count()
    yahoo_leagues = db.query(YahooLeague).count()
    
    # Activity stats (last 24 hours)
    day_ago = datetime.utcnow() - timedelta(days=1)
    active_today = db.query(User).filter(User.last_login >= day_ago).count()
    
    # Database stats
    player_count = db.query(Player).count()
    team_count = db.query(Team).count()
    
    stats = {
        "users": {
            "total": total_users,
            "active": active_users,
            "admins": admin_users,
            "recent_signups": recent_signups,
            "active_today": active_today
        },
        "leagues": {
            "espn": espn_leagues,
            "yahoo": yahoo_leagues,
            "total": espn_leagues + yahoo_leagues
        },
        "database": {
            "players": player_count,
            "teams": team_count
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Log the action
    log_admin_activity(
        db, admin.id, "admin.view_stats",
        request=request
    )
    
    return stats


# Activity Log Endpoints

@router.get("/logs")
async def get_activity_logs(
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
    
    total = query.count()
    logs = query.order_by(desc(AdminActivityLog.created_at)).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "logs": logs
    }


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