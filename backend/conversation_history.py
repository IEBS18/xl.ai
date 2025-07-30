# conversation_history.py
"""
Enhanced conversation history management with LangChain integration
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# LangChain imports - optional, will handle gracefully if not available
try:
    from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory, ConversationBufferMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain_community.chat_models import AzureChatOpenAI
    from langchain_community.chat_message_histories import ChatMessageHistory
    from langchain.callbacks.base import BaseCallbackHandler
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️ LangChain not available. Install with: pip install langchain langchain-openai")


class LangChainChatHistory(ChatMessageHistory):
    """LangChain-compatible chat message history that works with existing ConversationHistory"""
    
    def __init__(self, conversation_history_instance=None):
        super().__init__()  # Initialize parent ChatMessageHistory
        self.conv_history = conversation_history_instance
        self.messages: List[BaseMessage] = []
        
        # Load from existing conversation history if provided
        if self.conv_history:
            self._load_from_existing()
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the store"""
        self.messages.append(message)
        # Also add to existing conversation history format if available
        if self.conv_history:
            self._sync_to_existing(message)
    
    def clear(self) -> None:
        """Clear all messages"""
        self.messages = []
    
    def _load_from_existing(self):
        """Load existing conversation history into LangChain format"""
        try:
            if not hasattr(self.conv_history, 'history'):
                return
                
            for conv in self.conv_history.history:
                # Convert existing format to LangChain messages
                user_query = conv.get('user_query', '')
                if user_query:
                    user_msg = HumanMessage(content=user_query)
                    user_msg.timestamp = conv.get('timestamp', datetime.now().isoformat())
                    self.messages.append(user_msg)
                    
                    # Create AI response based on existing data
                    ai_content = self._create_ai_response_from_existing(conv)
                    ai_msg = AIMessage(content=ai_content)
                    ai_msg.timestamp = conv.get('timestamp', datetime.now().isoformat())
                    self.messages.append(ai_msg)
        except Exception as e:
            print(f"Warning: Could not load existing history into LangChain: {e}")
    
    def _sync_to_existing(self, message: BaseMessage):
        """Sync LangChain message to existing conversation history format"""
        try:
            if isinstance(message, HumanMessage):
                # This will be handled when the full conversation is added
                pass
            elif isinstance(message, AIMessage):
                # This will be handled when the full conversation is added
                pass
        except Exception as e:
            print(f"Warning: Could not sync to existing format: {e}")
    
    def _create_ai_response_from_existing(self, conv_data: dict) -> str:
        """Create AI response summary from existing conversation data"""
        response_parts = []
        
        if conv_data.get('success'):
            response_parts.append(f"Successfully completed {conv_data.get('response_type', 'analysis')}")
            
            if conv_data.get('dataframes_count', 0) > 0:
                response_parts.append(f"Generated {conv_data['dataframes_count']} DataFrames")
            
            if conv_data.get('generated_images'):
                response_parts.append(f"Created {len(conv_data['generated_images'])} visualizations")
        else:
            error_msg = conv_data.get('error', 'Unknown error')
            response_parts.append(f"Analysis failed: {error_msg}")
        
        return ". ".join(response_parts) if response_parts else "Analysis completed"


