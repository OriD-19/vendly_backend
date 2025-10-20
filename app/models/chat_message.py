from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Text, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.store import Store


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"  # For automated messages (order updates, etc.)


class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Foreign Keys
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    
    # Message Content
    message_type: Mapped[MessageType] = mapped_column(SQLEnum(MessageType), default=MessageType.TEXT)
    content: Mapped[str] = mapped_column(Text)
    attachment_url: Mapped[str | None] = mapped_column(String(500), default=None)
    
    # Message Metadata
    status: Mapped[MessageStatus] = mapped_column(SQLEnum(MessageStatus), default=MessageStatus.SENT)
    is_from_customer: Mapped[bool] = mapped_column(Boolean, default=True)  # True = customer, False = store
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    
    # Soft Delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    
    # Relationships
    sender: Mapped["User"] = relationship("User", back_populates="chat_messages")
    store: Mapped["Store"] = relationship("Store", back_populates="chat_messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, sender_id={self.sender_id}, store_id={self.store_id})>"
