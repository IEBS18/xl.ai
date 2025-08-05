
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
        filename = filename.split('/')[-1].split('\\')[-1]
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        filename = filename.strip('._')[:100]
        return filename or 'unnamed_file'

# Azure Blob Storage imports
from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions

# Import assistants components
from assistants.assistant_manager import AssistantManager
from assistants.thread_manager import ThreadManager
from assistants.file_manager import FileManager
from utils.streaming_adapter import StreamingAdapter

# Import all handlers and utilities
from query_classifier import SmartQueryClassifier
from .modified_handler import ConversationHandler
from .modified_handler import TextualAnalyticalHandler
from .modified_handler import AnalyticalHandler
from utils.utils import StreamingAnalyzer, StopAnalysisException

class EnhancedStreamingAnalyzer(StreamingAnalyzer):
    """
    Enhanced analyzer using OpenAI Assistants API while preserving all existing functionality.
    
    FIXED ISSUES:
    1. Conversational queries now use Assistants API properly
    2. Textual analytical queries return proper responses
    3. Full analytical queries always explain what they did
    4. Report generation returns HTML with proper type
    5. All generated files are returned to frontend
    """
    
    def __init__(self, session_id, socketio=None):
        # Initialize parent class with all existing functionality
        super().__init__(session_id, socketio)
        
        # Initialize assistants components
        self.assistant_manager = AssistantManager(session_id)
        self.thread_manager = ThreadManager()
        self.file_manager = FileManager()
        
        # Initialize query classification and handlers
        self.query_classifier = SmartQueryClassifier()
        self.conversation_handler = None
        self.textual_analytical_handler = None
        self.analytical_handler = None
        
        # Get or create thread (maps to session_id)
        self.thread_id = self.thread_manager.create_or_get_thread(session_id)
        
        # Track conversation state
        self.conversation_context = {
            "has_data": False,
            "filename": None,
            "shape": None,
            "columns": []
        }
        
        # Azure Blob Storage configuration (preserved from original)
        self.blob_service_client = None
        self.container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'analysis-files')
        self.analysis_folder_name = os.getenv('AZURE_ANALYSIS_FOLDER', 'data-analysis')
        self.blob_sas_url = None
        self._initialize_blob_client()
        
        # Assistants-specific tracking
        self.current_file_ids = []  # Track uploaded file IDs
        self.streaming_adapter = None
        
        # Track all generated files (not just images)
        self.generated_files = {
            'images': [],
            'reports': [],
            'data_files': [],
            'other': []
        }
        
        print(f"✅ Enhanced analyzer with Assistants API initialized for session: {session_id}")
    
    def _initialize_blob_client(self):
        """Initialize Azure Blob Storage client (preserved from original)"""
        try:
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            account_url = os.getenv('AZURE_STORAGE_ACCOUNT_URL')
            account_key = os.getenv('AZURE_STORAGE_KEY')
            
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
                
        except Exception as e:
            logging.error(f"Failed to initialize blob client: {str(e)}")
            self.blob_service_client = None

    def load_csv_from_sas_url(self, sas_url: str, file_extension: str = None) -> bool:
        """Load CSV or Excel file directly from SAS URL and upload to assistants"""
        try:
            # Store the SAS URL for future operations
            self.blob_sas_url = sas_url
            self.original_file_path = sas_url
            
            # Determine file type
            if file_extension:
                file_ext = file_extension.lower()
            else:
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

            # Upload to assistants for analysis
            self._upload_to_assistants(sas_url, file_ext)

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

    def _upload_to_assistants(self, sas_url: str, file_ext: str):
        """Upload file to OpenAI Assistants for analysis"""
        try:
            # Download file temporarily
            import requests
            import tempfile
            
            response = requests.get(sas_url)
            response.raise_for_status()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            try:
                # Upload to assistants
                file_id = self.file_manager.upload_csv_file(temp_path, self.session_id)
                self.current_file_ids.append(file_id)
                
                logging.info(f"✅ Uploaded file to assistants: {file_id}")
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logging.warning(f"⚠️ Could not delete temp file: {e}")
                    
        except Exception as e:
            logging.error(f"❌ Error uploading to assistants: {e}")
            # Continue without assistants file - can still do basic analysis
    
    def load_csv(self, filepath: str) -> bool:
        """Override load_csv to update conversation context and upload to assistants"""
        
        # Call parent method to load CSV
        success = super().load_csv(filepath)
        
        if success:
            # Upload to assistants
            try:
                file_id = self.file_manager.upload_csv_file(filepath, self.session_id)
                self.current_file_ids.append(file_id)
                logging.info(f"✅ Uploaded {filepath} to assistants: {file_id}")
            except Exception as e:
                logging.error(f"⚠️ Could not upload to assistants: {e}")
            
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
        """Initialize all query handlers with current data context"""
        
        try:
            # Initialize conversation handler (using assistants)
            self.conversation_handler = ConversationHandler(
                self.session_id, 
                self.socketio,
                assistant_manager=self.assistant_manager,
                thread_manager=self.thread_manager
            )
            
            # Initialize textual analytical handler (using assistants)
            if self.df is not None:
                self.textual_analytical_handler = TextualAnalyticalHandler(
                    self.session_id,
                    self.df,
                    self.socketio,
                    self.csv_info,
                    assistant_manager=self.assistant_manager,
                    thread_manager=self.thread_manager,
                    file_manager=self.file_manager
                )
            
            # Initialize analytical handler (using assistants)
            self.analytical_handler = AnalyticalHandler(
                self.session_id,
                self,
                self.socketio,
                assistant_manager=self.assistant_manager,
                thread_manager=self.thread_manager,
                file_manager=self.file_manager
            )
            
            print("✅ All query handlers initialized with Assistants API")
            
        except Exception as e:
            print(f"⚠️ Failed to initialize some handlers: {e}")
            # Continue anyway - fallback to original behavior
    
    def analyze_query_streaming(self, user_query: str) -> Dict[str, Any]:
        """
        FIXED analyze_query_streaming with proper response handling.
        
        Changes:
        1. Fixed conversational queries to return proper responses
        2. Fixed textual analytical queries to actually return data
        3. Added explanation generation for all analytical queries
        4. Fixed report generation and file handling
        """
        
        try:
            # Set analyzing flag
            self.is_analyzing = True
            
            # STEP 1: Smart Query Classification (FIXED)
            has_data = self.df is not None
            query_category, classification_metadata = self.query_classifier.classify_query(
                user_query, 
                has_data=has_data
            )
            
            self.emit_stream('status', f"🧠 Query classified as: {query_category}")
            
            print(f"📋 Query classified as: {query_category}")
            print(f"🔍 Metadata: {classification_metadata}")
            
            # STEP 2: Handle based on classification (FIXED)
            if not classification_metadata.get('requires_analysis', False):
                # Simple response, no analysis needed (FIXED TO USE ASSISTANTS)
                return self._handle_simple_conversational_query(user_query, query_category)
            
            # STEP 3: Route to appropriate handler for analytical queries (FIXED)
            result = self._route_query_to_handler_with_assistants(user_query, query_category, classification_metadata)
            
            # STEP 4: Add explanation to all analytical results (NEW)
            if result.get('success') and result.get('type') != 'conversational':
                result = self._add_explanation_to_result(result, user_query)
                
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
        
        return result
    
    def _handle_simple_conversational_query(self, user_query: str, category: str) -> Dict[str, Any]:
        """
        FIXED: Handle simple conversational queries using Assistants API
        """
        try:
            self.emit_stream('status', '💬 Processing conversational query with AI...')
            
            # Use Assistants API for conversational queries
            if self.assistant_manager and self.thread_manager:
                assistant_id = self.assistant_manager.create_or_get_assistant("conversational")
                
                # Add context about the data if available
                context_message = ""
                if self.df is not None:
                    context_message = f"\n\nContext: I have access to a dataset with {self.df.shape[0]} rows and {self.df.shape[1]} columns containing data about: {', '.join(list(self.df.columns)[:5])}"
                
                enhanced_query = user_query + context_message
                
                result = self.assistant_manager.run_assistant_analysis(
                    self.thread_id,
                    enhanced_query
                )
                
                if result.get("success"):
                    ai_response = result.get("response_content", self.query_classifier.get_simple_response(user_query, category))
                else:
                    ai_response = self.query_classifier.get_simple_response(user_query, category)
            else:
                ai_response = self.query_classifier.get_simple_response(user_query, category)
            
            # Stream the response
            self.emit_stream('response', ai_response)
            self.emit_stream('completion', 'Response complete!')
            
            return {
                "query": user_query,
                "type": "conversational",
                "success": True,
                "response": ai_response,
                "generated_images": [],
                "dataframes": {},
                "requires_analysis": False,
                "category": category,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            fallback_response = self.query_classifier.get_simple_response(user_query, category)
            self.emit_stream('response', fallback_response)
            
            return {
                "query": user_query,
                "type": "conversational",
                "success": True,
                "response": fallback_response,
                "generated_images": [],
                "dataframes": {},
                "error": f"AI response failed, used fallback: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _route_query_to_handler_with_assistants(self, user_query: str, category: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Route the query to the appropriate handler using Assistants API (FIXED)"""
        
        # Extract intent data
        intent_data = self.query_classifier.extract_analysis_intent(user_query, category, metadata)
        
        # Check for stop signal before routing
        self.check_stop_signal()
        
        # Route based on category (FIXED LOGIC)
        if category == "analytical":
            # Determine if it's complex analysis
            analysis_indicators = metadata.get('analysis_indicators', [])
            
            # Check for report request
            if self._is_report_request(user_query):
                return self._handle_report_generation_query(user_query, intent_data)
            
            # Complex analysis indicators
            complex_indicators = ['forecast', 'predict', 'report', 'comprehensive', 'detailed', 'chart', 'plot', 'graph', 'visualize']
            is_complex = any(indicator in analysis_indicators for indicator in complex_indicators)
            
            if is_complex or len(analysis_indicators) >= 3:
                return self._handle_fully_analytical_query_with_assistants(user_query, intent_data)
            else:
                return self._handle_textual_analytical_query_with_assistants(user_query, intent_data)
        
        else:
            # Fallback to original behavior
            print(f"⚠️ Unknown category '{category}', falling back to original analysis")
            return self._fallback_to_original_analysis(user_query)
    
    def _handle_textual_analytical_query_with_assistants(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """FIXED: Handle simple analytical queries using Assistants API"""
        
        print("📊 Handling textual analytical query with Assistants API")
        
        try:
            # Check if we have data
            if self.df is None:
                self.emit_stream('error', "No CSV file loaded. Please upload a CSV file first.")
                return {
                    "error": "No CSV file loaded",
                    "type": "textual_analytical",
                    "success": False
                }
            
            # Create textual analytical assistant
            assistant_id = self.assistant_manager.create_or_get_assistant("textual_analytical")
            
            # Enhance query with data context
            enhanced_query = f"""
            Answer this question about the dataset: {user_query}
            
            Dataset Info:
            - Shape: {self.df.shape}
            - Columns: {list(self.df.columns)}
            
            Provide a clear, concise answer with specific numbers and insights.
            """
            
            # Run assistant analysis with file attachments
            result = self.assistant_manager.run_assistant_analysis(
                self.thread_id,
                enhanced_query,
                file_ids=self.current_file_ids
            )
            
            if result.get("success"):
                # Extract result value
                response_text = result.get("response_content", "Analysis completed")
                
                # Stream the response
                self.emit_stream('output', response_text)
                self.emit_stream('completion', 'Analysis complete!')
                
                # Convert to expected format
                return {
                    "query": user_query,
                    "type": "textual_analytical", 
                    "success": True,
                    "response": response_text,
                    "generated_code": result.get("generated_code", ""),
                    "execution_result": {"success": True, "result": response_text},
                    "generated_images": [],
                    "dataframes": {},
                    "analysis_type": intent_data.get("analysis_type", "general"),
                    "timestamp": datetime.now().isoformat(),
                    "assistant_id": assistant_id,
                    "thread_id": self.thread_id
                }
            else:
                # Fallback to original handler
                return self._fallback_textual_analytical_handler(user_query, intent_data)
                
        except Exception as e:
            print(f"❌ Assistants textual analytical handler failed: {e}")
            return self._fallback_textual_analytical_handler(user_query, intent_data)
    
    def _handle_fully_analytical_query_with_assistants(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """FIXED: Handle complex analytical queries using Assistants API with streaming"""
        
        print("🔬 Handling fully analytical query with Assistants API")
        
        try:
            # Check if we have data
            if self.df is None:
                self.emit_stream('error', "No CSV file loaded. Please upload a CSV file first.")
                return {
                    "error": "No CSV file loaded",
                    "type": "fully_analytical",
                    "success": False
                }
            
            # Create data analyst assistant
            assistant_id = self.assistant_manager.create_or_get_assistant("data_analyst")
            
            # Enhance query for better analysis
            enhanced_query = f"""
            Analyze the dataset and answer: {user_query}
            
            Requirements:
            1. Perform thorough data analysis
            2. Create visualizations when appropriate
            3. Provide clear insights and explanations
            4. Generate charts/plots using matplotlib
            5. Explain what you found and what it means
            
            Dataset shape: {self.df.shape}
            Columns: {list(self.df.columns)}
            """
            
            # Add user message to thread
            self.thread_manager.add_message_to_thread(
                self.thread_id,
                "user",
                enhanced_query,
                file_ids=self.current_file_ids
            )
            
            # Create run
            run = self.assistant_manager.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=assistant_id
            )
            
            # Initialize streaming adapter
            self.streaming_adapter = StreamingAdapter(
                self.assistant_manager.client,
                self._emit_streaming_callback
            )
            
            # Stream the run with real-time updates
            result = self.streaming_adapter.stream_assistant_run(
                self.thread_id,
                run.id,
                self.session_id
            )
            
            if result.get("success"):
                # Download generated files (images, etc.)
                generated_files = self._download_and_categorize_generated_files(result.get("generated_files", []))
                
                # Convert to expected format with enhanced data
                return {
                    "query": user_query,
                    "type": "fully_analytical",
                    "success": True,
                    "response": result.get("response_content", ""),
                    "generated_code": result.get("generated_code", ""),
                    "execution_result": {
                        "success": True,
                        "output": "\n".join(result.get("execution_outputs", []))
                    },
                    "generated_images": generated_files.get('images', []),
                    "generated_files": generated_files,  # NEW: All file types
                    "dataframes": {},  # TODO: Extract DataFrames from assistant output
                    "analysis_type": intent_data.get("analysis_type", "general"),
                    "timestamp": datetime.now().isoformat(),
                    "assistant_id": assistant_id,
                    "thread_id": self.thread_id,
                    "run_id": run.id
                }
            else:
                # Fallback to original handler
                return self._fallback_fully_analytical_handler(user_query, intent_data)
                
        except Exception as e:
            print(f"❌ Assistants fully analytical handler failed: {e}")
            return self._fallback_fully_analytical_handler(user_query, intent_data)
    
    def _handle_report_generation_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """NEW: Handle report generation queries specifically"""
        
        print("📋 Handling report generation query")
        
        try:
            # First, run the analysis to get data
            analysis_result = self._handle_fully_analytical_query_with_assistants(user_query, intent_data)
            
            if not analysis_result.get("success"):
                return analysis_result
            
            # Generate HTML report
            report_html = self._generate_html_report(user_query, analysis_result)
            
            if report_html:
                # Save report to file
                report_filename = f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                report_path = self.reports_dir / report_filename
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report_html)
                
                # Upload to blob storage
                report_url = self._upload_file_to_blob(str(report_path), "reports")
                
                # Update generated files
                if 'reports' not in analysis_result.get('generated_files', {}):
                    analysis_result['generated_files'] = analysis_result.get('generated_files', {})
                    analysis_result['generated_files']['reports'] = []
                
                analysis_result['generated_files']['reports'].append({
                    'filename': report_filename,
                    'path': str(report_path),
                    'url': report_url,
                    'type': 'html_report'
                })
                
                # Update result type and add report content
                analysis_result.update({
                    "type": "report",  # FIXED: Use 'report' type
                    "report_html": report_html,
                    "report_url": report_url,
                    "report_filename": report_filename
                })
                
                # Stream the report
                self.emit_stream('report', {
                    'html': report_html,
                    'filename': report_filename,
                    'url': report_url
                })
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            return {
                "query": user_query,
                "type": "report",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_html_report(self, user_query: str, analysis_result: Dict[str, Any]) -> str:
        """Generate HTML report from analysis results"""
        
        try:
            report_title = f"Data Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Get generated images
            images_html = ""
            generated_files = analysis_result.get('generated_files', {})
            if 'images' in generated_files:
                images_html = "<h2>Visualizations</h2>"
                for img in generated_files['images']:
                    if 'url' in img:
                        images_html += f'<div><img src="{img["url"]}" alt="{img["filename"]}" style="max-width: 100%; height: auto; margin: 10px 0;"></div>'
            
            # Create HTML report
            html_report = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{report_title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                    h2 {{ color: #34495e; margin-top: 30px; }}
                    .analysis-section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .code-section {{ background: #2c3e50; color: white; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                    .metadata {{ color: #666; font-size: 0.9em; }}
                    img {{ border: 1px solid #ddd; border-radius: 8px; }}
                </style>
            </head>
            <body>
                <h1>{report_title}</h1>
                
                <div class="metadata">
                    <p><strong>Query:</strong> {user_query}</p>
                    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
                    <p><strong>Dataset Shape:</strong> {self.df.shape if self.df is not None else 'N/A'}</p>
                </div>
                
                <div class="analysis-section">
                    <h2>Analysis Results</h2>
                    <p>{analysis_result.get('response', 'Analysis completed successfully.')}</p>
                </div>
                
                {images_html}
                
                <div class="analysis-section">
                    <h2>Technical Details</h2>
                    <p><strong>Analysis Type:</strong> {analysis_result.get('analysis_type', 'General')}</p>
                    <p><strong>Success:</strong> {'Yes' if analysis_result.get('success') else 'No'}</p>
                    <div class="code-section">
                        <h3>Generated Code</h3>
                        <pre>{analysis_result.get('generated_code', 'No code generated')}</pre>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html_report
            
        except Exception as e:
            print(f"❌ Error generating HTML report: {e}")
            return f"<html><body><h1>Report Generation Error</h1><p>{str(e)}</p></body></html>"
    
    def _download_and_categorize_generated_files(self, file_ids: list) -> dict:
        """Download and categorize generated files from assistants"""
        categorized_files = {
            'images': [],
            'reports': [],
            'data_files': [],
            'other': []
        }
        
        for file_id in file_ids:
            try:
                # Get file info to determine type
                file_info = self.file_manager.get_file_info(file_id)
                filename = file_info.get('filename', f'file_{file_id}')
                
                # Determine file category
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    category = 'images'
                    save_dir = str(self.images_dir)
                elif filename.lower().endswith(('.html', '.htm')):
                    category = 'reports'
                    save_dir = str(self.reports_dir)
                elif filename.lower().endswith(('.csv', '.xlsx', '.json')):
                    category = 'data_files'
                    save_dir = str(self.data_dir)
                else:
                    category = 'other'
                    save_dir = str(self.output_dir)
                
                # Download file
                local_path = self.file_manager.download_generated_file(
                    file_id,
                    save_dir,
                    filename
                )
                
                # Upload to blob storage if available
                blob_url = None
                if self.blob_service_client:
                    blob_url = self._upload_file_to_blob(local_path, category)
                
                # Add to categorized files
                file_entry = {
                    'file_id': file_id,
                    'filename': filename,
                    'local_path': local_path,
                    'category': category,
                    'url': blob_url
                }
                
                categorized_files[category].append(file_entry)
                
                # For images, also emit to frontend immediately
                if category == 'images':
                    self._emit_image_to_frontend(local_path, blob_url)
                
            except Exception as e:
                logging.error(f"Error downloading file {file_id}: {e}")
                # Add to other category with error info
                categorized_files['other'].append({
                    'file_id': file_id,
                    'error': str(e),
                    'category': 'error'
                })
        
        return categorized_files
    
    def _emit_image_to_frontend(self, file_path: str, blob_url: str = None):
        """Emit image to frontend in expected format"""
        try:
            import base64
            with open(file_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            
            self.emit_stream('image', {
                'filename': os.path.basename(file_path),
                'data': f"data:image/png;base64,{img_data}",
                'path': file_path,
                'url': blob_url,
                'thisis': 3  # Assistant generated
            })
            
        except Exception as e:
            logging.error(f"Error emitting image: {e}")
    
    def _add_explanation_to_result(self, result: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        """NEW: Add explanation to analytical results"""
        
        if not result.get('success'):
            return result
        
        try:
            # Generate explanation based on what was done
            explanation = self._generate_analysis_explanation(result, user_query)
            
            # Add explanation to response
            current_response = result.get('response', '')
            if explanation:
                if current_response:
                    result['response'] = f"{current_response}\n\n### What I Did:\n{explanation}"
                else:
                    result['response'] = explanation
            
            # Stream the explanation
            if explanation:
                self.emit_stream('explanation', explanation)
            
        except Exception as e:
            print(f"⚠️ Failed to generate explanation: {e}")
        
        return result
    
    def _generate_analysis_explanation(self, result: Dict[str, Any], user_query: str) -> str:
        """Generate explanation of what was done in the analysis"""
        
        try:
            explanation_parts = []
            
            # Basic query analysis
            explanation_parts.append(f"I analyzed your request: '{user_query}'")
            
            # What type of analysis was performed
            analysis_type = result.get('analysis_type', result.get('type', 'general'))
            if analysis_type == 'forecasting':
                explanation_parts.append("• Performed forecasting analysis to predict future values")
            elif analysis_type == 'textual_analytical':
                explanation_parts.append("• Executed quick data analysis to answer your specific question")
            elif analysis_type == 'fully_analytical':
                explanation_parts.append("• Conducted comprehensive data analysis with visualizations")
            elif analysis_type == 'report':
                explanation_parts.append("• Generated a complete analytical report with insights and visualizations")
            
            # Code execution
            if result.get('generated_code'):
                explanation_parts.append("• Generated and executed Python code to analyze your data")
            
            # Files generated
            generated_files = result.get('generated_files', {})
            if generated_files:
                file_counts = []
                for category, files in generated_files.items():
                    if files:
                        file_counts.append(f"{len(files)} {category}")
                if file_counts:
                    explanation_parts.append(f"• Created {', '.join(file_counts)} for you")
            
            # Images generated (fallback)
            images = result.get('generated_images', [])
            if images and not generated_files.get('images'):
                explanation_parts.append(f"• Generated {len(images)} visualization(s)")
            
            # DataFrames created
            dataframes = result.get('dataframes', {})
            if dataframes:
                explanation_parts.append(f"• Created {len(dataframes)} data table(s) with results")
            
            # Success indicator
            if result.get('success'):
                explanation_parts.append("• Analysis completed successfully!")
            
            return "\n".join(explanation_parts)
            
        except Exception as e:
            return f"Analysis completed. (Explanation generation failed: {str(e)})"
    
    def _emit_streaming_callback(self, message_type: str, data: dict):
        """Callback for streaming adapter to emit data"""
        try:
            if self.socketio:
                self.socketio.emit('stream_data', data, room=self.session_id)
        except Exception as e:
            logging.error(f"Error in streaming callback: {e}")
    
    def _is_report_request(self, query: str) -> bool:
        """Detect if user is specifically requesting a report"""
        report_keywords = [
            'report', 'summary report', 'generate report', 'create report',
            'comprehensive report', 'strategic report', 'executive summary',
            'write report', 'full report', 'detailed report', 'analysis report'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in report_keywords)
    
    # Fallback methods to original handlers (PRESERVED)
    def _fallback_conversational_handler(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to original conversational handler"""
        try:
            if self.conversation_handler is None:
                self.conversation_handler = ConversationHandler(self.session_id, self.socketio)
            
            return self.conversation_handler.handle_conversational_query(
                user_query, 
                self.conversation_context
            )
        except Exception as e:
            return {
                "query": user_query,
                "type": "conversational",
                "success": True,
                "response": "I'm here to help you with data analysis. What would you like to explore in your dataset?",
                "generated_images": [],
                "dataframes": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def _fallback_textual_analytical_handler(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to original textual analytical handler"""
        try:
            if self.textual_analytical_handler is None:
                from .modified_handler import TextualAnalyticalHandler
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
            return self._fallback_to_original_analysis(user_query)
    
    def _fallback_fully_analytical_handler(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to original fully analytical handler"""
        try:
            if self.analytical_handler is None:
                from .modified_handler import AnalyticalHandler
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
            return self._fallback_to_original_analysis(user_query)
    
    def _fallback_to_original_analysis(self, user_query: str) -> Dict[str, Any]:
        """Fallback to the original analysis method when handlers fail"""
        
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
    
    def stop_current_analysis(self):
        """Stop current assistant analysis"""
        try:
            if self.streaming_adapter:
                self.streaming_adapter.stop_streaming()
            
            # Try to cancel any active runs
            if hasattr(self, 'current_run_id') and self.current_run_id:
                self.streaming_adapter.cancel_run(self.thread_id, self.current_run_id)
            
        except Exception as e:
            logging.error(f"Error stopping analysis: {e}")
    
    def cleanup_assistants_resources(self):
        """Clean up all assistants resources"""
        try:
            # Clean up files
            self.file_manager.cleanup_session_files(self.session_id)
            
            # Clean up thread
            self.thread_manager.cleanup_session_thread(self.session_id)
            
            # Clean up assistant
            self.assistant_manager.cleanup_assistant()
            
            logging.info(f"🧹 Cleaned up assistants resources for session: {self.session_id}")
            
        except Exception as e:
            logging.error(f"⚠️ Error cleaning up assistants resources: {e}")
    
    # Preserve all existing methods from parent class
    def get_conversation_context(self) -> Dict[str, Any]:
        """Get current conversation context for handlers"""
        return self.conversation_context.copy()
    
    def update_conversation_context(self, **kwargs):
        """Update conversation context"""
        self.conversation_context.update(kwargs)
    
    def get_analysis_capabilities(self) -> Dict[str, Any]:
        """Get information about analysis capabilities"""
        
        capabilities = {
            "conversational": {
                "description": "Friendly chat and questions about capabilities",
                "examples": ["Hi, how are you?", "What can you do?", "Tell me a joke"],
                "powered_by": "OpenAI Assistants API"
            },
            "textual_analytical": {
                "description": "Simple data questions with quick text answers",
                "examples": ["What is the highest revenue?", "How many rows are there?", "What's the average age?"],
                "powered_by": "OpenAI Assistants API with Code Interpreter"
            },
            "fully_analytical": {
                "description": "Complex analysis with visualizations and detailed reports",
                "examples": ["Generate a 5-year forecast", "Create a comprehensive report", "Analyze sales trends"],
                "powered_by": "OpenAI Assistants API with Code Interpreter and Streaming"
            },
            "report_generation": {
                "description": "Generate complete HTML reports with visualizations",
                "examples": ["Create a report", "Generate executive summary", "Make comprehensive analysis report"],
                "powered_by": "OpenAI Assistants API + Custom Report Generator"
            }
        }
        
        if self.df is not None:
            capabilities["data_info"] = {
                "shape": self.df.shape,
                "columns": list(self.df.columns),
                "numeric_columns": list(self.df.select_dtypes(include=['number']).columns),
                "categorical_columns": list(self.df.select_dtypes(include=['object']).columns),
                "assistant_files": len(self.current_file_ids),
                "thread_id": self.thread_id
            }
        
        return capabilities
    
    # Preserve existing blob storage methods and other methods...
    def _upload_file_to_blob(self, local_file_path: str, blob_subfolder: str) -> str:
        """Upload file to Azure Blob Storage and return public URL"""
        try:
            if not self.blob_service_client:
                return ""
            
            file_name = os.path.basename(local_file_path)
            blob_name = f"{self.analysis_folder_name}/{blob_subfolder}/{file_name}"
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            # Generate SAS URL for access
            account_name = self.blob_service_client.account_name
            account_key = os.getenv('AZURE_STORAGE_KEY')
            
            if account_key:
                sas_token = generate_blob_sas(
                    account_name=account_name,
                    container_name=self.container_name,
                    blob_name=blob_name,
                    account_key=account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=24)
                )
                
                return f"{blob_client.url}?{sas_token}"
            else:
                return blob_client.url
                
        except Exception as e:
            logging.error(f"Error uploading to blob: {e}")
            return ""
    
    # All other existing methods are inherited from parent class

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

    # Preserve existing blob storage methods
    def upload_stream_and_get_sas_url(self, file_stream, original_filename: str, blob_subfolder: str = None, expiry_hours: int = 168) -> dict:
        """Upload file stream directly to blob storage and return SAS token URL (preserved from original)"""
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
    
    # All other existing methods are inherited from parent class
    def __getattr__(self, name):
        """Ensure all parent methods are accessible"""
        if hasattr(super(), name):
            return getattr(super(), name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")