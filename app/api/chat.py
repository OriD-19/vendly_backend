from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat_message import (
    ChatMessageCreate,
    ChatMessageResponse,
    ConversationSummary,
    MarkAsReadRequest
)
from app.services.chat_service import ChatService
from app.utils.auth_dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])


# ========== Send Message ==========

@router.post("/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send a new chat message to a store.
    """
    chat_service = ChatService(db)
    message = chat_service.create_message(message_data, current_user.id)
    return message


# ========== Get Conversation ==========

@router.get("/conversations/{store_id}/messages", response_model=List[ChatMessageResponse])
def get_conversation(
    store_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get conversation history between current user and a specific store.
    Returns messages in chronological order (oldest first).
    """
    chat_service = ChatService(db)
    messages = chat_service.get_conversation(
        user_id=current_user.id,
        store_id=store_id,
        skip=skip,
        limit=limit
    )
    return messages


# ========== Get All User Conversations ==========

@router.get("/conversations", response_model=List[dict])
def get_user_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all conversations for the current user.
    Returns list of stores with last message and unread count.
    """
    chat_service = ChatService(db)
    conversations = chat_service.get_user_conversations(current_user.id)
    return conversations


# ========== Get Store Conversations (for store owners) ==========

@router.get("/stores/{store_id}/conversations", response_model=List[dict])
def get_store_conversations(
    store_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all conversations for a specific store (for store owners).
    Returns list of customers who have messaged the store.
    """
    # TODO: Add authorization check to ensure user owns the store
    chat_service = ChatService(db)
    conversations = chat_service.get_store_conversations(
        store_id=store_id,
        skip=skip,
        limit=limit
    )
    return conversations


# ========== Mark Messages as Read ==========

@router.post("/messages/read")
def mark_messages_as_read(
    request: MarkAsReadRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mark specific messages as read.
    """
    chat_service = ChatService(db)
    updated_count = chat_service.mark_as_read(request.message_ids, current_user.id)
    return {
        "message": f"{updated_count} messages marked as read",
        "updated_count": updated_count
    }


@router.post("/conversations/{store_id}/read")
def mark_conversation_as_read(
    store_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mark all messages in a conversation as read.
    """
    chat_service = ChatService(db)
    updated_count = chat_service.mark_conversation_as_read(current_user.id, store_id)
    return {
        "message": f"Conversation marked as read",
        "updated_count": updated_count
    }


# ========== Get Unread Count ==========

@router.get("/unread-count")
def get_unread_count(
    store_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get unread message count for the current user.
    If store_id is provided, returns count for that specific conversation.
    """
    chat_service = ChatService(db)
    count = chat_service.get_unread_count(current_user.id, store_id)
    return {
        "unread_count": count,
        "store_id": store_id
    }


@router.get("/stores/{store_id}/unread-count")
def get_store_unread_count(
    store_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get unread message count for a store (messages from customers).
    """
    # TODO: Add authorization check to ensure user owns the store
    chat_service = ChatService(db)
    count = chat_service.get_store_unread_count(store_id)
    return {
        "unread_count": count,
        "store_id": store_id
    }


# ========== Delete Message ==========

@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a message (soft delete).
    Only the sender can delete their own messages.
    """
    chat_service = ChatService(db)
    message = chat_service.delete_message(message_id, current_user.id)
    return {
        "message": "Message deleted successfully",
        "message_id": message.id
    }


# ========== Search Messages ==========

@router.get("/search", response_model=List[ChatMessageResponse])
def search_messages(
    query: str = Query(..., min_length=1),
    store_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search messages by content.
    """
    chat_service = ChatService(db)
    messages = chat_service.search_messages(
        user_id=current_user.id,
        search_term=query,
        store_id=store_id,
        skip=skip,
        limit=limit
    )
    return messages


# ========== Get Single Message ==========

@router.get("/messages/{message_id}", response_model=ChatMessageResponse)
def get_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a single message by ID.
    """
    chat_service = ChatService(db)
    message = chat_service.get_message_by_id(message_id)
    
    # Ensure user has access to this message
    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this message"
        )
    
    return message
