from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, computed_field


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
    production_cost: Optional[float] = Field(None, ge=0)
    discount_price: Optional[float] = Field(None, gt=0)
    discount_end_date: Optional[datetime] = None
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
    production_cost: Optional[float] = Field(None, ge=0)
    discount_price: Optional[float] = Field(None, gt=0)
    discount_end_date: Optional[datetime] = None
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
    
    @computed_field
    @property
    def has_active_offer(self) -> bool:
        """Check if product has an active discount offer."""
        if self.discount_price is None:
            return False
        if self.discount_end_date is None:
            return True  # No end date means offer is always active
        return self.discount_end_date > datetime.utcnow()
    
    @computed_field
    @property
    def effective_price(self) -> float:
        """Get the current effective price (discount or regular)."""
        if self.has_active_offer and self.discount_price is not None:
            return self.discount_price
        return self.price
    
    @computed_field
    @property
    def discount_percentage(self) -> Optional[float]:
        """Calculate discount percentage if offer is active."""
        if not self.has_active_offer or self.discount_price is None:
            return None
        return round(((self.price - self.discount_price) / self.price) * 100, 2)


class ProductBulkCreate(BaseModel):
    """Schema for creating multiple products at once"""
    products: List[ProductCreate] = Field(..., min_length=1, max_length=100)


class ProductBulkResponse(BaseModel):
    """Response for bulk product creation"""
    created: List[ProductResponse]
    failed: List[dict]  # Products that failed validation
    total_requested: int
    total_created: int
    total_failed: int
