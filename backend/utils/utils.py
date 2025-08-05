import os
import json
import uuid
import base64
from io import BytesIO
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
import traceback
import warnings
import re
from typing import Dict, Any, List, Tuple
import numpy as np

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import plotly 
import matplotlib.pyplot as plt
import seaborn as sns

# Import your existing analyzer
from legacy_codes.test2 import QuadraticCSVAnalyzer
from dotenv import load_dotenv

import requests
import tempfile

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

# Suppress warnings
warnings.filterwarnings('ignore')

load_dotenv()

# Global storage for stop signals per session
stop_signals = {}

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
            self.langchain_history = LangChainChatHistory(self)
            
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
                    k=10,
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
            "execution_output": response.get("execution_result", {}).get("output", ""),
            "is_conversational": response.get("is_conversational", False)
        }
        
        # Store only essential information to avoid large files
        if response.get("type") == "comprehensive_report":
            conversation["report_generated"] = True
            conversation["report_length"] = len(response.get("comprehensive_report", ""))
        elif response.get("type") == "conversational":
            conversation["ai_response"] = response.get("ai_response", "")
        
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
                if response.get("type") == "conversational":
                    ai_response = response.get("ai_response", "")
                else:
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
            conversational = sum(1 for h in self.history if h.get('is_conversational', False))
            
            query_types = {}
            for h in self.history:
                response_type = h.get('response_type', 'unknown')
                query_types[response_type] = query_types.get(response_type, 0) + 1
            
            summary = {
                "total_queries": total,
                "successful_queries": successful,
                "failed_queries": failed,
                "conversational_queries": conversational,
                "analytical_queries": total - conversational,
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
    
    def get_langchain_messages(self) -> List[BaseMessage]:
        """Get LangChain messages"""
        if self.langchain_enabled and hasattr(self, 'langchain_history'):
            return self.langchain_history.messages
        return []
    
    def export_langchain_conversation(self, format: str = 'json') -> str:
        """Export conversation using LangChain format"""
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
        """Clear LangChain memory"""
        if self.langchain_enabled and hasattr(self, 'langchain_history'):
            try:
                self.langchain_history.clear()
                if hasattr(self, 'active_memory'):
                    self.active_memory.clear()
                print("✅ LangChain memory cleared")
            except Exception as e:
                print(f"⚠️ Could not clear LangChain memory: {e}")


class StreamingAnalyzer(QuadraticCSVAnalyzer):
    """Extended analyzer with streaming capabilities and query classification for Flask integration."""
    
    def __init__(self, session_id, socketio=None):
        super().__init__()
        self.session_id = session_id
        self.streaming_outputs = []
        self.conversation_history = ConversationHistory(session_id, self.output_dir)
        self.socketio = socketio
        self.is_analyzing = False
        
        # Initialize simple memory - no need for complex chat history initialization
        self.memory = None  # Will be set up later if needed
    
    def emit_stream(self, message_type, data):
        """Emit streaming data to the frontend."""
        try:
            if self.socketio:
                self.socketio.emit('stream_data', {
                    'type': message_type,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
                
                # Check for stop signal
                if self.session_id in stop_signals and stop_signals[self.session_id]:
                    print(f"🛑 Analysis stopped by user for session: {self.session_id}")
                    self.socketio.emit('stream_data', {
                        'type': 'stopped',
                        'data': 'Analysis stopped by user',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                    raise StopAnalysisException("Analysis stopped by user")
                
                # Small delay for smooth streaming
                try:
                    # Try eventlet sleep first
                    import eventlet
                    eventlet.sleep(0.05)
                except ImportError:
                    # Fallback to regular sleep
                    time.sleep(0.05)
        except StopAnalysisException:
            raise  # Re-raise stop exception
        except Exception as e:
            print(f"Error emitting stream: {e}")
    
    def check_stop_signal(self):
        """Check if user has requested to stop analysis"""
        if self.session_id in stop_signals and stop_signals[self.session_id]:
            print(f"🛑 Stop signal detected for session: {self.session_id}")
            raise StopAnalysisException("Analysis stopped by user")
    
    def _classify_query(self, user_query: str) -> str:
        """
        Classify user query as either 'conversational' or 'analytical'
        
        Returns:
            'conversational' - for greetings, small talk, general questions
            'analytical' - for data analysis tasks
        """
        query_lower = user_query.lower().strip()
        
        # Common conversational patterns
        conversational_patterns = [
            # Greetings
            r'^(hi|hello|hey|good morning|good afternoon|good evening|hiya)(?:\s|$)',
            # How are you variants
            r'how are you',
            r'how\'s it going',
            r'how do you do',
            r'what\'s up',
            r'how\'s everything',
            # Thanks and responses
            r'^(thanks|thank you|ty|thx)',
            r'^(you\'re welcome|welcome|no problem|np)',
            # General questions about the AI
            r'who are you',
            r'what are you',
            r'what can you do',
            r'what is your name',
            r'tell me about yourself',
            r'how does this work',
            # Casual conversation
            r'^(yes|yeah|yep|ok|okay|sure|alright)(?:\s|$)',
            r'^(no|nope|nah)(?:\s|$)',
            r'nice to meet you',
            r'good to see you',
            r'have a good day',
            r'goodbye|bye|see you',
            # Help requests (general)
            r'^help(?:\s|$)',
            r'can you help',
            # Weather/time (general)
            r'what time is it',
            r'what\'s the weather',
            r'what things can you do?'
        ]
        
        # Data analysis keywords
        analytical_keywords = [
            'analyze', 'analysis', 'data', 'csv', 'dataframe', 'df', 'plot', 'chart', 'graph',
            'visualize', 'visualization', 'statistics', 'stats', 'mean', 'median', 'mode',
            'correlation', 'regression', 'forecast', 'predict', 'trend', 'pattern',
            'filter', 'group', 'sort', 'aggregate', 'sum', 'count', 'average',
            'show me', 'display', 'calculate', 'compute', 'find', 'search',
            'compare', 'comparison', 'revenue', 'sales', 'profit', 'performance',
            'top', 'bottom', 'best', 'worst', 'highest', 'lowest',
            'report', 'summary', 'insights', 'breakdown', 'distribution'
        ]
        
        # Check for conversational patterns first
        for pattern in conversational_patterns:
            if re.search(pattern, query_lower):
                return 'conversational'
        
        # Check for analytical keywords
        for keyword in analytical_keywords:
            if keyword in query_lower:
                return 'analytical'
        
        # Additional heuristics
        # Very short queries are often conversational
        if len(query_lower.split()) <= 2 and not any(kw in query_lower for kw in analytical_keywords):
            # But check if it's a question about data
            if any(word in query_lower for word in ['what', 'how', 'why', 'when', 'where', 'which']):
                # Could be analytical question, check context
                if any(word in query_lower for word in ['column', 'row', 'field', 'value', 'record']):
                    return 'analytical'
                return 'conversational'
            return 'conversational'
        
        # Longer queries with question words are more likely analytical if they mention data concepts
        question_words = ['what', 'how', 'why', 'when', 'where', 'which', 'who']
        if any(qw in query_lower for qw in question_words):
            # If no data keywords found, likely conversational
            if not any(kw in query_lower for kw in analytical_keywords):
                return 'conversational'
        
        # Default to analytical for ambiguous cases
        return 'analytical'
    
    def _handle_conversational_query(self, user_query: str) -> Dict[str, Any]:
        """
        Handle conversational queries with OpenAI directly
        """
        try:
            self.emit_stream('status', "💬 Handling conversational query...")
            
            # Get conversation context for more natural responses  
            context = self.conversation_history.get_context_for_ai(last_n=5)
            
            # Create a conversational system prompt
            system_prompt = f"""
You are a friendly AI assistant for a data analysis platform. You are currently in a chat session where users can upload CSV files and ask questions about their data.

Context about the current session:
- Session ID: {self.session_id}
- Data loaded: {'Yes' if self.df is not None else 'No'}
{f'- Data shape: {self.df.shape}' if self.df is not None else ''}
{f'- Columns: {list(self.df.columns)[:5]}{"..." if self.df is not None and len(self.df.columns) > 5 else ""}' if self.df is not None else ''}

Your role:
- Respond naturally to greetings, questions about yourself, and casual conversation
- Be helpful and friendly
- If users ask what you can do, mention you can analyze CSV data, create visualizations, and generate reports
- Keep responses concise but warm
- Don't generate code or perform data analysis for conversational queries
- If the conversation shifts to data analysis, encourage them to ask specific questions about their data

Previous conversation context:
{context if context else "This is the start of the conversation."}

Respond in a natural, conversational way.
"""
            
            # Get conversational response from OpenAI
            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7,  # Higher temperature for more natural conversation
                max_tokens=200    # Keep responses concise
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Stream the response
            self.emit_stream('conversational_response', ai_response)
            
            # Create result object
            result = {
                "query": user_query,
                "type": "conversational",
                "ai_response": ai_response,
                "success": True,
                "is_conversational": True,
                "generated_images": [],
                "dataframes": {},
                "data_update_available": False
            }
            
            print(f"💬 Conversational query handled: {user_query[:50]}...")
            print(f"🤖 Response: {ai_response[:100]}...")
            
            return result
            
        except Exception as e:
            print(f"❌ Error handling conversational query: {str(e)}")
            error_response = "I'm sorry, I encountered an error while trying to respond. How can I help you with your data analysis?"
            
            self.emit_stream('error', f"Conversational response failed: {str(e)}")
            
            return {
                "query": user_query,
                "type": "conversational",
                "ai_response": error_response,
                "success": False,
                "error": str(e),
                "is_conversational": True,
                "generated_images": [],
                "dataframes": {},
                "data_update_available": False
            }
    
    def analyze_query_streaming(self, user_query: str):
        """Enhanced analyze_query with query classification and routing."""
        try:
            # Set analyzing flag
            self.is_analyzing = True
            
            # Clear any existing stop signal
            if self.session_id in stop_signals:
                stop_signals[self.session_id] = False
            
            self.emit_stream('status', f"🔍 Classifying query: {user_query}")
            self.check_stop_signal()
            
            # Classify the query
            query_type = self._classify_query(user_query)
            
            print(f"📋 Query classified as: {query_type}")
            print(f"📝 Query: {user_query}")
            
            # Route based on classification
            if query_type == 'conversational':
                self.emit_stream('status', "💬 Routing to conversation handler...")
                result = self._handle_conversational_query(user_query)
            else:
                # Handle as analytical query
                if self.df is None:
                    self.emit_stream('error', "No CSV file loaded. Please upload a CSV first.")
                    result = {"error": "No CSV file loaded. Please load a CSV first.", "success": False}
                else:
                    self.emit_stream('status', "📊 Routing to data analysis handler...")
                    result = self._handle_analytical_query(user_query)
            
            # Record in history
            self.conversation_history.add_conversation(user_query, result)
            
            # Clear analyzing flag
            self.is_analyzing = False
            
            return result

        except StopAnalysisException:
            # Handle stop signal gracefully
            self.is_analyzing = False
            stop_result = {
                "error": "Analysis stopped by user",
                "type": "stopped",
                "success": False,
                "stopped_by_user": True
            }
            self.conversation_history.add_conversation(user_query, stop_result)
            return stop_result
            
        except Exception as e:
            # capture full traceback
            self.is_analyzing = False
            full_trace = traceback.format_exc()
            error_msg = f"Error analyzing query:\n{full_trace}"
            print(error_msg)
            self.emit_stream('error', error_msg)

            # record failure in history
            self.conversation_history.add_conversation(user_query, {
                "error": str(e),
                "traceback": full_trace,
                "type": "error",
                "success": False
            })

            return {
                "error": str(e),
                "traceback": full_trace,
                "type": "error",
                "success": False
            }
    
    def _handle_analytical_query(self, user_query: str):
        """Handle analytical queries (original logic)"""
        # announce incoming query
        self.emit_stream('status', f"Analyzing query: {user_query}")
        self.check_stop_signal()

        # reset per‑query state
        self.generated_images = []
        self.streaming_outputs = []

        # decide path
        is_report_request = self._is_report_request(user_query)
        data_request = self._extract_data_request(user_query)
        is_forecasting = any(
            kw in user_query.lower()
            for kw in ['forecast','predict','future','next','ahead','months','years','projection']
        )

        self.check_stop_signal()

        if is_report_request:
            result = self._generate_comprehensive_report_streaming(
                user_query,
                is_forecasting
            )
        else:
            self.emit_stream('status', "📊 Focusing on DataFrame results…")
            result = self._generate_dataframe_analysis_streaming_with_fallback(
                user_query,
                data_request,
                is_forecasting
            )

        return result
    
    def _create_system_prompt(self) -> str:
        """Create system prompt focused on DataFrame results and data updates."""
        return f"""
You are a Python code generator that MUST create COMPLETE, EXECUTABLE data analysis solutions.

MANDATORY REQUIREMENTS:
1. Generate COMPLETE Python code that runs from start to finish - NO PARTIAL CODE
2. ALWAYS include data exploration, analysis, modeling, AND visualization
3. NEVER stop at data exploration - always complete the full analysis
4. ALWAYS create charts/visualizations using matplotlib for EVERY analysis
5. Return results as DataFrames with meaningful column names
6. Use the 'df' variable (DataFrame is already loaded - NEVER use pd.read_csv())
7. Detect the header of the attached file. it is not important that the first attached file will be the header. 

VISUALIZATION REQUIREMENTS (MANDATORY):
- ALWAYS create at least one chart for every analysis
- Use Bar charts for comparisons, categories, rankings
- Use Line charts for trends, time series, forecasting
- Use Pie charts for revenue/profit breakdowns by category/SKU
- Save all plots using plt.savefig() and plt.show()
- Include proper titles, labels, and legends
- Use subtle, cleaned legends and labels along x-axis and y-axis. 

SUCCESS CRITERIA FOR EVERY RESPONSE:
✓ Code runs completely without errors
✓ Creates actionable DataFrame results
✓ Generates meaningful visualizations
✓ Returns complete analysis (not just exploration)
✓ Includes proper data insights

CORE PHILOSOPHY:
- Focus on returning ACTIONABLE DATA as DataFrames
- Create new columns, calculated fields, or enhanced datasets
- Always show what data would be ADDED or UPDATED in the original file
- Generate visualizations only when they add value to the data analysis
 
CRITICAL REQUIREMENTS:
1. Use 'df' variable which contains the loaded DataFrame - NEVER use pd.read_csv()
2. ALWAYS return results as DataFrames that can be merged/joined with original data
3. Create meaningful column names for new calculated fields
4. Show before/after data previews
5. Focus on data enrichment rather than just analysis
 
DATA OUTPUT PRIORITIES:
1. New calculated columns (trends, scores, rankings, categories)
2. Forecasted values with future dates
3. Cleaned/standardized versions of existing data
4. Category classifications and performance metrics
5. Statistical measures and derived insights
 
Data Context:
{self.csv_info}
 
EXAMPLE OUTPUT PATTERNS:
- Adding trend indicators: df['trend_direction'], df['growth_rate']
- Creating rankings: df['performance_rank'], df['category_score']
- Forecasting: future_predictions_df with new dates and predicted values
- Classifications: df['risk_category'], df['performance_tier']
- Metrics: df['volatility_score'], df['seasonal_index']
 
VISUALIZATION GUIDELINES:
- Generate visualizations only when they help understand the data modifications
- Always save plots using plt.savefig() when created
- Keep visualizations focused on showing the new data insights
 
DATA CLEANING RULES:
- Always clean string data before converting to numeric
- Handle missing values appropriately
- Ensure data types are correct for calculations
- Validate results before returning
 
EXECUTION FOCUS:
Return DataFrames that enhance the original dataset with new insights, predictions, or calculated fields.
Show exactly what data would be added to the original file.
You MUST complete the entire analysis with visualizations in one code block.
Focus on creating NEW DATA that enhances the original dataset.

----------------- PYTHON BASICS DOCUMENTATION (FOR REFERENCE) -----------------

# Common Python Structures:
my_list = [1, 2, 3]
my_dict = {{'key': 'value'}}
for item in my_list:
    print(item)

if x > 0:
    print("Positive")
elif x < 0:
    print("Negative")
else:
    print("Zero")

def my_func(x):
    return x * 2

# DataFrame Basics:
df.head()
df.info()
df.describe()
df['column_name']
df[['col1', 'col2']]
df[df['col'] > 10]
df.groupby('category').mean()
df['new'] = df['old'] * 0.1

# Plotting with matplotlib:
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(df['date'], df['value'])  # or plt.bar(), plt.pie()
plt.title("Trend Over Time")
plt.xlabel("Date")
plt.ylabel("Value")
plt.legend(["Series A"])
plt.savefig("trend_plot.png")
plt.show()

# Handling Missing Values:
df.dropna()
df.fillna(0)
df['col'].isna().sum()

# Type Conversion:
df['col'] = df['col'].astype(float)
df['date'] = pd.to_datetime(df['date'])

# Statistical Methods:
df['col'].mean()
df['col'].median()
df['col'].std()
df.corr()

# Forecasting Example with Prophet:
from prophet import Prophet

df_prophet = df.rename(columns={{'date': 'ds', 'value': 'y'}})
model = Prophet()
model.fit(df_prophet)
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

---------------- SYNTAX SAFETY CHECKLIST (MANDATORY FOR EVERY CODE) ----------------

✓ NO unexpected indent or over-indented lines
✓ All brackets ((), [], {{}}) and quotes ('' or "") are closed properly
✓ ALL import statements at the top
✓ No use of undefined variables or functions (e.g., using plt without import)
✓ Function definitions and loops are correctly indented (4 spaces)
✓ Each line is syntactically complete (e.g., no unclosed `if`, `for`, or `def`)
✓ Save and display all plots with both `plt.savefig()` AND `plt.show()`
"""
    
    def _streaming_print(self, *args, **kwargs):
        """Custom print function that streams output to frontend."""
        output_text = ' '.join(str(arg) for arg in args)
        self.streaming_outputs.append(output_text)
        self.emit_stream('output', output_text)
        print(*args, **kwargs)  # Also print to console
    
    # Include all other methods from the original StreamingAnalyzer class
    # (keeping all the existing methods for data analysis)
    
    def _generate_dataframe_analysis_streaming(self, user_query: str, data_request: Dict, is_forecasting: bool) -> Dict[str, Any]:
        """Generate analysis focused on returning actionable DataFrame results with stop checking"""
        
        # Check for stop signal before major operations
        self.check_stop_signal()
        
        # Enhanced prompt for DataFrame-focused analysis
        base_requirements = f"""
Generate Python code to: {user_query}
 
PRIMARY GOAL: Return actionable DataFrame results that can enhance the original dataset.
 
CRITICAL REQUIREMENTS:
- Use 'df' variable which contains the loaded DataFrame
- NEVER use pd.read_csv() or file paths
- Focus on creating NEW DATA that adds value to the original dataset
- Return results as DataFrames with meaningful column names
- Show before/after data previews
- Always give charts using matplotlib for visualization using Bar-Charts, Line Graphs, Pie Chart. 
- Use Line charts for forecastings and Trend analysis.
- Use PieChart for Revenue per Product or Category or SKU 
- Use Bar Chart for other types of viualisation
 
DATA OUTPUT FOCUS:
- Create calculated columns, derived metrics, or classifications
- Generate forecasted data with future dates if requested
- Add trend indicators, performance scores, or category rankings
- Provide data that can be merged back to the original file
- Provide the charts for the visualisations for tasks such as trend, revenue, forecast, predictions, analyzation, best products, performance.
 
RESULT STRUCTURE:
1. Examine original data structure
2. Perform calculations/analysis
3. Create enhanced DataFrame with new columns
4. Show preview of original vs enhanced data
5. Save results that can update the original file
6. Return the chart
 
REQUEST TYPE: {data_request['type']}
"""
        if is_forecasting:
            base_requirements = base_requirements + """
FORECASTING-SPECIFIC REQUIREMENTS:
- Create a separate DataFrame with future predictions
- Include future dates beyond the last date in dataset
- Provide confidence intervals or prediction ranges
- Return forecasted_data_df with columns: [Date, Predicted_Value, Confidence_Lower, Confidence_Upper]
- Show both historical trend analysis and future predictions

FORECASTING OUTPUT:
- Original data with trend indicators added
- Separate forecast DataFrame for future periods
- Combined visualization showing historical + predicted

===============================================
FORECASTING FUNDAMENTALS & CRITICAL DEFINITIONS
===============================================
 
FORECASTING DEFINITION:
Forecasting = Predicting FUTURE values that extend BEYOND the existing dataset's time range.
- Historical data: Used for training models
- Future predictions: Generated for periods AFTER the last date in the dataset
- NEVER predict on known historical values when asked to "forecast"
 
TIME SERIES FORECASTING MODELS & THEIR LOGIC:
 
1. LINEAR REGRESSION FORECASTING:
```
Pseudo-code:
1. Create time index (0, 1, 2, ..., n-1) for historical data
2. Fit: y = ax + b where x = time_index
3. For future predictions:
   - future_time_indices = [n, n+1, n+2, ..., n+forecast_periods-1]
   - future_values = model.predict(future_time_indices)
4. Convert future_time_indices back to actual future dates
```
 
2. MOVING AVERAGE FORECASTING:
```
Pseudo-code:
1. Simple Moving Average: forecast = mean(last_N_values)
2. Weighted Moving Average: forecast = sum(weights * last_N_values)
3. Exponential Moving Average:
   - alpha = smoothing_factor (0.1 to 0.3)
   - forecast = alpha * last_value + (1-alpha) * previous_forecast
```
 
3. AUTOREGRESSIVE (AR) MODELS:
```
Pseudo-code:
1. AR(p): y_t = c + φ₁*y_{{t-1}} + φ₂*y_{{t-2}} + ... + φ_p*y_{{t-p}} + ε_t
2. For forecasting:
   - Use last p values to predict next value
   - Recursively use predictions to forecast multiple periods ahead
3. Implementation: Use statsmodels.tsa.ar_model.AutoReg
```
 
4. ARIMA FORECASTING:
```
Pseudo-code:
1. ARIMA(p,d,q): Combines AR(p) + Integration(d) + MA(q)
2. Auto-detect parameters using auto_arima or AIC/BIC
3. For forecasting:
   - model.fit(historical_data)
   - forecast = model.forecast(steps=forecast_periods)
4. Implementation: Use statsmodels.tsa.arima.ARIMA
```
 
5. XGBOOST TIME SERIES FORECASTING:
```
Pseudo-code:
1. Create lagged features: [y_{{t-1}}, y_{{t-2}}, ..., y_{{t-window_size}}]
2. Feature matrix X: Each row = [lag1, lag2, ..., lag_window]
3. Target y: y_t (current value to predict)
4. Train: XGBRegressor.fit(X, y)
5. For multi-step forecasting:
   a. Predict next value using last window
   b. Add prediction to window, remove oldest value
   c. Repeat for each future period
```
 
6. LSTM NEURAL NETWORK FORECASTING:
```
Pseudo-code:
1. Reshape data: (samples, window_size, features)
2. Architecture: Input -> LSTM(50-100 units) -> Dense(1)
3. Training: Minimize MSE between predicted and actual
4. For forecasting:
   a. Use last window_size values as input
   b. Predict next value
   c. Update window with prediction
   d. Repeat for multiple periods
```
 
===============================================
MANDATORY FORECASTING IMPLEMENTATION RULES
===============================================
 
STEP 1: DATA PREPARATION
```python
# Always start with data exploration
print("=== DATA EXPLORATION ===")
print(f"DataFrame shape: {{df.shape}}")
print(f"Columns: {{df.columns.tolist()}}")
print(df.info())
print(df.head())
 
# Identify time and target columns
date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower() or 'year' in col.lower()]
numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
print(f"Potential date columns: {{date_columns}}")
print(f"Numeric columns: {{numeric_columns}}")
```
 
STEP 2: TIME SERIES PREPARATION
```python
# Clean and prepare time series
def prepare_time_series(df, date_col, target_col):
    # Convert date column
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
   
    # Clean target column
    if df[target_col].dtype == 'object':
        df[target_col] = df[target_col].astype(str).str.replace(',', '').str.replace('$', '').str.strip()
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
   
    # Remove missing values
    df = df.dropna(subset=[date_col, target_col])
   
    # Sort by date
    df = df.sort_values(date_col).reset_index(drop=True)
   
    return df
```
============================
XGBOOST ALGORITHM TEMPLATE
============================
- Use below code as template for xgboost algorithm: 

import pandas as pd
import numpy as np
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error, mean_absolute_error

print("=== STEP 1: DATA PREPARATION ===")
# Convert date and prepare data
df['Date'] = pd.to_datetime(df['Date'])


# Aggregate by date to create time series
daily_data = df.groupby('Date').agg({{
    'Revenue': 'sum',
    'Units Sold': 'sum',
    'Profit': 'sum'
}}).reset_index()

# Choose target variable (Revenue is primary choice)
target_col = 'Revenue'
print(f"Target variable: {{target_col}}")
print(f"Date range: {{daily_data['Date'].min()}} to {{daily_data['Date'].max()}}")
print(f"Data points: {{len(daily_data)}}")

print("=== STEP 2: FEATURE ENGINEERING ===")
def create_features(data, target_column, n_lags=7):
    features_df = data.copy()
    
    # Time-based features
    features_df['year'] = features_df['Date'].dt.year
    features_df['month'] = features_df['Date'].dt.month
    features_df['day'] = features_df['Date'].dt.day
    features_df['dayofweek'] = features_df['Date'].dt.dayofweek
    features_df['quarter'] = features_df['Date'].dt.quarter
    features_df['is_weekend'] = features_df['dayofweek'].isin([5, 6]).astype(int)
    
    # Lag features (previous values)
    for lag in range(1, n_lags + 1):
        features_df[f'{{target_column}}_lag_{{lag}}'] = features_df[target_column].shift(lag)
    
    # Rolling window features (moving averages)
    for window in [3, 7, 14, 30]:
        features_df[f'{{target_column}}_rolling_{{window}}'] = features_df[target_column].rolling(window).mean()
        features_df[f'{{target_column}}_rolling_std_{{window}}'] = features_df[target_column].rolling(window).std()
    
    # Growth rate features
    features_df[f'{{target_column}}_growth_1d'] = features_df[target_column].pct_change(1)
    features_df[f'{{target_column}}_growth_7d'] = features_df[target_column].pct_change(7)
    
    return features_df

# Create features
featured_data = create_features(daily_data, target_col, n_lags=14)
# Remove rows with NaN (due to lag features)
featured_data = featured_data.dropna().reset_index(drop=True)
print(f"Features created. Final shape: {{featured_data.shape}}")

print("=== STEP 3: MODEL TRAINING ===")
# Prepare feature columns
feature_columns = [col for col in featured_data.columns if col not in ['Date', target_col]]
X = featured_data[feature_columns]
y = featured_data[target_col]

# Split data (use last 20% for validation)
split_idx = int(len(featured_data) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

print(f"Training set: {{len(X_train)}} samples")
print(f"Test set: {{len(X_test)}} samples")

# Train XGBoost model with robust parameters
model = XGBRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# Evaluate model performance
train_pred = model.predict(X_train)
test_pred = model.predict(X_test)

train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
train_mae = mean_absolute_error(y_train, train_pred)
test_mae = mean_absolute_error(y_test, test_pred)

print(f"Model Performance:")
print(f"Train RMSE: {{train_rmse:.2f}}, MAE: {{train_mae:.2f}}")
print(f"Test RMSE: {{test_rmse:.2f}}, MAE: {{test_mae:.2f}}")

print("=== STEP 4: GENERATE 12-MONTH FORECAST ===")
# Generate future dates (365 days = 12 months)
last_date = featured_data['Date'].max()
future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=365, freq='D')
print(f"Forecasting from {{future_dates[0]}} to {{future_dates[-1]}}")

# Multi-step forecasting
forecast_predictions = []
forecast_lower = []
forecast_upper = []

# Get recent data for context
recent_data = featured_data.tail(30).copy()
all_predictions = list(featured_data[target_col].tail(14))

for i, future_date in enumerate(future_dates):
    # Create time-based features
    future_features = {{
        'year': future_date.year,
        'month': future_date.month,
        'day': future_date.day,
        'dayofweek': future_date.dayofweek,
        'quarter': future_date.quarter,
        'is_weekend': int(future_date.dayofweek in [5, 6])
    }}
    
    # Get recent values (combine historical + previous predictions)
    recent_values = all_predictions[-30:]  # Last 30 values
    
    # Create lag features
    for lag in range(1, 15):
        if lag <= len(recent_values):
            future_features[f'{{target_col}}_lag_{{lag}}'] = recent_values[-lag]
        else:
            future_features[f'{{target_col}}_lag_{{lag}}'] = recent_values[-1]
    
    # Create rolling features
    for window in [3, 7, 14, 30]:
        if len(recent_values) >= window:
            future_features[f'{{target_col}}_rolling_{{window}}'] = np.mean(recent_values[-window:])
            future_features[f'{{target_col}}_rolling_std_{{window}}'] = np.std(recent_values[-window:])
        else:
            future_features[f'{{target_col}}_rolling_{{window}}'] = np.mean(recent_values)
            future_features[f'{{target_col}}_rolling_std_{{window}}'] = np.std(recent_values)
    
    # Create growth features
    if len(recent_values) >= 2:
        future_features[f'{{target_col}}_growth_1d'] = (recent_values[-1] - recent_values[-2]) / recent_values[-2]
    else:
        future_features[f'{{target_col}}_growth_1d'] = 0
        
    if len(recent_values) >= 8:
        future_features[f'{{target_col}}_growth_7d'] = (recent_values[-1] - recent_values[-8]) / recent_values[-8]
    else:
        future_features[f'{{target_col}}_growth_7d'] = 0
    
    # Create feature vector (ensure same order as training)
    feature_vector = pd.DataFrame([future_features])
    feature_vector = feature_vector.reindex(columns=feature_columns, fill_value=0)
    
    # Make prediction
    prediction = model.predict(feature_vector)[0]
    
    # Add some uncertainty bounds (±15% based on test error)
    error_margin = test_rmse * 1.5
    lower_bound = max(0, prediction - error_margin)
    upper_bound = prediction + error_margin
    
    # Store predictions
    forecast_predictions.append(prediction)
    forecast_lower.append(lower_bound)
    forecast_upper.append(upper_bound)
    all_predictions.append(prediction)

print(f"Generated {{len(forecast_predictions)}} daily forecasts")

print("=== STEP 5: CREATE FORECASTED DATA ===")
# Create detailed forecasted_data DataFrame
forecasted_data = pd.DataFrame({{
'Date': future_dates,
'Predicted_Value': forecast_predictions,
'Confidence_Lower': forecast_lower,
'Confidence_Upper': forecast_upper,
'Model_Used': 'XGBoost',
'Target_Variable': target_col,
'Forecast_Day': range(1, len(future_dates) + 1)
}})

# Add monthly aggregation for easier interpretation
forecasted_data['Year_Month'] = forecasted_data['Date'].dt.to_period('M')
monthly_forecast = forecasted_data.groupby('Year_Month').agg({{
    'Predicted_Value': 'sum',
    'Confidence_Lower': 'sum',
    'Confidence_Upper': 'sum'
}}).reset_index()

print("FORECAST SUMMARY:")
print(f"Daily average forecast: {{forecasted_data['Predicted_Value'].mean():.2f}}")
print(f"Monthly forecast range: {{monthly_forecast['Predicted_Value'].min():.2f}} - {{monthly_forecast['Predicted_Value'].max():.2f}}")
print(f"Total 12-month forecast: {{forecasted_data['Predicted_Value'].sum():.2f}}")

print("=== STEP 6: MANDATORY VISUALIZATIONS ===")

# Create comprehensive visualization
fig, axes = plt.subplots(2, 2, figsize=(20, 12))

# 1. Historical vs Forecast (Daily)
ax1 = axes[0, 0]
# Plot last 90 days of historical data
recent_historical = daily_data.tail(90)
ax1.plot(recent_historical['Date'], recent_historical[target_col], 
         label='Historical (Last 90 days)', color='blue', linewidth=2)
ax1.plot(forecasted_data['Date'], forecasted_data['Predicted_Value'], 
         label='XGBoost Forecast (12 months)', color='red', linewidth=2, linestyle='--')
ax1.fill_between(forecasted_data['Date'], 
                forecasted_data['Confidence_Lower'], 
                forecasted_data['Confidence_Upper'], 
                alpha=0.2, color='red', label='Confidence Interval')
ax1.set_title('Daily Forecast: Historical vs Predicted', fontsize=14, fontweight='bold')
ax1.set_xlabel('Date')
ax1.set_ylabel(target_col)
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.tick_params(axis='x', rotation=45)

# 2. Monthly Aggregated Forecast
ax2 = axes[0, 1]
monthly_historical = daily_data.groupby(daily_data['Date'].dt.to_period('M'))[target_col].sum().tail(12)
ax2.bar(range(len(monthly_historical)), monthly_historical.values, 
        label='Historical (Last 12 months)', color='skyblue', alpha=0.7)
ax2.bar(range(len(monthly_historical), len(monthly_historical) + len(monthly_forecast)), 
        monthly_forecast['Predicted_Value'], 
        label='Forecasted (Next 12 months)', color='orange', alpha=0.7)
ax2.set_title('Monthly Forecast Comparison', fontsize=14, fontweight='bold')
ax2.set_xlabel('Month')
ax2.set_ylabel(f'Monthly {{target_col}}')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. Feature Importance
ax3 = axes[1, 0]
feature_importance = model.feature_importances_
top_features = sorted(zip(feature_columns, feature_importance), key=lambda x: x[1], reverse=True)[:10]
features, importances = zip(*top_features)
ax3.barh(range(len(features)), importances, color='green', alpha=0.7)
ax3.set_yticks(range(len(features)))
ax3.set_yticklabels(features)
ax3.set_title('Top 10 Feature Importance (XGBoost)', fontsize=14, fontweight='bold')
ax3.set_xlabel('Importance Score')
ax3.grid(True, alpha=0.3)

# 4. Forecast Distribution
ax4 = axes[1, 1]
ax4.hist(forecasted_data['Predicted_Value'], bins=30, color='purple', alpha=0.7, edgecolor='black')
ax4.axvline(forecasted_data['Predicted_Value'].mean(), color='red', linestyle='--', linewidth=2, 
        label=f'Mean: {{forecasted_data["Predicted_Value"].mean():.2f}}')
ax4.set_title('Distribution of Daily Forecasted Values', fontsize=14, fontweight='bold')
ax4.set_xlabel(f'Predicted {{target_col}}')
ax4.set_ylabel('Frequency')
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

============================
PROPHET ALGORITHM TEMPLATE
============================
- Use below code as template for prophet algorithm: 

import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import re

def detect_date_column(df):
    # Look for columns with datetime-like names or datetime types
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]':
            return col
        if 'date' in col.lower() or 'time' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
                return col
            except:
                continue
    raise ValueError("Could not find a valid date column.")

def detect_target_column(df, user_query):
    # Try to match column name from query
    user_query_lower = user_query.lower()
    for col in df.columns:
        if col.lower() in user_query_lower:
            if pd.api.types.is_numeric_dtype(df[col]):
                return col
    # Fallback: choose first numeric column
    numeric_cols = df.select_dtypes(include='number').columns
    if len(numeric_cols) > 0:
        return numeric_cols[0]
    raise ValueError("Could not find a numeric target column.")

def extract_periods(user_query):
    # Default to 12 months
    match = re.search(r'next (\d+)\s*(day|week|month|year)', user_query.lower())
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        freq_map = {
            'day': ('D', num),
            'week': ('W', num),
            'month': ('M', num),
            'year': ('Y', num)
        }
        return freq_map[unit]
    return 'M', 12  # Default: 12 months

def forecast_from_user_query(file_path, user_query):
    df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)

    # Detect columns
    date_col = detect_date_column(df)
    target_col = detect_target_column(df, user_query)
    freq, periods = extract_periods(user_query)

    df = df[[date_col, target_col]].dropna()
    df.rename(columns={date_col: 'ds', target_col: 'y'}, inplace=True)
    df['ds'] = pd.to_datetime(df['ds'])

    # Fit Prophet
    model = Prophet()
    model.fit(df)

    future = model.make_future_dataframe(periods=periods, freq=freq)
    forecast = model.predict(future)

    # Plot forecast
    model.plot(forecast)
    plt.title(f"Forecast for '{{target_col}}'")
    plt.grid(True)
    plt.show()

    # Plot components
    model.plot_components(forecast)
    plt.show()

    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)

============================
ARIMA/SARIMA/SARIMAX ALGORITHM TEMPLATE
============================
- Use below code as template for arima/sarima/sarimax algorithm:  

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import STL
from pandas.tseries.frequencies import to_offset

# 1. Detect the date column
def detect_date_column(df):
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]':
            return col
        if 'date' in col.lower() or 'time' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
                return col
            except:
                continue
    raise ValueError("No valid date column found.")

# 2. Detect the target column from query or numerics
def detect_target_column(df, query):
    query_lower = query.lower()
    for col in df.columns:
        if col.lower() in query_lower and pd.api.types.is_numeric_dtype(df[col]):
            return col
    numeric_cols = df.select_dtypes(include='number').columns
    if len(numeric_cols) > 0:
        return numeric_cols[0]
    raise ValueError("No numeric target column found.")

# 3. Detect forecast period and frequency
def extract_forecast_params(query):
    match = re.search(r'next (\d+)\s*(day|week|month|year)', query.lower())
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        freq_map = {
            'day': ('D', num),
            'week': ('W', num),
            'month': ('M', num),
            'year': ('Y', num)
        }
        return freq_map[unit]
    return 'M', 12  # default to 12 months

# 4. Detect if seasonality is present (for SARIMA)
def detect_seasonality(y, period):
    stl = STL(y, period=period)
    result = stl.fit()
    seasonal_strength = np.var(result.seasonal) / (np.var(result.seasonal) + np.var(result.resid))
    return seasonal_strength > 0.1  # Arbitrary threshold

# 5. Main ARIMA pipeline
def forecast_with_arima(file_path, user_query):
    df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
    date_col = detect_date_column(df)
    target_col = detect_target_column(df, user_query)
    freq, periods = extract_forecast_params(user_query)

    df[date_col] = pd.to_datetime(df[date_col])
    df = df[[date_col, target_col]].dropna()
    df.set_index(date_col, inplace=True)
    df = df.asfreq(to_offset(freq))
    y = df[target_col]

    # Check for seasonality
    seasonal = detect_seasonality(y, period=12 if freq in ['M', 'W'] else 7)

    if seasonal:
        print("Using SARIMA model (seasonal)")
        model = SARIMAX(y, order=(1,1,1), seasonal_order=(1,1,1,12), enforce_stationarity=False, enforce_invertibility=False)
    else:
        print("Using ARIMA model (no seasonality)")
        model = SARIMAX(y, order=(1,1,1), seasonal_order=(0,0,0,0))

    results = model.fit(disp=False)

    forecast = results.get_forecast(steps=periods)
    forecast_df = forecast.summary_frame()
    forecast_index = pd.date_range(start=y.index[-1] + to_offset(freq), periods=periods, freq=freq)
    forecast_df.index = forecast_index

    # Plot forecast
    plt.figure(figsize=(10, 5))
    plt.plot(y, label='Observed')
    plt.plot(forecast_df['mean'], label='Forecast')
    plt.fill_between(forecast_df.index, forecast_df['mean_ci_lower'], forecast_df['mean_ci_upper'], color='lightblue', alpha=0.4)
    plt.title(f"{'SARIMA' if seasonal else 'ARIMA'} Forecast of '{target_col}'")
    plt.legend()
    plt.grid(True)
    plt.show()

    return forecast_df[['mean', 'mean_ci_lower', 'mean_ci_upper']]

============================
LSTM ALGORITHM TEMPLATE
============================
- Use below code as template for lstm algorithm: 

import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, GRU, Dense
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping

def detect_date_column(df):
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]':
            return col
        if 'date' in col.lower() or 'time' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
                return col
            except:
                continue
    raise ValueError("No valid date column found.")

def detect_target_column(df, query):
    query = query.lower()
    for col in df.columns:
        if col.lower() in query and pd.api.types.is_numeric_dtype(df[col]):
            return col
    numeric_cols = df.select_dtypes(include='number').columns
    if len(numeric_cols) > 0:
        return numeric_cols[0]
    raise ValueError("No numeric target column found.")

def extract_forecast_params(query):
    match = re.search(r'next (\d+)\s*(day|week|month|year)', query.lower())
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        freq_map = {
            'day': ('D', num),
            'week': ('W', num * 7),
            'month': ('M', num * 30),
            'year': ('Y', num * 365)
        }
        return freq_map[unit]
    return 'D', 30  # default: next 30 days

def create_sequences(data, window_size):
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i+window_size])
        y.append(data[i+window_size])
    return np.array(X), np.array(y)

def forecast_with_lstm_or_gru(file_path, user_query, model_type='lstm', window_size=30):
    df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)

    date_col = detect_date_column(df)
    target_col = detect_target_column(df, user_query)
    freq, forecast_steps = extract_forecast_params(user_query)

    df[date_col] = pd.to_datetime(df[date_col])
    df.sort_values(by=date_col, inplace=True)
    df = df[[date_col, target_col]].dropna().set_index(date_col)
    df = df.asfreq(freq)

    data = df[target_col].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)

    # Create sequences
    X, y = create_sequences(data_scaled, window_size)
    X = X.reshape((X.shape[0], X.shape[1], 1))  # (samples, timesteps, features)

    # Build model
    model = Sequential()
    if model_type.lower() == 'gru':
        model.add(GRU(64, input_shape=(window_size, 1)))
    else:
        model.add(LSTM(64, input_shape=(window_size, 1)))
    model.add(Dense(1))
    model.compile(loss='mse', optimizer=Adam(learning_rate=0.001))
    model.fit(X, y, epochs=50, batch_size=16, verbose=0, callbacks=[EarlyStopping(patience=5)])

    # Forecast next values
    last_sequence = data_scaled[-window_size:].reshape(1, window_size, 1)
    forecast_scaled = []
    for _ in range(forecast_steps):
        pred = model.predict(last_sequence)[0][0]
        forecast_scaled.append(pred)
        last_sequence = np.append(last_sequence[:,1:,:], [[[pred]]], axis=1)

    forecast = scaler.inverse_transform(np.array(forecast_scaled).reshape(-1, 1)).flatten()

    # Build forecast DataFrame
    future_dates = pd.date_range(start=df.index[-1] + pd.Timedelta(1, unit=freq), periods=forecast_steps, freq=freq)
    forecast_df = pd.DataFrame({'ds': future_dates, 'forecast': forecast})

    # Plot forecast
    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df[target_col], label='History')
    plt.plot(forecast_df['ds'], forecast_df['forecast'], label='Forecast')
    plt.title(f"{model_type.upper()} Forecast for '{target_col}'")
    plt.legend()
    plt.grid(True)
    plt.show()

    return forecast_df


"""
        else:
            base_requirements = base_requirements
        
   
        # Check for stop signal before generating code
        self.check_stop_signal()
        
        self.emit_stream('status', "Generating analysis code...")
        
        # Get conversation context for AI
        context = self.conversation_history.get_context_for_ai()
        
        # Generate and execute the analysis code - Enhanced with context
        prompt_with_context = base_requirements + context
        
        # Check for stop signal before API call
        self.check_stop_signal()
        
        response = self.openai_client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "assistant",   "content": prompt_with_context}
            ],
        )
        
        generated_code = response.choices[0].message.content
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0].strip()
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0].strip()
        
        print(" Generated code:")
        print(generated_code)
        print("-" * 50)
        self.emit_stream('code', generated_code)
        
        # Check for stop signal before execution
        self.check_stop_signal()
        
        self.emit_stream('status', "Executing generated code...")
        result = self._execute_code_streaming(generated_code)
        
        # Process results to extract DataFrames
        dataframes_found = {}
        if result.get("success") and result.get("variables"):
            for var_name, var_value in result["variables"].items():
                if isinstance(var_value, pd.DataFrame):
                    dataframes_found[var_name] = var_value
                    print(f"Found DataFrame: {var_name} (Shape: {var_value.shape})")
                    
                    # Stream the dataframe data
                    self.emit_stream('dataframe', {
                        'name': var_name,
                        'shape': var_value.shape,
                        'columns': list(var_value.columns),
                        'preview': generate_tailwind_table(var_value),
                        'data': var_value.to_dict('records')[:100] if len(var_value) > 0 else []
                    })
        
        # Prepare the result
        analysis_result = {
            "query": user_query,
            "type": "dataframe_analysis",
            "request_type": data_request['type'],
            "generated_code": generated_code,
            "execution_result": result,
            "success": result.get("success", False),
            "is_forecasting": is_forecasting,
            "generated_images": self.generated_images.copy(),
            "dataframes": dataframes_found,
            "data_update_available": len(dataframes_found) > 0
        }
        
        # Show data updates if successful
        if result.get("success") and dataframes_found:
            print(f"\nAnalysis completed successfully!")
            print(f"📊 Generated {len(dataframes_found)} result DataFrames")
            self.emit_stream('success', f"Analysis completed successfully! Generated {len(dataframes_found)} result DataFrames")
            
            # Save the main result DataFrame
            main_df_name = list(dataframes_found.keys())[0]
            main_df = dataframes_found[main_df_name]
            
            if len(main_df) > 0:
                # Show preview
                self.show_data_preview(self.original_df, main_df)
                
                # Save for potential file update
                update_name = data_request['type'].replace('_', '-')
                saved_path = self.save_data_updates(main_df, update_name)
                analysis_result["saved_data_path"] = saved_path
                
                print(f"\n💡 NEXT STEPS:")
                print(f"   • Review the data updates above")
                print(f"   • Data saved to: {self.data_dir}")
                print(f"   • Use this data to update your original file")
                if is_forecasting:
                    print(f"   • Forecast data can be appended to extend your dataset")
        
        return analysis_result
    
    # Continue with the rest of the existing methods...
    # (All other methods remain the same from the original StreamingAnalyzer)
    
    def _execute_code_streaming(self, code: str) -> Dict[str, Any]:
        """Execute generated Python code with timeout and better error handling"""
        import sys
        import platform
        from contextlib import contextmanager
        
        @contextmanager
        def timeout_context(seconds):
            """Context manager for execution timeout - cross-platform"""
            if platform.system() != 'Windows':
                # Use signal-based timeout on Unix systems
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Code execution timed out after {seconds} seconds")
                
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)
                
                try:
                    yield
                finally:
                    signal.signal(signal.SIGALRM, old_handler)
                    signal.alarm(0)
            else:
                # Use threading-based timeout on Windows
                import threading
                import time
                
                timeout_occurred = threading.Event()
                
                def timeout_thread():
                    time.sleep(seconds)
                    timeout_occurred.set()
                
                timer = threading.Thread(target=timeout_thread)
                timer.daemon = True
                timer.start()
                
                try:
                    yield
                    if timeout_occurred.is_set():
                        raise TimeoutError(f"Code execution timed out after {seconds} seconds")
                finally:
                    timeout_occurred.set()  # Stop the timer
        
        try:
            # Check for stop signal before execution
            self.check_stop_signal()
            
            from scipy import stats
            
            # Set matplotlib to non-interactive mode and use Agg backend
            plt.switch_backend('Agg')
            plt.ioff()
            
            exec_globals = {
                'df': self.df,
                'pd': pd,
                'np': np,
                'plt': plt,
                'sns': sns,
                'json': json,
                'os': os,
                'warnings': warnings,
                'print': self._streaming_print,
                're': re,
                'stats': stats,
                'datetime': datetime,
                'timedelta': timedelta,
                'Path': Path,
                'images_dir': str(self.images_dir)
            }
            
            # Add sklearn libraries
            try:
                from sklearn.linear_model import LinearRegression
                from sklearn.model_selection import train_test_split
                from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
                from sklearn.preprocessing import StandardScaler, MinMaxScaler, PolynomialFeatures
                
                exec_globals.update({
                    'LinearRegression': LinearRegression,
                    'train_test_split': train_test_split,
                    'mean_squared_error': mean_squared_error,
                    'r2_score': r2_score,
                    'mean_absolute_error': mean_absolute_error,
                    'StandardScaler': StandardScaler,
                    'MinMaxScaler': MinMaxScaler,
                    'PolynomialFeatures': PolynomialFeatures
                })
            except ImportError as e:
                self.emit_stream('output', f" Some sklearn libraries not available: {e}")
            
            # Add statsmodels for time series
            try:
                import statsmodels.api as sm
                from statsmodels.tsa.arima.model import ARIMA
                from statsmodels.tsa.seasonal import seasonal_decompose
                from statsmodels.tsa.holtwinters import ExponentialSmoothing
                
                exec_globals.update({
                    'sm': sm,
                    'ARIMA': ARIMA,
                    'seasonal_decompose': seasonal_decompose,
                    'ExponentialSmoothing': ExponentialSmoothing
                })
            except ImportError:
                self.emit_stream('output', "Statsmodels not available. Install with: pip install statsmodels")
            
            # Add XGBoost
            try:
                import xgboost as xgb
                from xgboost import XGBRegressor
                exec_globals.update({'xgb': xgb, 'XGBRegressor': XGBRegressor})
            except ImportError:
                self.emit_stream('output', "XGBoost not available. Install with: pip install xgboost")
            
            self.emit_stream('status', "▶Executing code...")
            
            exec_locals = {}
            
            # Execute all code at once with timeout
            try:
                if platform.system() != 'Windows':
                    with timeout_context(120):  # 2 minute timeout for entire execution
                        exec(code, exec_globals, exec_locals)
                else:
                    # On Windows, execute without signal-based timeout
                    exec(code, exec_globals, exec_locals)
                    
            except TimeoutError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Code execution timed out"
                }
            except StopAnalysisException:
                raise  # Re-raise stop exception
            
            self.emit_stream('status', "Capturing visualizations...")
            
            # Capture images with timeout protection
            try:
                captured_images = self._capture_matplotlib_plots_streaming()
                plt.close('all')
            except Exception as img_error:
                self.emit_stream('output', f"Image capture failed: {img_error}")
                captured_images = []
                plt.close('all')
            
            # Result processing
            result_vars = {k: v for k, v in exec_locals.items() if not k.startswith('_')}
            
            return {
                "success": True,
                "output": "Code executed successfully!",
                "variables": result_vars,
                "captured_images": captured_images,
                "message": f"Execution completed successfully! Captured {len(captured_images)} images."
            }
            
        except StopAnalysisException:
            raise  # Re-raise stop exception
        except Exception as e:
            self.emit_stream('error', f"Execution failed: {str(e)}")
            # Ensure matplotlib is cleaned up even on error
            try:
                plt.close('all')
            except:
                pass
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "message": f"Execution failed: {str(e)}"
            }
    
    def _capture_matplotlib_plots_streaming(self) -> List[str]:
        """Capture any matplotlib plots that were created during code execution with streaming"""
        captured_images = []
        
        fig_nums = plt.get_fignums()
        
        for i, fig_num in enumerate(fig_nums):
            try:
                # Check for stop signal
                self.check_stop_signal()
                
                fig = plt.figure(fig_num)
                
                timestamp = datetime.now().strftime("%H%M%S")
                image_filename = f"plot_{timestamp}_{i+1}.png"
                image_path = self.images_dir / image_filename
                
                # Save the image
                fig.savefig(image_path, dpi=300, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
                
                public_url = self._upload_image_to_blob(str(image_path))
                if public_url:
                    captured_images.append(public_url)
                    self.generated_images.append(public_url)
                else:
                    captured_images.append(str(image_path))
                    self.generated_images.append(image_filename)
                
                # Convert to base64 and stream to frontend
                try:
                    with open(image_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                    
                    self.emit_stream('image', {
                        'filename': image_filename,
                        'data': f"data:image/png;base64,{img_data}",
                        'path': str(image_path),
                        'thisis': 2
                    })
                    
                    print(f"Saved and streamed plot: {image_filename}")
                    
                except Exception as stream_error:
                    print(f"Failed to stream image {image_filename}: {stream_error}")
                
            except StopAnalysisException:
                raise  # Re-raise stop exception
            except Exception as e:
                print(f"Failed to save plot {i+1}: {str(e)}")
        
        return captured_images
    
    def _generate_dataframe_analysis_streaming_with_fallback(self, user_query: str, data_request: Dict, is_forecasting: bool) -> Dict[str, Any]:
        """Enhanced version with automatic fallback on failure and stop checking"""
        
        # Check for stop signal
        self.check_stop_signal()
        
        # First, try the original generation logic
        original_result = self._generate_dataframe_analysis_streaming(user_query, data_request, is_forecasting)
        
        # If original execution was successful, return it
        if original_result.get("success"):
            return original_result
        
        # Check for stop signal before fallback
        self.check_stop_signal()
        
        # If original execution failed, trigger fallback
        self.emit_stream('warning', "Initial code generation failed. Attempting regeneration with error context...")
        
        failed_code = original_result.get("generated_code", "")
        error_message = original_result.get("execution_result", {}).get("error", "Unknown error")
        
        # Call the fallback function
        fallback_result = self._regenerate_code_with_fallback(
            user_query=user_query,
            data_request=data_request,
            is_forecasting=is_forecasting,
            failed_code=failed_code,
            error_message=error_message,
            max_retries=3
        )
        
        return fallback_result
    
    def _regenerate_code_with_fallback(self, user_query: str, data_request: Dict, is_forecasting: bool, 
                                   failed_code: str, error_message: str, max_retries: int = 2) -> Dict[str, Any]:
        """Fallback function to regenerate code when execution fails with stop checking"""
        
        self.emit_stream('status', f"Code execution failed. Attempting to regenerate...")
        
        # Check for stop signal
        self.check_stop_signal()
        
        # Create enhanced prompt with error context (keeping the original logic)
        error_context_prompt = f"""
    PREVIOUS ATTEMPT FAILED - PLEASE FIX THE ISSUES:

    ORIGINAL REQUEST: {user_query}
    REQUEST TYPE: {data_request['type']}

    FAILED CODE:
    ```python
    {failed_code}
    ```

    ERROR MESSAGE:
    {error_message}

    CRITICAL FIXES NEEDED:
    1. Analyze the error message above and fix the root cause
    2. Ensure all required libraries are properly imported
    3. Handle missing columns gracefully with proper error checking
    4. Use proper data type conversions and null handling
    5. Validate data structure before processing

    COMMON ERROR PATTERNS TO AVOID:
    - KeyError: Check if columns exist before accessing them
    - ValueError: Validate data types and handle conversion errors
    - IndexError: Check DataFrame length before indexing
    - AttributeError: Verify DataFrame methods and attributes exist
    - TypeError: Ensure proper data type matching

    FALLBACK STRATEGIES:
    - Use try-except blocks for risky operations
    - Provide alternative column names if primary ones don't exist
    - Use .get() method for dictionary-like access
    - Add data validation steps before processing
    - Include fallback methods if primary analysis fails
    """
        
        # Attempt regeneration with retries
        for attempt in range(max_retries):
            try:
                # Check for stop signal before each attempt
                self.check_stop_signal()
                
                self.emit_stream('status', f"Regeneration attempt {attempt + 1}/{max_retries}")
                
                # Generate new code with error context
                context = self.conversation_history.get_context_for_ai()
                prompt_with_context = error_context_prompt + context
                
                response = self.openai_client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": self._create_system_prompt()},
                        {"role": "user", "content": prompt_with_context}
                    ],
                )
                
                regenerated_code = response.choices[0].message.content
                if "```python" in regenerated_code:
                    regenerated_code = regenerated_code.split("```python")[1].split("```")[0].strip()
                elif "```" in regenerated_code:
                    regenerated_code = regenerated_code.split("```")[1].split("```")[0].strip()
                
                # print(f"Regenerated code (attempt {attempt + 1}):")
                print(regenerated_code)
                print("-" * 50)
                
                self.emit_stream('code', f"{regenerated_code}")
                
                # Check for stop signal before execution
                self.check_stop_signal()
                
                # Execute the regenerated code
                self.emit_stream('status', f"Executing regenerated code...")
                result = self._execute_code_streaming(regenerated_code)
                
                # If successful, process and return results
                if result.get("success"):
                    self.emit_stream('success', f"Code regeneration successful on attempt {attempt + 1}!")
                    
                    # Process results same as original function
                    dataframes_found = {}
                    if result.get("variables"):
                        for var_name, var_value in result["variables"].items():
                            if isinstance(var_value, pd.DataFrame):
                                dataframes_found[var_name] = var_value
                                print(f"Found DataFrame: {var_name} (Shape: {var_value.shape})")
                                
                                self.emit_stream('dataframe', {
                                    'name': var_name,
                                    'shape': var_value.shape,
                                    'columns': list(var_value.columns),
                                    'preview': generate_tailwind_table(var_value),
                                    'data': var_value.to_dict('records')[:100] if len(var_value) > 0 else []
                                })
                    
                    analysis_result = {
                        "query": user_query,
                        "type": "dataframe_analysis",
                        "request_type": data_request['type'],
                        "generated_code": regenerated_code,
                        "execution_result": result,
                        "success": True,
                        "is_forecasting": is_forecasting,
                        "generated_images": self.generated_images.copy(),
                        "dataframes": dataframes_found,
                        "data_update_available": len(dataframes_found) > 0,
                        "regenerated": True,
                        "regeneration_attempt": attempt + 1
                    }
                    
                    return analysis_result
                
                else:
                    # Update error message for next attempt
                    error_message = result.get("error", "Unknown error occurred")
                    failed_code = regenerated_code
                    self.emit_stream('error', f"Regeneration attempt {attempt + 1} failed: {error_message}")
                    continue
                    
            except StopAnalysisException:
                raise  # Re-raise stop exception
            except Exception as e:
                error_message = str(e)
                self.emit_stream('error', f"Regeneration attempt {attempt + 1} failed with exception: {error_message}")
                continue
        
        # If all retries failed, return failure result
        self.emit_stream('error', f"All regeneration attempts failed after {max_retries} tries")
        
        return {
            "query": user_query,
            "type": "dataframe_analysis",
            "request_type": data_request['type'],
            "generated_code": failed_code,
            "execution_result": {"success": False, "error": error_message},
            "success": False,
            "is_forecasting": is_forecasting,
            "generated_images": [],
            "dataframes": {},
            "data_update_available": False,
            "regenerated": False,
            "regeneration_failed": True,
            "final_error": error_message
        }
    
    def _generate_comprehensive_report_streaming(self, user_query: str, is_forecasting: bool) -> Dict[str, Any]:
        """Generate comprehensive report when specifically requested with stop checking"""
        print("\nGenerating comprehensive strategic report...")
        self.emit_stream('status', "Generating comprehensive strategic report...")
        
        try:
            # Check for stop signal
            self.check_stop_signal()
            
            # First run the analysis to get data
            data_request = self._extract_data_request(user_query)
            analysis_result = self._generate_dataframe_analysis_streaming_with_fallback(user_query, data_request, is_forecasting)
            
            if not analysis_result.get("success"):
                return {
                    "error": "Cannot generate report - analysis failed",
                    "type": "report_error"
                }
            
            # Check for stop signal
            self.check_stop_signal()
            
            self.emit_stream('status', "📝 Converting images and generating report...")
            
            # Convert all images to base64
            base64_images = self._convert_images_to_base64()
            print(f"Converted {len(base64_images)} images to base64")
            
            # Check for stop signal
            self.check_stop_signal()
            
            # Generate the report
            market_topic = self._extract_market_topic(user_query)
            target_variable = self._extract_target_variable(user_query)
            forecast_periods = self._extract_forecast_periods(user_query) if is_forecasting else 6
            
            # Prepare data context
            data_context = self._prepare_report_data_context(analysis_result, target_variable)
            
            report = self.generate_forecast_report(
                data_context=data_context,
                forecast_results=analysis_result,
                client_name="Executive Leadership Team",
                market_topic=market_topic,
                forecast_periods=forecast_periods,
                target_variable=target_variable,
            )
            
            # Stream the report to frontend
            self.emit_stream('report', report)
            
            analysis_result.update({
                "type": "comprehensive_report",
                "comprehensive_report": report,
                "report_generated": True,
                "market_topic": market_topic,
                "target_variable": target_variable,
                "forecast_periods": forecast_periods,
            })
            
            print("Comprehensive strategic report generated successfully!")
            self.emit_stream('success', "Comprehensive strategic report generated successfully!")
            
        except StopAnalysisException:
            raise  # Re-raise stop exception
        except Exception as report_error:
            print(f"⚠️ Report generation failed: {str(report_error)}")
            print(f"Traceback: {traceback.format_exc()}")
            self.emit_stream('error', f"Report generation failed: {str(report_error)}")
            analysis_result.update({
                "report_error": str(report_error),
                "report_generated": False,
                "type": "report_error"
            })
        
        return analysis_result
    
    def _convert_images_to_base64(self) -> Dict[str, str]:
        """Convert all generated images to base64 for HTML embedding."""
        base64_images = {}
        
        # Convert existing saved images
        for i, img_filename in enumerate(self.generated_images):
            try:
                # Check for stop signal
                self.check_stop_signal()
                
                img_path = self.images_dir / img_filename
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                        base64_images[f"image_{i+1}"] = img_data
                        print(f"Converted {img_filename} to base64")
            except StopAnalysisException:
                raise  # Re-raise stop exception
            except Exception as e:
                print(f"Failed to convert {img_filename}: {e}")
        
        # Also capture any currently open matplotlib figures
        fig_nums = plt.get_fignums()
        for i, fig_num in enumerate(fig_nums):
            try:
                # Check for stop signal
                self.check_stop_signal()
                
                fig = plt.figure(fig_num)
                buffer = BytesIO()
                fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                        facecolor='white', edgecolor='none')
                buffer.seek(0)
                img_data = base64.b64encode(buffer.read()).decode('utf-8')
                base64_images[f"figure_{i+1}"] = img_data
                buffer.close()
                print(f"Converted matplotlib figure {fig_num} to base64")
            except StopAnalysisException:
                raise  # Re-raise stop exception
            except Exception as e:
                print(f"Failed to convert figure {fig_num}: {e}")
        
        return base64_images


