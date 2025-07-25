
try:
    import eventlet
    eventlet.monkey_patch()
    EVENTLET_AVAILABLE = True
    print("✅ Eventlet monkey patch applied successfully")
except ImportError:
    EVENTLET_AVAILABLE = False
    print("⚠️  Eventlet not available, using threading mode")
except Exception as e:
    EVENTLET_AVAILABLE = False
    print(f"⚠️  Eventlet monkey patch failed: {e}")
    print("   Continuing with threading mode...")

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

from flask import Flask, render_template, request, jsonify, session, send_file, Response
from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# Import your existing analyzer
from test2 import QuadraticCSVAnalyzer
from dotenv import load_dotenv

from auth import auth_blueprint, init_db

import requests
import tempfile

# GOTENBERG_URL = "http://localhost:3000/forms/chromium/convert/html"

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

GOTENBERG_URL=os.getenv('GOTENBERG_URL')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

app.register_blueprint(auth_blueprint, url_prefix='/auth')

# Initialize database on startup
try:
    init_db()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️  Database initialization failed: {e}")
    print("   Auth features may not work properly")

# Comprehensive CORS configuration for multiple frontend sources
allowed_origins = [
    "http://localhost:5173", 
    "http://localhost", 
    "http://127.0.0.1:5173",
    "https://preview--data-scope-ai-lens.lovable.app",
    "https://*.lovable.app",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://20.197.12.172"
]

CORS(app, origins=allowed_origins, supports_credentials=True)

# Initialize SocketIO with robust configuration
async_mode = 'eventlet' if EVENTLET_AVAILABLE else 'threading'

