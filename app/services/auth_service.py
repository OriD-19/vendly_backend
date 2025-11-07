from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.user import User, UserType
from app.config import Config


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ========== Password Hashing ==========
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain text password."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain text password against a hashed password."""
        return pwd_context.verify(plain_password, hashed_password)
    
    # ========== User Authentication ==========
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username and password.
        Returns the User object if authentication is successful, None otherwise.
        """
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    # ========== JWT Token Creation ==========
    def create_jwt_tokens(self, user: User) -> Dict[str, str]:
        """
        Create JWT tokens for a user.
        """
        token_data = {
            "sub": str(user.id),
            "username": user.username
        }

        access_token = AuthService.create_access_token(token_data)
        refresh_token = AuthService.create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    @staticmethod
    def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        Default expiration: 15 minutes
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "type": "access"
        })
        encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT refresh token.
        Default expiration: 15 days
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })
        encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_tokens(user: User) -> Dict[str, Any]:
        """
        Create both access and refresh tokens for a user.
        Returns a dictionary with tokens and user details.
        """
        # Prepare token data
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type
        }
        
        # Add store details if user is a store owner
        if user.user_type == UserType.STORE and hasattr(user, 'store') and user.store:
            token_data.update({
                "store_id": user.store.id,
                "store_name": user.store.name
            })
        
        # Create tokens
        access_token = AuthService.create_access_token(token_data)
        refresh_token = AuthService.create_refresh_token(token_data)
        
        # Prepare user details
        user_details = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type
        }
        
        # Add store details if available
        if user.user_type == UserType.STORE:
            # Try to get store details
            try:
                store = user.store if hasattr(user, 'store') and user.store else None
                if store:
                    user_details['store'] = {
                        'id': store.id,
                        'name': store.name,
                        'location': store.store_location,
                        'type': store.type
                    }
            except Exception:
                # Fallback if store retrieval fails
                user_details['store'] = None
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_details
        }
    
    # ========== JWT Token Verification ==========
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
        """
        Verify and decode a JWT token.
        Returns the payload if valid, None otherwise.
        """
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
            
            # Check if token type matches
            if payload.get("type") != token_type:
                return None
            
            # jwt.decode() already validates expiration, no need for manual check
            return payload
        except JWTError:
            return None
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Get user from a valid access token.
        """
        payload = self.verify_token(token, token_type="access")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        return user
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Generate a new access token using a valid refresh token.
        """
        payload = self.verify_token(refresh_token, token_type="refresh")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        username = payload.get("username")
        
        if not user_id or not username:
            return None
        
        # Verify user still exists
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return None
        
        # Create new access token
        token_data = {
            "sub": str(user_id),
            "username": username
        }
        access_token = self.create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }