"""
Rate limiting middleware for API endpoints
"""

import time
import asyncio
from typing import Dict, Optional, Callable
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit violations"""
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)}
        )


class RateLimiter:
    """Token bucket rate limiter implementation"""
    
    def __init__(self, rate: int, per: float, burst: Optional[int] = None):
        """
        Initialize rate limiter
        
        Args:
            rate: Number of requests allowed
            per: Time period in seconds
            burst: Maximum burst size (defaults to rate)
        """
        self.rate = rate
        self.per = per
        self.burst = burst or rate
        self.allowance = float(self.burst)
        self.last_check = time.time()
    
    def allow_request(self) -> tuple[bool, float]:
        """
        Check if request is allowed
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        
        # Replenish tokens
        self.allowance += time_passed * (self.rate / self.per)
        if self.allowance > self.burst:
            self.allowance = float(self.burst)
        
        if self.allowance < 1.0:
            # Calculate retry after
            retry_after = (1.0 - self.allowance) * (self.per / self.rate)
            return False, retry_after
        
        self.allowance -= 1.0
        return True, 0.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(
        self,
        app,
        default_limit: int = 60,
        default_window: int = 60,
        espn_limit: int = 10,
        espn_window: int = 60,
        ai_limit: int = 20,
        ai_window: int = 3600
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window = default_window
        self.espn_limit = espn_limit
        self.espn_window = espn_window
        self.ai_limit = ai_limit
        self.ai_window = ai_window
        
        # Storage for rate limiters per client
        self.limiters: Dict[str, Dict[str, RateLimiter]] = defaultdict(dict)
        
        # Cleanup old limiters periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def get_client_id(self, request: Request) -> str:
        """Extract client identifier from request"""
        # Try to get authenticated user ID
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        client = request.client
        if client:
            return f"ip:{client.host}"
        
        return "ip:unknown"
    
    def get_rate_limit_key(self, request: Request) -> str:
        """Determine rate limit category for request"""
        path = request.url.path
        
        # ESPN API endpoints
        if "/api/espn" in path:
            return "espn"
        
        # AI/ML endpoints
        if any(x in path for x in ["/ai/", "/recommendations", "/analysis"]):
            return "ai"
        
        # Default rate limit
        return "default"
    
    def get_limiter(self, client_id: str, category: str) -> RateLimiter:
        """Get or create rate limiter for client and category"""
        key = f"{client_id}:{category}"
        
        if key not in self.limiters[client_id]:
            if category == "espn":
                rate_limiter = RateLimiter(self.espn_limit, self.espn_window)
            elif category == "ai":
                rate_limiter = RateLimiter(self.ai_limit, self.ai_window)
            else:
                rate_limiter = RateLimiter(self.default_limit, self.default_window)
            
            self.limiters[client_id][key] = rate_limiter
        
        return self.limiters[client_id][key]
    
    def cleanup_old_limiters(self):
        """Remove old rate limiters to prevent memory leaks"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        self.last_cleanup = current_time
        
        # Remove limiters that haven't been used recently
        cutoff_time = current_time - 3600  # 1 hour
        
        clients_to_remove = []
        for client_id, limiters in self.limiters.items():
            if all(l.last_check < cutoff_time for l in limiters.values()):
                clients_to_remove.append(client_id)
        
        for client_id in clients_to_remove:
            del self.limiters[client_id]
        
        if clients_to_remove:
            logger.info(f"Cleaned up {len(clients_to_remove)} old rate limiters")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""
        
        # Skip rate limiting for certain paths
        if request.url.path in ["/api/docs", "/api/openapi.json", "/api/health"]:
            return await call_next(request)
        
        # Periodic cleanup
        self.cleanup_old_limiters()
        
        # Get client and category
        client_id = self.get_client_id(request)
        category = self.get_rate_limit_key(request)
        
        # Get rate limiter
        limiter = self.get_limiter(client_id, category)
        
        # Check rate limit
        allowed, retry_after = limiter.allow_request()
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {category} "
                f"endpoint {request.url.path}"
            )
            raise RateLimitExceeded(retry_after=int(retry_after))
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Category"] = category
        response.headers["X-RateLimit-Remaining"] = str(int(limiter.allowance))
        
        return response


class APIRateLimiter:
    """Service-level rate limiter for external API calls"""
    
    def __init__(self, name: str, calls_per_minute: int = 30):
        self.name = name
        self.calls_per_minute = calls_per_minute
        self.window_size = 60  # 1 minute window
        self.calls = deque()
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(self) -> bool:
        """Check if API call is allowed"""
        async with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.window_size)
            
            # Remove old calls
            while self.calls and self.calls[0] < cutoff:
                self.calls.popleft()
            
            # Check if under limit
            if len(self.calls) >= self.calls_per_minute:
                return False
            
            # Record this call
            self.calls.append(now)
            return True
    
    async def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        while not await self.check_rate_limit():
            # Calculate wait time
            if self.calls:
                oldest_call = self.calls[0]
                wait_time = (
                    oldest_call + timedelta(seconds=self.window_size) - 
                    datetime.utcnow()
                ).total_seconds()
                
                if wait_time > 0:
                    logger.info(
                        f"{self.name} rate limit reached, "
                        f"waiting {wait_time:.1f}s"
                    )
                    await asyncio.sleep(wait_time + 0.1)
                else:
                    await asyncio.sleep(1)
            else:
                await asyncio.sleep(1)


# Global rate limiters for external APIs
espn_rate_limiter = APIRateLimiter("ESPN", calls_per_minute=30)
ai_rate_limiter = APIRateLimiter("AI", calls_per_minute=20)