socketio = SocketIO(
    app, 
    cors_allowed_origins=allowed_origins,
    async_mode=async_mode,
    transports=['polling', 'websocket'],
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25
)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global storage for analyzer instances per session
analyzers = {}
session_data = {}


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
    """Enhanced conversation history with LangChain integration - KEEPING ALL EXISTING METHODS"""
    
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
    
    # ... rest of the existing methods remain unchanged ...
    
    def load_history(self):
        """Load conversation history from file if it exists - UNCHANGED METHOD"""
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
        """Save conversation history to file - UNCHANGED METHOD"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Could not save conversation history: {e}")
    
    def add_conversation(self, user_query: str, response: Dict[str, Any]):
        """Add a new conversation to history - ENHANCED BUT UNCHANGED SIGNATURE"""
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
        """Get recent conversation context for AI - ENHANCED BUT UNCHANGED SIGNATURE"""
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
        """Get session summary - ENHANCED BUT UNCHANGED SIGNATURE"""
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
        """Calculate session duration - UNCHANGED METHOD"""
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


class StreamingAnalyzer(QuadraticCSVAnalyzer):
    """Extended analyzer with streaming capabilities for Flask integration."""
    
    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id
        self.streaming_outputs = []
        self.conversation_history = ConversationHistory(session_id, self.output_dir)
        
        # Initialize simple memory - no need for complex chat history initialization
        self.memory = None  # Will be set up later if needed
    
    def emit_stream(self, message_type, data):
        """Emit streaming data to the frontend."""
        try:
            socketio.emit('stream_data', {
                'type': message_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            if EVENTLET_AVAILABLE:
                socketio.sleep(0.05)  # Small delay for smooth streaming
            else:
                time.sleep(0.05)
        except Exception as e:
            print(f"Error emitting stream: {e}")
        
    def analyze_query_streaming(self, user_query: str):
        """Enhanced analyze_query with real-time streaming that matches original behavior EXACTLY."""
        if self.df is None:
            self.emit_stream('error', "No CSV file loaded. Please upload a CSV first.")
            return {"error": "No CSV file loaded. Please load a CSV first."}

        try:
            # announce incoming query
            self.emit_stream('status', f"🤖 Analyzing query: {user_query}")

            # reset per‑query state
            self.generated_images = []
            self.streaming_outputs = []

            # decide path
            is_report_request = self._is_report_request(user_query)
            data_request      = self._extract_data_request(user_query)
            is_forecasting   = any(
                kw in user_query.lower()
                for kw in ['forecast','predict','future','next','ahead','months','years','projection']
            )

            if is_report_request:
                self.emit_stream('status', "📋 Generating comprehensive report…")
                # make sure your helper signature matches these args!
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

            # record in history
            self.conversation_history.add_conversation(user_query, result)
            return result

        except Exception as e:
            # capture full traceback
            full_trace = traceback.format_exc()
            error_msg  = f"Error analyzing query:\n{full_trace}"
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

VISUALIZATION REQUIREMENTS (MANDATORY):
- ALWAYS create at least one chart for every analysis
- Use Bar charts for comparisons, categories, rankings
- Use Line charts for trends, time series, forecasting
- Use Pie charts for revenue/profit breakdowns by category/SKU
- Save all plots using plt.savefig() and plt.show()
- Include proper titles, labels, and legends

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
 
CSV Data Context:
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
"""    
    
    def _generate_dataframe_analysis_streaming(self, user_query: str, data_request: Dict, is_forecasting: bool) -> Dict[str, Any]:
        """Generate analysis focused on returning actionable DataFrame results - EXACT COPY from test2.py"""
       
        # Enhanced prompt for DataFrame-focused analysis - EXACT COPY from test2.py
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
            enhanced_prompt = base_requirements + f"""
FORECASTING-SPECIFIC REQUIREMENTS:
- Create a separate DataFrame with future predictions
- Target variable are to be choose betweeen revenue, sales, units sold, quantity and similar data. 
- Never drop the Date column. 
- Always first run the xgBoost algorithm{{given below in example}}for forecasting or prediction then go with the user suggested model if any
- Include future dates beyond the last date in dataset
- Provide confidence intervals or prediction ranges
- Return forecasted_data_df with columns: [Date, Predicted_Value, Confidence_Lower, Confidence_Upper]
- Show both historical trend analysis and future predictions

FORECASTING OUTPUT:
- Original data with trend indicators added
- Separate forecast DataFrame for future periods
- Combined visualization showing historical + predicted
- Viuslaisation must be in Line or Bar charts for forecating and predictions

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

 
2. AUTOREGRESSIVE (AR) MODELS:
```
Pseudo-code:
1. AR(p): y_t = c + φ₁*y_{{t-1}} + φ₂*y_{{t-2}} + ... + φ_p*y_{{t-p}} + ε_t
2. For forecasting:
   - Use last p values to predict next value
   - Recursively use predictions to forecast multiple periods ahead
3. Implementation: Use statsmodels.tsa.ar_model.AutoReg
```
 
3. ARIMA FORECASTING:
```
Pseudo-code:
1. ARIMA(p,d,q): Combines AR(p) + Integration(d) + MA(q)
2. Auto-detect parameters using auto_arima or AIC/BIC
3. For forecasting:
   - model.fit(historical_data)
   - forecast = model.forecast(steps=forecast_periods)
4. Implementation: Use statsmodels.tsa.arima.ARIMA
```
 
4. XGBOOST TIME SERIES FORECASTING:
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
 
5. LSTM NEURAL NETWORK FORECASTING:
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
 
STEP 3: FUTURE DATE GENERATION
```python
def generate_future_dates(last_date, periods, frequency):
    \"\"\"Generate future dates beyond the dataset\"\"\"
    if frequency == 'D':
        return pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods, freq='D')
    elif frequency == 'W':
        return pd.date_range(start=last_date + pd.Timedelta(weeks=1), periods=periods, freq='W')
    elif frequency == 'M':
        return pd.date_range(start=last_date + pd.DateOffset(months=1), periods=periods, freq='M')
    elif frequency == 'Y':
        return pd.date_range(start=last_date + pd.DateOffset(years=1), periods=periods, freq='Y')
   
# Usage example:
last_historical_date = df[date_col].max()
future_dates = generate_future_dates(last_historical_date, forecast_periods, frequency)
print(f"Historical data ends: {{last_historical_date}}")
print(f"Forecasting from: {{future_dates[0]}} to {{future_dates[-1]}}")
```
 
CRITICAL EXECUTION REQUIREMENTS
===============================================
 
1. ALWAYS use the variable 'df' to reference the loaded DataFrame - NEVER use pd.read_csv()
2. ALWAYS start with data exploration: df.info(), df.head(), column analysis
3. ALWAYS generate future dates that come AFTER the last date in the dataset
4. ALWAYS implement multiple forecasting models for comparison
5. ALWAYS use recursive/iterative prediction for multi-step ahead forecasting
6. ALWAYS create visualizations showing clear separation between historical and forecasted data
7. ALWAYS provide forecast summary statistics and comparison tables
8. ALWAYS include proper error handling with fallback models
9. ALWAYS validate that forecasted dates are in the future, not historical
 
DATA CLEANING RULES:
- Always clean string data before converting to numeric: .astype(str).str.replace(',', '').str.strip()
- Handle empty strings and spaces: replace with np.nan or 0
- Use pd.to_numeric(errors='coerce') for safe conversion
- Check for object dtype columns that should be numeric
- Remove or skip completely empty columns (like 'Unnamed' columns)
 
FORECASTING VALIDATION CHECKLIST:
✓ Historical data used for training only
✓ Future dates generated beyond dataset range  
✓ Multiple models implemented and compared
✓ Recursive forecasting for multi-step predictions
✓ Proper data cleaning and preprocessing
✓ Clear visualization with historical vs forecasted data
✓ Summary statistics and model comparison
✓ Error handling with fallback options
 
Remember: Forecasting means predicting the FUTURE, not explaining the past!
"""
        else:
            enhanced_prompt = base_requirements + f"""
ANALYSIS-SPECIFIC REQUIREMENTS:
- Add calculated fields to enhance business insights
- Create performance metrics, rankings, or categorizations  
- Generate trend indicators and growth rates
- Provide statistical measures as new columns
- Focus on actionable business intelligence

ANALYSIS OUTPUT:
- Enhanced DataFrame with new calculated columns
- Summary statistics as additional rows/columns
- Category-wise metrics and comparisons
- Data quality indicators and flags
"""
        
        self.emit_stream('status', "🤖 Generating analysis code...")
        
        # Get conversation context for AI
        context = self.conversation_history.get_context_for_ai()
        
        # Generate and execute the analysis code - Enhanced with context
        prompt_with_context = enhanced_prompt + context
        
        response = self.openai_client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user",   "content": prompt_with_context}
            ],
            # temperature=0.1,
        )
        
        generated_code = response.choices[0].message.content
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0].strip()
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0].strip()
        
        print("📝 Generated code:")
        print(generated_code)
        print("-" * 50)
        self.emit_stream('code', generated_code)
        
        self.emit_stream('status', "⚡ Executing generated code...")
        result = self._execute_code_streaming(generated_code)
        
        # Process results to extract DataFrames - EXACT COPY from test2.py
        dataframes_found = {}
        if result.get("success") and result.get("variables"):
            for var_name, var_value in result["variables"].items():
                if isinstance(var_value, pd.DataFrame):
                    dataframes_found[var_name] = var_value
                    print(f"📊 Found DataFrame: {var_name} (Shape: {var_value.shape})")
                    
                    # Stream the dataframe data
                    self.emit_stream('dataframe', {
                        'name': var_name,
                        'shape': var_value.shape,
                        'columns': list(var_value.columns),
                        'preview': generate_tailwind_table(var_value),
                        'data': var_value.to_dict('records')[:100] if len(var_value) > 0 else []
                    })
        
        # Prepare the result - EXACT COPY from test2.py
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
        
        # Show data updates if successful - EXACT COPY from test2.py
        if result.get("success") and dataframes_found:
            print(f"\n✅ Analysis completed successfully!")
            print(f"📊 Generated {len(dataframes_found)} result DataFrames")
            self.emit_stream('success', f"✅ Analysis completed successfully! Generated {len(dataframes_found)} result DataFrames")
            
            # Save the main result DataFrame - EXACT COPY from test2.py
            main_df_name = list(dataframes_found.keys())[0]
            main_df = dataframes_found[main_df_name]
            
            if len(main_df) > 0:
                # Show preview - EXACT COPY from test2.py
                self.show_data_preview(self.original_df, main_df)
                
                # Save for potential file update - EXACT COPY from test2.py
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
            
            # Add sklearn libraries - EXACT COPY from test2.py
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
                self.emit_stream('output', f"⚠️ Some sklearn libraries not available: {e}")
            
            # Add statsmodels for time series - EXACT COPY from test2.py
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
                self.emit_stream('output', "⚠️ Statsmodels not available. Install with: pip install statsmodels")
            
            # Add XGBoost - EXACT COPY from test2.py
            try:
                import xgboost as xgb
                from xgboost import XGBRegressor
                exec_globals.update({'xgb': xgb, 'XGBRegressor': XGBRegressor})
            except ImportError:
                self.emit_stream('output', "⚠️ XGBoost not available. Install with: pip install xgboost")
            
            self.emit_stream('status', "▶️ Executing code...")
            
            exec_locals = {}
            
            # Execute with timeout (reduced to 60 seconds for faster response)
            try:
                if platform.system() != 'Windows':
                    with timeout_context(60):  # 1 minute timeout on Unix
                        exec(code, exec_globals, exec_locals)
                else:
                    # On Windows, execute without signal-based timeout
                    exec(code, exec_globals, exec_locals)
            except TimeoutError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"❌ Code execution timed out after 1 minute"
                }
            
            self.emit_stream('status', "📸 Capturing visualizations...")
            
            # Capture images with timeout protection
            try:
                captured_images = self._capture_matplotlib_plots_streaming()
                plt.close('all')
            except Exception as img_error:
                self.emit_stream('output', f"⚠️ Image capture failed: {img_error}")
                captured_images = []
                plt.close('all')
            
            # EXACT same result processing as original - EXACT COPY from test2.py
            result_vars = {k: v for k, v in exec_locals.items() if not k.startswith('_')}
            
            return {
                "success": True,
                "output": "Code executed successfully!",
                "variables": result_vars,
                "captured_images": captured_images,
                "message": f"✅ Execution completed successfully! Captured {len(captured_images)} images."
            }
            
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
                "message": f"❌ Execution failed: {str(e)}"
            }

    def _regenerate_code_with_fallback(self, user_query: str, data_request: Dict, is_forecasting: bool, 
                                   failed_code: str, error_message: str, max_retries: int = 2) -> Dict[str, Any]:
        """
    Fallback function to regenerate code when execution fails
    """
        
        self.emit_stream('status', f"🔄 Code execution failed. Attempting to regenerate...")
        print("fai;ed code:", failed_code)
        # Create enhanced prompt with error context
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

    MANDATORY ERROR HANDLING TEMPLATE:
    ```python
    try:
        # Your main analysis code here
        pass
    except KeyError as e:
        print(f"⚠️ Column not found: {{e}}. Available columns: {{df.columns.tolist()}}")
        # Provide alternative approach
    except ValueError as e:
        print(f"⚠️ Data conversion error: {{e}}")
        # Handle data type issues
    except Exception as e:
        print(f"⚠️ Unexpected error: {{e}}")
        # Provide minimal fallback result
    ```

    ENHANCED REQUIREMENTS:
    """
        
        # Add the original requirements based on forecasting or analysis
        if is_forecasting:
            error_context_prompt += """
    FORECASTING-SPECIFIC ERROR FIXES:
    - Ensure date columns are properly identified and converted
    - Handle missing or invalid date formats
    - Keep in mind that never to drop Date, Datetime columns
    - Validate that target columns contain numeric data
    - Provide fallback if advanced models fail (use simple moving average)
    - Generate future dates correctly beyond the dataset range

    FORECASTING FALLBACK HIERARCHY:
    1. Primary: Advanced models (ARIMA, SARIMA,EMA, FBProphet etc.)
    2. Secondary: Linear regression with time trend
    3. Tertiary: Moving averages (simple, exponential)
    4. Fallback: Last known value with trend adjustment

    FORECASTING ERROR HANDLING:
    ```python
    # Always include this forecasting fallback
    try:
        # Advanced forecasting code
        pass
    except Exception as e:
        print(f"⚠️ Advanced forecasting failed: {e}")
        print("🔄 Falling back to simple moving average...")
        
        # Simple fallback forecasting
        window_size = min(12, len(df) // 4)
        last_values = df[target_col].tail(window_size)
        simple_forecast = last_values.mean()
        
        # Create simple forecast DataFrame
        forecast_df = pd.DataFrame({
            'Date': future_dates,
            'Predicted_Value': [simple_forecast] * len(future_dates),
            'Confidence_Lower': [simple_forecast * 0.9] * len(future_dates),
            'Confidence_Upper': [simple_forecast * 1.1] * len(future_dates)
        })
    ```
    """
        else:
            error_context_prompt += """
    ANALYSIS-SPECIFIC ERROR FIXES:
    - Validate column existence before calculations
    - Handle mixed data types in columns
    - Provide alternative metrics if primary ones fail
    - Use robust statistical methods that handle outliers
    - Include data quality checks

    ANALYSIS FALLBACK HIERARCHY:
    1. Primary: Advanced calculated metrics
    2. Secondary: Basic statistical measures, Use simpler algortihms as SARIMA and ARIMA
    3. Tertiary: Simple aggregations
    4. Fallback: Data structure summary

    ANALYSIS ERROR HANDLING:
    ```python
    # Always include this analysis fallback
    try:
        # Advanced analysis code
        pass
    except Exception as e:
        print(f"⚠️ Advanced analysis failed: {e}")
        print("🔄 Falling back to basic analysis...")
        
        # Simple fallback analysis
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            # Create basic summary
            summary_df = df[numeric_cols].describe()
            print("📊 Basic statistical summary:")
            print(summary_df)
        else:
            print("⚠️ No numeric columns found for analysis")
    ```
    """
        
        # Add data exploration requirements
        error_context_prompt += """
    MANDATORY DATA EXPLORATION (Always include this first):
    ```python
    print("=== DEBUGGING DATA STRUCTURE ===")
    print(f"DataFrame shape: {df.shape}")
    print(f"Column names: {df.columns.tolist()}")
    print(f"Data types: {df.dtypes}")
    print(f"Missing values: {df.isnull().sum()}")
    print(f"Sample data:")
    print(df.head())

    # Check for object columns that might be numeric
    object_cols = df.select_dtypes(include=['object']).columns
    for col in object_cols:
        print(f"Column '{col}' sample values: {df[col].dropna().head().tolist()}")
    ```

    FINAL REQUIREMENTS:
    - Always start with data exploration
    - Use robust error handling throughout
    - Provide meaningful fallback options
    - Test column existence before use
    - Return results even if primary analysis fails
    - Include clear error messages and solutions
    - If no code works then generate the code for SARIMA/ARIMA code 
    """
    
    # Attempt regeneration with retries
        for attempt in range(max_retries):
            try:
                self.emit_stream('status', f"🔄 Regeneration attempt {attempt + 1}/{max_retries}")
                
                # Generate new code with error context
                # Include conversation context for better error fixing
                context = self.conversation_history.get_context_for_ai()
                prompt_with_context = error_context_prompt + context
                
                response = self.openai_client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": self._create_system_prompt()},
                        {"role": "user", "content": prompt_with_context}
                    ],
                    # temperature=0.2,  # Slightly higher temperature for more creative error solutions
                )
                
                regenerated_code = response.choices[0].message.content
                if "```python" in regenerated_code:
                    regenerated_code = regenerated_code.split("```python")[1].split("```")[0].strip()
                elif "```" in regenerated_code:
                    regenerated_code = regenerated_code.split("```")[1].split("```")[0].strip()
                
                print(f"🔄 Regenerated code (attempt {attempt + 1}):")
                print(regenerated_code)
                print("-" * 50)
                
                self.emit_stream('code', f"Regenerated code (attempt {attempt + 1}):\n{regenerated_code}")
                
                # Execute the regenerated code
                self.emit_stream('status', f"⚡ Executing regenerated code...")
                result = self._execute_code_streaming(regenerated_code)
                
                # If successful, process and return results
                if result.get("success"):
                    self.emit_stream('success', f"✅ Code regeneration successful on attempt {attempt + 1}!")
                    
                    # Process results same as original function
                    dataframes_found = {}
                    if result.get("variables"):
                        for var_name, var_value in result["variables"].items():
                            if isinstance(var_value, pd.DataFrame):
                                dataframes_found[var_name] = var_value
                                print(f"📊 Found DataFrame: {var_name} (Shape: {var_value.shape})")
                                
                                self.emit_stream('dataframe', {
                                    'name': var_name,
                                    'shape': var_value.shape,
                                    'columns': list(var_value.columns),
                                    'preview': generate_tailwind_table(var_value),
                                    'data': var_value.to_dict('records')[:100] if len(var_value) > 0 else []
                                })
                    
                    # *** THIS IS THE KEY FIX: Add the same post-processing as the original function ***
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
                    
                    # *** CRITICAL: Add the same data processing steps as the original function ***
                    if result.get("success") and dataframes_found:
                        print(f"\n✅ Analysis completed successfully!")
                        print(f"📊 Generated {len(dataframes_found)} result DataFrames")
                        self.emit_stream('success', f"✅ Analysis completed successfully! Generated {len(dataframes_found)} result DataFrames")
                        
                        # Save the main result DataFrame - SAME AS ORIGINAL
                        main_df_name = list(dataframes_found.keys())[0]
                        main_df = dataframes_found[main_df_name]
                        
                        if len(main_df) > 0:
                            # Show preview - SAME AS ORIGINAL
                            self.show_data_preview(self.original_df, main_df)
                            
                            # Save for potential file update - SAME AS ORIGINAL
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
                
                else:
                    # Update error message for next attempt
                    error_message = result.get("error", "Unknown error occurred")
                    failed_code = regenerated_code
                    self.emit_stream('error', f"❌ Regeneration attempt {attempt + 1} failed: {error_message}")
                    
                    # Continue to next attempt
                    continue
                    
            except Exception as e:
                error_message = str(e)
                self.emit_stream('error', f"❌ Regeneration attempt {attempt + 1} failed with exception: {error_message}")
                continue
        
        # If all retries failed, return failure result
        self.emit_stream('error', f"❌ All regeneration attempts failed after {max_retries} tries")
        
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
    def _generate_dataframe_analysis_streaming_with_fallback(self, user_query: str, data_request: Dict, is_forecasting: bool) -> Dict[str, Any]:
        """
        Enhanced version of the original function with automatic fallback on failure
        """
        
        # First, try the original generation logic
        original_result = self._generate_dataframe_analysis_streaming(user_query, data_request, is_forecasting)
        
        # If original execution was successful, return it
        if original_result.get("success"):
            return original_result
        
        # If original execution failed, trigger fallback
        self.emit_stream('warning', "⚠️ Initial code generation failed. Attempting regeneration with error context...")
        
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
    
    def _streaming_print(self, *args, **kwargs):
        """Custom print function that streams output to frontend."""
        output_text = ' '.join(str(arg) for arg in args)
        self.streaming_outputs.append(output_text)
        self.emit_stream('output', output_text)
        print(*args, **kwargs)  # Also print to console
    
    def _capture_matplotlib_plots_streaming(self) -> List[str]:
        """Capture any matplotlib plots that were created during code execution - EXACT COPY from test2.py with streaming"""
        captured_images = []
        
        fig_nums = plt.get_fignums()
        
        for i, fig_num in enumerate(fig_nums):
            try:
                fig = plt.figure(fig_num)
                
                timestamp = datetime.now().strftime("%H%M%S")
                image_filename = f"plot_{timestamp}_{i+1}.png"
                image_path = self.images_dir / image_filename
                
                # Save the image - EXACT COPY from test2.py
                fig.savefig(image_path, dpi=300, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
                
                public_url = self._upload_image_to_blob(str(image_path))
                if public_url:
                    captured_images.append(public_url)
                    self.generated_images.append(public_url)
                else:
                    captured_images.append(str(image_path))
                    self.generated_images.append(image_filename)
                # captured_images.append(str(image_path))
                # self.generated_images.append(image_filename)
                
                # Convert to base64 and stream to frontend
                try:
                    with open(image_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                    
                    self.emit_stream('image', {
                        'filename': image_filename,
                        'data': f"data:image/png;base64,{img_data}",
                        'path': str(image_path)
                    })
                    
                    print(f"📸 Saved and streamed plot: {image_filename}")
                    
                except Exception as stream_error:
                    print(f"⚠️ Failed to stream image {image_filename}: {stream_error}")
                
            except Exception as e:
                print(f"⚠️ Failed to save plot {i+1}: {str(e)}")
        
        return captured_images
    
    ##BASE64
    def _convert_images_to_base64(self) -> Dict[str, str]:
        """Convert all generated images to base64 for HTML embedding."""
        base64_images = {}
        
        # Convert existing saved images
        for i, img_filename in enumerate(self.generated_images):
            try:
                img_path = self.images_dir / img_filename
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                        base64_images[f"image_{i+1}"] = img_data
                        print(f"📸 Converted {img_filename} to base64")
            except Exception as e:
                print(f"⚠️ Failed to convert {img_filename}: {e}")
        
        # Also capture any currently open matplotlib figures
        fig_nums = plt.get_fignums()
        for i, fig_num in enumerate(fig_nums):
            try:
                fig = plt.figure(fig_num)
                buffer = BytesIO()
                fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                        facecolor='white', edgecolor='none')
                buffer.seek(0)
                img_data = base64.b64encode(buffer.read()).decode('utf-8')
                base64_images[f"figure_{i+1}"] = img_data
                buffer.close()
                print(f"📸 Converted matplotlib figure {fig_num} to base64")
            except Exception as e:
                print(f"⚠️ Failed to convert figure {fig_num}: {e}")
        
        return base64_images

    def _generate_comprehensive_report_streaming(self, user_query: str, is_forecasting: bool) -> Dict[str, Any]:
        """Generate comprehensive report when specifically requested - FIXED VERSION"""
        print("\n📋 Generating comprehensive strategic report...")
        self.emit_stream('status', "📋 Generating comprehensive strategic report...")
        
        try:
            # First run the analysis to get data
            data_request = self._extract_data_request(user_query)
            analysis_result = self._generate_dataframe_analysis_streaming_with_fallback(user_query, data_request, is_forecasting)
            
            if not analysis_result.get("success"):
                return {
                    "error": "Cannot generate report - analysis failed",
                    "type": "report_error"
                }
            
            self.emit_stream('status', "📝 Converting images and generating report...")
            
            # FIXED: Convert all images to base64
            base64_images = self._convert_images_to_base64()
            print(f"📸 Converted {len(base64_images)} images to base64")
            
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
                # base64_images=base64_images  # Pass the base64 images
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
                # "base64_images_count": len(base64_images)
            })
            
            print("✅ Comprehensive strategic report generated successfully!")
            self.emit_stream('success', "✅ Comprehensive strategic report generated successfully!")
            
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

def generate_tailwind_table(df):
    """
    Generate a clean, theme-aware HTML table that works with your ThemeProvider
    """
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


def generate_simple_table(df):
    """
    Generate a minimal, clean table for better theme compatibility
    """
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




@app.route('/')
def index():
    """Main chat interface."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')


