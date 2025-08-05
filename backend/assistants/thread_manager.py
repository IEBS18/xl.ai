import os
import logging
from typing import Dict, Any, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class ThreadManager:
    """
    Manages OpenAI Threads for conversation continuity.
    Maps session_id -> thread_id for seamless integration.
    """
    
    def __init__(self):
        self.client = self._setup_azure_client()
        self.thread_cache = {}  # session_id -> thread_id mapping
    
    def _setup_azure_client(self) -> AzureOpenAI:
        """Setup Azure OpenAI client"""
        return AzureOpenAI(
            api_key=os.getenv("AZUREAPI"),
            api_version=os.getenv("AZUREVERSION", "2024-05-01-preview"),
            azure_endpoint=os.getenv("AZUREENDPOINT")
        )
    
    def create_or_get_thread(self, session_id: str) -> str:
        """
        Create or retrieve thread for session.
        Returns thread_id which equals session_id in your system.
        """
        try:
            # Check if we already have a thread for this session
            if session_id in self.thread_cache:
                thread_id = self.thread_cache[session_id]
                # Verify thread still exists
                if self._verify_thread_exists(thread_id):
                    return thread_id
                else:
                    # Thread was deleted, remove from cache
                    del self.thread_cache[session_id]
            
            # Create new thread
            thread = self.client.beta.threads.create(
                metadata={
                    "session_id": session_id,
                    "created_at": import_datetime().now().isoformat()
                }
            )
            
            thread_id = thread.id
            self.thread_cache[session_id] = thread_id
            
            logging.info(f"✅ Created thread {thread_id} for session {session_id}")
            return thread_id
            
        except Exception as e:
            logging.error(f"❌ Error creating thread for session {session_id}: {e}")
            raise
    
    def _verify_thread_exists(self, thread_id: str) -> bool:
        """Verify that a thread still exists"""
        try:
            self.client.beta.threads.retrieve(thread_id)
            return True
        except Exception:
            return False
    
    def add_message_to_thread(self, thread_id: str, role: str, content: str, 
                             file_ids: Optional[list] = None) -> str:
        """Add a message to the thread"""
        try:
            message_data = {
                "thread_id": thread_id,
                "role": role,
                "content": content
            }
            
            if file_ids:
                message_data["attachments"] = [
                    {"file_id": file_id, "tools": [{"type": "code_interpreter"}]}
                    for file_id in file_ids
                ]
            
            message = self.client.beta.threads.messages.create(**message_data)
            return message.id
            
        except Exception as e:
            logging.error(f"❌ Error adding message to thread {thread_id}: {e}")
            raise
    
    def get_thread_messages(self, thread_id: str, limit: int = 20) -> list:
        """Get messages from thread"""
        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=limit
            )
            return messages.data
        except Exception as e:
            logging.error(f"❌ Error getting messages from thread {thread_id}: {e}")
            return []
    
    def clear_thread(self, thread_id: str) -> bool:
        """Clear all messages from a thread (if supported) or delete and recreate"""
        try:
            # OpenAI doesn't support clearing messages, so we delete the thread
            # The calling code should create a new thread as needed
            self.client.beta.threads.delete(thread_id)
            
            # Remove from cache
            session_id = None
            for sid, tid in self.thread_cache.items():
                if tid == thread_id:
                    session_id = sid
                    break
            
            if session_id:
                del self.thread_cache[session_id]
            
            logging.info(f"🗑️ Deleted thread: {thread_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error clearing thread {thread_id}: {e}")
            return False
    
    def get_thread_for_session(self, session_id: str) -> Optional[str]:
        """Get thread ID for a session"""
        return self.thread_cache.get(session_id)
    
    def cleanup_session_thread(self, session_id: str) -> bool:
        """Clean up thread for a specific session"""
        thread_id = self.thread_cache.get(session_id)
        if thread_id:
            return self.clear_thread(thread_id)
        return True

def import_datetime():
    """Import datetime to avoid issues"""
    from datetime import datetime
    return datetime