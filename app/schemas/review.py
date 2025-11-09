from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ========== Review Schemas ==========

class ReviewBase(BaseModel):
    """Base schema for review data"""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, max_length=2000, description="Optional review comment")


class ReviewCreate(ReviewBase):
    """Schema for creating a new review"""
    product_id: int = Field(..., description="ID of the product being reviewed")
    
    @field_validator('comment')
    @classmethod
    def validate_comment(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class ReviewUpdate(BaseModel):
    """Schema for updating an existing review"""
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, max_length=2000, description="Optional review comment")
    
    @field_validator('comment')
    @classmethod
    def validate_comment(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class ReviewResponse(ReviewBase):
    """Schema for review response"""
    id: int
    product_id: int
    customer_id: int
    customer_username: str = Field(..., description="Username of the reviewer")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProductReviewStats(BaseModel):
    """Statistics for product reviews"""
    product_id: int
    total_reviews: int = Field(..., description="Total number of reviews")
    average_rating: float = Field(..., description="Average rating (0-5)")
    rating_distribution: dict[int, int] = Field(
        ..., 
        description="Distribution of ratings (1-5 stars with counts)"
    )
    # Example: {"1": 2, "2": 5, "3": 10, "4": 20, "5": 15}


class StoreReviewStats(BaseModel):
    """Statistics for store reviews (aggregate of all products)"""
    store_id: int
    total_reviews: int = Field(..., description="Total reviews across all products")
    average_rating: float = Field(..., description="Average rating across all products (0-5)")
    total_products_reviewed: int = Field(..., description="Number of products with at least one review")
    rating_distribution: dict[int, int] = Field(
        ..., 
        description="Distribution of ratings across all products"
    )
