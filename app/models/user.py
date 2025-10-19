from datetime import datetime
from enum import Enum
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserType(str, Enum):
    CUSTOMER = 'customer'
    STORE = 'store'


class PaymentMethod(str, Enum):
    CREDIT_CARD = 'credit_card'
    PAYPAL = 'paypal'
    BANK_TRANSFER = 'bank_transfer'


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), nullable=False, unique=True)
    email = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String(128), nullable=False)

    # differentiate between customer and store owner
    user_type = Column(SQLEnum(UserType), nullable=False,
                       default=UserType.CUSTOMER)

    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(), nullable=False, onupdate=datetime.now)

    # relationships
    preferences = relationship(
        "UserPreferences", back_populates="user", uselist=False)

    __mapper_args__ = {
        'polymorphic_on': user_type,
        'polymorphic_identity': UserType.CUSTOMER,
    }


class Customer(User):
    __mapper_args__ = {
        'polymorphic_identity': UserType.CUSTOMER,
    }

    phone = Column(String(20), nullable=True)
    preferred_payment_method = Column(SQLEnum(PaymentMethod), nullable=True)


class StoreOwner(User):
    __mapper_args__ = {
        'polymorphic_identity': UserType.STORE,
    }

    store_id = Column(Integer, ForeignKey('stores.id'), nullable=True)
    store = relationship("Store", back_populates="owner")
    # expressed as a percentage
    commission_rate = Column(Integer, nullable=False, default=5)


class UserPreferences(Base):
    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True)

    # preference fields
    theme = Column(String(50), nullable=False, default='light')
    notifications_enabled = Column(Boolean, nullable=False, default=True)
    email_alerts = Column(Boolean, nullable=False, default=True)
    timezone = Column(String(50), nullable=False, default='UTC')
    language = Column(String(50), nullable=False, default='en')
    currency = Column(String(10), nullable=False, default='USD')

    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(), nullable=False, onupdate=datetime.now)

    user = relationship("User", back_populates="preferences")
