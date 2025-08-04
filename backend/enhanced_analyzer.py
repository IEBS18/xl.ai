import os
import re
import traceback
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path
import pandas as pd

# Try to import secure_filename, provide fallback if not available
try:
    from werkzeug.utils import secure_filename
except ImportError:
    def secure_filename(filename):
        """Fallback secure_filename implementation"""
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]
        # Keep only alphanumeric, dots, hyphens, underscores
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        # Remove leading dots and underscores, limit length
        filename = filename.strip('._')[:100]
        return filename or 'unnamed_file'

# Azure Blob Storage imports
from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions

# Import all handlers and utilities
from query_classifier import QueryClassifier
from conversation_handler import ConversationHandler
from textual_analytical_handler import TextualAnalyticalHandler
from analytical_handler import AnalyticalHandler
from utils import StreamingAnalyzer, StopAnalysisException

class EnhancedStreamingAnalyzer(StreamingAnalyzer):
    """
    Enhanced analyzer that adds conversational capabilities AND blob storage support
    while preserving all existing functionality.
    
    This class extends the original StreamingAnalyzer and adds:
    1. Conversational queries - Friendly chatbot responses
    2. Textual analytical queries - Simple data questions with text responses
    3. Fully analytical queries - Complex analysis with streaming and visualizations (original behavior)
    4. Azure Blob Storage integration with SAS token support
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
        
        # Azure Blob Storage configuration
        self.blob_service_client = None
        self.container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'analysis-files')
        self.analysis_folder_name = os.getenv('AZURE_ANALYSIS_FOLDER', 'data-analysis')
        self.blob_sas_url = None  # Store the SAS URL for direct access
        self._initialize_blob_client()
        
        print(f"✅ Enhanced analyzer with blob storage initialized for session: {session_id}")
    
    def _initialize_blob_client(self):
        """Initialize Azure Blob Storage client"""
        try:
            # Try connection string first
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            
            # Get account URL and key from your environment variables
            account_url = os.getenv('AZURE_STORAGE_ACCOUNT_URL')
            account_key = os.getenv('AZURE_STORAGE_KEY')
            
            # Extract account name from URL if available
            account_name = None
            if account_url:
                # Extract account name from URL like https://storageaccount.blob.core.windows.net
                try:
                    account_name = account_url.split("//")[1].split(".")[0]
                except:
                    pass
            
            # Try connection string first
            if connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                logging.info("✅ Initialized blob client from connection string")
            elif account_url and account_key:
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=account_key
                )
                logging.info(f"✅ Initialized blob client from URL: {account_url}")
            else:
                logging.warning("❌ Azure Blob Storage credentials not found.")
                logging.warning("Required: AZURE_STORAGE_ACCOUNT_URL and AZURE_STORAGE_KEY")
                logging.warning("Or: AZURE_STORAGE_CONNECTION_STRING")
                
        except Exception as e:
            logging.error(f"Failed to initialize blob client: {str(e)}")
            self.blob_service_client = None

    def _upload_file_to_blob_direct(self, file_stream, original_filename: str, blob_subfolder: str) -> str:
        """
        Upload file stream directly to Azure Blob Storage without saving locally.
        Returns the blob name for SAS generation.
        """
        try:
            logging.info(f"🧪 Uploading file stream: {original_filename}")

            # Validate required instance variables
            if not self.analysis_folder_name or not self.container_name:
                logging.error("❌ Missing required configuration in class instance.")
                return ""

            # Build the blob path with timestamp to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = secure_filename(original_filename)
            file_name = f"{timestamp}_{safe_filename}"
            blob_name = f"{self.analysis_folder_name}/{blob_subfolder}/{file_name}".strip('/')
            
            logging.debug(f"📁 Target blob path: {blob_name}")

            # Ensure blob_service_client is initialized
            if not self.blob_service_client:
                logging.error("❌ BlobServiceClient is not initialized.")
                return ""

            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            # Reset stream position and upload directly
            file_stream.seek(0)
            blob_client.upload_blob(
                file_stream,
                overwrite=True,
                content_settings=ContentSettings(content_type="application/octet-stream")
            )
            
            logging.info(f"📤 Uploaded file to blob: {self.container_name}/{blob_name}")
            return blob_name

        except Exception as e:
            logging.exception(f"⚠️ Exception occurred during direct file upload: {str(e)}")
            return ""
    
    def _generate_sas_token_url(self, blob_name: str, expiry_hours: int = 168) -> str:
        """Generate a SAS token URL for secure access to the blob file."""
        try:
            if not self.blob_service_client:
                logging.error("❌ BlobServiceClient is not initialized.")
                return ""
            
            # Get account key and URL from your environment variables
            account_key = os.getenv('AZURE_STORAGE_KEY')
            account_url = os.getenv('AZURE_STORAGE_ACCOUNT_URL')
            
            # Extract account name from URL
            account_name = None
            if account_url:
                try:
                    account_name = account_url.split("//")[1].split(".")[0]
                except:
                    pass
            
            # Try to get from blob service client if not available
            if not account_key or not account_name:
                if hasattr(self.blob_service_client, 'account_name'):
                    account_name = self.blob_service_client.account_name
                if hasattr(self.blob_service_client.credential, 'account_key'):
                    account_key = self.blob_service_client.credential.account_key
            
            if not account_key or not account_name:
                logging.error("❌ Account credentials not available for SAS token generation.")
                logging.error("Required: AZURE_STORAGE_ACCOUNT_URL and AZURE_STORAGE_KEY")
                return ""
            
            # Generate SAS token with longer expiry for analysis purposes
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            # Construct full URL with SAS token
            blob_url = f"https://{account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
            sas_url = f"{blob_url}?{sas_token}"
            
            logging.info(f"🔐 Generated SAS token URL (expires in {expiry_hours}h)")
            return sas_url
            
        except Exception as e:
            logging.exception(f"⚠️ Exception occurred during SAS token generation: {str(e)}")
            return ""

    def upload_stream_and_get_sas_url(self, file_stream, original_filename: str, blob_subfolder: str = None, expiry_hours: int = 168) -> dict:
        """Upload file stream directly to blob storage and return SAS token URL."""
        if blob_subfolder is None:
            blob_subfolder = self.session_id
            
        try:
            # Upload file stream directly to blob
            blob_name = self._upload_file_to_blob_direct(file_stream, original_filename, blob_subfolder)
            
            if not blob_name:
                return {
                    'success': False,
                    'error': 'Failed to upload file to blob storage',
                    'sas_url': '',
                    'blob_name': ''
                }
            
            # Generate SAS token URL
            sas_url = self._generate_sas_token_url(blob_name, expiry_hours)
            
            if not sas_url:
                return {
                    'success': False,
                    'error': 'Failed to generate SAS token URL',
                    'sas_url': '',
                    'blob_name': blob_name
                }
            
            return {
                'success': True,
                'sas_url': sas_url,
                'blob_name': blob_name,
                'expiry_hours': expiry_hours,
                'expires_at': (datetime.utcnow() + timedelta(hours=expiry_hours)).isoformat()
            }
            
        except Exception as e:
            logging.exception(f"⚠️ Exception in upload_stream_and_get_sas_url: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sas_url': '',
                'blob_name': ''
            }

    def load_csv_from_sas_url(self, sas_url: str, file_extension: str = None) -> bool:
        """Load CSV or Excel file directly from SAS URL without local storage."""
        try:
            # Store the SAS URL for future operations
            self.blob_sas_url = sas_url
            self.original_file_path = sas_url
            
            # Determine file type
            if file_extension:
                file_ext = file_extension.lower()
            else:
                # Try to extract from URL (remove query parameters first)
                clean_url = sas_url.split('?')[0]
                file_ext = os.path.splitext(clean_url)[-1].lower()
            
            logging.info(f"📥 Loading file directly from SAS URL")
            logging.info(f"📄 File extension: {file_ext}")

            # Load file directly from URL based on extension
            if file_ext == ".csv":
                self.df = pd.read_csv(sas_url, encoding="utf-8")
            elif file_ext in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
                self.df = pd.read_excel(sas_url, engine="openpyxl")
            elif file_ext == ".xls":
                self.df = pd.read_excel(sas_url, engine="xlrd")
            elif file_ext == ".ods":
                self.df = pd.read_excel(sas_url, engine="odf")
            elif file_ext == ".xlsb":
                import pyxlsb
                self.df = pd.read_excel(sas_url, engine="pyxlsb")
            else:
                raise ValueError(f"Unsupported file extension: {file_ext}")
            
            # Convert all data to strings and fill nulls
            self.df.columns = self.df.columns.astype(str)
            self.df.index = self.df.index.astype(str)
            self.df = self.df.applymap(lambda x: "" if pd.isna(x) else str(x))
            
            self.csv_info = self._generate_csv_info()

            print(f"✅ File loaded successfully from blob storage!")
            print(f"📊 Shape: {self.df.shape}")
            print(f"🔍 Columns: {list(self.df.columns)}")

            # Store original data for comparison
            self.original_df = self.df.copy()
            self._generate_basic_trends()

            # Update conversation context
            self.conversation_context.update({
                "has_data": True,
                "filename": "blob_storage_file",
                "shape": self.df.shape,
                "columns": list(self.df.columns)
            })
            
            # Initialize handlers now that we have data
            self._initialize_handlers()

            return True

        except Exception as e:
            print(f"❌ Error loading file from SAS URL: {str(e)}")
            logging.exception("Detailed error loading file from SAS URL")
            return False

    def get_data_subset_from_blob(self, rows: int = 1000) -> pd.DataFrame:
        """
        Get a subset of data directly from blob storage for operations that don't need full dataset.
        This saves memory and processing time.
        """
        try:
            if not self.blob_sas_url:
                logging.warning("No blob SAS URL available, using loaded DataFrame")
                return self.df.head(rows) if self.df is not None else pd.DataFrame()
            
            # Determine file extension
            clean_url = self.blob_sas_url.split('?')[0]
            file_ext = os.path.splitext(clean_url)[-1].lower()
            
            if file_ext == ".csv":
                # For CSV, we can read only first N rows
                subset_df = pd.read_csv(self.blob_sas_url, encoding="utf-8", nrows=rows)
            else:
                # For Excel files, read all and take subset (Excel engines don't support nrows well)
                subset_df = pd.read_excel(self.blob_sas_url, engine="openpyxl").head(rows)
            
            # Apply same transformations as main load
            subset_df.columns = subset_df.columns.astype(str)
            subset_df = subset_df.applymap(lambda x: "" if pd.isna(x) else str(x))
            
            return subset_df
            
        except Exception as e:
            logging.exception(f"Error getting data subset from blob: {str(e)}")
            return self.df.head(rows) if self.df is not None else pd.DataFrame()
    
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
    
    def _generate_csv_info(self) -> str:
        """Generate CSV info - calls parent method if available"""
        if hasattr(super(), '_generate_csv_info'):
            return super()._generate_csv_info()
        else:
            # Basic fallback implementation
            if self.df is not None:
                return f"Dataset with {self.df.shape[0]} rows and {self.df.shape[1]} columns"
            return "No dataset loaded"
    
    def _generate_basic_trends(self):
        """Generate basic trends - calls parent method if available"""
        if hasattr(super(), '_generate_basic_trends'):
            super()._generate_basic_trends()
        else:
            # Basic fallback - do nothing
            pass
    
    # Preserve all existing methods from parent class
    # The parent StreamingAnalyzer methods are automatically inherited
    
    def __getattr__(self, name):
        """Ensure all parent methods are accessible."""
        if hasattr(super(), name):
            return getattr(super(), name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")