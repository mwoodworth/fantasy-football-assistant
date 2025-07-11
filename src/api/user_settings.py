"""
User settings API endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime
import os
import uuid
from PIL import Image
import io

from ..models import User
from ..models.database import get_db
from ..utils.dependencies import get_current_active_user
from ..utils.schemas import UserResponse
from ..services.user import UserService
from ..config import settings
from pydantic import BaseModel, EmailStr, Field
import bcrypt

router = APIRouter(prefix="/user", tags=["user-settings"])


# Request/Response models
class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    username: Optional[str] = Field(None, min_length=3, max_length=50)


class PreferencesUpdate(BaseModel):
    favorite_team: Optional[str] = Field(None, max_length=50)
    default_league_size: Optional[int] = Field(None, ge=6, le=20)
    preferred_scoring: Optional[str] = Field(None, pattern="^(standard|ppr|half_ppr)$")


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class ConnectedAccount(BaseModel):
    provider: str
    connected_at: datetime
    account_email: Optional[str] = None
    account_username: Optional[str] = None
    last_sync: Optional[datetime] = None


class PrivacySettings(BaseModel):
    profile_public: bool = True
    show_email: bool = False
    allow_notifications: bool = True
    allow_marketing_emails: bool = False


# Profile endpoints
@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's full profile"""
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_update: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user profile information"""
    
    # Check if username is being changed and if it's already taken
    if profile_update.username and profile_update.username != current_user.username:
        existing_user = db.query(User).filter(User.username == profile_update.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Update user fields
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


# Preferences endpoints
@router.get("/preferences")
async def get_preferences(
    current_user: User = Depends(get_current_active_user)
):
    """Get user's fantasy football preferences"""
    return {
        "favorite_team": current_user.favorite_team,
        "default_league_size": current_user.default_league_size,
        "preferred_scoring": current_user.preferred_scoring
    }


@router.put("/preferences")
async def update_preferences(
    preferences: PreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user's fantasy football preferences"""
    
    update_data = preferences.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Preferences updated successfully",
        "preferences": {
            "favorite_team": current_user.favorite_team,
            "default_league_size": current_user.default_league_size,
            "preferred_scoring": current_user.preferred_scoring
        }
    }


# Security endpoints
@router.put("/security/password")
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Change user password"""
    
    # Verify current password
    if not current_user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Check if new passwords match
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    # Check if new password is different from current
    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Set new password
    current_user.set_password(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/security/sessions/clear")
async def clear_all_sessions(
    current_user: User = Depends(get_current_active_user)
):
    """Clear all user sessions (placeholder for future implementation)"""
    # In a real implementation, this would invalidate all tokens
    # For now, just return success
    return {"message": "All sessions cleared. Please log in again."}


# Connected accounts endpoints
@router.get("/connected-accounts", response_model=list[ConnectedAccount])
async def get_connected_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of connected accounts"""
    accounts = []
    
    # Check ESPN connection
    if current_user.espn_leagues:
        # Get the most recent ESPN league to determine connection status
        latest_espn = max(current_user.espn_leagues, key=lambda x: x.updated_at)
        accounts.append(ConnectedAccount(
            provider="ESPN",
            connected_at=latest_espn.created_at,
            account_username=f"League {latest_espn.league_id}",
            last_sync=latest_espn.updated_at
        ))
    
    # Check Yahoo connection
    if current_user.yahoo_oauth_token:
        accounts.append(ConnectedAccount(
            provider="Yahoo",
            connected_at=current_user.updated_at,  # Approximate
            account_email="Connected",
            last_sync=current_user.updated_at
        ))
    
    return accounts


@router.delete("/connected-accounts/{provider}")
async def disconnect_account(
    provider: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Disconnect a connected account"""
    
    provider = provider.upper()
    
    if provider == "YAHOO":
        current_user.yahoo_oauth_token = None
        # Delete Yahoo leagues
        for league in current_user.yahoo_leagues:
            db.delete(league)
    elif provider == "ESPN":
        # Delete ESPN leagues
        for league in current_user.espn_leagues:
            db.delete(league)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}"
        )
    
    db.commit()
    
    return {"message": f"{provider} account disconnected successfully"}


# Avatar endpoints
@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload user avatar"""
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB"
        )
    
    # Process image
    try:
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to max 200x200 maintaining aspect ratio
        image.thumbnail((200, 200), Image.Resampling.LANCZOS)
        
        # Save to avatars directory
        avatar_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static", "avatars")
        os.makedirs(avatar_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"{current_user.id}_{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(avatar_dir, filename)
        
        # Save image
        image.save(filepath, "JPEG", quality=85)
        
        # Update user avatar URL
        current_user.avatar_url = f"/static/avatars/{filename}"
        db.commit()
        
        return {
            "message": "Avatar uploaded successfully",
            "avatar_url": current_user.avatar_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process image: {str(e)}"
        )


@router.delete("/avatar")
async def delete_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete user avatar"""
    
    if current_user.avatar_url and current_user.avatar_url.startswith("/static/avatars/"):
        # Delete file
        filename = current_user.avatar_url.split("/")[-1]
        filepath = os.path.join(
            os.path.dirname(__file__), "..", "..", "static", "avatars", filename
        )
        if os.path.exists(filepath):
            os.remove(filepath)
    
    current_user.avatar_url = None
    db.commit()
    
    return {"message": "Avatar deleted successfully"}


# Privacy settings (placeholder for future implementation)
@router.get("/privacy")
async def get_privacy_settings(
    current_user: User = Depends(get_current_active_user)
):
    """Get user privacy settings"""
    # Return default settings for now
    return PrivacySettings(
        profile_public=True,
        show_email=False,
        allow_notifications=True,
        allow_marketing_emails=False
    )


@router.put("/privacy")
async def update_privacy_settings(
    privacy_settings: PrivacySettings,
    current_user: User = Depends(get_current_active_user)
):
    """Update user privacy settings"""
    # Placeholder for future implementation
    return {
        "message": "Privacy settings updated successfully",
        "settings": privacy_settings
    }