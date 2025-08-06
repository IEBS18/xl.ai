"""
Enhanced conversation management with AI conversational features and LangChain integration
"""
import json
import re
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

# LangChain imports - optional, will handle gracefully if not available
try:
    from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain_community.chat_models import AzureChatOpenAI
    from langchain_community.chat_message_histories import ChatMessageHistory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

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
    """Enhanced conversation history with LangChain integration and AI conversational features"""
    
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
            import os
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

class ConversationalManager:
    """Manages AI-powered conversational responses"""
    
    def __init__(self, openai_client, df: pd.DataFrame = None):
        self.openai_client = openai_client
        self.df = df
        self.MODEL = "gpt-4"  # Set your model here
    
    def is_casual_conversation(self, user_query: str) -> bool:
        """Detect if the query is casual conversation rather than data analysis"""
        query_lower = user_query.lower().strip()
        
        # Greeting patterns
        greeting_patterns = [
            r'^hi\b', r'^hello\b', r'^hey\b', r'^good\s+(morning|afternoon|evening)\b',
            r'^greetings\b', r'^howdy\b', r'^hiya\b', r'^sup\b', r'^wassup\b'
        ]
        
        # Casual conversation patterns
        casual_patterns = [
            r'how\s+(are\s+you|r\s+u)', r'what\'?s\s+up', r'how\s+do\s+you\s+do',
            r'nice\s+to\s+meet', r'pleasure\s+to\s+meet', r'good\s+to\s+see',
            r'^thanks?\b', r'^thank\s+you', r'^appreciate', r'^ty\b', r'^thx\b',
            r'^bye\b', r'^goodbye\b', r'^see\s+you', r'^take\s+care', r'^cya\b',
            r'who\s+are\s+you', r'what\s+are\s+you', r'tell\s+me\s+about\s+yourself',
            r'what\s+can\s+you\s+do', r'help\s+me\s+understand', r'how\s+does\s+this\s+work',
            r'what\s+is\s+this', r'explain\s+this\s+to\s+me', r'how\s+do\s+i\s+use',
            r'you\s+there', r'anyone\s+there', r'can\s+you\s+hear\s+me'
        ]
        
        # Check for greetings
        for pattern in greeting_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check for casual conversation
        for pattern in casual_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check if query is very short and non-analytical
        if len(query_lower.split()) <= 4:
            non_analytical_words = {
                'hi', 'hello', 'hey', 'thanks', 'thank', 'you', 'bye', 'goodbye',
                'yes', 'no', 'ok', 'okay', 'sure', 'fine', 'good', 'great',
                'awesome', 'cool', 'nice', 'wow', 'amazing', 'perfect', 'sup',
                'wassup', 'yo', 'hiya', 'howdy', 'thx', 'ty', 'cya'
            }
            query_words = set(query_lower.split())
            if query_words.issubset(non_analytical_words):
                return True
        
        # Data analysis keywords that indicate NOT casual conversation
        data_keywords = [
            'analyze', 'analysis', 'data', 'forecast', 'predict', 'trend', 'chart',
            'graph', 'plot', 'visualize', 'report', 'summary', 'calculate', 'show',
            'display', 'generate', 'create', 'find', 'search', 'filter', 'sort',
            'group', 'count', 'average', 'total', 'sum', 'correlation', 'revenue',
            'sales', 'profit', 'growth', 'performance', 'insight', 'pattern'
        ]
        
        # If query contains data analysis keywords, it's probably not casual
        if any(keyword in query_lower for keyword in data_keywords):
            return False
        
        return False

    def get_user_context(self, conversation_history=None) -> str:
        """Get contextual information about the user's session"""
        context_parts = []
        
        # Data context
        if self.df is not None:
            context_parts.append(f"User has a dataset loaded with {self.df.shape[0]:,} rows and {self.df.shape[1]} columns")
            
            # Add column information
            if hasattr(self.df, 'columns'):
                numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    context_parts.append(f"Dataset contains numeric columns like: {', '.join(numeric_cols[:3])}")
                
                # Check for date columns
                date_cols = [col for col in self.df.columns if 'date' in col.lower() or 'time' in col.lower()]
                if date_cols:
                    context_parts.append(f"Dataset has time-series data with date columns: {', '.join(date_cols[:2])}")
        else:
            context_parts.append("No dataset uploaded yet")
        
        # Conversation history context
        if conversation_history and hasattr(conversation_history, 'history'):
            total_interactions = len(conversation_history.history)
            successful_analyses = sum(1 for h in conversation_history.history if h.get('success', False))
            
            if total_interactions > 0:
                context_parts.append(f"This is interaction #{total_interactions + 1} in the session")
                if successful_analyses > 0:
                    context_parts.append(f"Have completed {successful_analyses} successful analyses together")
            
            # Recent conversation context
            if total_interactions > 0:
                recent = conversation_history.history[-1]
                if recent.get('response_type'):
                    context_parts.append(f"Last interaction was: {recent['response_type']}")
        
        return "; ".join(context_parts) if context_parts else "New session starting"

    def generate_ai_conversational_response(self, user_query: str, conversation_history=None) -> str:
        """Generate natural conversational response using AI with enhanced context"""
        try:
            # Get comprehensive context
            user_context = self.get_user_context(conversation_history)
            
            # Determine conversation type for better prompting
            query_lower = user_query.lower().strip()
            conversation_type = "general"
            
            if any(greet in query_lower for greet in ['hi', 'hello', 'hey', 'sup']):
                conversation_type = "greeting"
            elif any(how in query_lower for how in ['how are you', 'how r u']):
                conversation_type = "wellbeing_check"
            elif any(thanks in query_lower for thanks in ['thanks', 'thank you', 'thx']):
                conversation_type = "gratitude"
            elif any(bye in query_lower for bye in ['bye', 'goodbye', 'see you', 'cya']):
                conversation_type = "farewell"
            elif any(identity in query_lower for identity in ['who are you', 'what are you']):
                conversation_type = "identity_question"
            elif any(capability in query_lower for capability in ['what can you do', 'help me', 'how does this work']):
                conversation_type = "capability_inquiry"
            
            # Create context-aware prompt
            conversational_prompt = f"""You are a friendly, enthusiastic AI data analyst assistant. You love helping people discover insights from their data.

CONVERSATION TYPE: {conversation_type}
USER MESSAGE: "{user_query}"
SESSION CONTEXT: {user_context}

PERSONALITY TRAITS:
- Friendly and approachable, like talking to a helpful colleague
- Enthusiastic about data and insights
- Professional but not formal or robotic
- Encouraging and supportive
- Sometimes use light emojis (1-2 max)

RESPONSE GUIDELINES:
- Keep responses brief (1-3 sentences max)
- Be natural and conversational
- Reference the session context when relevant
- Always be helpful and encouraging
- End with an offer to help when appropriate

EXAMPLES OF GOOD RESPONSES:
- Greeting: "Hey! Great to see you back. Ready to dive into some data magic? ✨"
- First time greeting: "Hi there! I'm excited to help you explore your data. What insights are we hunting for today?"
- How are you: "I'm fantastic and ready to crunch some numbers! How can I help you unlock insights from your data?"
- Thanks: "You're absolutely welcome! I love helping with data puzzles. What else can we discover together?"
- With loaded data: "Hey! I see you've got that {self.df.shape[0]:,} row dataset ready. What story should we uncover from it?" if self.df is not None else "Hi there! Ready to upload some data and discover insights?"

Generate a natural, context-aware response (don't include quotes in your response):"""

            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a friendly, enthusiastic AI data analyst. Respond naturally and conversationally. Never include quotes around your response."
                    },
                    {"role": "user", "content": conversational_prompt}
                ],
                max_tokens=120,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Clean up any quotes or formatting artifacts
            ai_response = ai_response.replace('"', '').replace("'", "'")
            if ai_response.startswith("Response: "):
                ai_response = ai_response[10:]
            
            return ai_response
            
        except Exception as e:
            print(f"⚠️ AI conversational response failed: {e}")
            # Enhanced fallback responses with more personality
            query_lower = user_query.lower().strip()
            
            fallback_responses = {
                'greeting': [
                    "Hey there! 😊 Ready to dive into some data insights?",
                    "Hi! Great to see you. What data mysteries should we solve today?",
                    "Hello! I'm excited to help you discover what your data has to say!"
                ],
                'wellbeing': [
                    "I'm doing fantastic, thanks! Ready to turn your data into gold. How can I help?",
                    "Great, thanks for asking! I'm pumped up and ready for some serious data analysis. What's on your mind?",
                    "I'm excellent! Nothing makes me happier than helping with data insights. What shall we explore?"
                ],
                'thanks': [
                    "You're very welcome! Happy to help anytime. Got more data questions?",
                    "My pleasure! I love solving data puzzles. What else can we discover?",
                    "Absolutely! That's what I'm here for. Ready for the next challenge?"
                ],
                'bye': [
                    "Take care! Come back anytime you need data insights. 👋",
                    "See you later! I'll be here whenever you need to unlock more data secrets!",
                    "Goodbye! Thanks for letting me help with your data journey. Until next time! ✨"
                ]
            }
            
            # Choose appropriate fallback
            if any(greet in query_lower for greet in ['hi', 'hello', 'hey']):
                return np.random.choice(fallback_responses['greeting'])
            elif 'how are you' in query_lower:
                return np.random.choice(fallback_responses['wellbeing'])
            elif any(thanks in query_lower for thanks in ['thanks', 'thank you']):
                return np.random.choice(fallback_responses['thanks'])
            elif any(bye in query_lower for bye in ['bye', 'goodbye']):
                return np.random.choice(fallback_responses['bye'])
            else:
                return "I'm here to help! What would you like to explore in your data? 🚀"

    def handle_no_data_query(self, user_query: str) -> Dict[str, Any]:
        """Handle queries when no data is uploaded using AI with personality"""
        try:
            guidance_prompt = f"""The user said: "{user_query}"

They don't have any data uploaded yet, but they seem interested in data analysis.

You are a friendly, helpful AI data analyst. Generate a response that:
- Acknowledges what they want to do
- Gently explains they need to upload data first  
- Makes it sound easy and exciting
- Suggests what they can do once they upload
- Keep it encouraging and brief (2-3 sentences max)
- Use 1-2 emojis to keep it friendly
- Don't use quotes in your response

Be conversational and enthusiastic like you're talking to a friend who's about to discover something cool.

Generate response:"""

            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are an enthusiastic, helpful AI data analyst. Be encouraging and friendly."},
                    {"role": "user", "content": guidance_prompt}
                ],
                max_tokens=100,
                temperature=0.6
            )
            
            ai_response = response.choices[0].message.content.strip()
            ai_response = ai_response.replace('"', '').replace("'", "'")
            
            return {
                "query": user_query,
                "type": "guidance_response", 
                "success": False,
                "response": ai_response,
                "error": "No CSV file loaded. Please load a CSV first."
            }
            
        except Exception as e:
            print(f"⚠️ AI guidance response failed: {e}")
            return {
                "query": user_query,
                "type": "guidance_response", 
                "success": False,
                "response": "I'd love to help with that! 📊 Just upload your CSV or Excel file first, then we can dive into some amazing insights together!",
                "error": "No CSV file loaded. Please load a CSV first."
            }