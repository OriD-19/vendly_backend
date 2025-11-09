from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ========== Category Schemas ==========

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class CategoryCreate(CategoryBase):
    pass


class CategoryBulkCreate(BaseModel):
    """Schema for creating multiple categories at once"""
    categories: List[CategoryCreate] = Field(..., min_length=1, max_length=100)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryWithProductCount(CategoryResponse):
    """Category with product count for menu displays"""
    product_count: int = Field(..., description="Number of active products in this category")


class CategoryBulkResponse(BaseModel):
    """Response for bulk category creation"""
    created: List[CategoryResponse]
    skipped: List[dict]  # Categories that already existed
    total_requested: int
    total_created: int
    total_skipped: int
