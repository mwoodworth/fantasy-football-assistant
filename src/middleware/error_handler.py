"""
Global error handling middleware
"""

import sys
import traceback
import logging
from typing import Union, Dict, Any, Optional
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from pydantic import ValidationError

from ..services.espn_integration import ESPNServiceError, ESPNAuthError

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format"""
    
    @staticmethod
    def create(
        error_type: str,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "error": {
                "type": error_type,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "details": details or {}
            }
        }


async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions"""
    
    # Generate request ID for tracking
    request_id = getattr(request.state, "request_id", None)
    
    # Log the full exception
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Don't expose internal errors in production
    if getattr(request.app.state, "debug", False):
        error_details = {
            "traceback": traceback.format_exc().split("\n")
        }
    else:
        error_details = None
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse.create(
            error_type="internal_error",
            message="An unexpected error occurred. Please try again later.",
            status_code=500,
            details=error_details,
            request_id=request_id
        )
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    
    request_id = getattr(request.state, "request_id", None)
    
    # Log 5xx errors
    if exc.status_code >= 500:
        logger.error(
            f"HTTP {exc.status_code}: {exc.detail}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method
            }
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.create(
            error_type="http_error",
            message=exc.detail,
            status_code=exc.status_code,
            details=getattr(exc, "headers", None),
            request_id=request_id
        ),
        headers=getattr(exc, "headers", None)
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors"""
    
    request_id = getattr(request.state, "request_id", None)
    
    # Format validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation error: {len(errors)} errors",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "errors": errors
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse.create(
            error_type="validation_error",
            message="Invalid request data",
            status_code=422,
            details={"errors": errors},
            request_id=request_id
        )
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database exceptions"""
    
    request_id = getattr(request.state, "request_id", None)
    
    # Determine error type and message
    if isinstance(exc, IntegrityError):
        error_type = "database_integrity_error"
        message = "Database constraint violation"
        status_code = status.HTTP_409_CONFLICT
        
        # Extract useful info from integrity errors
        details = {}
        if "UNIQUE constraint failed" in str(exc):
            details["constraint"] = "unique_violation"
        elif "FOREIGN KEY constraint failed" in str(exc):
            details["constraint"] = "foreign_key_violation"
            
    elif isinstance(exc, OperationalError):
        error_type = "database_connection_error"
        message = "Database connection error"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        details = {"retry_after": 30}
        
    else:
        error_type = "database_error"
        message = "Database operation failed"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        details = None
    
    logger.error(
        f"Database error: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse.create(
            error_type=error_type,
            message=message,
            status_code=status_code,
            details=details,
            request_id=request_id
        )
    )


async def espn_exception_handler(request: Request, exc: ESPNServiceError) -> JSONResponse:
    """Handle ESPN service exceptions"""
    
    request_id = getattr(request.state, "request_id", None)
    
    if isinstance(exc, ESPNAuthError):
        error_type = "espn_auth_error"
        message = "ESPN authentication failed. Please check your credentials."
        status_code = status.HTTP_401_UNAUTHORIZED
        details = {"auth_required": True}
    else:
        error_type = "espn_service_error"
        message = "ESPN service temporarily unavailable"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        details = {"retry_after": 60}
    
    logger.error(
        f"ESPN service error: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_type": error_type
        }
    )
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse.create(
            error_type=error_type,
            message=message,
            status_code=status_code,
            details=details,
            request_id=request_id
        )
    )


def setup_exception_handlers(app):
    """Configure all exception handlers for the app"""
    
    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # Database errors
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    
    # ESPN service errors
    app.add_exception_handler(ESPNServiceError, espn_exception_handler)
    
    # Catch-all handler
    app.add_exception_handler(Exception, global_error_handler)
    
    logger.info("Exception handlers configured")