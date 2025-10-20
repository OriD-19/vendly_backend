from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, AccessTokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.utils.auth_dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    Creates a user account with hashed password.
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    auth_service = AuthService(db)
    hashed_password = auth_service.hash_password(user_data.password)
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        user_type=user_data.user_type
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint.
    Authenticates user and returns access and refresh tokens.
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    tokens = auth_service.create_tokens(user.id, user.username)
    
    return tokens


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token endpoint.
    Takes a valid refresh token and returns a new access token.
    """
    auth_service = AuthService(db)
    
    # Get new access token
    new_token = auth_service.refresh_access_token(refresh_data.refresh_token)
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return new_token


@router.post("/logout")
def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout endpoint.
    In a stateless JWT system, logout is handled client-side by deleting tokens.
    This endpoint exists for consistency and can be extended with token blacklisting.
    
    Requires authentication to ensure only authenticated users can logout.
    """
    return {
        "message": "Successfully logged out. Please delete your tokens.",
        "username": current_user.username
    }


@router.post("/verify-token")
def verify_token(current_user: User = Depends(get_current_active_user)):
    """
    Verify if the provided access token is valid.
    Returns user information if token is valid.
    
    Useful for:
    - Client-side token validation
    - Checking if user is still authenticated
    - Getting current user info without dedicated endpoint
    """
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "user_type": current_user.user_type
        }
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get the current authenticated user's profile.
    Alternative to /users/me endpoint.
    
    Returns full user information for the authenticated user.
    """
    return current_user