@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file_with_session():
    """Handle CSV file upload and create a new session."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        return jsonify({'error': 'Please upload a CSV or Excel file'}), 400
    
    try:
        # Generate new session ID for this upload
        new_session_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Initialize analyzer for this session
        analyzer = StreamingAnalyzer(new_session_id)
        
        # Load the CSV
        if analyzer.load_csv(filepath):
            analyzers[new_session_id] = analyzer
            session_data[new_session_id] = {
                'filename': file.filename,
                'filepath': filepath,
                'upload_time': datetime.now().isoformat(),
                'shape': analyzer.df.shape,
                'columns': list(analyzer.df.columns),
                'created_by': session.get('user_id', 'anonymous'),  # Track user if available
                'last_activity': datetime.now().isoformat()
            }
            
            print(f"✅ Created new session: {new_session_id} for file: {file.filename}")
            
            response = jsonify({
                'success': True,
                'sessionId': new_session_id,
                'message': f'File uploaded successfully! Shape: {analyzer.df.shape}',
                'data': {
                    'filename': file.filename,
                    'shape': analyzer.df.shape,
                    'columns': list(analyzer.df.columns),
                    'preview': generate_tailwind_table(analyzer.df.head()),
                    'data': analyzer.df.head(100).to_dict('records'), 
                    'sessionId': new_session_id
                }
            })
            origin = request.headers.get('Origin', '*')
            response.headers.add('Access-Control-Allow-Origin', origin)
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response
        else:
            return jsonify({'error': 'Failed to load CSV file'}), 400
            
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    html_content = request.data.decode("utf-8")  # or use request.form['html'] if using form data

    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp_html:
        tmp_html.write(html_content)
        tmp_html_path = tmp_html.name

    try:
        # Send HTML to Gotenberg
        with open(tmp_html_path, "rb") as html_file:
            files = {
                "files": ("index.html", html_file, "text/html"),
            }

            response = requests.post(GOTENBERG_URL, files=files)

        if response.status_code == 200:
            # Save PDF to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(response.content)
                tmp_pdf_path = tmp_pdf.name

            return send_file(tmp_pdf_path, as_attachment=True, download_name="output.pdf", mimetype="application/pdf")
        else:
            return jsonify({"error": "Gotenberg conversion failed", "details": response.text}), 500

    finally:
        # Clean up temp HTML (PDF will be deleted by Flask after send_file)
        if os.path.exists(tmp_html_path):
            os.remove(tmp_html_path)

@app.route('/session/<session_id>/info', methods=['GET', 'OPTIONS'])
def get_session_info(session_id):
    """Get information about a specific session."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        if session_id not in analyzers or session_id not in session_data:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        # Update last activity
        session_data[session_id]['last_activity'] = datetime.now().isoformat()
        
        # Get session info
        file_info = session_data[session_id]
        analyzer = analyzers[session_id]
        
        # Get conversation history summary
        history_summary = analyzer.conversation_history.get_summary()
        
        response = jsonify({
            'success': True,
            'sessionId': session_id,
            'fileInfo': file_info,
            'historyCount': len(analyzer.conversation_history.history),
            'historySummary': history_summary,
            'dataPreview': generate_tailwind_table(analyzer.df.head()) if analyzer.df is not None else None
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Session info error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get session info: {str(e)}'
        }), 500
    
