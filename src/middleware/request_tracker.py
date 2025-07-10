"""
Request tracking and logging middleware
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

logger = logging.getLogger(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking and logging requests"""
    
    def __init__(
        self,
        app,
        log_request_body: bool = False,
        log_response_body: bool = False,
        slow_request_threshold: float = 1.0
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracking"""
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error and re-raise
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {type(e).__name__}",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "process_time": process_time,
                    "error": str(e)
                }
            )
            raise
        
        # Calculate process time
        process_time = time.time() - start_time
        
        # Add tracking headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        # Log response
        await self._log_response(request, response, request_id, process_time)
        
        # Log slow requests
        if process_time > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected: {process_time:.2f}s",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "process_time": process_time
                }
            )
        
        return response
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request"""
        
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client": f"{request.client.host}:{request.client.port}" if request.client else None
        }
        
        # Optionally log request body
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Store body for later use
                    request.state.body = body
                    # Try to parse as JSON
                    try:
                        log_data["body"] = json.loads(body)
                    except json.JSONDecodeError:
                        log_data["body"] = body.decode("utf-8", errors="ignore")[:1000]
            except Exception as e:
                log_data["body_error"] = str(e)
        
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra=log_data
        )
    
    async def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        process_time: float
    ):
        """Log outgoing response"""
        
        log_data = {
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time": process_time,
            "path": request.url.path,
            "method": request.method
        }
        
        # Log response body for errors
        if self.log_response_body and response.status_code >= 400:
            try:
                # This is tricky with streaming responses
                if hasattr(response, "body"):
                    log_data["response_body"] = response.body[:1000]
            except Exception:
                pass
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        logger.log(
            log_level,
            f"Response: {response.status_code} {request.method} {request.url.path} ({process_time:.3f}s)",
            extra=log_data
        )


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring API performance"""
    
    def __init__(self, app):
        super().__init__(app)
        self.endpoint_stats = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track endpoint performance"""
        
        endpoint = f"{request.method} {request.url.path}"
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Update statistics
        process_time = time.time() - start_time
        self._update_stats(endpoint, process_time, response.status_code)
        
        return response
    
    def _update_stats(self, endpoint: str, process_time: float, status_code: int):
        """Update endpoint statistics"""
        
        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = {
                "count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "errors": 0,
                "last_called": None
            }
        
        stats = self.endpoint_stats[endpoint]
        stats["count"] += 1
        stats["total_time"] += process_time
        stats["min_time"] = min(stats["min_time"], process_time)
        stats["max_time"] = max(stats["max_time"], process_time)
        stats["last_called"] = time.time()
        
        if status_code >= 400:
            stats["errors"] += 1
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        
        results = {}
        for endpoint, stats in self.endpoint_stats.items():
            if stats["count"] > 0:
                results[endpoint] = {
                    "count": stats["count"],
                    "avg_time": stats["total_time"] / stats["count"],
                    "min_time": stats["min_time"],
                    "max_time": stats["max_time"],
                    "error_rate": stats["errors"] / stats["count"],
                    "last_called": stats["last_called"]
                }
        
        return results