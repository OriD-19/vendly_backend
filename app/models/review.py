from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product


class Review(Base):
    """
    Product review model.
    
    Features:
    - Each customer can only review a product once
    - Rating from 1 to 5 stars
    - Optional comment
    - Editable and deletable by the customer who created it
    """
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Review content
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 stars
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    customer_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    customer: Mapped["User"] = relationship("User", back_populates="reviews")  # type: ignore
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")  # type: ignore
    
    # Constraints
    __table_args__ = (
        # Each customer can only review a product once
        UniqueConstraint('customer_id', 'product_id', name='unique_customer_product_review'),
        # Rating must be between 1 and 5
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range_check'),
    )
