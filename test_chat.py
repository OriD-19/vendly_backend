"""
Chat System Test Script
Tests the chat messaging endpoints
"""

import requests
import time
from datetime import datetime


class ChatTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.user_id = None
        self.test_store_id = 1
        
    def login(self, username, password):
        """Login and get access token"""
        print("\n🔐 Logging in...")
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            print(f"✅ Login successful!")
            print(f"   Token: {self.access_token[:20]}...")
            return True
        else:
            print(f"❌ Login failed: {response.json()}")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def send_message(self, content, store_id=None):
        """Send a chat message"""
        store_id = store_id or self.test_store_id
        
        print(f"\n📤 Sending message to store {store_id}...")
        response = requests.post(
            f"{self.base_url}/chat/messages",
            headers=self.get_headers(),
            json={
                "content": content,
                "store_id": store_id,
                "message_type": "text",
                "is_from_customer": True
            }
        )
        
        if response.status_code == 201:
            message = response.json()
            print(f"✅ Message sent!")
            print(f"   ID: {message['id']}")
            print(f"   Content: {message['content']}")
            print(f"   Status: {message['status']}")
            return message
        else:
            print(f"❌ Failed to send message: {response.json()}")
            return None
    
    def get_conversations(self):
        """Get all user conversations"""
        print("\n💬 Getting all conversations...")
        response = requests.get(
            f"{self.base_url}/chat/conversations",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            conversations = response.json()
            print(f"✅ Found {len(conversations)} conversation(s)")
            
            for conv in conversations:
                unread = conv.get('unread_count', 0)
                badge = f" ({unread} unread)" if unread > 0 else ""
                print(f"\n   📍 Store: {conv['store_name']}{badge}")
                print(f"      Last message: {conv.get('last_message', 'N/A')}")
                print(f"      Time: {conv.get('last_message_at', 'N/A')}")
            
            return conversations
        else:
            print(f"❌ Failed to get conversations: {response.json()}")
            return []
    
    def get_conversation_messages(self, store_id=None, limit=10):
        """Get messages from a conversation"""
        store_id = store_id or self.test_store_id
        
        print(f"\n📨 Getting messages from store {store_id}...")
        response = requests.get(
            f"{self.base_url}/chat/conversations/{store_id}/messages",
            headers=self.get_headers(),
            params={"skip": 0, "limit": limit}
        )
        
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ Retrieved {len(messages)} message(s)")
            
            for msg in messages:
                direction = "→" if msg['is_from_customer'] else "←"
                status_icon = "✓✓" if msg['status'] == 'read' else "✓"
                print(f"\n   {direction} [{msg['created_at'][:19]}] {status_icon}")
                print(f"      {msg['content']}")
            
            return messages
        else:
            print(f"❌ Failed to get messages: {response.json()}")
            return []
    
    def mark_conversation_as_read(self, store_id=None):
        """Mark all messages in a conversation as read"""
        store_id = store_id or self.test_store_id
        
        print(f"\n✓ Marking conversation {store_id} as read...")
        response = requests.post(
            f"{self.base_url}/chat/conversations/{store_id}/read",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Marked {result['updated_count']} message(s) as read")
            return result
        else:
            print(f"❌ Failed to mark as read: {response.json()}")
            return None
    
    def get_unread_count(self, store_id=None):
        """Get unread message count"""
        print("\n🔔 Getting unread count...")
        
        params = {}
        if store_id:
            params['store_id'] = store_id
        
        response = requests.get(
            f"{self.base_url}/chat/unread-count",
            headers=self.get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            result = response.json()
            count = result['unread_count']
            print(f"✅ You have {count} unread message(s)")
            return count
        else:
            print(f"❌ Failed to get unread count: {response.json()}")
            return 0
    
    def search_messages(self, query, store_id=None):
        """Search messages"""
        print(f"\n🔍 Searching for: '{query}'...")
        
        params = {"query": query}
        if store_id:
            params['store_id'] = store_id
        
        response = requests.get(
            f"{self.base_url}/chat/search",
            headers=self.get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ Found {len(messages)} message(s)")
            
            for msg in messages:
                print(f"\n   📍 Store ID: {msg['store_id']}")
                print(f"      Content: {msg['content']}")
                print(f"      Date: {msg['created_at'][:19]}")
            
            return messages
        else:
            print(f"❌ Search failed: {response.json()}")
            return []
    
    def delete_message(self, message_id):
        """Delete a message"""
        print(f"\n🗑️  Deleting message {message_id}...")
        response = requests.delete(
            f"{self.base_url}/chat/messages/{message_id}",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            print(f"✅ Message deleted successfully")
            return True
        else:
            print(f"❌ Failed to delete message: {response.json()}")
            return False
    
    def run_full_test(self):
        """Run complete test suite"""
        print("=" * 60)
        print("🧪 CHAT SYSTEM TEST SUITE")
        print("=" * 60)
        
        # Test 1: Send messages
        print("\n📋 Test 1: Send Messages")
        print("-" * 60)
        msg1 = self.send_message("Hello! Is this product available?")
        time.sleep(0.5)
        msg2 = self.send_message("What's the price?")
        time.sleep(0.5)
        msg3 = self.send_message("Can I get a discount?")
        
        if not all([msg1, msg2, msg3]):
            print("\n❌ Message sending test failed!")
            return
        
        # Test 2: Get conversations
        print("\n📋 Test 2: Get Conversations")
        print("-" * 60)
        conversations = self.get_conversations()
        
        # Test 3: Get conversation messages
        print("\n📋 Test 3: Get Conversation Messages")
        print("-" * 60)
        messages = self.get_conversation_messages(limit=10)
        
        # Test 4: Get unread count
        print("\n📋 Test 4: Get Unread Count")
        print("-" * 60)
        unread_count = self.get_unread_count()
        
        # Test 5: Mark as read
        print("\n📋 Test 5: Mark Conversation as Read")
        print("-" * 60)
        self.mark_conversation_as_read()
        
        # Test 6: Verify unread count decreased
        print("\n📋 Test 6: Verify Unread Count")
        print("-" * 60)
        new_unread = self.get_unread_count()
        
        # Test 7: Search messages
        print("\n📋 Test 7: Search Messages")
        print("-" * 60)
        self.search_messages("product")
        
        # Test 8: Delete a message
        if msg1:
            print("\n📋 Test 8: Delete Message")
            print("-" * 60)
            self.delete_message(msg1['id'])
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ TEST SUITE COMPLETED!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   • Messages sent: 3")
        print(f"   • Conversations found: {len(conversations)}")
        print(f"   • Messages retrieved: {len(messages)}")
        print(f"   • Initial unread count: {unread_count}")
        print(f"   • Final unread count: {new_unread}")
        print(f"   • Messages deleted: 1")


def main():
    """Main test function"""
    print("🚀 Chat System Tester")
    print("-" * 60)
    
    # Configuration
    base_url = input("Enter API URL (default: http://localhost:8000): ").strip()
    if not base_url:
        base_url = "http://localhost:8000"
    
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    
    # Initialize tester
    tester = ChatTester(base_url)
    
    # Login
    if not tester.login(username, password):
        print("\n❌ Authentication failed. Exiting...")
        return
    
    # Run tests
    while True:
        print("\n" + "=" * 60)
        print("Chat System Test Menu")
        print("=" * 60)
        print("1. Send a message")
        print("2. View all conversations")
        print("3. View conversation messages")
        print("4. Mark conversation as read")
        print("5. Get unread count")
        print("6. Search messages")
        print("7. Run full test suite")
        print("8. Exit")
        print("-" * 60)
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == "1":
            content = input("Enter message content: ").strip()
            if content:
                tester.send_message(content)
        
        elif choice == "2":
            tester.get_conversations()
        
        elif choice == "3":
            limit = input("Enter message limit (default: 10): ").strip()
            limit = int(limit) if limit else 10
            tester.get_conversation_messages(limit=limit)
        
        elif choice == "4":
            tester.mark_conversation_as_read()
        
        elif choice == "5":
            tester.get_unread_count()
        
        elif choice == "6":
            query = input("Enter search query: ").strip()
            if query:
                tester.search_messages(query)
        
        elif choice == "7":
            tester.run_full_test()
        
        elif choice == "8":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
