from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.store import Store
    from app.models.category import Category
    from app.models.order import OrderProduct


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)

    # product details
    name: Mapped[str] = mapped_column(String(80))
    short_description: Mapped[str | None] = mapped_column(String(255), default=None)
    long_description: Mapped[str | None] = mapped_column(String(1000), default=None)

    price: Mapped[float] = mapped_column(Float)
    production_cost: Mapped[float] = mapped_column(Float, default=0.0)  # Cost to produce/acquire the product
    discount_price: Mapped[float | None] = mapped_column(Float, default=None)  # Discounted price (null = no discount)
    discount_end_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)  # Discount expiry date
    stock: Mapped[int] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # store relationship
    store_id: Mapped[int] = mapped_column(ForeignKey('stores.id'))
    store: Mapped["Store"] = relationship("Store", back_populates="products") # type: ignore

    # category relationship
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    category: Mapped["Category"] = relationship("Category", back_populates="products") # type: ignore

    # tags relationship
    tags: Mapped[List["Tag"]] = relationship("Tag", secondary="product_tags", back_populates="products")

    # images
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product")

    # get all orders containing this product
    orders: Mapped[List["OrderProduct"]] = relationship("OrderProduct", back_populates="product") # type: ignore


class Tag(Base):
    __tablename__ = 'tags'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    products: Mapped[List["Product"]] = relationship(
        "Product", secondary="product_tags", back_populates="tags")


class ProductTag(Base):
    __tablename__ = 'product_tags'

    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey('tags.id'), primary_key=True)


class ProductImage(Base):
    __tablename__ = 'product_images'

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    # url to the image stored in s3
    image_url: Mapped[str] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    product: Mapped["Product"] = relationship("Product", back_populates="images")
