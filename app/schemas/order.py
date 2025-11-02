from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.order import OrderStatus


# ========== Order Product Schemas ==========

class OrderProductBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)


class OrderProductCreate(BaseModel):
    """Schema for creating order products. Price is fetched from database."""
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderProductUpdate(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)


class OrderProductResponse(OrderProductBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)


# ========== Order Schemas ==========

class OrderBase(BaseModel):
    shipping_address: str = Field(..., max_length=255)
    shipping_city: str = Field(..., max_length=100)
    shipping_postal_code: str = Field(..., max_length=20)
    shipping_country: str = Field(..., max_length=100)


class OrderCreate(OrderBase):
    products: List[OrderProductCreate] = Field(..., min_length=1)


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    shipping_address: Optional[str] = Field(None, max_length=255)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_postal_code: Optional[str] = Field(None, max_length=20)
    shipping_country: Optional[str] = Field(None, max_length=100)


class OrderResponse(OrderBase):
    id: int
    order_number: str
    customer_id: int
    total_amount: float
    status: OrderStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    products: List[OrderProductResponse] = []

    model_config = ConfigDict(from_attributes=True)