class StopAnalysisException(Exception):
    """Custom exception for stopping analysis"""
    pass


def generate_tailwind_table(df):
    """Generate a clean, theme-aware HTML table that works with your ThemeProvider"""
    import pandas as pd
    
    # Limit rows for performance
    display_df = df.head(100) if len(df) > 100 else df
    total_rows = len(df)
    
    html = f'''
    <div class="w-full space-y-4">
        <!-- Table Info Header -->
        <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 transition-all duration-300">
            <div class="flex items-center space-x-6">
                <div class="flex items-center space-x-2">
                    <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span class="text-sm font-medium text-gray-900 dark:text-white">
                        {total_rows:,} rows
                    </span>
                </div>
                <div class="flex items-center space-x-2">
                    <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span class="text-sm font-medium text-gray-900 dark:text-white">
                        {len(df.columns)} columns
                    </span>
                </div>
            </div>
            {f'<span class="text-xs px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">Showing first {len(display_df)} rows</span>' if total_rows > 100 else ''}
        </div>
        
        <!-- Table Container -->
        <div class="bg-white dark:bg-black rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden transition-all duration-300">
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead class="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                        <tr>
    '''
    
    # Add headers
    for col in df.columns:
        html += f'''
                            <th class="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">
                                {col}
                            </th>
        '''
    
    html += '''
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-gray-800">
    '''
    
    # Add rows
    for idx, row in display_df.iterrows():
        html += '''
                        <tr class="hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors duration-150">
        '''
        
        for val in row:
            # Format values based on type
            if pd.isna(val):
                formatted_val = '<span class="text-gray-400 dark:text-gray-500 italic">—</span>'
            elif isinstance(val, bool):
                if val:
                    formatted_val = '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">True</span>'
                else:
                    formatted_val = '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">False</span>'
            elif isinstance(val, (int, float)) and not isinstance(val, bool):
                # Format numbers
                if isinstance(val, float):
                    if abs(val) >= 1000000:
                        display_num = f'{val/1000000:.1f}M'
                    elif abs(val) >= 1000:
                        display_num = f'{val/1000:.1f}K'
                    else:
                        display_num = f'{val:.2f}'
                else:
                    if abs(val) >= 1000000:
                        display_num = f'{val/1000000:.1f}M'
                    elif abs(val) >= 1000:
                        display_num = f'{val/1000:.1f}K'
                    else:
                        display_num = f'{val:,}'
                
                formatted_val = f'<span class="font-mono text-gray-900 dark:text-white">{display_num}</span>'
            else:
                # String values
                str_val = str(val)
                if len(str_val) > 30:
                    formatted_val = f'<span class="text-gray-900 dark:text-white" title="{str_val}">{str_val[:27]}...</span>'
                else:
                    formatted_val = f'<span class="text-gray-900 dark:text-white">{str_val}</span>'
            
            html += f'''
                            <td class="px-6 py-4 text-sm whitespace-nowrap">
                                {formatted_val}
                            </td>
            '''
        
        html += '''
                        </tr>
        '''
    
    html += '''
                    </tbody>
                </table>
            </div>
        </div>
    '''
    
    # Add pagination info if needed
    if total_rows > 100:
        html += f'''
        <div class="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-200 dark:border-blue-800">
            <span class="text-sm text-blue-700 dark:text-blue-300">
                Showing {len(display_df)} of {total_rows:,} total rows
            </span>
        </div>
        '''
    
    html += '''
    </div>
    '''
    
    return html


