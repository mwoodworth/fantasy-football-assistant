"""Yahoo OAuth2 authentication client."""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from authlib.integrations.requests_client import OAuth2Session
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

class YahooOAuthClient:
    """Handles Yahoo OAuth2 authentication flow."""
    
    AUTHORIZATION_URL = "https://api.login.yahoo.com/oauth2/request_auth"
    TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
    REDIRECT_URI = os.getenv("YAHOO_REDIRECT_URI", "http://localhost:8000/yahoo/callback")
    
    def __init__(self):
        self.client_id = os.getenv("YAHOO_CLIENT_ID", "")
        self.client_secret = os.getenv("YAHOO_CLIENT_SECRET", "")
        self._oauth = None
        
    def _ensure_configured(self):
        """Ensure OAuth credentials are configured."""
        if not self.client_id or not self.client_secret:
            raise ValueError("Yahoo OAuth credentials not configured. Set YAHOO_CLIENT_ID and YAHOO_CLIENT_SECRET")
        
        if self._oauth is None:
            self._oauth = OAuth2Session(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.REDIRECT_URI,
                scope="fspt-r"  # Fantasy Sports Read permission
            )
    
    @property
    def oauth(self):
        """Get OAuth session, ensuring it's configured."""
        self._ensure_configured()
        return self._oauth
    
    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """Get the authorization URL for user consent.
        
        Returns:
            Tuple of (authorization_url, state)
        """
        return self.oauth.create_authorization_url(
            self.AUTHORIZATION_URL,
            state=state
        )
    
    def fetch_token(self, authorization_response: str) -> Dict[str, Any]:
        """Exchange authorization code for access token.
        
        Args:
            authorization_response: The full callback URL with authorization code
            
        Returns:
            Token dictionary with access_token, refresh_token, etc.
        """
        token = self.oauth.fetch_token(
            self.TOKEN_URL,
            authorization_response=authorization_response,
            auth=HTTPBasicAuth(self.client_id, self.client_secret)
        )
        
        # Add expiration timestamp for easier handling
        if "expires_in" in token:
            token["expires_at"] = datetime.utcnow() + timedelta(seconds=token["expires_in"])
        
        return token
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired access token.
        
        Args:
            refresh_token: The refresh token from previous authentication
            
        Returns:
            New token dictionary
        """
        token = self.oauth.refresh_token(
            self.TOKEN_URL,
            refresh_token=refresh_token,
            auth=HTTPBasicAuth(self.client_id, self.client_secret)
        )
        
        if "expires_in" in token:
            token["expires_at"] = datetime.utcnow() + timedelta(seconds=token["expires_in"])
        
        return token
    
    def is_token_expired(self, token: Dict[str, Any]) -> bool:
        """Check if token is expired or about to expire.
        
        Args:
            token: Token dictionary with expires_at field
            
        Returns:
            True if token is expired or expires in less than 5 minutes
        """
        if "expires_at" not in token:
            return True
        
        expires_at = token["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        
        # Consider token expired if it expires in less than 5 minutes
        return datetime.utcnow() + timedelta(minutes=5) > expires_at