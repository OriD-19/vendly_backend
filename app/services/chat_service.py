from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status
from app.models.chat_message import ChatMessage, MessageStatus, MessageType
from app.models.store import Store
from app.models.user import User
from app.schemas.chat_message import ChatMessageCreate, ChatMessageUpdate


class ChatService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ========== Create Message ==========
    
    def create_message(self, message_data: ChatMessageCreate, sender_id: int) -> ChatMessage:
        """
        Create a new chat message.
        Validates that the store exists before creating.
        """
        # Verify store exists
        store = self.db.query(Store).filter(Store.id == message_data.store_id).first()
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store with id {message_data.store_id} not found"
            )
        
        # Verify sender exists
        sender = self.db.query(User).filter(User.id == sender_id).first()
        if not sender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sender not found"
            )
        
        message = ChatMessage(
            sender_id=sender_id,
            store_id=message_data.store_id,
            content=message_data.content,
            message_type=message_data.message_type,
            attachment_url=message_data.attachment_url,
            is_from_customer=message_data.is_from_customer,
            status=MessageStatus.SENT
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    # ========== Get Single Message ==========
    
    def get_message_by_id(self, message_id: int) -> ChatMessage:
        """
        Get a single message by ID.
        Raises HTTPException if not found.
        """
        message = self.db.query(ChatMessage).filter(
            ChatMessage.id == message_id
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with id {message_id} not found"
            )
        
        return message
    
    # ========== Get Conversation History ==========
    
    def get_conversation(
        self,
        user_id: int,
        store_id: int,
        skip: int = 0,
        limit: int = 50,
        include_deleted: bool = False
    ) -> List[ChatMessage]:
        """
        Get conversation history between a user and a store.
        Returns messages in chronological order (oldest first).
        """
        query = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.sender_id == user_id,
                ChatMessage.store_id == store_id
            )
        )
        
        if not include_deleted:
            query = query.filter(ChatMessage.is_deleted == False)
        
        # Get messages in reverse order, then reverse the list
        messages = (
            query
            .order_by(desc(ChatMessage.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Return in chronological order (oldest first)
        return list(reversed(messages))
    
    # ========== Get Store Conversations ==========
    
    def get_store_conversations(
        self,
        store_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get all conversations for a specific store.
        Returns a list of users who have messaged the store with conversation metadata.
        """
        # Subquery to get the latest message for each user
        subquery = (
            self.db.query(
                ChatMessage.sender_id,
                func.max(ChatMessage.created_at).label('last_message_at')
            )
            .filter(
                and_(
                    ChatMessage.store_id == store_id,
                    ChatMessage.is_deleted == False
                )
            )
            .group_by(ChatMessage.sender_id)
            .subquery()
        )
        
        # Get conversation details
        conversations = (
            self.db.query(
                User.id.label('user_id'),
                User.username.label('username'),
                ChatMessage.content.label('last_message'),
                ChatMessage.created_at.label('last_message_at'),
                func.count(ChatMessage.id).filter(
                    and_(
                        ChatMessage.status != MessageStatus.READ,
                        ChatMessage.is_from_customer == True
                    )
                ).label('unread_count')
            )
            .join(User, ChatMessage.sender_id == User.id)
            .join(
                subquery,
                and_(
                    ChatMessage.sender_id == subquery.c.sender_id,
                    ChatMessage.created_at == subquery.c.last_message_at
                )
            )
            .filter(
                and_(
                    ChatMessage.store_id == store_id,
                    ChatMessage.is_deleted == False
                )
            )
            .group_by(
                User.id,
                User.username,
                ChatMessage.content,
                ChatMessage.created_at
            )
            .order_by(desc('last_message_at'))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [
            {
                'user_id': conv.user_id,
                'username': conv.username,
                'last_message': conv.last_message,
                'last_message_at': conv.last_message_at,
                'unread_count': conv.unread_count or 0
            }
            for conv in conversations
        ]
    
    # ========== Get All Conversations for User ==========
    
    def get_user_conversations(self, user_id: int) -> List[Dict]:
        """
        Get all conversations for a user with unread counts.
        Returns list of stores the user has messaged.
        """
        # Subquery to get the latest message for each store
        subquery = (
            self.db.query(
                ChatMessage.store_id,
                func.max(ChatMessage.created_at).label('last_message_at')
            )
            .filter(
                and_(
                    ChatMessage.sender_id == user_id,
                    ChatMessage.is_deleted == False
                )
            )
            .group_by(ChatMessage.store_id)
            .subquery()
        )
        
        conversations = (
            self.db.query(
                Store.id.label('store_id'),
                Store.name.label('store_name'),
                ChatMessage.content.label('last_message'),
                ChatMessage.created_at.label('last_message_at'),
                func.count(ChatMessage.id).filter(
                    and_(
                        ChatMessage.status != MessageStatus.READ,
                        ChatMessage.is_from_customer == False
                    )
                ).label('unread_count')
            )
            .join(Store, ChatMessage.store_id == Store.id)
            .join(
                subquery,
                and_(
                    ChatMessage.store_id == subquery.c.store_id,
                    ChatMessage.created_at == subquery.c.last_message_at
                )
            )
            .filter(
                and_(
                    ChatMessage.sender_id == user_id,
                    ChatMessage.is_deleted == False
                )
            )
            .group_by(
                Store.id,
                Store.name,
                ChatMessage.content,
                ChatMessage.created_at
            )
            .order_by(desc('last_message_at'))
            .all()
        )
        
        return [
            {
                'store_id': conv.store_id,
                'store_name': conv.store_name,
                'last_message': conv.last_message,
                'last_message_at': conv.last_message_at,
                'unread_count': conv.unread_count or 0
            }
            for conv in conversations
        ]
    
    # ========== Mark Messages as Read ==========
    
    def mark_as_read(self, message_ids: List[int], user_id: int) -> int:
        """
        Mark messages as read.
        Returns count of updated messages.
        """
        if not message_ids:
            return 0
        
        updated = (
            self.db.query(ChatMessage)
            .filter(
                and_(
                    ChatMessage.id.in_(message_ids),
                    ChatMessage.sender_id == user_id,
                    ChatMessage.status != MessageStatus.READ
                )
            )
            .update(
                {
                    "status": MessageStatus.READ,
                    "read_at": datetime.utcnow()
                },
                synchronize_session=False
            )
        )
        
        self.db.commit()
        return updated
    
    def mark_conversation_as_read(self, user_id: int, store_id: int) -> int:
        """
        Mark all messages in a conversation as read.
        Returns count of updated messages.
        """
        updated = (
            self.db.query(ChatMessage)
            .filter(
                and_(
                    ChatMessage.sender_id == user_id,
                    ChatMessage.store_id == store_id,
                    ChatMessage.status != MessageStatus.READ,
                    ChatMessage.is_deleted == False
                )
            )
            .update(
                {
                    "status": MessageStatus.READ,
                    "read_at": datetime.utcnow()
                },
                synchronize_session=False
            )
        )
        
        self.db.commit()
        return updated
    
    # ========== Get Unread Count ==========
    
    def get_unread_count(self, user_id: int, store_id: Optional[int] = None) -> int:
        """
        Get unread message count for a user.
        If store_id is provided, returns count for that specific conversation.
        """
        query = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.sender_id == user_id,
                ChatMessage.status != MessageStatus.READ,
                ChatMessage.is_deleted == False
            )
        )
        
        if store_id:
            query = query.filter(ChatMessage.store_id == store_id)
        
        return query.count()
    
    def get_store_unread_count(self, store_id: int) -> int:
        """
        Get unread message count for a store (messages from customers).
        """
        count = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.store_id == store_id,
                ChatMessage.is_from_customer == True,
                ChatMessage.status != MessageStatus.READ,
                ChatMessage.is_deleted == False
            )
        ).count()
        
        return count
    
    # ========== Delete Message (Soft Delete) ==========
    
    def delete_message(self, message_id: int, user_id: int) -> ChatMessage:
        """
        Soft delete a message.
        Only the sender can delete their own messages.
        """
        message = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.sender_id == user_id
            )
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or you don't have permission to delete it"
            )
        
        message.is_deleted = True
        message.deleted_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    # ========== Search Messages ==========
    
    def search_messages(
        self,
        user_id: int,
        search_term: str,
        store_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[ChatMessage]:
        """
        Search messages by content.
        """
        search_pattern = f"%{search_term}%"
        
        query = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.sender_id == user_id,
                ChatMessage.content.ilike(search_pattern),
                ChatMessage.is_deleted == False
            )
        )
        
        if store_id:
            query = query.filter(ChatMessage.store_id == store_id)
        
        messages = (
            query
            .order_by(desc(ChatMessage.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return messages
    
    # ========== System Messages ==========
    
    def create_system_message(
        self,
        user_id: int,
        store_id: int,
        content: str
    ) -> ChatMessage:
        """
        Create an automated system message (e.g., order updates).
        """
        message = ChatMessage(
            sender_id=user_id,
            store_id=store_id,
            content=content,
            message_type=MessageType.SYSTEM,
            is_from_customer=False,
            status=MessageStatus.DELIVERED
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
