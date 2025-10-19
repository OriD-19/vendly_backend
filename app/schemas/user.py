from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserType, PaymentMethod


# ========== User Schemas ==========

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    user_type: UserType = UserType.CUSTOMER


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=80)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    id: int
    user_type: UserType
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== Customer Schemas ==========

class CustomerCreate(UserCreate):
    user_type: UserType = UserType.CUSTOMER
    phone: Optional[str] = Field(None, max_length=20)
    preferred_payment_method: Optional[PaymentMethod] = None


class CustomerUpdate(UserUpdate):
    phone: Optional[str] = Field(None, max_length=20)
    preferred_payment_method: Optional[PaymentMethod] = None


class CustomerResponse(UserResponse):
    phone: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethod] = None

    model_config = ConfigDict(from_attributes=True)


# ========== Store Owner Schemas ==========

class StoreOwnerCreate(UserCreate):
    user_type: UserType = UserType.STORE
    store_id: Optional[int] = None
    commission_rate: int = Field(default=5, ge=0, le=100)


class StoreOwnerUpdate(UserUpdate):
    store_id: Optional[int] = None
    commission_rate: Optional[int] = Field(None, ge=0, le=100)


class StoreOwnerResponse(UserResponse):
    store_id: Optional[int] = None
    commission_rate: int

    model_config = ConfigDict(from_attributes=True)


# ========== User Preferences Schemas ==========

class UserPreferencesBase(BaseModel):
    theme: str = Field(default="light", max_length=50)
    notifications_enabled: bool = True
    email_alerts: bool = True
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="en", max_length=50)
    currency: str = Field(default="USD", max_length=10)


class UserPreferencesCreate(UserPreferencesBase):
    user_id: int


class UserPreferencesUpdate(BaseModel):
    theme: Optional[str] = Field(None, max_length=50)
    notifications_enabled: Optional[bool] = None
    email_alerts: Optional[bool] = None
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=10)


class UserPreferencesResponse(UserPreferencesBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
