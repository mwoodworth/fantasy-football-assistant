"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta

from ..models.database import get_db
from ..models.user import User
from ..services.auth import AuthService
from ..services.user import UserService
from ..utils.schemas import (
    UserCreate, UserResponse, LoginRequest, TokenResponse, 
    RefreshTokenRequest, UserUpdate
)
from ..utils.dependencies import get_current_active_user
from ..config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    
    # Additional validation
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long. For better security, use a mix of uppercase, lowercase, numbers, and special characters."
        )
    
    if len(user_data.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )
    
    # Check for common weak passwords
    weak_passwords = ['password', '12345678', 'password123', 'admin123', 'qwerty123', 'welcome123']
    if user_data.password.lower() in weak_passwords:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password is too common and easily guessable. Please choose a stronger password with a mix of letters, numbers, and special characters."
        )
    
    try:
        # Create new user
        user = UserService.create_user(
            db=db,
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            favorite_team=user_data.favorite_team
        )
        
        return UserResponse.model_validate(user)
        
    except HTTPException:
        # Re-raise HTTPExceptions with their specific error messages
        raise
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logging.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration. Please try again or contact support if the problem persists."
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens"""
    
    # Determine if login by email or username
    user = None
    if login_data.email:
        user = AuthService.authenticate_user(
            db, login_data.email, login_data.password, by_email=True
        )
    elif login_data.username:
        user = AuthService.authenticate_user(
            db, login_data.username, login_data.password, by_email=False
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Create tokens
    tokens = AuthService.create_user_tokens(user)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    try:
        # Verify refresh token
        payload = AuthService.verify_token(refresh_data.refresh_token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = UserService.get_user_by_id(db, int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        tokens = AuthService.create_user_tokens(user)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user=UserResponse.model_validate(user)
        )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    
    updated_user = UserService.update_user(
        db=db,
        user=current_user,
        **user_update.model_dump(exclude_unset=True)
    )
    
    return UserResponse.model_validate(updated_user)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """Logout user (client should discard tokens)"""
    
    # In a more sophisticated implementation, you might:
    # - Add token to blacklist
    # - Update last_logout timestamp
    # - Clear session data
    
    return {"message": "Successfully logged out"}


@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate user account"""
    
    UserService.deactivate_user(db, current_user)
    
    return {"message": "Account deactivated successfully"}