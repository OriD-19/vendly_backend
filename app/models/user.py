from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), nullable=False, unique=True)
    email = Column(String(120), nullable=False, unique=True)
    location = Column(String(120), nullable=True)
    password_hash = Column(String(128), nullable=False)

    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(), nullable=False, onupdate=datetime.now)
    
    # relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    
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
