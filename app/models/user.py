from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.chat_message import ChatMessage
    from app.models.order import Order
    from app.models.store import Store
    from app.models.review import Review


class UserType(str, Enum):
    CUSTOMER = 'customer'
    STORE = 'store'


class PaymentMethod(str, Enum):
    CREDIT_CARD = 'credit_card'
    PAYPAL = 'paypal'
    BANK_TRANSFER = 'bank_transfer'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    # differentiate between customer and store owner
    user_type: Mapped[UserType] = mapped_column(
        SQLEnum(UserType), default=UserType.CUSTOMER
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # relationships
    preferences: Mapped[Optional["UserPreferences"]] = relationship(
        "UserPreferences", back_populates="user", uselist=False)
    chat_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="sender") #type: ignore
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer") #type: ignore
    store: Mapped[Optional["Store"]] = relationship("Store", back_populates="owner", foreign_keys="Store.owner_id") #type: ignore
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="customer") #type: ignore

    __mapper_args__ = {
        'polymorphic_on': user_type,
        'polymorphic_identity': UserType.CUSTOMER,
    }


class Customer(User):
    __mapper_args__ = {
        'polymorphic_identity': UserType.CUSTOMER,
    }

    phone: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    preferred_payment_method: Mapped[Optional[PaymentMethod]] = mapped_column(
        SQLEnum(PaymentMethod), default=None
    )


class StoreOwner(User):
    __mapper_args__ = {
        'polymorphic_identity': UserType.STORE,
    }

    store_id: Mapped[Optional[int]] = mapped_column(ForeignKey('stores.id'), default=None)
    # expressed as a percentage
    commission_rate: Mapped[int] = mapped_column(default=5)
    
    # Add a relationship to the store
    owned_store: Mapped[Optional["Store"]] = relationship("Store", back_populates="owner", foreign_keys=[store_id])


class UserPreferences(Base):
    __tablename__ = 'user_preferences'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True)

    # preference fields
    theme: Mapped[str] = mapped_column(String(50), default='light')
    notifications_enabled: Mapped[bool] = mapped_column(default=True)
    email_alerts: Mapped[bool] = mapped_column(default=True)
    timezone: Mapped[str] = mapped_column(String(50), default='UTC')
    language: Mapped[str] = mapped_column(String(50), default='en')
    currency: Mapped[str] = mapped_column(String(10), default='USD')

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    user: Mapped["User"] = relationship("User", back_populates="preferences")
