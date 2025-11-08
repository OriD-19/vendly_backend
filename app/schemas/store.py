from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ========== Store Schemas ==========

class StoreBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    store_location: str = Field(..., max_length=120)
    type: str = Field(..., max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    profile_image: Optional[str] = Field(None, max_length=255)


class StoreCreate(StoreBase):
    owner_id: int


class StoreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    store_location: Optional[str] = Field(None, max_length=120)
    type: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    profile_image: Optional[str] = Field(None, max_length=255)


class StoreResponse(StoreBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    showcase_images: List[str] = Field(default_factory=list, description="URLs of latest product images for showcase")

    model_config = ConfigDict(from_attributes=True)