class ConversationHistory:
    """Enhanced conversation history with LangChain integration"""
    
    def __init__(self, session_id: str, output_dir: Path):
        self.session_id = session_id
        self.output_dir = output_dir
        self.history_file = output_dir / f"conversation_history_{session_id}.json"
        self.history = []
        
        # Initialize LangChain components
        self._init_langchain_components()
        
        # Load existing history
        self.load_history()
    
    def _init_langchain_components(self):
        """Initialize LangChain components"""
        if not LANGCHAIN_AVAILABLE:
            self.langchain_enabled = False
            return
            
        try:
            # Create LangChain-compatible chat history
            self.langchain_history = LangChainChatHistory(self)  # Pass self as conversation_history_instance
            
            # Initialize Azure OpenAI for LangChain (if credentials available)
            azure_endpoint = os.getenv('AZUREENDPOINT')
            azure_key = os.getenv('AZUREAPI')
            azure_version = os.getenv('AZUREVERSION')
            
            if azure_endpoint and azure_key and azure_version:
                self.llm = AzureChatOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=azure_key,
                    api_version=azure_version,
                    deployment_name=os.getenv('AZURE_DEPLOYMENT_NAME', 'gpt-4'),
                    temperature=0.1
                )
                
                # Initialize memory strategies
                self.buffer_memory = ConversationBufferWindowMemory(
                    chat_memory=self.langchain_history,
                    k=10,  # Keep last 10 exchanges
                    return_messages=True
                )
                
                self.summary_memory = ConversationSummaryBufferMemory(
                    llm=self.llm,
                    chat_memory=self.langchain_history,
                    max_token_limit=2000,
                    return_messages=True
                )
                
                # Use summary memory for better context management
                self.active_memory = self.summary_memory
                self.langchain_enabled = True
                print("✅ LangChain conversation history initialized")
                
            else:
                self.langchain_enabled = False
                print("⚠️ LangChain disabled - Azure OpenAI credentials not found")
                
        except Exception as e:
            self.langchain_enabled = False
            print(f"⚠️ LangChain initialization failed: {e}")
    
    def load_history(self):
        """Load conversation history from file if it exists"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                print(f"📜 Loaded {len(self.history)} previous conversations")
                
                # Reload LangChain history if enabled
                if self.langchain_enabled and hasattr(self, 'langchain_history'):
                    self.langchain_history._load_from_existing()
                    
        except Exception as e:
            print(f"⚠️ Could not load conversation history: {e}")
            self.history = []
    
    def save_history(self):
        """Save conversation history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Could not save conversation history: {e}")
    
    def add_conversation(self, user_query: str, response: Dict[str, Any]):
        """Add a new conversation to history"""
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "response_type": response.get("type", "unknown"),
            "success": response.get("success", False),
            "error": response.get("error", None),
            "generated_images": response.get("generated_images", []),
            "dataframes_count": len(response.get("dataframes", {})),
            "execution_output": response.get("execution_result", {}).get("output", "")
        }
        
        # Store only essential information to avoid large files
        if response.get("type") == "comprehensive_report":
            conversation["report_generated"] = True
            conversation["report_length"] = len(response.get("comprehensive_report", ""))
        
        self.history.append(conversation)
        self.save_history()
        
        # Add to LangChain memory if enabled
        if self.langchain_enabled and hasattr(self, 'langchain_history'):
            try:
                # Add user message
                human_msg = HumanMessage(content=user_query)
                human_msg.timestamp = conversation["timestamp"]
                self.langchain_history.add_message(human_msg)
                
                # Add AI response
                ai_response = self._create_ai_response_summary(response)
                ai_msg = AIMessage(content=ai_response)
                ai_msg.timestamp = conversation["timestamp"]
                self.langchain_history.add_message(ai_msg)
                
            except Exception as e:
                print(f"⚠️ Could not add to LangChain memory: {e}")
    
    def _create_ai_response_summary(self, response: Dict[str, Any]) -> str:
        """Create AI response summary for LangChain"""
        if response.get("success"):
            summary = f"Successfully completed {response.get('type', 'analysis')}. "
            
            if response.get("dataframes"):
                summary += f"Generated {len(response['dataframes'])} DataFrames. "
            
            if response.get("generated_images"):
                summary += f"Created {len(response['generated_images'])} visualizations. "
            
            if response.get("type") == "comprehensive_report":
                summary += "Comprehensive strategic report generated."
            
            return summary
        else:
            return f"Analysis failed: {response.get('error', 'Unknown error')}"
    
    def get_context_for_ai(self, last_n: int = 5) -> str:
        """Get recent conversation context for AI"""
        # First try LangChain context if available
        if self.langchain_enabled and hasattr(self, 'active_memory'):
            try:
                return self._get_langchain_context_for_ai()
            except Exception as e:
                print(f"⚠️ LangChain context failed, falling back to original: {e}")
        
        # Fallback to original implementation
        if not self.history:
            return ""
        
        recent_history = self.history[-last_n:]
        context = "\n### RECENT CONVERSATION CONTEXT:\n"
        
        for i, conv in enumerate(recent_history, 1):
            context += f"\n{i}. Previous Query: {conv['user_query']}\n"
            context += f"   Response Type: {conv['response_type']}\n"
            context += f"   Success: {conv['success']}\n"
            
            if conv.get('generated_images'):
                context += f"   Generated Images: {len(conv['generated_images'])}\n"
            
            if conv.get('dataframes_count', 0) > 0:
                context += f"   Generated DataFrames: {conv['dataframes_count']}\n"
            
            if conv.get('error'):
                context += f"   Error: {conv['error'][:100]}...\n"
        
        context += "\nUse this context to provide more relevant and coherent responses.\n"
        return context
    
    def _get_langchain_context_for_ai(self) -> str:
        """Get LangChain-powered context for AI"""
        try:
            # Get memory variables
            memory_vars = self.active_memory.load_memory_variables({})
            
            context = "\n### ENHANCED CONVERSATION CONTEXT (LangChain):\n"
            context += "Build upon previous analyses and refer to past results when appropriate.\n"
            
            # Add conversation history
            if 'history' in memory_vars:
                context += "\n### RECENT CONVERSATION HISTORY:\n"
                messages = memory_vars['history']
                
                for i, message in enumerate(messages[-10:], 1):  # Last 10 messages
                    if isinstance(message, HumanMessage):
                        context += f"\n{i}. USER: {message.content}\n"
                    elif isinstance(message, AIMessage):
                        # Truncate long AI responses for context
                        ai_content = message.content[:300] + "..." if len(message.content) > 300 else message.content
                        context += f"   AI: {ai_content}\n"
            
            # Add summary if available
            if hasattr(self.active_memory, 'moving_summary_buffer') and self.active_memory.moving_summary_buffer:
                context += f"\n### CONVERSATION SUMMARY:\n{self.active_memory.moving_summary_buffer}\n"
            
            context += "\nUse this enhanced context to provide more relevant and coherent responses.\n"
            return context
            
        except Exception as e:
            print(f"Error getting LangChain AI context: {e}")
            # Fallback to original method
            return self.get_context_for_ai()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        # Original summary
        if not self.history:
            summary = {"total_queries": 0, "successful_queries": 0, "failed_queries": 0}
        else:
            total = len(self.history)
            successful = sum(1 for h in self.history if h.get('success', False))
            failed = total - successful
            
            query_types = {}
            for h in self.history:
                response_type = h.get('response_type', 'unknown')
                query_types[response_type] = query_types.get(response_type, 0) + 1
            
            summary = {
                "total_queries": total,
                "successful_queries": successful,
                "failed_queries": failed,
                "query_types": query_types,
                "session_duration": self._calculate_session_duration()
            }
        
        # Add LangChain enhancements if available
        if self.langchain_enabled and hasattr(self, 'langchain_history'):
            try:
                summary["langchain_enabled"] = True
                summary["total_langchain_messages"] = len(self.langchain_history.messages)
                
                if hasattr(self.active_memory, 'moving_summary_buffer') and self.active_memory.moving_summary_buffer:
                    summary["ai_conversation_summary"] = self.active_memory.moving_summary_buffer
                    
            except Exception as e:
                print(f"⚠️ Could not get LangChain summary: {e}")
                summary["langchain_enabled"] = False
        else:
            summary["langchain_enabled"] = False
        
        return summary
    
    def _calculate_session_duration(self) -> str:
        """Calculate session duration"""
        if len(self.history) < 2:
            return "N/A"
        
        start_time = datetime.fromisoformat(self.history[0]['timestamp'])
        end_time = datetime.fromisoformat(self.history[-1]['timestamp'])
        duration = end_time - start_time
        
        return str(duration).split('.')[0]  # Remove microseconds
    
    # NEW METHODS - Additional LangChain functionality
    def get_langchain_messages(self) -> List[BaseMessage]:
        """Get LangChain messages (new method)"""
        if self.langchain_enabled and hasattr(self, 'langchain_history'):
            return self.langchain_history.messages
        return []
    
    def export_langchain_conversation(self, format: str = 'json') -> str:
        """Export conversation using LangChain format (new method)"""
        if not self.langchain_enabled or not hasattr(self, 'langchain_history'):
            return json.dumps({"error": "LangChain not enabled"})
        
        try:
            if format == 'json':
                messages_data = []
                for msg in self.langchain_history.messages:
                    messages_data.append({
                        'type': msg.__class__.__name__,
                        'content': msg.content,
                        'timestamp': getattr(msg, 'timestamp', datetime.now().isoformat())
                    })
                
                return json.dumps({
                    'session_id': self.session_id,
                    'messages': messages_data,
                    'summary': self.get_summary()
                }, indent=2, ensure_ascii=False)
            
            elif format == 'text':
                text_export = f"LangChain Conversation Export - Session: {self.session_id}\n"
                text_export += f"Created: {datetime.now().isoformat()}\n"
                text_export += "=" * 50 + "\n\n"
                
                for message in self.langchain_history.messages:
                    timestamp = getattr(message, 'timestamp', 'Unknown time')
                    if isinstance(message, HumanMessage):
                        text_export += f"[{timestamp}] USER: {message.content}\n\n"
                    elif isinstance(message, AIMessage):
                        text_export += f"[{timestamp}] AI: {message.content}\n\n"
                
                return text_export
            
        except Exception as e:
            return f"Error exporting LangChain conversation: {e}"
    
    def clear_langchain_memory(self):
        """Clear LangChain memory (new method)"""
        if self.langchain_enabled and hasattr(self, 'langchain_history'):
            try:
                self.langchain_history.clear()
                if hasattr(self, 'active_memory'):
                    self.active_memory.clear()
                print("✅ LangChain memory cleared")
            except Exception as e:
                print(f"⚠️ Could not clear LangChain memory: {e}")