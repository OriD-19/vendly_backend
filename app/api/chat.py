from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat_message import (
    ChatMessageCreate,
    ChatMessageResponse,
    ConversationSummary,
    MarkAsReadRequest
)
from app.services.chat_service import ChatService
from app.utils.auth_dependencies import get_current_active_user, get_websocket_user
from app.models.user import User
from app.websockets.chat_websocket import manager
import logging

logger = logging.getLogger(__name__)

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


# ========== WebSocket Real-Time Chat ==========

@router.websocket("/ws/{store_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    store_id: int,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for real-time chat.
    
    **Authentication:**
    Pass JWT token as query parameter: `ws://api.example.com/chat/ws/123?token=<your_jwt_token>`
    
    **Connection URL:**
    ```
    ws://localhost:8000/chat/ws/{store_id}?token=<jwt_token>
    ```
    
    **Message Types (Client -> Server):**
    
    1. **Send Message:**
    ```json
    {
        "type": "send_message",
        "data": {
            "content": "Hello, I have a question about this product",
            "message_type": "text",
            "is_from_customer": true,
            "attachment_url": null
        }
    }
    ```
    
    2. **Typing Indicator:**
    ```json
    {
        "type": "typing",
        "data": {
            "is_typing": true
        }
    }
    ```
    
    3. **Mark Messages as Read:**
    ```json
    {
        "type": "mark_read",
        "data": {
            "message_ids": [1, 2, 3]
        }
    }
    ```
    
    **Message Types (Server -> Client):**
    
    1. **New Message:**
    ```json
    {
        "type": "new_message",
        "data": {
            "id": 123,
            "content": "Hello!",
            "sender_id": 456,
            "store_id": 1,
            "created_at": "2025-11-09T10:30:00",
            "message_type": "text",
            "is_from_customer": true,
            "status": "sent",
            "read_at": null
        }
    }
    ```
            "message_type": "text",
            "is_from_customer": true
        }
    }
    ```
    
    2. **Typing Indicator:**
    ```json
    {
        "type": "typing",
        "data": {
            "user_id": 456,
            "store_id": 1,
            "is_typing": true
        }
    }
    ```
    
    3. **User Status:**
    ```json
    {
        "type": "user_status",
        "data": {
            "user_id": 456,
            "is_online": true
        }
    }
    ```
    
    4. **Read Receipt:**
    ```json
    {
        "type": "read_receipt",
        "data": {
            "message_ids": [1, 2, 3],
            "updated_count": 3
        }
    }
    ```
    
    **Error Handling:**
    - Connection closes with code 1008 if authentication fails
    - Connection closes with code 1011 if server error occurs
    """
    current_user: Optional[User] = None
    
    # Authenticate user with a temporary database session
    db_auth = next(get_db())
    try:
        current_user = await get_websocket_user(websocket, token, db_auth)
    except HTTPException:
        logger.warning(f"WebSocket authentication failed for store {store_id}")
        db_auth.close()
        return
    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}", exc_info=True)
        db_auth.close()
        try:
            await websocket.close(code=1011, reason="Authentication error")
        except:
            pass
        return
    finally:
        # Close authentication session
        db_auth.close()
    
    try:
        # Connect to chat
        await manager.connect(websocket, current_user.id, store_id)
        logger.info(f"User {current_user.id} connected to store {store_id} chat")
        
        # Main message loop
        while True:
            try:
                # Receive message from WebSocket
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "send_message":
                    # Use a new database session for each message operation
                    db = next(get_db())
                    try:
                        chat_service = ChatService(db)
                        
                        # Handle new message
                        message_data = data.get("data", {})
                        
                        # Create message in database
                        chat_message = ChatMessageCreate(
                            content=message_data.get("content", ""),
                            store_id=store_id,
                            message_type=message_data.get("message_type", "text"),
                            is_from_customer=message_data.get("is_from_customer", True),
                            attachment_url=message_data.get("attachment_url")
                        )
                        
                        db_message = chat_service.create_message(chat_message, current_user.id)
                        
                        # Broadcast to conversation participants
                        await manager.broadcast_to_conversation(
                            {
                                "type": "new_message",
                                "data": {
                                    "id": db_message.id,
                                    "content": db_message.content,
                                    "sender_id": db_message.sender_id,
                                    "store_id": db_message.store_id,
                                    "created_at": db_message.created_at.isoformat(),
                                    "message_type": db_message.message_type.value,
                                    "is_from_customer": db_message.is_from_customer,
                                    "status": db_message.status.value,
                                    "read_at": db_message.read_at.isoformat() if db_message.read_at else None
                                }
                            },
                            current_user.id,
                            store_id
                        )
                        
                        logger.info(f"Message {db_message.id} sent by user {current_user.id} to store {store_id}")
                    finally:
                        # Always close the database session
                        db.close()
                
                elif message_type == "typing":
                    # Handle typing indicator (no database needed)
                    is_typing = data.get("data", {}).get("is_typing", False)
                    await manager.broadcast_typing_indicator(
                        current_user.id,
                        store_id,
                        is_typing
                    )
                    logger.debug(f"Typing indicator: user {current_user.id}, is_typing={is_typing}")
                
                elif message_type == "mark_read":
                    # Use a new database session for mark read operation
                    db = next(get_db())
                    try:
                        chat_service = ChatService(db)
                        
                        # Handle read receipt
                        message_ids = data.get("data", {}).get("message_ids", [])
                        updated_count = chat_service.mark_as_read(message_ids, current_user.id)
                        
                        # Send confirmation back
                        await manager.send_personal_message(
                            {
                                "type": "read_receipt",
                                "data": {
                                    "message_ids": message_ids,
                                    "updated_count": updated_count
                                }
                            },
                            current_user.id,
                            store_id
                        )
                        logger.info(f"Marked {updated_count} messages as read for user {current_user.id}")
                    finally:
                        # Always close the database session
                        db.close()
                
                else:
                    # Unknown message type
                    logger.warning(f"Unknown message type: {message_type}")
                    await manager.send_personal_message(
                        {
                            "type": "error",
                            "data": {
                                "message": f"Unknown message type: {message_type}"
                            }
                        },
                        current_user.id,
                        store_id
                    )
            
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "data": {
                            "message": f"Error processing message: {str(e)}"
                        }
                    },
                    current_user.id,
                    store_id
                )
    
    except WebSocketDisconnect:
        manager.disconnect(current_user.id, store_id)
        await manager.broadcast_user_status(current_user.id, store_id, is_online=False)
        logger.info(f"User {current_user.id} disconnected from store {store_id} chat")
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        manager.disconnect(current_user.id, store_id)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
