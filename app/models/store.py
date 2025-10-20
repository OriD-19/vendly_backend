from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Store(Base):
    __tablename__ = 'stores'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)

    # store information
    phone: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    email: Mapped[Optional[str]] = mapped_column(String(120), default=None)
    store_location: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(50))

    # location images
    # stored in an S3 bucket (ideally, lol), this field contains the URL/path to the image
    profile_image: Mapped[Optional[str]] = mapped_column(String(255), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    products: Mapped[List["Product"]] = relationship("Product", back_populates="store") # type: ignore
    owner: Mapped["User"] = relationship("User", back_populates="stores") # type: ignore
    chat_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="store") # type: ignore
