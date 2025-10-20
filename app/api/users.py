from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.utils.auth_dependencies import get_current_active_user
from app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information.
    Requires valid access token.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.
    Users can only update their own profile.
    """
    # Check if new username already exists (if being updated)
    if user_data.username and user_data.username != current_user.username:
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Check if new email already exists (if being updated)
    if user_data.email and user_data.email != current_user.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update user fields
    update_data = user_data.model_dump(exclude_unset=True, exclude={'password'})
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    # Handle password update separately if provided
    if user_data.password:
        auth_service = AuthService(db)
        current_user.password_hash = auth_service.hash_password(user_data.password)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete the current user's account.
    This is a permanent action and cannot be undone.
    """
    db.delete(current_user)
    db.commit()
    return None


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user information by ID.
    Requires authentication.
    
    Note: Consider adding privacy controls to limit what information
    is visible to other users vs the user themselves.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    user_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of users with optional filtering.
    Requires authentication.
    
    Query Parameters:
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 100, max: 200)
    - user_type: Filter by user type (customer, store_owner)
    - search: Search by username or email
    """
    query = db.query(User)
    
    # Filter by user type
    if user_type:
        query = query.filter(User.user_type == user_type)
    
    # Search by username or email
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_filter)) | 
            (User.email.ilike(search_filter))
        )
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return users


@router.get("/username/{username}", response_model=UserResponse)
def get_user_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user information by username.
    Requires authentication.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    return user