def stop_analysis_for_session(session_id: str):
    """Set stop signal for a specific session"""
    global stop_signals
    stop_signals[session_id] = True
    print(f"🛑 Stop signal set for session: {session_id}")


def clear_stop_signal_for_session(session_id: str):
    """Clear stop signal for a specific session"""
    global stop_signals
    if session_id in stop_signals:
        stop_signals[session_id] = False
    print(f"✅ Stop signal cleared for session: {session_id}")


def cleanup_session_data(session_id: str, session_data: dict, analyzers: dict):
    """Clean up session data and resources"""
    deleted_items = []
    
    # Remove from analyzers
    if session_id in analyzers:
        # Clean up any file handles or resources
        analyzer = analyzers[session_id]
        if hasattr(analyzer, 'cleanup'):
            analyzer.cleanup()
        del analyzers[session_id]
        deleted_items.append('analyzer')
        print(f"🗑️  Deleted analyzer for session: {session_id}")
    
    # Remove from session data
    if session_id in session_data:
        # Optionally clean up uploaded files
        file_path = session_data[session_id].get('filepath')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_items.append('uploaded_file')
                print(f"🗑️  Deleted uploaded file: {file_path}")
            except Exception as e:
                print(f"⚠️  Could not delete file {file_path}: {e}")
        
        del session_data[session_id]
        deleted_items.append('session_data')
        print(f"🗑️  Deleted session data for: {session_id}")
    
    # Clear stop signals
    if session_id in stop_signals:
        del stop_signals[session_id]
        deleted_items.append('stop_signal')
        print(f"🗑️  Cleared stop signal for: {session_id}")
    
    return deleted_items

