from enum import Enum
from datetime import datetime
from sqlalchemy import CheckConstraint, Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from app.database import Base


class OrderStatus(str, Enum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELED = 'canceled'


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(50), nullable=False, unique=True)

    customer_id = Column(Integer, ForeignKey(
        'users.id'), nullable=False, index=True)
    customer = relationship(
        "User", back_populates="orders", foreign_keys=[customer_id])

    total_amount = Column(Integer, nullable=False)

    # all products for this order
    products = relationship("OrderProduct", back_populates="order")

    status = Column(SQLEnum(OrderStatus), nullable=False,
                    default=OrderStatus.PENDING)

    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(), nullable=False, onupdate=datetime.now)

    # shipping information
    shipping_address = Column(String(255), nullable=False)
    shipping_city = Column(String(100), nullable=False)
    shipping_postal_code = Column(String(20), nullable=False)
    shipping_country = Column(String(100), nullable=False)
    shipped_at = Column(DateTime(), nullable=True)
    delivered_at = Column(DateTime(), nullable=True)
    canceled_at = Column(DateTime(), nullable=True)

    # __table_args__ = (
    #     # database custom constraint because we like consistency :)
    #     CheckConstraint(
    #         "customer_id IN (SELECT id FROM users WHERE user_type = 'customer')",
    #         name='chk_order_customer_valid'
    #     ),
    # )


class OrderProduct(Base):
    __tablename__ = 'order_products'

    id = Column(Integer, primary_key=True, autoincrement=True)

    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    order = relationship("Order", back_populates="products")

    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product = relationship("Product")

    quantity = Column(Integer, nullable=False)
    unit_price = Column(Integer, nullable=False)  # price at the time of order
