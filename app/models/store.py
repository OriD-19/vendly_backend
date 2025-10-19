from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from app.database import Base


class Store(Base):
    __tablename__ = 'stores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), nullable=False, unique=True)
    owner_id = Column(Integer, ForeignKey('users.id'),
                      nullable=False, index=True)

    # store information
    phone = Column(String(20), nullable=True)
    email = Column(String(120), nullable=True)
    store_location = Column(String(120), nullable=False)
    type = Column(String(50), nullable=False)

    # location images
    # stored in an S3 bucket (ideally, lol), this field contains the URL/path to the image
    profile_image = Column(String(255), nullable=True)

    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(), nullable=False, onupdate=datetime.now)

    products = relationship("Product", back_populates="store")
    owner = relationship("User", back_populates="stores")