@app.route('/session/<session_id>/upload', methods=['POST', 'OPTIONS'])
def upload_to_existing_session(session_id):
    """Upload a file to an existing session (replace existing file)."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        return jsonify({'error': 'Please upload a CSV or Excel file'}), 400
    
    try:
        # Check if session exists
        if session_id not in analyzers:
            return jsonify({'error': 'Session not found'}), 404
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Update existing analyzer
        analyzer = analyzers[session_id]
        
        # Load the new CSV
        if analyzer.load_csv(filepath):
            # Update session data
            session_data[session_id].update({
                'filename': file.filename,
                'filepath': filepath,
                'upload_time': datetime.now().isoformat(),
                'shape': analyzer.df.shape,
                'columns': list(analyzer.df.columns),
                'last_activity': datetime.now().isoformat()
            })
            
            print(f"✅ Updated session: {session_id} with new file: {file.filename}")
            
            response = jsonify({
                'success': True,
                'sessionId': session_id,
                'message': f'File updated successfully! Shape: {analyzer.df.shape}',
                'data': {
                    'filename': file.filename,
                    'shape': analyzer.df.shape,
                    'columns': list(analyzer.df.columns),
                    'preview': generate_tailwind_table(analyzer.df.head())
                }
            })
            origin = request.headers.get('Origin', '*')
            response.headers.add('Access-Control-Allow-Origin', origin)
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response
        else:
            return jsonify({'error': 'Failed to load CSV file'}), 400
            
    except Exception as e:
        print(f"❌ Session upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/session/<session_id>/history', methods=['GET', 'OPTIONS'])
def get_session_history(session_id):
    """Get conversation history for a specific session."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        if session_id not in analyzers:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        # Update last activity
        if session_id in session_data:
            session_data[session_id]['last_activity'] = datetime.now().isoformat()
        
        analyzer = analyzers[session_id]
        history = analyzer.conversation_history.history
        summary = analyzer.conversation_history.get_summary()
        
        response = jsonify({
            'success': True,
            'sessionId': session_id,
            'history': history,
            'summary': summary,
            'totalQueries': len(history)
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Session history error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get session history: {str(e)}'
        }), 500

