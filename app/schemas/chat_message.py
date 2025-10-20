from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


# Base Schema
class ChatMessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: MessageType = MessageType.TEXT
    attachment_url: Optional[str] = Field(None, max_length=500)


# Create Schema
class ChatMessageCreate(ChatMessageBase):
    store_id: int
    is_from_customer: bool = True


# Update Schema (for marking as read)
class ChatMessageUpdate(BaseModel):
    status: Optional[MessageStatus] = None
    read_at: Optional[datetime] = None


# Response Schema
class ChatMessageResponse(ChatMessageBase):
    id: int
    sender_id: int
    store_id: int
    status: MessageStatus
    is_from_customer: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    is_deleted: bool
    
    model_config = ConfigDict(from_attributes=True)


# Conversation Summary
class ConversationSummary(BaseModel):
    store_id: int
    store_name: str
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# Mark as Read Request
class MarkAsReadRequest(BaseModel):
    message_ids: List[int]


# WebSocket Message Schema
class WebSocketMessage(BaseModel):
    type: str  # "message", "typing", "read_receipt"
    data: dict