def cleanup_session_data_with_assistants(session_id: str, session_data: dict, analyzers: dict):
    """Enhanced cleanup that includes assistants resources"""
    deleted_items = []
    
    # Remove from analyzers with assistants cleanup
    if session_id in analyzers:
        analyzer = analyzers[session_id]
        
        # Enhanced cleanup for assistants
        if hasattr(analyzer, 'cleanup_assistants_resources'):
            try:
                analyzer.cleanup_assistants_resources()
                deleted_items.append('assistants_resources')
                print(f"🗑️ Cleaned up assistants resources for session: {session_id}")
            except Exception as e:
                print(f"⚠️ Error cleaning up assistants resources: {e}")
        
        # Original cleanup
        if hasattr(analyzer, 'cleanup'):
            try:
                analyzer.cleanup()
                deleted_items.append('analyzer_cleanup')
            except Exception as e:
                print(f"⚠️ Error in analyzer cleanup: {e}")
        
        del analyzers[session_id]
        deleted_items.append('analyzer')
        print(f"🗑️ Deleted enhanced analyzer for session: {session_id}")
    
    # Remove from session data
    if session_id in session_data:
        file_path = session_data[session_id].get('filepath')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_items.append('uploaded_file')
                print(f"🗑️ Deleted uploaded file: {file_path}")
            except Exception as e:
                print(f"⚠️ Could not delete file {file_path}: {e}")
        
        del session_data[session_id]
        deleted_items.append('session_data')
        print(f"🗑️ Deleted session data for: {session_id}")
    
    # Clear stop signals
    if session_id in stop_signals:
        del stop_signals[session_id]
        deleted_items.append('stop_signal')
        print(f"🗑️ Cleared stop signal for: {session_id}")
    
    return deleted_items

