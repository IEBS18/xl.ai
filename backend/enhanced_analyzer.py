import os
import traceback
from datetime import datetime
from typing import Dict, Any
import pandas as pd

# Import all handlers and utilities
from query_classifier import QueryClassifier
from conversation_handler import ConversationHandler
from textual_analytical_handler import TextualAnalyticalHandler
from analytical_handler import AnalyticalHandler
from utils import StreamingAnalyzer, StopAnalysisException

class EnhancedStreamingAnalyzer(StreamingAnalyzer):
    """
    Enhanced analyzer that adds conversational capabilities while preserving all existing functionality.
    
    This class extends the original StreamingAnalyzer and adds query classification to handle:
    1. Conversational queries - Friendly chatbot responses
    2. Textual analytical queries - Simple data questions with text responses
    3. Fully analytical queries - Complex analysis with streaming and visualizations (original behavior)
    """
    
    def __init__(self, session_id, socketio=None):
        # Initialize parent class with all existing functionality
        super().__init__(session_id, socketio)
        
        # Initialize new components
        self.query_classifier = QueryClassifier()
        self.conversation_handler = None
        self.textual_analytical_handler = None
        self.analytical_handler = None
        
        # Track conversation state
        self.conversation_context = {
            "has_data": False,
            "filename": None,
            "shape": None,
            "columns": []
        }
        
        print(f"✅ Enhanced analyzer initialized for session: {session_id}")
    
    def load_csv(self, filepath: str) -> bool:
        """Override load_csv to update conversation context and initialize handlers."""
        
        # Call parent method to load CSV
        success = super().load_csv(filepath)
        
        if success:
            # Update conversation context
            self.conversation_context.update({
                "has_data": True,
                "filename": os.path.basename(filepath),
                "shape": self.df.shape,
                "columns": list(self.df.columns)
            })
            
            # Initialize handlers now that we have data
            self._initialize_handlers()
            
            print(f"✅ CSV loaded and handlers initialized for enhanced analysis")
        
        return success
    
    def _initialize_handlers(self):
        """Initialize all query handlers with current data context."""
        
        try:
            # Initialize conversation handler
            self.conversation_handler = ConversationHandler(
                self.session_id, 
                self.socketio
            )
            
            # Initialize textual analytical handler (needs DataFrame)
            if self.df is not None:
                self.textual_analytical_handler = TextualAnalyticalHandler(
                    self.session_id,
                    self.df,
                    self.socketio,
                    self.csv_info
                )
            
            # Initialize analytical handler (uses existing analyzer methods)
            self.analytical_handler = AnalyticalHandler(
                self.session_id,
                self,  # Pass self as analyzer instance
                self.socketio
            )
            
            print("✅ All query handlers initialized successfully")
            
        except Exception as e:
            print(f"⚠️ Failed to initialize some handlers: {e}")
            # Continue anyway - fallback to original behavior
    
    def analyze_query_streaming(self, user_query: str) -> Dict[str, Any]:
        """
        Enhanced analyze_query_streaming with conversational capabilities.
        
        This method now:
        1. Classifies the query type
        2. Routes to appropriate handler
        3. Falls back to original behavior if needed
        4. Preserves all existing functionality and session management
        """
        
        try:
            # Set analyzing flag (preserving existing behavior)
            self.is_analyzing = True
            
            # Clear any existing stop signal (preserving existing behavior)
            if hasattr(self, 'session_id'):
                from utils import stop_signals, clear_stop_signal_for_session
                clear_stop_signal_for_session(self.session_id)
            
            # Check for stop signal (preserving existing behavior)
            self.check_stop_signal()
            
            self.emit_stream('status', f"🤖 Processing your message: {user_query}")
            
            # STEP 1: Classify the query
            query_category, classification_metadata = self.query_classifier.classify_query(
                user_query, 
                self.csv_info if hasattr(self, 'csv_info') else ""
            )
            
            print(f"📋 Query classified as: {query_category}")
            print(f"📊 Classification confidence: {classification_metadata.get('confidence', 'unknown')}")
            
            # STEP 2: Route to appropriate handler based on classification
            result = self._route_query_to_handler(user_query, query_category, classification_metadata)
            
            # STEP 3: Record in conversation history (preserving existing behavior)
            if hasattr(self, 'conversation_history'):
                self.conversation_history.add_conversation(user_query, result)
            
            # Clear analyzing flag (preserving existing behavior)
            self.is_analyzing = False
            
            return result
            
        except StopAnalysisException:
            # Handle stop signal gracefully (preserving existing behavior)
            self.is_analyzing = False
            stop_result = {
                "error": "Analysis stopped by user",
                "type": "stopped",
                "success": False,
                "stopped_by_user": True
            }
            if hasattr(self, 'conversation_history'):
                self.conversation_history.add_conversation(user_query, stop_result)
            return stop_result
            
        except Exception as e:
            # Handle errors gracefully (preserving existing behavior)
            self.is_analyzing = False
            full_trace = traceback.format_exc()
            error_msg = f"Error analyzing query:\n{full_trace}"
            print(error_msg)
            self.emit_stream('error', error_msg)
            
            # Record failure in history (preserving existing behavior)
            error_result = {
                "error": str(e),
                "traceback": full_trace,
                "type": "error",
                "success": False
            }
            if hasattr(self, 'conversation_history'):
                self.conversation_history.add_conversation(user_query, error_result)
            
            return error_result
    
    def _route_query_to_handler(self, user_query: str, category: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Route the query to the appropriate handler based on classification."""
        
        # Extract intent data
        intent_data = self.query_classifier.extract_analysis_intent(user_query, category, metadata)
        
        # Check for stop signal before routing
        self.check_stop_signal()
        
        # Route based on category
        if category == "conversational":
            return self._handle_conversational_query(user_query, intent_data)
            
        elif category == "textual_analytical":
            return self._handle_textual_analytical_query(user_query, intent_data)
            
        elif category == "fully_analytical":
            return self._handle_fully_analytical_query(user_query, intent_data)
            
        else:
            # Fallback to original behavior
            print(f"⚠️ Unknown category '{category}', falling back to original analysis")
            return self._fallback_to_original_analysis(user_query)
    
    def _handle_conversational_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversational queries."""
        
        print("💬 Handling conversational query")
        
        try:
            if self.conversation_handler is None:
                # Initialize if not already done
                self.conversation_handler = ConversationHandler(self.session_id, self.socketio)
            
            # Pass conversation context
            return self.conversation_handler.handle_conversational_query(
                user_query, 
                self.conversation_context
            )
            
        except Exception as e:
            print(f"❌ Conversational handler failed: {e}")
            # Fallback to simple response
            return {
                "query": user_query,
                "type": "conversational",
                "success": True,
                "response": "I'm here to help you with data analysis. What would you like to explore in your dataset?",
                "generated_images": [],
                "dataframes": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def _handle_textual_analytical_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle simple analytical queries that need text responses."""
        
        print("📊 Handling textual analytical query")
        
        try:
            # Check if we have data
            if self.df is None:
                self.emit_stream('error', "No CSV file loaded. Please upload a CSV file first.")
                return {
                    "error": "No CSV file loaded",
                    "type": "textual_analytical",
                    "success": False
                }
            
            # Initialize handler if needed
            if self.textual_analytical_handler is None:
                self.textual_analytical_handler = TextualAnalyticalHandler(
                    self.session_id,
                    self.df,
                    self.socketio,
                    self.csv_info
                )
            
            return self.textual_analytical_handler.handle_textual_analytical_query(
                user_query, 
                intent_data
            )
            
        except Exception as e:
            print(f"❌ Textual analytical handler failed: {e}")
            # Fallback to original analysis
            return self._fallback_to_original_analysis(user_query)
    
    def _handle_fully_analytical_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complex analytical queries using existing full analysis."""
        
        print("🔬 Handling fully analytical query")
        
        try:
            # Check if we have data
            if self.df is None:
                self.emit_stream('error', "No CSV file loaded. Please upload a CSV file first.")
                return {
                    "error": "No CSV file loaded",
                    "type": "fully_analytical", 
                    "success": False
                }
            
            # Initialize handler if needed
            if self.analytical_handler is None:
                self.analytical_handler = AnalyticalHandler(
                    self.session_id,
                    self,
                    self.socketio
                )
            
            return self.analytical_handler.handle_fully_analytical_query(
                user_query,
                intent_data
            )
            
        except Exception as e:
            print(f"❌ Analytical handler failed: {e}")
            # Fallback to original analysis
            return self._fallback_to_original_analysis(user_query)
    
    def _fallback_to_original_analysis(self, user_query: str) -> Dict[str, Any]:
        """Fallback to the original analysis method when handlers fail."""
        
        print("🔄 Falling back to original analysis method")
        self.emit_stream('status', "Using original analysis method...")
        
        try:
            # Use the parent class's original method
            return super().analyze_query_streaming(user_query)
            
        except Exception as e:
            print(f"❌ Even original analysis failed: {e}")
            return {
                "error": str(e),
                "type": "fallback_error",
                "success": False,
                "message": "Both enhanced and original analysis methods failed. Please try rephrasing your query.",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_conversation_context(self) -> Dict[str, Any]:
        """Get current conversation context for handlers."""
        return self.conversation_context.copy()
    
    def update_conversation_context(self, **kwargs):
        """Update conversation context."""
        self.conversation_context.update(kwargs)
    
    def get_analysis_capabilities(self) -> Dict[str, Any]:
        """Get information about analysis capabilities for conversational responses."""
        
        capabilities = {
            "conversational": {
                "description": "Friendly chat and questions about capabilities",
                "examples": ["Hi, how are you?", "What can you do?", "Tell me a joke"]
            },
            "textual_analytical": {
                "description": "Simple data questions with quick text answers",
                "examples": ["What is the highest revenue?", "How many rows are there?", "What's the average age?"]
            },
            "fully_analytical": {
                "description": "Complex analysis with visualizations and detailed reports",
                "examples": ["Generate a 5-year forecast", "Create a comprehensive report", "Analyze sales trends"]
            }
        }
        
        if self.df is not None:
            capabilities["data_info"] = {
                "shape": self.df.shape,
                "columns": list(self.df.columns),
                "numeric_columns": list(self.df.select_dtypes(include=['number']).columns),
                "categorical_columns": list(self.df.select_dtypes(include=['object']).columns)
            }
        
        return capabilities
    
    # Preserve all existing methods from parent class
    # The parent StreamingAnalyzer methods are automatically inherited
    
    def __getattr__(self, name):
        """Ensure all parent methods are accessible."""
        if hasattr(super(), name):
            return getattr(super(), name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")