from pydantic import BaseModel, Field


# ========== Authentication Schemas ==========

class LoginRequest(BaseModel):
    """Schema for user login request."""
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Schema for token response (login and refresh)."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """Schema for access token refresh response."""
    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str