def is_session_inactive(session_info: dict, max_inactive_hours: float = 6.0) -> bool:
    """Check if a session is inactive based on last activity"""
    try:
        last_activity = session_info.get('last_activity', session_info.get('upload_time'))
        if not last_activity:
            return True
            
        last_activity_time = datetime.fromisoformat(last_activity)
        current_time = datetime.now()
        inactive_hours = (current_time - last_activity_time).total_seconds() / 3600
        
        return inactive_hours > max_inactive_hours
    except Exception as e:
        print(f"⚠️ Error checking session inactivity: {e}")
        return True  # Consider it inactive if we can't determine


def is_session_too_old(session_info: dict, max_age_hours: float = 24.0) -> bool:
    """Check if a session is too old based on upload time"""
    try:
        upload_time = session_info.get('upload_time')
        if not upload_time:
            return True
            
        upload_time_dt = datetime.fromisoformat(upload_time)
        current_time = datetime.now()
        age_hours = (current_time - upload_time_dt).total_seconds() / 3600
        
        return age_hours > max_age_hours
    except Exception as e:
        print(f"⚠️ Error checking session age: {e}")
        return True  # Consider it too old if we can't determine


def update_session_activity(session_id: str, session_data: dict):
    """Update last activity timestamp for a session"""
    if session_id in session_data:
        session_data[session_id]['last_activity'] = datetime.now().isoformat()
        return True
    return False


