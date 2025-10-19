from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ========== Category Schemas ==========

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
