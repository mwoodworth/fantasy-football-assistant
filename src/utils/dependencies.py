"""
FastAPI dependencies for authentication and database access
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.user import User
from ..services.auth import AuthService

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token
    """
    token = credentials.credentials
    user = AuthService.get_user_from_token(token, db)
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current authenticated and active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if token is provided, otherwise return None
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user = AuthService.get_user_from_token(token, db)
        return user if user.is_active else None
    except HTTPException:
        return None


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current user and verify they are an admin
    """
    if not current_user.is_admin and not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_superadmin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current user and verify they are a superadmin
    """
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required"
        )
    return current_user


def require_permission(permission: str):
    """
    Decorator to require specific permission for an endpoint
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker