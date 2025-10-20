# WebSocket Chat Implementation
# This module will handle real-time chat messaging using WebSockets

from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.chat_service import ChatService
from app.models.user import User
import json


class ConnectionManager:
    """
    Manages WebSocket connections for real-time chat.
    
    Features:
    - User connection tracking
    - Message broadcasting
    - Typing indicators
    - Online status
    """
    
    def __init__(self):
        # Store active connections: {user_id: {store_id: WebSocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # Track online users
        self.online_users: Set[int] = set()
    
    async def connect(self, websocket: WebSocket, user_id: int, store_id: int):
        """Accept WebSocket connection and track user."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        self.active_connections[user_id][store_id] = websocket
        self.online_users.add(user_id)
        
        # Notify others that user is online
        await self.broadcast_user_status(user_id, store_id, is_online=True)
    
    def disconnect(self, user_id: int, store_id: int):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            if store_id in self.active_connections[user_id]:
                del self.active_connections[user_id][store_id]
            
            # If user has no more active connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                self.online_users.discard(user_id)
    
    async def send_personal_message(self, message: dict, user_id: int, store_id: int):
        """Send message to a specific user's WebSocket."""
        if user_id in self.active_connections:
            if store_id in self.active_connections[user_id]:
                websocket = self.active_connections[user_id][store_id]
                await websocket.send_json(message)
    
    async def broadcast_to_conversation(
        self,
        message: dict,
        user_id: int,
        store_id: int,
        exclude_sender: bool = False
    ):
        """
        Broadcast message to all participants in a conversation.
        """
        # Send to customer
        if not exclude_sender or message.get('sender_id') != user_id:
            await self.send_personal_message(message, user_id, store_id)
        
        # TODO: Send to store owner(s)
        # This requires store owner lookup logic
    
    async def broadcast_typing_indicator(
        self,
        user_id: int,
        store_id: int,
        is_typing: bool
    ):
        """Broadcast typing indicator to conversation participants."""
        message = {
            "type": "typing",
            "data": {
                "user_id": user_id,
                "store_id": store_id,
                "is_typing": is_typing
            }
        }
        await self.broadcast_to_conversation(message, user_id, store_id, exclude_sender=True)
    
    async def broadcast_user_status(
        self,
        user_id: int,
        store_id: int,
        is_online: bool
    ):
        """Broadcast user online/offline status."""
        message = {
            "type": "user_status",
            "data": {
                "user_id": user_id,
                "is_online": is_online
            }
        }
        await self.broadcast_to_conversation(message, user_id, store_id, exclude_sender=True)
    
    def is_user_online(self, user_id: int) -> bool:
        """Check if user is currently online."""
        return user_id in self.online_users


# Global connection manager instance
manager = ConnectionManager()


# WebSocket endpoint (to be added to router)
async def websocket_endpoint(
    websocket: WebSocket,
    store_id: int,
    current_user: User,  # TODO: Add WebSocket authentication
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat.
    
    Usage:
        ws://localhost:8000/chat/ws/{store_id}
    
    Message Types:
        - send_message: Send a new message
        - typing: Send typing indicator
        - mark_read: Mark messages as read
    """
    await manager.connect(websocket, current_user.id, store_id)
    chat_service = ChatService(db)
    
    try:
        while True:
            # Receive message from WebSocket
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "send_message":
                # Handle new message
                message_data = data.get("data", {})
                
                # Create message in database
                from app.schemas.chat_message import ChatMessageCreate
                chat_message = ChatMessageCreate(
                    content=message_data["content"],
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
                            "is_from_customer": db_message.is_from_customer
                        }
                    },
                    current_user.id,
                    store_id
                )
            
            elif message_type == "typing":
                # Handle typing indicator
                is_typing = data.get("data", {}).get("is_typing", False)
                await manager.broadcast_typing_indicator(
                    current_user.id,
                    store_id,
                    is_typing
                )
            
            elif message_type == "mark_read":
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
    
    except WebSocketDisconnect:
        manager.disconnect(current_user.id, store_id)
        await manager.broadcast_user_status(current_user.id, store_id, is_online=False)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(current_user.id, store_id)


# TODO: Add to router in app/api/chat.py:
# @router.websocket("/ws/{store_id}")
# async def websocket_chat_endpoint(
#     websocket: WebSocket,
#     store_id: int,
#     db: Session = Depends(get_db)
# ):
#     # TODO: Implement WebSocket authentication
#     # For now, you need to pass token and validate user
#     await websocket_endpoint(websocket, store_id, current_user, db)