def get_session_stats(session_data: dict, analyzers: dict) -> dict:
    """Get comprehensive session statistics"""
    current_time = datetime.now()
    active_sessions = 0
    inactive_sessions = 0
    old_sessions = 0
    total_conversations = 0
    total_conversational = 0
    total_analytical = 0
    
    for session_id, session_info in session_data.items():
        # Check if session is active
        if is_session_inactive(session_info):
            inactive_sessions += 1
        else:
            active_sessions += 1
            
        # Check if session is old
        if is_session_too_old(session_info):
            old_sessions += 1
            
        # Count conversations
        if session_id in analyzers:
            history = analyzers[session_id].conversation_history.history
            total_conversations += len(history)
            
            # Count conversational vs analytical
            for conv in history:
                if conv.get('is_conversational', False):
                    total_conversational += 1
                else:
                    total_analytical += 1
    
    return {
        'total_sessions': len(session_data),
        'active_sessions': active_sessions,
        'inactive_sessions': inactive_sessions,
        'old_sessions': old_sessions,
        'total_conversations': total_conversations,
        'conversational_queries': total_conversational,
        'analytical_queries': total_analytical,
        'server_time': current_time.isoformat(),
        'analyzers_count': len(analyzers),
        'stop_signals_count': len(stop_signals)
    }


