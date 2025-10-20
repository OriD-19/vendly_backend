"""
Logging Middleware for Vendly API
Logs all incoming requests and outgoing responses.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs request and response information.
    
    Features:
    - Logs HTTP method, path, status code
    - Measures request processing time
    - Adds custom headers with timing info
    - Logs user information if authenticated
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Start timer
        start_time = time.time()
        
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", f"{time.time()}")
        
        # Get user info if available
        user_info = ""
        if hasattr(request.state, "is_authenticated") and request.state.is_authenticated:
            user_info = f" | User: {request.state.username} (ID: {request.state.user_id})"
        
        # Log incoming request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path}{user_info}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"[{request_id}] Completed in {process_time:.3f}s - Status: {response.status_code}"
        )
        
        # Add custom headers
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        response.headers["X-Request-ID"] = request_id
        
        return response