@app.route('/session/<session_id>/delete', methods=['DELETE', 'OPTIONS'])
def delete_session(session_id):
    """Delete a specific session and clean up resources."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
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
        
        if not deleted_items:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        response = jsonify({
            'success': True,
            'sessionId': session_id,
            'message': f'Session deleted successfully',
            'deletedItems': deleted_items
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Session deletion error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete session: {str(e)}'
        }), 500
    
@app.route('/sessions', methods=['GET', 'OPTIONS'])
def list_sessions():
    """List all active sessions."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        sessions = []
        current_time = datetime.now()
        
        for session_id in list(analyzers.keys()):  # Use list() to avoid dict changed during iteration
            if session_id in session_data:
                session_info = session_data[session_id]
                
                # Calculate session age
                upload_time = datetime.fromisoformat(session_info.get('upload_time', current_time.isoformat()))
                age_hours = (current_time - upload_time).total_seconds() / 3600
                
                # Calculate last activity
                last_activity = session_info.get('last_activity', session_info.get('upload_time'))
                last_activity_time = datetime.fromisoformat(last_activity)
                inactive_hours = (current_time - last_activity_time).total_seconds() / 3600
                
                session_data_item = {
                    'sessionId': session_id,
                    'filename': session_info.get('filename'),
                    'uploadTime': session_info.get('upload_time'),
                    'lastActivity': last_activity,
                    'ageHours': round(age_hours, 2),
                    'inactiveHours': round(inactive_hours, 2),
                    'shape': session_info.get('shape'),
                    'conversationCount': len(analyzers[session_id].conversation_history.history),
                    'createdBy': session_info.get('created_by', 'unknown')
                }
                sessions.append(session_data_item)
        
        # Sort by last activity (most recent first)
        sessions.sort(key=lambda x: x['lastActivity'], reverse=True)
        
        response = jsonify({
            'success': True,
            'sessions': sessions,
            'totalSessions': len(sessions),
            'serverTime': current_time.isoformat()
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Sessions listing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to list sessions: {str(e)}'
        }), 500