def validate_session_exists(session_id: str, analyzers: dict, session_data: dict) -> tuple[bool, str]:
    """Validate that a session exists and is properly initialized"""
    if not session_id:
        return False, "No session ID provided"
    
    if session_id not in analyzers:
        return False, f"Session {session_id} not found in analyzers"
    
    if session_id not in session_data:
        return False, f"Session {session_id} not found in session data"
    
    analyzer = analyzers[session_id]
    if analyzer.df is None:
        return False, f"Session {session_id} has no loaded data"
    
    return True, "Session is valid"


def create_session_summary(session_id: str, session_data: dict, analyzers: dict) -> dict:
    """Create a comprehensive session summary"""
    if session_id not in session_data or session_id not in analyzers:
        return {"error": "Session not found"}
    
    session_info = session_data[session_id]
    analyzer = analyzers[session_id]
    
    # Calculate session metrics
    current_time = datetime.now()
    upload_time = datetime.fromisoformat(session_info.get('upload_time', current_time.isoformat()))
    age_hours = (current_time - upload_time).total_seconds() / 3600
    
    last_activity = session_info.get('last_activity', session_info.get('upload_time'))
    last_activity_time = datetime.fromisoformat(last_activity)
    inactive_hours = (current_time - last_activity_time).total_seconds() / 3600
    
    # Get conversation history summary
    history_summary = analyzer.conversation_history.get_summary()
    
    return {
        'sessionId': session_id,
        'filename': session_info.get('filename'),
        'uploadTime': session_info.get('upload_time'),
        'lastActivity': last_activity,
        'ageHours': round(age_hours, 2),
        'inactiveHours': round(inactive_hours, 2),
        'shape': session_info.get('shape'),
        'columns': session_info.get('columns'),
        'conversationCount': len(analyzer.conversation_history.history),
        'createdBy': session_info.get('created_by', 'unknown'),
        'historySummary': history_summary,
        'isAnalyzing': getattr(analyzer, 'is_analyzing', False),
        'hasStopSignal': session_id in stop_signals and stop_signals[session_id],
        'langchainEnabled': getattr(analyzer.conversation_history, 'langchain_enabled', False)
    }


