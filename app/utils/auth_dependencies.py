from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from the access token.
    Raises HTTPException if token is invalid or user not found.
    """
    token = credentials.credentials
    auth_service = AuthService(db)
    
    user = auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure the current user is active.
    Can be extended with additional user status checks.
    """
    # Add any additional checks here (e.g., is_active, is_verified, etc.)
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally get the current user.
    Returns None if no valid token is provided.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    auth_service = AuthService(db)
    
    return auth_service.get_user_from_token(token)


async def get_websocket_user(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to authenticate WebSocket connections.
    
    Token can be provided via:
    1. Query parameter: ?token=<jwt_token>
    2. WebSocket subprotocol header
    
    Raises:
        WebSocket close with code 1008 (Policy Violation) if authentication fails
    """
    # Try to get token from query params
    if not token:
        token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )
    
    auth_service = AuthService(db)
    user = auth_service.get_user_from_token(token)
    
    if not user:
        await websocket.close(code=1008, reason="Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return user