@app.route('/sessions/cleanup', methods=['POST', 'OPTIONS'])
def cleanup_old_sessions():
    """Clean up old inactive sessions."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        # Get cleanup parameters from request
        data = request.get_json() or {}
        max_age_hours = data.get('maxAgeHours', 24)  # Default: 24 hours
        max_inactive_hours = data.get('maxInactiveHours', 6)  # Default: 6 hours inactive
        
        current_time = datetime.now()
        sessions_to_delete = []
        
        # Find sessions to clean up
        for session_id in list(analyzers.keys()):
            if session_id in session_data:
                session_info = session_data[session_id]
                
                # Check age
                upload_time = datetime.fromisoformat(session_info.get('upload_time', current_time.isoformat()))
                age_hours = (current_time - upload_time).total_seconds() / 3600
                
                # Check inactivity
                last_activity = session_info.get('last_activity', session_info.get('upload_time'))
                last_activity_time = datetime.fromisoformat(last_activity)
                inactive_hours = (current_time - last_activity_time).total_seconds() / 3600
                
                # Mark for deletion if too old or inactive
                if age_hours > max_age_hours or inactive_hours > max_inactive_hours:
                    sessions_to_delete.append({
                        'sessionId': session_id,
                        'reason': 'too_old' if age_hours > max_age_hours else 'inactive',
                        'ageHours': age_hours,
                        'inactiveHours': inactive_hours
                    })
        
        # Delete marked sessions
        deleted_sessions = []
        for session_info in sessions_to_delete:
            session_id = session_info['sessionId']
            try:
                # Use the delete_session logic
                if session_id in analyzers:
                    del analyzers[session_id]
                if session_id in session_data:
                    # Clean up file if exists
                    file_path = session_data[session_id].get('filepath')
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                    del session_data[session_id]
                
                deleted_sessions.append(session_info)
                print(f"🗑️  Cleaned up session: {session_id} ({session_info['reason']})")
                
            except Exception as e:
                print(f"⚠️  Failed to clean up session {session_id}: {e}")
        
        response = jsonify({
            'success': True,
            'deletedSessions': deleted_sessions,
            'totalDeleted': len(deleted_sessions),
            'remainingSessions': len(analyzers),
            'cleanupTime': current_time.isoformat()
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Session cleanup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to cleanup sessions: {str(e)}'
        }), 500
    

@app.route('/clear-session', methods=['POST', 'OPTIONS'])
def clear_session():
    """Clear current session data and create a new session."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        # Get current session ID
        current_session_id = session.get('session_id')
        
        # Clean up current session data
        if current_session_id:
            # Remove from global analyzers
            if current_session_id in analyzers:
                del analyzers[current_session_id]
                print(f"🗑️  Cleared analyzer for session: {current_session_id}")
            
            # Remove from session data
            if current_session_id in session_data:
                del session_data[current_session_id]
                print(f"🗑️  Cleared session data for: {current_session_id}")
        
        # Generate new session ID
        new_session_id = str(uuid.uuid4())
        session['session_id'] = new_session_id
        
        print(f"✨ Created new session: {new_session_id}")
        
        response = jsonify({
            'success': True,
            'message': 'Session cleared successfully',
            'new_session_id': new_session_id
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Error clearing session: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to clear session: {str(e)}'
        }), 500

