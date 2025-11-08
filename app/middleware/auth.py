"""
Authentication Middleware for Vendly API
Handles JWT token validation and user context injection.

This middleware extracts JWT tokens from Authorization headers,
validates them, and injects user information into the request state.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import JWTError, jwt
from app.config import Config
from app.database import SessionLocal
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


# Routes that don't require authentication
PUBLIC_ROUTES = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
}

# Routes that start with these prefixes are public
PUBLIC_PREFIXES = [
    "/static",
    "/docs",
    "/redoc",
]

# Specific route patterns that are public (require method + path check)
PUBLIC_ROUTE_PATTERNS = {
    # Store endpoints (public browsing)
    ("GET", "/stores"),
    ("GET", "/stores/"),
    ("GET", "/stores/search"),
    # Product endpoints (public browsing)
    ("GET", "/products"),
    ("GET", "/products/"),
    # Categories (public browsing)
    ("GET", "/categories"),
    ("GET", "/categories/"),
}


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT Authentication Middleware.
    
    Features:
    - Validates JWT tokens from Authorization header
    - Injects user info into request.state
    - Supports public routes (no auth required)
    - Supports protected routes (auth required)
    - Provides detailed error messages
    
    Usage:
        app.add_middleware(AuthMiddleware)
    
    Access user in endpoints:
        def my_endpoint(request: Request):
            user_id = request.state.user_id
            username = request.state.username
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.secret_key = Config.SECRET_KEY
        self.algorithm = Config.ALGORITHM
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and validate authentication if needed.
        """
        # Initialize request state
        request.state.user_id = None
        request.state.username = None
        request.state.user_type = None
        request.state.is_authenticated = False
        
        # Allow OPTIONS requests (CORS preflight) without authentication
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Check if route is public
        if self._is_public_route(request.method, request.url.path):
            # Public route - no auth required
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")
        
        if not auth_header:
            # No token provided for protected route
            return self._unauthorized_response("Missing authorization header")
        
        if not auth_header.startswith("Bearer "):
            return self._unauthorized_response("Invalid authorization header format. Use: Bearer <token>")
        
        token = auth_header.split(" ")[1]
        
        # Validate token and extract user info
        try:
            payload = self._verify_token(token)
            
            if not payload:
                return self._unauthorized_response("Invalid or expired token")
            
            # Extract user information from token
            user_id = payload.get("sub")
            username = payload.get("username")
            user_type = payload.get("user_type")
            
            if not user_id or not username:
                return self._unauthorized_response("Invalid token payload")
            
            # Verify user exists in database
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == int(user_id)).first()
                
                if not user:
                    return self._unauthorized_response("User not found")
                
                # Inject user info into request state
                request.state.user_id = user.id
                request.state.username = user.username
                request.state.user_type = user.user_type.value if hasattr(user.user_type, 'value') else user_type
                request.state.is_authenticated = True
                request.state.user = user  # Full user object if needed
                
                logger.debug(f"Authenticated user: {username} (ID: {user_id})")
                
            finally:
                db.close()
            
            # Continue to endpoint
            response = await call_next(request)
            return response
            
        except JWTError as e:
            logger.warning(f"JWT validation error: {str(e)}")
            return self._unauthorized_response("Invalid token")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return self._server_error_response("Authentication failed")
    
    def _verify_token(self, token: str) -> dict | None:
        """
        Verify JWT token and return payload.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload dict or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            return None
    
    def _is_public_route(self, method: str, path: str) -> bool:
        """
        Check if route is public (doesn't require authentication).
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            
        Returns:
            True if route is public, False otherwise
        """
        # Exact match
        if path in PUBLIC_ROUTES:
            return True
        
        # Prefix match
        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True
        
        # Method + path pattern match (for browsing endpoints)
        if (method, path) in PUBLIC_ROUTE_PATTERNS:
            return True
        
        # Check if it's a GET request to a specific resource (e.g., /stores/123)
        # Allow GET requests to stores and products for public browsing
        if method == "GET":
            # /stores/:id
            if path.startswith("/stores/") and path.count("/") == 2:
                # Check if it's a numeric ID (not /stores/my-store)
                store_id = path.split("/")[2]
                if store_id.isdigit():
                    return True
            
            # /stores/:id/products (public product browsing)
            if path.startswith("/stores/") and "/products" in path:
                return True
            
            # /stores/:id/products/count
            if path.startswith("/stores/") and path.endswith("/products/count"):
                return True
            
            # /products/:id
            if path.startswith("/products/") and path.count("/") == 2:
                product_id = path.split("/")[2]
                if product_id.isdigit():
                    return True
            
            # /categories/:id
            if path.startswith("/categories/") and path.count("/") == 2:
                category_id = path.split("/")[2]
                if category_id.isdigit():
                    return True
        
        return False
    
    def _unauthorized_response(self, detail: str) -> JSONResponse:
        """
        Return 401 Unauthorized response.
        """
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": detail,
                "error_type": "authentication_error"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    def _server_error_response(self, detail: str) -> JSONResponse:
        """
        Return 500 Internal Server Error response.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": detail,
                "error_type": "server_error"
            }
        )


class OptionalAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional JWT Authentication Middleware.
    
    Similar to AuthMiddleware but doesn't block requests without tokens.
    Useful for endpoints that work differently based on auth status.
    
    Features:
    - Validates JWT tokens if present
    - Doesn't block if token is missing
    - Injects user info into request.state if authenticated
    
    Usage:
        app.add_middleware(OptionalAuthMiddleware)
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.secret_key = Config.SECRET_KEY
        self.algorithm = Config.ALGORITHM
    
    async def dispatch(self, request: Request, call_next):
        """Process request with optional authentication."""
        # Initialize request state
        request.state.user_id = None
        request.state.username = None
        request.state.user_type = None
        request.state.is_authenticated = False
        
        # Extract token if present
        auth_header = request.headers.get("authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            try:
                payload = jwt.decode(
                    token,
                    self.secret_key,
                    algorithms=[self.algorithm]
                )
                
                user_id = payload.get("sub")
                username = payload.get("username")
                user_type = payload.get("user_type")
                
                if user_id and username:
                    # Verify user exists
                    db = SessionLocal()
                    try:
                        user = db.query(User).filter(User.id == int(user_id)).first()
                        
                        if user:
                            request.state.user_id = user.id
                            request.state.username = user.username
                            request.state.user_type = user.user_type.value if hasattr(user.user_type, 'value') else user_type
                            request.state.is_authenticated = True
                            request.state.user = user
                            
                            logger.debug(f"Optional auth: Authenticated user {username}")
                    finally:
                        db.close()
                        
            except JWTError as e:
                # Invalid token, but don't block request
                logger.debug(f"Optional auth: Invalid token - {str(e)}")
                pass
            except Exception as e:
                logger.warning(f"Optional auth error: {str(e)}")
                pass
        
        response = await call_next(request)
        return response
