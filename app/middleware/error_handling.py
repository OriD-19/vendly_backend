"""
Error Handling Middleware for Vendly API
Catches and formats exceptions consistently.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from jose.exceptions import JWTError
import logging

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handler middleware.
    
    Features:
    - Catches all unhandled exceptions
    - Formats errors consistently
    - Logs errors with context
    - Returns proper HTTP status codes
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except StarletteHTTPException as exc:
            # HTTP exceptions (400, 401, 404, etc.)
            logger.warning(
                f"HTTP Exception: {exc.status_code} - {exc.detail} | "
                f"Path: {request.url.path}"
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "detail": exc.detail,
                    "error_type": "http_exception",
                    "path": request.url.path
                }
            )
        
        except RequestValidationError as exc:
            # Pydantic validation errors
            logger.warning(f"Validation error: {exc.errors()}")
            return JSONResponse(
                status_code=422,
                content={
                    "detail": "Validation error",
                    "error_type": "validation_error",
                    "errors": exc.errors()
                }
            )
        
        except JWTError as exc:
            # JWT errors (should be caught by auth middleware)
            logger.error(f"JWT error: {str(exc)}")
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Authentication failed",
                    "error_type": "jwt_error"
                }
            )
        
        except ValueError as exc:
            # Value errors (bad input)
            logger.warning(f"Value error: {str(exc)}")
            return JSONResponse(
                status_code=400,
                content={
                    "detail": str(exc),
                    "error_type": "value_error"
                }
            )
        
        except Exception as exc:
            # Catch-all for unexpected errors
            logger.error(
                f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error_type": "internal_error",
                    "message": "An unexpected error occurred. Please try again later."
                }
            )
