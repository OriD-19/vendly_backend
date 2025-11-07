from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, AccessTokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.utils.auth_dependencies import get_current_active_user
from app.models.user import UserType

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    Creates a user account with hashed password.
    For store owners, automatically creates their store.
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
    
    # If store owner, create their store
    store = None
    if new_user.user_type == UserType.STORE:
        from app.services.store_service import StoreService
        from app.schemas.store import StoreCreate
        from app.models.user import StoreOwner
        from sqlalchemy.orm import joinedload
        
        store_service = StoreService(db)
        store_data = StoreCreate(
            name=user_data.store_name,
            owner_id=new_user.id,
            store_location=user_data.store_location,
            type=user_data.type,
            phone=user_data.phone
        )
        store = store_service.create_store(store_data, new_user)
        
        # Update the store owner's store_id
        if isinstance(new_user, StoreOwner):
            new_user.store_id = store.id
            db.commit()
        
        # Reload user with store relationship eagerly loaded
        new_user = db.query(User).options(joinedload(User.store)).filter(User.id == new_user.id).first()
    else:
        # Refresh user to ensure all relationships are loaded
        db.refresh(new_user)
    
    # Create and return tokens
    tokens = auth_service.create_tokens(new_user, store)
    
    # Explicitly construct the response to ensure proper serialization
    from app.schemas.auth import TokenResponse as TokenResponseSchema
    response = TokenResponseSchema(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=tokens["user"]
    )
    
    return response


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
    
    # Get store if user is a store owner and eager load it
    store = None
    if user.user_type == UserType.STORE:
        from app.models.store import Store
        from sqlalchemy.orm import joinedload
        # Reload user with store relationship
        user = db.query(User).options(joinedload(User.store)).filter(User.id == user.id).first()
        store = db.query(Store).filter(Store.owner_id == user.id).first()
    
    # Create tokens
    tokens = auth_service.create_tokens(user, store)
    
    # Explicitly construct the response to ensure proper serialization
    from app.schemas.auth import TokenResponse as TokenResponseSchema
    response = TokenResponseSchema(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=tokens["user"]
    )
    
    return response


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