def generate_simple_table(df):
    """Generate a minimal, clean table for better theme compatibility"""
    import pandas as pd
    
    display_df = df.head(50) if len(df) > 50 else df
    
    html = f'''
    <div class="w-full">
        <div class="mb-4 text-sm text-gray-600 dark:text-gray-400">
            {len(df)} rows × {len(df.columns)} columns
        </div>
        
        <div class="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
            <table class="w-full bg-white dark:bg-black">
                <thead>
                    <tr class="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
    '''
    
    # Simple headers
    for col in df.columns:
        html += f'''
                        <th class="px-4 py-3 text-left text-sm font-medium text-gray-900 dark:text-white">
                            {col}
                        </th>
        '''
    
    html += '''
                    </tr>
                </thead>
                <tbody>
    '''
    
    # Simple rows
    for idx, row in display_df.iterrows():
        bg_class = "bg-white dark:bg-black" if idx % 2 == 0 else "bg-gray-50 dark:bg-gray-900"
        html += f'''
                    <tr class="{bg_class} hover:bg-gray-100 dark:hover:bg-gray-800 border-b border-gray-100 dark:border-gray-800">
        '''
        
        for val in row:
            if pd.isna(val):
                cell_content = '<span class="text-gray-400">—</span>'
            else:
                cell_content = str(val)
            
            html += f'''
                        <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">
                            {cell_content}
                        </td>
            '''
        
        html += '''
                    </tr>
        '''
    
    html += '''
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    return html