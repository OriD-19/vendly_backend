from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.database import Base


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # product details
    name = Column(String(80), nullable=False)
    short_description = Column(String(255), nullable=True)
    long_description = Column(String(1000), nullable=True)

    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # specifications as JSON object
    # in the frontend, this should be a dynamic form allowing key-value pairs
    # specifications = Column(JSONB, nullable=True)

    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(), nullable=False, onupdate=datetime.now)

    # store relationship
    store_id = Column(Integer, ForeignKey('stores.id'), nullable=False)
    store = relationship("Store", back_populates="products")

    # category relationship
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    category = relationship("Category", back_populates="products")

    # tags relationship
    tags = relationship("Tag", secondary="product_tags",
                        back_populates="products")

    # images
    images = relationship("ProductImage", back_populates="product")

    # get all orders containing this product
    orders = relationship("OrderProduct", back_populates="product")


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)

    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(), nullable=False, onupdate=datetime.now)

    products = relationship(
        "Product", secondary="product_tags", back_populates="tags")


class ProductTag(Base):
    __tablename__ = 'product_tags'

    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)


class ProductImage(Base):
    __tablename__ = 'product_images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    # url to the image stored in s3
    image_url = Column(String(255), nullable=False)

    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(), nullable=False, onupdate=datetime.now)

    product = relationship("Product", back_populates="images")
