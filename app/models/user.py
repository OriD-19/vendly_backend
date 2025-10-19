from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


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
    password_hash: Mapped[str] = mapped_column(String(128))

    # differentiate between customer and store owner
    user_type: Mapped[UserType] = mapped_column(
        SQLEnum(UserType), default=UserType.CUSTOMER
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # relationships
    preferences: Mapped[Optional["UserPreferences"]] = relationship(
        "UserPreferences", back_populates="user", uselist=False)

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
    store: Mapped[Optional["Store"]] = relationship("Store", back_populates="owner") # type: ignore
    # expressed as a percentage
    commission_rate: Mapped[int] = mapped_column(default=5)


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
