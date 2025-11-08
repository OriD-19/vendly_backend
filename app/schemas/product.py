from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ========== Tag Schemas ==========

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)


class TagResponse(TagBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== Product Image Schemas ==========

class ProductImageBase(BaseModel):
    image_url: str = Field(..., max_length=255)


class ProductImageCreate(ProductImageBase):
    product_id: int


class ProductImageUpdate(BaseModel):
    image_url: Optional[str] = Field(None, max_length=255)


class ProductImageResponse(ProductImageBase):
    id: int
    product_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== Product Schemas ==========

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    short_description: Optional[str] = Field(None, max_length=255)
    long_description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    store_id: int
    category_id: int
    tag_ids: Optional[List[int]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    short_description: Optional[str] = Field(None, max_length=255)
    long_description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None


class ProductResponse(ProductBase):
    id: int
    store_id: int
    category_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagResponse] = []
    images: List[ProductImageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProductBulkCreate(BaseModel):
    """Schema for creating multiple products at once"""
    products: List[ProductCreate] = Field(..., min_items=1, max_items=100)


class ProductBulkResponse(BaseModel):
    """Response for bulk product creation"""
    created: List[ProductResponse]
    failed: List[dict]  # Products that failed validation
    total_requested: int
    total_created: int
    total_failed: int