@app.route('/conversation-history', methods=['GET', 'OPTIONS'])
def get_conversation_history():
    """Get conversation history for the current session."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    session_id = session.get('session_id')
    if not session_id or session_id not in analyzers:
        return jsonify({'error': 'No active session found'}), 404
    
    try:
        analyzer = analyzers[session_id]
        history = analyzer.conversation_history.history
        summary = analyzer.conversation_history.get_summary()
        
        response = jsonify({
            'success': True,
            'history': history,
            'summary': summary
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        return jsonify({'error': f'Failed to get conversation history: {str(e)}'}), 500


# Add new Flask routes for LangChain functionality (keeping existing routes unchanged)

@app.route('/api/langchain-status', methods=['GET', 'OPTIONS'])
def langchain_status():
    """Check LangChain integration status"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    session_id = session.get('session_id')
    if not session_id or session_id not in analyzers:
        return jsonify({'langchain_enabled': False, 'reason': 'No active session'})
    
    try:
        analyzer = analyzers[session_id]
        if hasattr(analyzer, 'conversation_history'):
            langchain_enabled = getattr(analyzer.conversation_history, 'langchain_enabled', False)
            
            status = {
                'langchain_enabled': langchain_enabled,
                'total_messages': len(analyzer.conversation_history.get_langchain_messages()) if langchain_enabled else 0,
                'memory_type': 'ConversationSummaryBufferMemory' if langchain_enabled else None
            }
        else:
            status = {'langchain_enabled': False, 'reason': 'Conversation history not available'}
        
        response = jsonify(status)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        return jsonify({'error': f'Failed to get LangChain status: {str(e)}'}), 500


