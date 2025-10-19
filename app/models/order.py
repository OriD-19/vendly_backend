from enum import Enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class OrderStatus(str, Enum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELED = 'canceled'


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True)

    customer_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    customer: Mapped["User"] = relationship( # type: ignore
        "User", back_populates="orders", foreign_keys=[customer_id]
    )

    total_amount: Mapped[int] = mapped_column()

    # all products for this order
    products: Mapped[List["OrderProduct"]] = relationship("OrderProduct", back_populates="order")

    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # shipping information
    shipping_address: Mapped[str] = mapped_column(String(255))
    shipping_city: Mapped[str] = mapped_column(String(100))
    shipping_postal_code: Mapped[str] = mapped_column(String(20))
    shipping_country: Mapped[str] = mapped_column(String(100))
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)

    # __table_args__ = (
    #     # database custom constraint because we like consistency :)
    #     CheckConstraint(
    #         "customer_id IN (SELECT id FROM users WHERE user_type = 'customer')",
    #         name='chk_order_customer_valid'
    #     ),
    # )


class OrderProduct(Base):
    __tablename__ = 'order_products'

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'))
    order: Mapped["Order"] = relationship("Order", back_populates="products")

    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    product: Mapped["Product"] = relationship("Product") # type: ignore

    quantity: Mapped[int] = mapped_column()
    unit_price: Mapped[int] = mapped_column()  # price at the time of order