@app.route('/api/export-langchain-conversation', methods=['GET', 'OPTIONS'])
def export_langchain_conversation():
    """Export LangChain conversation history"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    session_id = session.get('session_id')
    format_type = request.args.get('format', 'json')  # json or text
    
    if not session_id or session_id not in analyzers:
        return jsonify({'error': 'No active session found'}), 404
    
    try:
        analyzer = analyzers[session_id]
        
        if hasattr(analyzer, 'conversation_history') and analyzer.conversation_history.langchain_enabled:
            exported_data = analyzer.conversation_history.export_langchain_conversation(format_type)
            
            if format_type == 'text':
                return Response(
                    exported_data,
                    mimetype='text/plain',
                    headers={'Content-Disposition': f'attachment; filename=langchain_conversation_{session_id}.txt'}
                )
            else:
                return Response(
                    exported_data,
                    mimetype='application/json',
                    headers={'Content-Disposition': f'attachment; filename=langchain_conversation_{session_id}.json'}
                )
        else:
            return jsonify({'error': 'LangChain conversation history not available'}), 404
        
    except Exception as e:
        return jsonify({'error': f'Failed to export LangChain conversation: {str(e)}'}), 500


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    # Generate session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    join_room(session_id)
    
    print(f"Client connected with session: {session_id}")
    emit('status', {'message': 'Connected to analysis server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    session_id = session.get('session_id')
    print(f'Client disconnected: {session_id}')


@socketio.on('send_message')
def handle_message(data):
    """Handle chat messages and process queries."""
    session_id = session.get('session_id')
    
    if not session_id:
        emit('stream_data', {
            'type': 'error',
            'data': 'Session not found. Please refresh the page and try again.',
            'timestamp': datetime.now().isoformat()
        })
        return
    
    print(f"Processing message for session: {session_id}")
    print(f"Available analyzers: {list(analyzers.keys())}")
    print(f"Session data: {list(session_data.keys())}")
    
    if session_id not in analyzers:
        emit('stream_data', {
            'type': 'error',
            'data': 'Please upload a CSV file first. Session data not found.',
            'timestamp': datetime.now().isoformat()
        })
        return
    
    query = data.get('message', '').strip()
    if not query:
        return
    
    # Process the query directly with better error handling
    def process_query():
        try:
            analyzer = analyzers[session_id]
            analyzer.session_id = session_id  # Ensure session ID is set
            
            # Start the analysis
            result = analyzer.analyze_query_streaming(query)
            
            # Send completion signal
            socketio.emit('stream_data', {
                'type': 'completion',
                'data': 'Analysis completed successfully!',
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            socketio.emit('stream_data', {
                'type': 'error',
                'data': f'Analysis failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
    
    # Run in a daemon thread for non-blocking execution
    thread = threading.Thread(target=process_query)
    thread.daemon = True
    thread.start()

# ADD THESE NEW HANDLERS TO YOUR app.py

@socketio.on('join_session')
def handle_join_session(data):
    """Handle client joining a specific session room."""
    session_id = data.get('sessionId')
    if session_id:
        join_room(session_id)
        print(f"🔌 Client joined session room: {session_id}")
        emit('status', {'message': f'Joined session {session_id}'})
        
        # Update last activity
        if session_id in session_data:
            session_data[session_id]['last_activity'] = datetime.now().isoformat()
    else:
        print("❌ No session ID provided for join_session")
        emit('error', {'message': 'No session ID provided'})

@socketio.on('leave_session')
def handle_leave_session(data):
    """Handle client leaving a specific session room."""
    session_id = data.get('sessionId')
    if session_id:
        leave_room(session_id)
        print(f"🔌 Client left session room: {session_id}")
        emit('status', {'message': f'Left session {session_id}'})

@socketio.on('send_message_with_session')
def handle_message_with_session(data):
    """Handle chat messages for a specific session."""
    session_id = data.get('sessionId')
    query = data.get('message', '').strip()
    
    if not session_id:
        emit('stream_data', {
            'type': 'error',
            'data': 'No session ID provided. Please refresh and try again.',
            'timestamp': datetime.now().isoformat()
        })
        return
    
    if not query:
        return
    
    print(f"💬 Processing message for session: {session_id}")
    
    if session_id not in analyzers:
        emit('stream_data', {
            'type': 'error',
            'data': f'Session {session_id} not found. Please go back to home and upload a file.',
            'timestamp': datetime.now().isoformat()
        })
        return
    
    # Update last activity
    if session_id in session_data:
        session_data[session_id]['last_activity'] = datetime.now().isoformat()
    
    # Process the query with session-specific analyzer
    def process_query():
        try:
            analyzer = analyzers[session_id]
            analyzer.session_id = session_id
            
            # Start the analysis
            result = analyzer.analyze_query_streaming(query)
            
            # Send completion signal to the specific session room
            socketio.emit('stream_data', {
                'type': 'completion',
                'data': 'Analysis completed successfully!',
                'timestamp': datetime.now().isoformat(),
                'sessionId': session_id
            }, room=session_id)
            
        except Exception as e:
            print(f"❌ Analysis error for session {session_id}: {str(e)}")
            socketio.emit('stream_data', {
                'type': 'error',
                'data': f'Analysis failed: {str(e)}',
                'timestamp': datetime.now().isoformat(),
                'sessionId': session_id
            }, room=session_id)
    
    # Run in a daemon thread
    thread = threading.Thread(target=process_query)
    thread.daemon = True
    thread.start()

@app.route('/debug-session')
def debug_session():
    """Debug endpoint to check session state."""
    session_id = session.get('session_id')
    return jsonify({
        'session_id': session_id,
        'has_analyzer': session_id in analyzers if session_id else False,
        'has_session_data': session_id in session_data if session_id else False,
        'analyzers_count': len(analyzers),
        'session_data_count': len(session_data),
        'analyzer_keys': list(analyzers.keys()),
        'session_data_keys': list(session_data.keys())
    })


@app.route('/download/<filename>')
def download_file(filename):
    """Download generated files."""
    session_id = session.get('session_id')
    if session_id in analyzers:
        analyzer = analyzers[session_id]
        # Check in various output directories
        for dir_path in [analyzer.images_dir, analyzer.reports_dir, analyzer.data_dir]:
            file_path = dir_path / filename
            if file_path.exists():
                return send_file(file_path, as_attachment=True)
    
    return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    # Verify environment variables
    required_vars = ["AZUREAPI", "AZUREVERSION", "AZUREENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set the following:")
        print("- AZUREAPI: Your Azure OpenAI API key")
        print("- AZUREVERSION: API version (e.g., '2024-02-01')")
        print("- AZUREENDPOINT: Your Azure OpenAI endpoint")
        exit(1)
    
    print("🚀 Starting Flask CSV Analysis Chatbot...")
    print("📊 Backend running on http://localhost:5000")
    print("🔗 Connect your React frontend to this backend")
    print(f"⚙️  Using {async_mode} async mode")
    
    if LANGCHAIN_AVAILABLE:
        print("✅ LangChain available for enhanced conversation history")
    else:
        print("⚠️  LangChain not available - using basic conversation history")
    
    if EVENTLET_AVAILABLE:
        print("✅ Using eventlet for optimal WebSocket support")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    else:
        print("⚠️  Using threading mode - install eventlet for better performance")
        print("   pip install eventlet")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)