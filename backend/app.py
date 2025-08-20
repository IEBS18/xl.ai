
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

import base64
import logging
import os
import json
import re
from urllib.parse import urlparse
import uuid
from datetime import datetime
import threading
import traceback
from pathlib import Path
import asyncio


from flask import Flask, render_template, request, jsonify, session, send_file, Response
from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd

# Import ENHANCED analyzer and utilities (UPDATED for Assistants API)
from handlers.enhanced_analyzer import EnhancedStreamingAnalyzer 
from utils.utils import (
    ConversationHistory,
    generate_tailwind_table,
    generate_sheet_images_with_highlighting,
    generate_simple_table,
    stop_analysis_for_session,
    clear_stop_signal_for_session,
    cleanup_session_data,
    is_session_inactive,
    is_session_too_old,
    update_session_activity,
    get_session_stats,
    validate_session_exists,
    create_session_summary,
    StopAnalysisException,
    LANGCHAIN_AVAILABLE
)

from dotenv import load_dotenv
from auth import auth_blueprint, init_db
import requests
import tempfile

from flask_mail import Mail


load_dotenv()

GOTENBERG_URL = os.getenv('GOTENBERG_URL')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024  # 50MB max file size

# Register auth blueprint
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_FROM')

# Initialize Flask-Mail
mail = Mail(app)

# Make mail app available to blueprints through environ
@app.before_request
def set_mail_app():
    from flask import request
    request.environ['mail_app'] = app

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
    "http://20.197.12.172",
    "https://insipredict.ai",
    "https://www.insipredict.ai"
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

# NEW: Ensure reports output directory exists
REPORTS_OUTPUT_DIR = os.path.join(os.getcwd(), 'backend', 'output')
os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)
print(f"📁 Reports output directory: {REPORTS_OUTPUT_DIR}")
# Global storage for analyzer instances per session - NOW USING ENHANCED ANALYZER WITH ASSISTANTS API
analyzers = {}
session_data = {}

# Session cleanup configuration
SESSION_CLEANUP_ENABLED = True
SESSION_MAX_AGE_HOURS = 24
SESSION_MAX_INACTIVE_HOURS = 24

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main chat interface."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')


@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file_with_session():
    """Handle CSV file upload - ENHANCED for Assistants API support"""
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
        
        # Initialize ENHANCED analyzer (now with Assistants API)
        analyzer = EnhancedStreamingAnalyzer(new_session_id, socketio)
        
        # Check if blob storage is available
        if not analyzer.blob_service_client:
            return jsonify({'error': 'Blob storage not configured. Please check Azure credentials.'}), 500
        
        logging.info("Processing file upload with Assistants API support")
        
        # Upload file stream directly to blob storage and get SAS URL
        blob_result = analyzer.upload_stream_and_get_sas_url(
            file.stream, 
            file.filename, 
            expiry_hours=168  # 7 days
        )
        
        if not blob_result['success']:
            return jsonify({'error': f"Failed to upload to blob storage: {blob_result.get('error')}"}), 500
        
        # Load and analyze file directly from SAS URL (this also uploads to Assistants)
        file_extension = os.path.splitext(file.filename)[-1]
        if not analyzer.load_csv_from_sas_url(blob_result['sas_url'], file_extension):
            return jsonify({'error': 'Failed to load and analyze file from blob storage'}), 500
        
        # Store analyzer and session data
        analyzers[new_session_id] = analyzer
        session_data[new_session_id] = {
            'filename': file.filename,
            'blob_sas_url': blob_result['sas_url'],
            'blob_name': blob_result['blob_name'],
            'sas_expires_at': blob_result['expires_at'],
            'upload_time': datetime.now().isoformat(),
            'shape': analyzer.df.shape,
            'columns': list(analyzer.df.columns),
            'created_by': session.get('user_id', 'anonymous'),
            'last_activity': datetime.now().isoformat(),
            'analyzer_type': 'enhanced_assistants',  # Updated type
            'storage_type': 'blob_only',
            'assistants_enabled': True,  # New flag
            'thread_id': analyzer.thread_id  # Store thread ID
        }
           
        # Clear any existing stop signals for this session
        clear_stop_signal_for_session(new_session_id)
           
        print(f"✅ Created new ASSISTANTS session: {new_session_id} for file: {file.filename}")
        print(f"📁 File stored and analyzed with Assistants API")
           
        # Generate page-based preview for all file types
        try:
            # Download file temporarily for page preview generation
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, file.filename)
            
            # Download from blob to temp file for preview generation
            blob_client = analyzer.blob_service_client.get_blob_client(
                container=analyzer.container_name, 
                blob=blob_result['blob_name']
            )
            
            with open(temp_file_path, "wb") as temp_file:
                blob_data = blob_client.download_blob()
                temp_file.write(blob_data.readall())
            
            # Use new image-based preview system for all file types
            preview_html = generate_sheet_images_with_highlighting(temp_file_path, max_sheets=3)
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
        except Exception as e:
            print(f"Failed to generate file preview: {e}")
            # Fallback to simple message in image-style layout
            preview_html = f'''
            <div class="sheet-images-preview bg-gray-50 dark:bg-gray-900 p-6">
                <div class="max-w-6xl mx-auto">
                    <div class="mb-6">
                        <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">File Uploaded Successfully</h2>
                        <p class="text-gray-600 dark:text-gray-300">Preview generation encountered an issue, but file processing completed.</p>
                    </div>
                    <div class="sheet-image-container">
                        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
                            <div class="bg-gray-50 dark:bg-gray-700 px-6 py-4 border-b">
                                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{file.filename}</h3>
                                <p class="text-sm text-gray-600 dark:text-gray-300">
                                    File processed: {analyzer.df.shape[0]} rows × {analyzer.df.shape[1]} columns
                                </p>
                            </div>
                            <div class="p-8 text-center">
                                <div class="bg-blue-50 dark:bg-blue-900 p-6 rounded-lg">
                                    <div class="text-blue-600 dark:text-blue-300 mb-4">
                                        <svg class="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                        </svg>
                                    </div>
                                    <h4 class="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">File Ready for Analysis</h4>
                                    <p class="text-blue-800 dark:text-blue-200">
                                        Your file has been successfully uploaded and is ready for analysis. You can now ask questions about your data.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            '''

        response_data = {
            'success': True,
            'sessionId': new_session_id,
            'message': f'File uploaded and analyzed with Assistants API! Shape: {analyzer.df.shape}',
            'data': {
                'filename': file.filename,
                'shape': analyzer.df.shape,
                'columns': list(analyzer.df.columns),
                'preview': preview_html,
                'sheets': {
                    'preview': preview_html
                },
                'data': analyzer.df.head(100).to_dict('records'),
                'sessionId': new_session_id,
                'storage_type': 'blob_only',
                'blob_info': {
                    'blob_name': blob_result['blob_name'],
                    'expires_at': blob_result['expires_at'],
                    'expiry_hours': blob_result['expiry_hours']
                },
                'assistants_info': {  # New section
                    'thread_id': analyzer.thread_id,
                    'assistants_enabled': True,
                    'file_uploaded_to_assistants': len(analyzer.current_file_ids) > 0
                },
                'features': {
                    'conversational': True,
                    'textual_analytical': True,
                    'fully_analytical': True,
                    'enhanced_capabilities': True,
                    'blob_storage_only': True,
                    'memory_efficient': True,
                    'assistants_api': True  # New feature flag
                }
            }
        }
        
        # Add multiple sheets info if available (for Excel files with multiple sheets)
        if hasattr(analyzer, 'sheets_info') and analyzer.sheets_info:
            response_data['data']['sheets'] = list(analyzer.sheets_info.values())
            print(f"📊 Added {len(response_data['data']['sheets'])} sheets to upload response")
        
        response = jsonify(response_data)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
           
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        logging.exception("Detailed upload error")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

def convert_external_images_to_base64(html_content):
    """
    Convert external image URLs in HTML to base64 data URLs - FIXED VERSION
    Handles duplicate images by downloading once and reusing base64 data
    """
    
    # More comprehensive regex to catch different img tag formats
    img_pattern = r'<img[^>]+src\s*=\s*["\']([^"\']+)["\'][^>]*>'
    
    # Cache for downloaded images: URL -> base64 data URL
    image_cache = {}
    processed_count = 0
    
    logging.info(f"Starting image conversion process...")
    
    def replace_img_src(match):
        nonlocal processed_count
        full_img_tag = match.group(0)
        img_url = match.group(1).strip('\'"')  # Remove any quotes
        
        # Skip if already base64 or relative URL
        if (img_url.startswith('data:') or 
            not img_url.startswith(('http://', 'https://'))):
            return full_img_tag
        
        # Check if we already have this image cached
        if img_url in image_cache:
            logging.info(f"🔄 Using cached base64 for: {img_url[:80]}...")
            # Create new img tag with cached base64 src
            new_img_tag = re.sub(
                r'src\s*=\s*["\']?[^"\'>\s]+["\']?', 
                f'src="{image_cache[img_url]}"', 
                full_img_tag, 
                flags=re.IGNORECASE
            )
            processed_count += 1
            return new_img_tag
        
        try:
            logging.info(f"🔄 Converting: {img_url[:80]}...")
            
            # Download with retry logic and proper headers
            success = False
            content = None
            content_type = None
            
            for attempt in range(3):  # Try 3 times
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                    
                    response = requests.get(
                        img_url, 
                        timeout=30, 
                        headers=headers, 
                        stream=False,
                        allow_redirects=True,
                        verify=True
                    )
                    response.raise_for_status()
                    
                    # Read content
                    content = response.content
                    if len(content) == 0:
                        raise ValueError("Empty image content")
                    
                    # Get content type
                    content_type = response.headers.get('content-type', '').lower()
                    
                    success = True
                    break
                    
                except Exception as e:
                    logging.warning(f"⚠️ Attempt {attempt + 1} failed for {img_url}: {str(e)}")
                    if attempt == 2:  # Last attempt
                        raise
            
            if not success or not content:
                logging.error(f"❌ Failed to download {img_url}")
                return full_img_tag
            
            # Determine content type if not provided or invalid
            if not content_type or not content_type.startswith('image/'):
                # Try to guess from URL extension
                parsed_url = urlparse(img_url)
                extension = os.path.splitext(parsed_url.path)[1].lower()
                extension_map = {
                    '.jpg': 'image/jpeg', 
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png', 
                    '.gif': 'image/gif',
                    '.svg': 'image/svg+xml', 
                    '.webp': 'image/webp',
                    '.bmp': 'image/bmp',
                    '.tiff': 'image/tiff',
                    '.ico': 'image/x-icon'
                }
                content_type = extension_map.get(extension, 'image/png')
            
            # Clean content type (remove charset and other parameters)
            content_type = content_type.split(';')[0].strip()
            
            # Convert to base64
            try:
                img_base64 = base64.b64encode(content).decode('utf-8')
                data_url = f"data:{content_type};base64,{img_base64}"
                
                # Validate base64 encoding
                if len(img_base64) < 10:
                    raise ValueError("Base64 encoding too short")
                
                # Cache the base64 data URL for reuse
                image_cache[img_url] = data_url
                
                # Create new img tag with base64 src
                new_img_tag = re.sub(
                    r'src\s*=\s*["\']?[^"\'>\s]+["\']?', 
                    f'src="{data_url}"', 
                    full_img_tag, 
                    flags=re.IGNORECASE
                )
                
                processed_count += 1
                logging.info(f"✅ Converted successfully ({len(content)} bytes) -> {len(img_base64)} base64 chars")
                
                return new_img_tag
                
            except Exception as encode_error:
                logging.error(f"❌ Base64 encoding failed for {img_url}: {str(encode_error)}")
                return full_img_tag
                
        except Exception as e:
            logging.error(f"❌ Failed to convert {img_url}: {str(e)}")
            return full_img_tag
    
    # Process all img tags
    try:
        updated_html = re.sub(img_pattern, replace_img_src, html_content, flags=re.IGNORECASE)
        logging.info(f"🎯 Total unique images downloaded: {len(image_cache)}")
        logging.info(f"🎯 Total image tags processed: {processed_count}")
        return updated_html
    except Exception as e:
        logging.error(f"❌ Error processing HTML: {str(e)}")
        return html_content


async def generate_pdf_with_playwright(html_content):
    """
    Generate PDF using Playwright - works perfectly in Docker
    """
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Launch browser with Docker-friendly settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection'
                ]
            )
            
            page = await browser.new_page()
            
            # Set viewport for consistent rendering
            await page.set_viewport_size({"width": 1200, "height": 800})
            
            # Set content and wait for everything to load
            await page.set_content(html_content, wait_until='networkidle')
            
            # Wait for all images to load (this handles external images automatically)
            await page.wait_for_load_state('networkidle')
            
            # Additional wait for any lazy-loaded content
            await page.wait_for_timeout(5000)  # 5 seconds
            
            # Wait for all images specifically
            try:
                await page.wait_for_function("""
                    () => {
                        const images = Array.from(document.images);
                        return images.every(img => img.complete);
                    }
                """, timeout=10000)
            except:
                logging.warning("Some images may not have loaded completely")
            
            # Generate PDF with high quality settings
            pdf_bytes = await page.pdf(
                format='A4',
                margin={
                    'top': '0.4in',
                    'bottom': '0.4in', 
                    'left': '0.4in',
                    'right': '0.4in'
                },
                print_background=True,
                prefer_css_page_size=True,
                display_header_footer=False,
                scale=1.0
            )
            
            await browser.close()
            logging.info(f"✅ PDF generated successfully with Playwright ({len(pdf_bytes)} bytes)")
            return pdf_bytes
            
    except Exception as e:
        logging.error(f"❌ Playwright PDF generation failed: {e}")
        raise


def generate_pdf_with_playwright_sync(html_content):
    """Synchronous wrapper for Playwright - handles event loops properly"""
    try:
        # Check if we're in an existing event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in a running loop, we need to use run_in_executor
            import concurrent.futures
            import threading
            
            def run_async():
                return asyncio.run(generate_pdf_with_playwright(html_content))
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async)
                return future.result(timeout=60)  # 60 second timeout
                
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(generate_pdf_with_playwright(html_content))
            
    except Exception as e:
        logging.error(f"❌ Playwright sync wrapper failed: {e}")
        raise


@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    """
    Generate PDF from HTML content using Playwright - DOCKER OPTIMIZED
    """
    try:
        html_content = request.data.decode("utf-8")
        logging.info(f"📄 Processing HTML content ({len(html_content)} characters)")
        
        # Count images for debugging
        import re
        img_pattern = r'<img[^>]*?src\s*=\s*["\']([^"\']+)["\']'
        images = re.findall(img_pattern, html_content, re.IGNORECASE)
        external_images = [img for img in images if img.startswith(('http://', 'https://'))]
        
        logging.info(f"🔍 Found {len(images)} total images, {len(external_images)} external")
        
        # Generate PDF with Playwright (handles images automatically)
        pdf_bytes = generate_pdf_with_playwright_sync(html_content)
        
        if not pdf_bytes:
            raise ValueError("PDF generation returned empty result")
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(pdf_bytes)
            pdf_path = f.name
        
        logging.info(f"💾 PDF saved to: {pdf_path}")
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name="business_analysis_report.pdf",
            mimetype="application/pdf"
        )
        
    except ImportError as e:
        logging.error(f"❌ Playwright not available: {e}")
        return jsonify({
            "error": "Playwright not installed", 
            "details": "Please install playwright: pip install playwright && playwright install chromium"
        }), 500
        
    except Exception as e:
        logging.error(f"💥 Error in generate_pdf: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": "PDF generation failed", 
            "details": str(e)
        }), 500
    
@app.route('/session/<session_id>/info', methods=['GET', 'OPTIONS'])
def get_session_info(session_id):
    """Get information about a specific session - ENHANCED for Assistants"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        # Validate session exists
        is_valid, error_msg = validate_session_exists(session_id, analyzers, session_data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 404
        
        # Update last activity
        update_session_activity(session_id, session_data)
        
        # Get comprehensive session summary
        session_summary = create_session_summary(session_id, session_data, analyzers)
        
        # Get analyzer for data preview
        analyzer = analyzers[session_id]
        
        # Add enhanced analyzer capabilities info
        enhanced_info = {}
        if isinstance(analyzer, EnhancedStreamingAnalyzer):
            enhanced_info ={
                'enhanced_analyzer': True,
                'ai_routing_enabled': True,  # NEW
                'query_router_available': hasattr(analyzer.query_classifier, 'routers'),  # NEW
                'assistants_enabled': True,
                'thread_id': getattr(analyzer, 'thread_id', None),
                'uploaded_files_count': len(getattr(analyzer, 'current_file_ids', [])),
                'capabilities': analyzer.get_analysis_capabilities(),
                'conversation_context': analyzer.get_conversation_context(),
                'routing_features': {  # NEW
                    'intelligent_classification': True,
                    'context_aware_routing': True,
                    'automatic_fallback': True,
                    'dynamic_assistant_selection': True
                }
            }
        # Add data preview if DataFrame is available
        data_preview = None
        if analyzer.df is not None:
            try:
                # Create temporary file from DataFrame and generate image preview
                import tempfile
                import os
                
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, f"session_{session_id}_preview.csv")
                
                # Save DataFrame to temporary CSV file
                analyzer.df.head(100).to_csv(temp_file_path, index=False)
                
                # Generate image preview from temporary file
                data_preview = generate_sheet_images_with_highlighting(temp_file_path, max_sheets=1)
                
                # Clean up temporary file
                os.unlink(temp_file_path)
                
            except Exception as e:
                print(f"Failed to generate data preview: {e}")
                data_preview = '''
                <div class="sheet-images-preview bg-gray-50 dark:bg-gray-900 p-6">
                    <div class="max-w-4xl mx-auto">
                        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 text-center">
                            <p class="text-gray-600 dark:text-gray-300">Data preview unavailable</p>
                        </div>
                    </div>
                </div>
                '''
        
        # Create complete session info with preview
        file_info = {
            'filename': session_summary.get('filename'),
            'shape': session_summary.get('shape'),
            'columns': session_summary.get('columns'),
            'uploadTime': session_summary.get('uploadTime'),
            'lastActivity': session_summary.get('lastActivity'),
            'sessionId': session_id,
            'preview': data_preview,
            'sheets': {
                'preview': data_preview
            },
            'data': analyzer.df.head(100).to_dict('records') if analyzer.df is not None else []
        }
        
        # Add multiple sheets info if available (for Excel files)
        if hasattr(analyzer, 'sheets_info') and analyzer.sheets_info:
            file_info['sheets'] = list(analyzer.sheets_info.values())
            print(f"📊 Added {len(file_info['sheets'])} sheets to file info")
        else:
            # Single sheet (CSV or single sheet Excel)
            file_info['sheets'] = [{
                'name': session_summary.get('filename', 'Sheet1'),
                'shape': session_summary.get('shape'),
                'columns': session_summary.get('columns'),
                'preview': data_preview,
                'data': analyzer.df.head(100).to_dict('records') if analyzer.df is not None else []
            }]
        
        session_info = {
            'success': True,
            'fileInfo': file_info,
            **session_summary,
            **enhanced_info
        }
        
        response = jsonify(session_info)
        
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
    """Upload a file to an existing session (replace existing file) - UPDATED FOR ENHANCED ANALYZER."""
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
        
        # Load the new CSV (this will reinitialize handlers for enhanced analyzer)
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
            
            # Clear any existing stop signals for this session
            clear_stop_signal_for_session(session_id)
            
            print(f"✅ Updated session: {session_id} with new file: {file.filename}")
            
            # Generate image preview for updated file
            try:
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, f"upload_{session_id}_{file.filename}")
                
                # Determine file extension and save accordingly
                if file.filename.lower().endswith(('.xlsx', '.xls')):
                    analyzer.df.head(100).to_excel(temp_file_path, index=False)
                else:
                    analyzer.df.head(100).to_csv(temp_file_path, index=False)
                
                # Generate image preview
                preview_html = generate_sheet_images_with_highlighting(temp_file_path, max_sheets=1)
                
                # Clean up
                os.unlink(temp_file_path)
                
            except Exception as e:
                print(f"Failed to generate upload preview: {e}")
                preview_html = f'''
                <div class="sheet-images-preview bg-gray-50 dark:bg-gray-900 p-6">
                    <div class="max-w-4xl mx-auto">
                        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 text-center">
                            <div class="bg-green-50 dark:bg-green-900 p-4 rounded-lg">
                                <h3 class="text-lg font-semibold text-green-900 dark:text-green-100 mb-2">File Updated</h3>
                                <p class="text-green-800 dark:text-green-200">
                                    {file.filename} processed: {analyzer.df.shape[0]} rows × {analyzer.df.shape[1]} columns
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
                '''

            response_data = {
                'success': True,
                'sessionId': session_id,
                'message': f'File updated successfully! Shape: {analyzer.df.shape}',
                'data': {
                    'filename': file.filename,
                    'shape': analyzer.df.shape,
                    'columns': list(analyzer.df.columns),
                    'preview': preview_html,
                    'sheets': {
                        'preview': preview_html
                    }
                }
            }
            
            # Add enhanced capabilities info
            if isinstance(analyzer, EnhancedStreamingAnalyzer):
                response_data['data']['features'] = {
                    'conversational': True,
                    'textual_analytical': True,
                    'fully_analytical': True,
                    'enhanced_capabilities': True,
                    'assistants_api': True
                }
            
            response = jsonify(response_data)
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
        # Validate session exists
        is_valid, error_msg = validate_session_exists(session_id, analyzers, session_data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 404
        
        # Update last activity
        update_session_activity(session_id, session_data)
        
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
    
## SESSION CONTROL ROUTES
@app.route('/session/<session_id>/stop', methods=['POST', 'OPTIONS'])
def stop_session_analysis(session_id):
    """Stop current analysis for a specific session - ENHANCED for Assistants"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        # Get stop type from request body
        data = request.get_json() or {}
        stop_type = data.get('type', 'query')  # 'query' or 'session'
        
        # Validate session exists
        is_valid, error_msg = validate_session_exists(session_id, analyzers, session_data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 404
        
        if stop_type == 'session':
            # TERMINATE ENTIRE SESSION including assistants cleanup
            print(f"🛑 Terminating entire session with assistants cleanup: {session_id}")
            
            # Set stop signal first
            stop_analysis_for_session(session_id)
            
            # Stop any running assistants analysis
            analyzer = analyzers.get(session_id)
            if analyzer and hasattr(analyzer, 'stop_current_analysis'):
                analyzer.stop_current_analysis()
            
            # Emit session termination signal
            socketio.emit('stream_data', {
                'type': 'session_terminated',
                'data': '🛑 Session terminated by user',
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
            # Clean up session after a brief delay to allow message delivery
            def delayed_cleanup():
                import time
                time.sleep(1)  # Allow WebSocket message to be sent
                
                # Enhanced cleanup for assistants
                if analyzer and hasattr(analyzer, 'cleanup_assistants_resources'):
                    analyzer.cleanup_assistants_resources()
                
                cleanup_session_data_with_assistants(session_id, session_data, analyzers)
                print(f"🗑️ Session {session_id} terminated and cleaned up (including assistants)")
            
            cleanup_thread = threading.Thread(target=delayed_cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
            response_data = {
                'success': True,
                'sessionId': session_id,
                'message': 'Session terminated (including assistants cleanup)',
                'action': 'session_terminated',
                'timestamp': datetime.now().isoformat()
            }
            
        else:
            # STOP CURRENT QUERY ONLY (default behavior)
            print(f"🛑 Stopping current query for session: {session_id}")
            
            # Set stop signal
            stop_analysis_for_session(session_id)
            
            # Stop assistants analysis if running
            analyzer = analyzers.get(session_id)
            if analyzer and hasattr(analyzer, 'stop_current_analysis'):
                analyzer.stop_current_analysis()
            
            # Update last activity
            update_session_activity(session_id, session_data)
            
            # Emit stop signal via WebSocket
            socketio.emit('stream_data', {
                'type': 'stop_requested',
                'data': 'Stop requested by user...',
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
            response_data = {
                'success': True,
                'sessionId': session_id,
                'message': 'Analysis stop requested',
                'action': 'query_stopped',
                'timestamp': datetime.now().isoformat()
            }
        
        response = jsonify(response_data)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Stop analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to stop analysis: {str(e)}'
        }), 500


@app.route('/session/<session_id>/terminate', methods=['POST', 'OPTIONS'])
def terminate_session(session_id):
    """Terminate and clean up a specific session - ENHANCED for Assistants"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        # Validate session exists
        is_valid, error_msg = validate_session_exists(session_id, analyzers, session_data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 404
        
        print(f"🛑 Terminating session: {session_id}")
        
        # Stop any running analysis
        stop_analysis_for_session(session_id)
        
        # Enhanced cleanup for assistants
        analyzer = analyzers.get(session_id)
        if analyzer and hasattr(analyzer, 'cleanup_assistants_resources'):
            analyzer.cleanup_assistants_resources()
        
        # Clean up session data
        deleted_items = cleanup_session_data_with_assistants(session_id, session_data, analyzers)
        
        response_data = {
            'success': True,
            'sessionId': session_id,
            'message': 'Session terminated and cleaned up',
            'deletedItems': deleted_items,
            'timestamp': datetime.now().isoformat()
        }
        
        response = jsonify(response_data)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Terminate session error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to terminate session: {str(e)}'
        }), 500


@app.route('/session/<session_id>/delete', methods=['DELETE', 'OPTIONS'])
def delete_session(session_id):
    """Delete a specific session - ENHANCED for Assistants"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        # Check if session exists
        if session_id not in analyzers and session_id not in session_data:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        print(f"🗑️ Deleting session: {session_id}")
        
        # Enhanced cleanup for assistants
        analyzer = analyzers.get(session_id)
        if analyzer and hasattr(analyzer, 'cleanup_assistants_resources'):
            analyzer.cleanup_assistants_resources()
        
        # Clean up session data
        deleted_items = cleanup_session_data_with_assistants(session_id, session_data, analyzers)
        
        response_data = {
            'success': True,
            'sessionId': session_id,
            'message': 'Session deleted successfully',
            'deletedItems': deleted_items,
            'timestamp': datetime.now().isoformat()
        }
        
        response = jsonify(response_data)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Delete session error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete session: {str(e)}'
        }), 500


@app.route('/sessions', methods=['GET', 'OPTIONS'])
def list_sessions():
    """List all active sessions with comprehensive information - ENHANCED for Assistants"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        sessions = []
        
        for session_id in list(analyzers.keys()):
            if session_id in session_data:
                session_summary = create_session_summary(session_id, session_data, analyzers)
                
                # Add enhanced analyzer info
                if isinstance(analyzers[session_id], EnhancedStreamingAnalyzer):
                    session_summary['enhanced_analyzer'] = True
                    session_summary['ai_routing_enabled'] = True  # NEW
                    session_summary['assistants_enabled'] = True
                    session_summary['thread_id'] = getattr(analyzers[session_id], 'thread_id', None)
                
                sessions.append(session_summary)
        
        # Sort by last activity (most recent first)
        sessions.sort(key=lambda x: x.get('lastActivity', ''), reverse=True)
        
        # Get overall statistics
        stats = get_session_stats(session_data, analyzers)
        
        # Add enhanced analyzer stats
        enhanced_count = sum(1 for analyzer in analyzers.values() 
                           if isinstance(analyzer, EnhancedStreamingAnalyzer))
        assistants_count = sum(1 for analyzer in analyzers.values() 
                             if isinstance(analyzer, EnhancedStreamingAnalyzer) and hasattr(analyzer, 'thread_id'))
        ai_routing_count = sum(1 for analyzer in analyzers.values()
                             if isinstance(analyzer, EnhancedStreamingAnalyzer) and 
                             hasattr(analyzer.query_classifier, 'routers'))

        stats['enhanced_analyzers_count'] = enhanced_count
        stats['assistants_enabled_count'] = assistants_count
        stats['ai_routing_enabled_count'] = ai_routing_count
        
        response = jsonify({
            'success': True,
            'sessions': sessions,
            'statistics': stats
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
def cleanup_sessions():
    """Clean up old and inactive sessions - ENHANCED for Assistants"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        print("🧹 Manual session cleanup requested...")
        
        # Get cleanup parameters from request
        data = request.get_json() or {}
        max_age_hours = data.get('maxAgeHours', SESSION_MAX_AGE_HOURS)
        max_inactive_hours = data.get('maxInactiveHours', SESSION_MAX_INACTIVE_HOURS)
        
        sessions_to_delete = []
        current_time = datetime.now()
        
        for session_id in list(analyzers.keys()):
            if session_id in session_data:
                session_info = session_data[session_id]
                
                if (is_session_too_old(session_info, max_age_hours) or 
                    is_session_inactive(session_info, max_inactive_hours)):
                    sessions_to_delete.append(session_id)
        
        # Clean up old sessions with enhanced cleanup
        cleaned_sessions = []
        for session_id in sessions_to_delete:
            try:
                # Enhanced cleanup for assistants
                analyzer = analyzers.get(session_id)
                if analyzer and hasattr(analyzer, 'cleanup_assistants_resources'):
                    analyzer.cleanup_assistants_resources()
                
                deleted_items = cleanup_session_data_with_assistants(session_id, session_data, analyzers)
                if deleted_items:
                    cleaned_sessions.append({
                        'sessionId': session_id,
                        'deletedItems': deleted_items
                    })
                    print(f"🧹 Cleaned session: {session_id}")
            except Exception as e:
                print(f"⚠️ Failed to clean session {session_id}: {e}")
        
        response_data = {
            'success': True,
            'message': f'Cleaned up {len(cleaned_sessions)} sessions',
            'cleanedSessions': cleaned_sessions,
            'totalCleaned': len(cleaned_sessions),
            'parameters': {
                'maxAgeHours': max_age_hours,
                'maxInactiveHours': max_inactive_hours
            },
            'timestamp': datetime.now().isoformat()
        }
        
        response = jsonify(response_data)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Cleanup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Cleanup failed: {str(e)}'
        }), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection with improved session management."""
    # Generate session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    join_room(session_id)
    
    print(f"Client connected with session: {session_id}")
    emit('status', {
        'message': 'Connected to enhanced analysis server with Assistants API',
        'sessionId': session_id,
        'timestamp': datetime.now().isoformat(),
        'features': {
            'conversational': True,
            'textual_analytical': True,
            'fully_analytical': True,
            'assistants_api': True
        }
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    session_id = session.get('session_id')
    if session_id:
        print(f'🔌 Client disconnected: {session_id}')
        # Update last activity when disconnecting
        update_session_activity(session_id, session_data)


@socketio.on('join_session')
def handle_join_session(data):
    """Handle client joining a specific session room."""
    session_id = data.get('sessionId')
    if session_id:
        join_room(session_id)
        print(f"Client joined session room: {session_id}")
        
        # Update last activity
        update_session_activity(session_id, session_data)
        
        # Clear any existing stop signals when joining
        clear_stop_signal_for_session(session_id)
        
        # Check if this is an enhanced analyzer session
        enhanced_features = {}
        if session_id in analyzers and isinstance(analyzers[session_id], EnhancedStreamingAnalyzer):
            analyzer = analyzers[session_id]
            enhanced_features = {
                'conversational': True,
                'textual_analytical': True,
                'fully_analytical': True,
                'enhanced_capabilities': True,
                'assistants_api': True,
                'thread_id': getattr(analyzer, 'thread_id', None),
                'uploaded_files_count': len(getattr(analyzer, 'current_file_ids', []))
            }
        
        emit('status', {
            'message': f'Joined session {session_id} with Assistants API',
            'sessionId': session_id,
            'timestamp': datetime.now().isoformat(),
            'features': enhanced_features
        })
    else:
        print("No session ID provided for join_session")
        emit('error', {'message': 'No session ID provided'})

# app.py - UPDATED socket handler to properly handle DataFrames and code

@socketio.on('send_message_with_session')
def handle_message_with_session(data):
    """ENHANCED Handle chat messages with new report type support"""
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
        emit('stream_data', {
            'type': 'error',
            'data': 'Please provide a message to analyze.',
            'timestamp': datetime.now().isoformat()
        })
        return
    
    print(f"Processing message for session: {session_id}")
    print(f"Query: {query}")
    
    # Validate session exists
    is_valid, error_msg = validate_session_exists(session_id, analyzers, session_data)
    if not is_valid:
        emit('stream_data', {
            'type': 'error',
            'data': f'{error_msg}. Please go back to home and upload a file.',
            'timestamp': datetime.now().isoformat()
        })
        return
    
    # Update last activity
    update_session_activity(session_id, session_data)
    
    # Clear any existing stop signals
    clear_stop_signal_for_session(session_id)
    
    # Process the query with ENHANCED analyzer
    def process_query():
        try:
            analyzer = analyzers[session_id]
            analyzer.session_id = session_id
            
            # Emit starting analysis
            socketio.emit('stream_data', {
                'type': 'analysis_started',
                'data': f'🤖 Processing your message with Assistants API: {query}',
                'timestamp': datetime.now().isoformat(),
                'sessionId': session_id
            }, room=session_id)
            
            # Start the ENHANCED analysis
            result = analyzer.analyze_query_streaming(user_query=query)

            if result is None:
                result = {}
            
            # ENHANCED: Handle different result types including new "report" type
            if result.get("type") == "conversational":
                # Conversational response - simple completion
                completion_data = {
                    'type': 'completion',
                    'data': 'Conversation completed!',
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': session_id,
                    'result': {
                        'success': result.get('success', False),
                        'type': result.get('type', 'conversational'),
                        'response': result.get('response', ''),
                        'requires_analysis': False,
                        'has_dataframes': False,
                        'has_code': False
                    }
                }
                
            elif result.get("type") == "textual_analytical":
                # Simple analysis - text response with potential DataFrames and code
                dataframes = result.get('dataframes', {})
                generated_code = result.get('generated_code', '')
                
                completion_data = {
                    'type': 'completion',
                    'data': 'Analysis completed!',
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': session_id,
                    'result': {
                        'success': result.get('success', False),
                        'type': result.get('type', 'textual_analytical'),
                        'response': result.get('response', ''),
                        'dataframes_count': len(dataframes),
                        'analysis_type': result.get('analysis_type', 'general'),
                        'has_dataframes': len(dataframes) > 0,
                        'has_code': bool(_extract_code_string(generated_code)),
                        'code_lines': _count_code_lines(generated_code)
                    }
                }
                
                # Emit DataFrames and code
                _emit_dataframes_to_frontend(dataframes, session_id, socketio)
                _emit_code_to_frontend(generated_code, session_id, socketio)
                _emit_summary_to_frontend(analysis_summary, session_id, socketio, result)

            elif result.get("type") == "report":
                # NEW: Enhanced report type with plain text report and embedded images
                dataframes = result.get('dataframes', {})
                generated_code = result.get('generated_code', '')
                plain_text_report = result.get('comprehensive_report', '')
                embedded_images = result.get('embedded_images', [])
                analysis_summary = result.get('analysis_summary', '')
                completion_data = {
                    'type': 'completion',  # Special completion type for reports
                    'data': 'Comprehensive business report generated successfully!',
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': session_id,
                    'result': {
                        'success': result.get('success', False),
                        'type': 'report',
                        'response': result.get('response', ''),
                        'report_content': plain_text_report,
                        'report_type': result.get('report_type', 'plain_text_with_images'),
                        'embedded_images_count': len(embedded_images),
                        'embedded_images': embedded_images,
                        'report_generated': result.get('report_generated', True),
                        'images_count': len(result.get('generated_images', [])),
                        'files_generated': result.get('generated_files', {}),
                        'dataframes_count': len(dataframes),
                        'has_dataframes': len(dataframes) > 0,
                        'has_code': bool(_extract_code_string(generated_code)),
                        'code_lines': _count_code_lines(generated_code),
                        'assistant_generated': result.get('report_assistant_used', False),
                        'same_thread_analysis': result.get('same_thread_analysis', False),
                        'has_summary': bool(analysis_summary),  # NEW
                        'summary_generated': result.get('summary_generated', False),  # NEW
                        'summary_type': result.get('summary_type', 'executive')  # NEW
                    }
                }
                
                # NEW: Emit the plain text report with embedded image URLs
                socketio.emit('stream_data', {
                    'type': 'plain_text_report',
                    'data': {
                        'content': plain_text_report,
                        'embedded_images': embedded_images,
                        'report_type': result.get('report_type', 'plain_text_with_images'),
                        'generated_by': 'report_generator_assistant'
                    },
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': session_id
                }, room=session_id)
                
                # Emit DataFrames and code for reports
                _emit_dataframes_to_frontend(dataframes, session_id, socketio)
                _emit_code_to_frontend(generated_code, session_id, socketio)
                _emit_summary_to_frontend(analysis_summary, session_id, socketio, result)

            elif result.get("type") == "fully_analytical":
                # Complex analysis without report generation (fallback case)
                dataframes = result.get('dataframes', {})
                generated_code = result.get('generated_code', '')
                analysis_summary = result.get('analysis_summary', '')
                
                completion_data = {
                    'type': 'completion',
                    'data': 'Complex analysis completed successfully!',
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': session_id,
                    'result': {
                        'success': result.get('success', False),
                        'type': result.get('type', 'fully_analytical'),
                        'response': result.get('response', ''),
                        'dataframes_count': len(dataframes),
                        'images_count': len(result.get('generated_images', [])),
                        'generated_files': result.get('generated_files', {}),
                        'assistants_used': result.get('assistant_used', False),
                        'thread_id': result.get('thread_id', None),
                        'has_dataframes': len(dataframes) > 0,
                        'has_code': bool(_extract_code_string(generated_code)),
                        'code_lines': _count_code_lines(generated_code),
                        'has_summary': bool(analysis_summary),  # NEW
                        'summary_generated': result.get('summary_generated', False),  # NEW
                        'summary_type': result.get('summary_type', 'executive')  # NEW
                    }
                }
                
                # Emit generated files
                generated_files = result.get('generated_files', {})
                for file_type, files in generated_files.items():
                    if files:
                        socketio.emit('stream_data', {
                            'type': f'{file_type}_files',
                            'data': {
                                'files': files,
                                'count': len(files),
                                'type': file_type
                            },
                            'timestamp': datetime.now().isoformat(),
                            'sessionId': session_id
                        }, room=session_id)
                
                # Emit DataFrames and code
                _emit_dataframes_to_frontend(dataframes, session_id, socketio)
                _emit_code_to_frontend(generated_code, session_id, socketio)
                _emit_summary_to_frontend(analysis_summary, session_id, socketio, result)

            elif result.get("stopped_by_user"):
                # Analysis was stopped
                socketio.emit('stream_data', {
                    'type': 'stopped',
                    'data': 'Analysis stopped by user',
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': session_id
                }, room=session_id)
                return
                
            else:
                # Default/fallback completion
                dataframes = result.get('dataframes', {})
                generated_code = result.get('generated_code', '')
                
                completion_data = {
                    'type': 'completion',
                    'data': 'Analysis completed!',
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': session_id,
                    'result': {
                        'success': result.get('success', False),
                        'type': result.get('type', 'unknown'),
                        'response': result.get('response', 'Analysis completed'),
                        'dataframes_count': len(dataframes),
                        'images_count': len(result.get('generated_images', [])),
                        'has_dataframes': len(dataframes) > 0,
                        'has_code': bool(_extract_code_string(generated_code)),
                        'code_lines': _count_code_lines(generated_code),
                        'has_summary': bool(analysis_summary),  # NEW
                        'summary_generated': result.get('summary_generated', False),  # NEW
                        'summary_type': result.get('summary_type', 'executive')  # NEW
                    }
                }
                
                # Emit DataFrames and code for fallback cases
                _emit_dataframes_to_frontend(dataframes, session_id, socketio)
                _emit_code_to_frontend(generated_code, session_id, socketio)
                _emit_summary_to_frontend(analysis_summary, session_id, socketio, result)
            
            # Send final completion signal
            socketio.emit('stream_data', completion_data, room=session_id)
            
        except StopAnalysisException:
            print(f"Analysis stopped by user for session {session_id}")
            
        except Exception as e:
            logging.error(f"Analysis error for session {session_id}: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
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

# NEW: Helper functions to properly handle DataFrames and code emission
    def _emit_summary_to_frontend(analysis_summary: str, session_id: str, socketio_instance, result: dict):
            """
            NEW: Emit analysis summary to frontend as simple 'response' type for frontend compatibility.
            
            This function emits the executive summary in the same format as regular responses
            to ensure frontend compatibility without breaking existing response handling.
            """
            try:
                if not analysis_summary or not analysis_summary.strip():
                    return
                
                # Emit in simple format matching existing response pattern
                socketio_instance.emit('stream_data', {
                    'type': 'response',
                    'data': analysis_summary.strip(),
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': session_id
                }, room=session_id)
                
                print(f"📝 Emitted analysis summary to frontend: {len(analysis_summary)} characters")
                
            except Exception as e:
                logging.error(f"Error emitting summary to frontend: {e}")
                print(f"❌ Failed to emit summary: {e}")

def _emit_dataframes_to_frontend(dataframes: dict, session_id: str, socketio_instance):
    """
    NEW: Emit DataFrames to frontend with proper structure and type identification.
    
    This function ensures DataFrames are sent to the frontend in the correct format
    while preserving the actual DataFrame objects in the backend.
    """
    try:
        if not dataframes:
            return
        
        for df_name, df_info in dataframes.items():
            if isinstance(df_info, dict) and df_info.get('type') == 'dataframe':
                # Structured DataFrame info
                df_data = df_info.get('data')
                if isinstance(df_data, pd.DataFrame):
                    socketio_instance.emit('stream_data', {
                        'type': 'dataframe',
                        'data': {
                            'name': df_name,
                            'type': 'dataframe',
                            'shape': df_info.get('shape', df_data.shape),
                            'columns': df_info.get('columns', list(df_data.columns)),
                            'preview': df_info.get('preview', ''),
                            'json_data': df_info.get('json_data', df_data.head(100).to_dict('records')),
                            'summary': {
                                'rows': len(df_data),
                                'columns': len(df_data.columns),
                                'memory_usage': df_data.memory_usage(deep=True).sum(),
                                'dtypes': df_data.dtypes.to_dict()
                            },
                            'thisis': 5  # Enhanced analyzer generated
                        },
                        'timestamp': datetime.now().isoformat(),
                        'sessionId': session_id
                    }, room=session_id)
                    
                    print(f"📊 Emitted DataFrame '{df_name}' to frontend: {df_data.shape}")
                    
            elif isinstance(df_info, pd.DataFrame):
                # Direct DataFrame object
                socketio_instance.emit('stream_data', {
                    'type': 'dataframe',
                    'data': {
                        'name': df_name,
                        'type': 'dataframe',
                        'shape': df_info.shape,
                        'columns': list(df_info.columns),
                        'preview': _generate_simple_table_preview(df_info),
                        'json_data': df_info.head(100).to_dict('records'),
                        'summary': {
                            'rows': len(df_info),
                            'columns': len(df_info.columns),
                            'memory_usage': df_info.memory_usage(deep=True).sum(),
                            'dtypes': df_info.dtypes.to_dict()
                        },
                        'thisis': 5  # Enhanced analyzer generated
                    },
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': session_id
                }, room=session_id)
                
                print(f"📊 Emitted DataFrame '{df_name}' to frontend: {df_info.shape}")
                
    except Exception as e:
        logging.error(f"Error emitting DataFrames to frontend: {e}")
        print(f"❌ Failed to emit DataFrames: {e}")


def _emit_code_to_frontend(generated_code, session_id: str, socketio_instance):
    """
    NEW: Emit generated code to frontend with proper structure and type identification.
    
    This function ensures generated code is sent to the frontend in the correct format
    while preserving the actual code string in the backend.
    """
    try:
        if not generated_code:
            return
        
        # Extract actual code string
        if isinstance(generated_code, dict):
            code_string = generated_code.get('code', '')
            code_type = generated_code.get('type', 'code')
            language = generated_code.get('language', 'python')
            lines = generated_code.get('lines', 0)
        else:
            code_string = str(generated_code)
            code_type = 'code'
            language = 'python'
            lines = len(code_string.split('\n')) if code_string else 0
        
        if code_string.strip():
            socketio_instance.emit('stream_data', {
                'type': 'code',
                'data': {
                    'code': code_string,
                    'type': code_type,
                    'language': language,
                    'lines': lines,
                    'preview': code_string[:500] + '...' if len(code_string) > 500 else code_string,
                    'summary': {
                        'total_lines': lines,
                        'non_empty_lines': len([line for line in code_string.split('\n') if line.strip()]),
                        'imports': len([line for line in code_string.split('\n') if line.strip().startswith('import')]),
                        'functions': len([line for line in code_string.split('\n') if line.strip().startswith('def ')]),
                        'size_bytes': len(code_string.encode('utf-8'))
                    },
                    'thisis': 'generated_code'
                },
                'timestamp': datetime.now().isoformat(),
                'sessionId': session_id
            }, room=session_id)
            
            print(f"💻 Emitted generated code to frontend: {lines} lines")
            
    except Exception as e:
        logging.error(f"Error emitting code to frontend: {e}")
        print(f"❌ Failed to emit code: {e}")


def _extract_code_string(generated_code) -> str:
    """Extract actual code string from various formats"""
    if isinstance(generated_code, dict):
        return generated_code.get('code', '')
    elif isinstance(generated_code, str):
        return generated_code
    else:
        return str(generated_code) if generated_code else ''


def _count_code_lines(generated_code) -> int:
    """Count lines in generated code"""
    code_string = _extract_code_string(generated_code)
    return len(code_string.split('\n')) if code_string else 0


def _generate_simple_table_preview(df: pd.DataFrame) -> str:
    """Generate a simple HTML preview for DataFrame"""
    try:
        from utils.utils import generate_simple_table
        return generate_simple_table(df.head(10))
    except Exception as e:
        print(f"Error generating table preview: {e}")
        return f"<p>DataFrame with {df.shape[0]} rows and {df.shape[1]} columns</p>"

@socketio.on('stop_analysis')
def handle_stop_analysis(data):
    """Handle stop analysis requests - ENHANCED for Assistants"""
    session_id = data.get('sessionId')
    if not session_id:
        emit('error', {'message': 'No session ID provided'})
        return
    
    print(f"🛑 Stop analysis requested for session: {session_id}")
    
    # Set stop signal
    stop_analysis_for_session(session_id)
    
    # Stop assistants analysis if running
    analyzer = analyzers.get(session_id)
    if analyzer and hasattr(analyzer, 'stop_current_analysis'):
        analyzer.stop_current_analysis()
    
    # Update last activity
    update_session_activity(session_id, session_data)
    
    emit('stream_data', {
        'type': 'stop_requested',
        'data': 'Stop requested by user...',
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('terminate_session')
def handle_terminate_session(data):
    """Handle session termination requests - ENHANCED for Assistants"""
    session_id = data.get('sessionId')
    if not session_id:
        emit('error', {'message': 'No session ID provided'})
        return
    
    print(f"🛑 Session termination requested: {session_id}")
    
    # Stop any running analysis
    stop_analysis_for_session(session_id)
    
    # Enhanced cleanup for assistants
    analyzer = analyzers.get(session_id)
    if analyzer and hasattr(analyzer, 'cleanup_assistants_resources'):
        analyzer.cleanup_assistants_resources()
    
    # Clean up session
    try:
        deleted_items = cleanup_session_data_with_assistants(session_id, session_data, analyzers)
        
        emit('stream_data', {
            'type': 'session_terminated',
            'data': 'Session terminated and cleaned up (including assistants)',
            'timestamp': datetime.now().isoformat(),
            'deletedItems': deleted_items
        })
        
        print(f"🗑️ Session {session_id} terminated and cleaned up")
        
    except Exception as e:
        print(f"❌ Error during session termination: {e}")
        emit('error', {'message': f'Error during termination: {str(e)}'})


@socketio.on('get_session_status')
def handle_get_session_status(data):
    """Get status of a specific session - ENHANCED for Assistants"""
    session_id = data.get('sessionId')
    if not session_id:
        emit('error', {'message': 'No session ID provided'})
        return
    
    try:
        if session_id in analyzers and session_id in session_data:
            analyzer = analyzers[session_id]
            session_info = session_data[session_id]
            
            status_data = {
                'sessionId': session_id,
                'exists': True,
                'filename': session_info.get('filename'),
                'shape': session_info.get('shape'),
                'uploadTime': session_info.get('upload_time'),
                'lastActivity': session_info.get('last_activity'),
                'isAnalyzing': getattr(analyzer, 'is_analyzing', False),
                'assistantsEnabled': isinstance(analyzer, EnhancedStreamingAnalyzer),
                'threadId': getattr(analyzer, 'thread_id', None),
                'uploadedFilesCount': len(getattr(analyzer, 'current_file_ids', []))
            }
        else:
            status_data = {
                'sessionId': session_id,
                'exists': False
            }
        
        emit('session_status', status_data)
        
    except Exception as e:
        print(f"❌ Error getting session status: {e}")
        emit('error', {'message': f'Error getting session status: {str(e)}'})
# ==================== BACKGROUND TASKS ====================

def cleanup_session_data_with_assistants(session_id: str, session_data: dict, analyzers: dict):
    """Enhanced cleanup that includes AI routing and assistants resources"""
    deleted_items = []
    
    # Remove from analyzers with enhanced cleanup
    if session_id in analyzers:
        analyzer = analyzers[session_id]
        
        # Enhanced cleanup for AI routing
        if hasattr(analyzer, 'query_classifier') and hasattr(analyzer.query_classifier, 'cleanup_session'):
            try:
                analyzer.query_classifier.cleanup_session(session_id)
                deleted_items.append('ai_query_router')
                print(f"🧭 Cleaned up AI query router for session: {session_id}")
            except Exception as e:
                print(f"⚠️ Error cleaning up AI query router: {e}")
        
        # Enhanced cleanup for assistants
        if hasattr(analyzer, 'cleanup_assistants_resources'):
            try:
                analyzer.cleanup_assistants_resources()
                deleted_items.append('assistants_resources')
            except Exception as e:
                print(f"⚠️ Error cleaning up assistants resources: {e}")
        
        # Original cleanup
        if hasattr(analyzer, 'cleanup'):
            analyzer.cleanup()
        
        del analyzers[session_id]
        deleted_items.append('enhanced_analyzer')
        print(f"🗑️ Deleted enhanced analyzer with AI routing for session: {session_id}")
    
    # Remove from session data (existing logic)
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
    
    # Clear stop signals (existing logic)
    if hasattr(__import__('utils.utils'), 'stop_signals'):
        stop_signals = getattr(__import__('utils.utils'), 'stop_signals')
        if session_id in stop_signals:
            del stop_signals[session_id]
            deleted_items.append('stop_signal')
            print(f"🗑️ Cleared stop signal for: {session_id}")
    
    return deleted_items

    
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
        from utils import stop_signals
        del stop_signals[session_id]
        deleted_items.append('stop_signal')
        print(f"🗑️ Cleared stop signal for: {session_id}")
    
    return deleted_items


def periodic_cleanup():
    """Periodic cleanup of old sessions with enhanced assistants cleanup"""
    if not SESSION_CLEANUP_ENABLED:
        return
    
    try:
        print("🧹 Running periodic session cleanup with assistants support...")
        
        sessions_to_delete = []
        current_time = datetime.now()
        
        for session_id in list(analyzers.keys()):
            if session_id in session_data:
                session_info = session_data[session_id]
                
                if (is_session_too_old(session_info, SESSION_MAX_AGE_HOURS) or 
                    is_session_inactive(session_info, SESSION_MAX_INACTIVE_HOURS)):
                    sessions_to_delete.append(session_id)
        
        # Clean up old sessions with enhanced cleanup
        cleaned_count = 0
        for session_id in sessions_to_delete:
            try:
                # Enhanced cleanup for assistants
                analyzer = analyzers.get(session_id)
                if analyzer and hasattr(analyzer, 'cleanup_assistants_resources'):
                    analyzer.cleanup_assistants_resources()
                
                deleted_items = cleanup_session_data_with_assistants(session_id, session_data, analyzers)
                if deleted_items:
                    cleaned_count += 1
                    print(f"🗑️ Auto-cleaned session with assistants: {session_id}")
            except Exception as e:
                print(f"⚠️ Failed to auto-clean session {session_id}: {e}")
        
        if cleaned_count > 0:
            print(f"🧹 Periodic cleanup completed: {cleaned_count} sessions cleaned (including assistants)")
        
    except Exception as e:
        print(f"❌ Periodic cleanup error: {e}")


def schedule_periodic_cleanup():
    """Schedule periodic cleanup to run every 30 minutes."""
    import threading
    import time
    
    def cleanup_loop():
        while True:
            time.sleep(1800)  # 30 minutes
            periodic_cleanup()
    
    cleanup_thread = threading.Thread(target=cleanup_loop)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    print("🕐 Scheduled periodic cleanup every 30 minutes (with assistants support)")


# ==================== MAIN APPLICATION ====================

# Find the existing startup logging section and update it:

if __name__ == '__main__':
    # Verify environment variables (UPDATED for Assistants API)
    required_vars = ["AZUREAPI", "AZUREVERSION", "AZUREENDPOINT", "AZUREMODEL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set the following:")
        print("- AZUREAPI: Your Azure OpenAI API key")
        print("- AZUREVERSION: API version (e.g., '2024-05-01-preview' for Assistants)")
        print("- AZUREENDPOINT: Your Azure OpenAI endpoint")
        print("- AZUREMODEL: Your deployment name")
        exit(1)
    
    # Validate API version for Assistants support
    api_version = os.getenv("AZUREVERSION")
    if not api_version or "2024-05-01-preview" not in api_version:
        print("⚠️ WARNING: AZUREVERSION should be '2024-05-01-preview' or newer for Assistants API support")
        print(f"   Current version: {api_version}")
        print("   Assistants API features may not work properly")
    
    print("🚀 Starting Enhanced Flask CSV Analysis Chatbot with Assistants API...")
    print("🤖 NEW ASSISTANTS API FEATURES:")
    print("   🧠 OpenAI Assistants with Code Interpreter")
    print("   💬 Enhanced conversational queries")
    print("   📊 Advanced textual analytical queries")
    print("   🔬 Powerful fully analytical queries with streaming")
    print("   🧵 Persistent conversation threads")
    print("   📁 Seamless file management")
    print("   📄 Local HTML report download and serving")  # NEW
    print("   🔄 Automatic fallback to original implementation")
    print()
    print("📊 Backend running on http://localhost:5000")
    print("🔗 Connect your React frontend to this backend")
    print(f"⚙️  Using {async_mode} async mode")
    print(f"🧹 Session cleanup: {'Enabled' if SESSION_CLEANUP_ENABLED else 'Disabled'}")
    print(f"⏰ Max session age: {SESSION_MAX_AGE_HOURS} hours")
    print(f"💤 Max inactive time: {SESSION_MAX_INACTIVE_HOURS} hours")
    print(f"📁 Reports directory: {REPORTS_OUTPUT_DIR}")  # NEW
    
    # Enhanced feature status
    print()
    print("🔧 ENHANCED FEATURES STATUS:")
    print(f"✅ Assistants API: Enabled")
    print(f"✅ Code Interpreter: Enabled")
    print(f"✅ Streaming Adaptation: Enabled")
    print(f"✅ Thread Management: Enabled")
    print(f"✅ File Management: Enabled")
    print(f"✅ Local Report Download: Enabled")  # NEW
    print(f"✅ Report Serving Routes: /reports/<filename>")  # NEW
    print(f"✅ Automatic Fallback: Enabled")
    print(f"✅ Blob Storage: {'Enabled' if os.getenv('AZURE_STORAGE_ACCOUNT_URL') else 'Disabled'}")
    
    if LANGCHAIN_AVAILABLE:
        print("✅ LangChain available for enhanced conversation history")
    else:
        print("⚠️  LangChain not available - using basic conversation history")
    
    if EVENTLET_AVAILABLE:
        print("✅ Using eventlet for optimal WebSocket support")
    else:
        print("⚠️  Using threading mode - install eventlet for better performance")
        print("   pip install eventlet")
    
    # Assistants API compatibility check
    try:
        from assistants.assistant_manager import AssistantManager
        print("✅ Assistants API components loaded successfully")
    except ImportError as e:
        print(f"⚠️  Assistants API components not found: {e}")
        print("   System will fall back to original implementation")
    
    # Start periodic cleanup if enabled
    if SESSION_CLEANUP_ENABLED:
        schedule_periodic_cleanup()
    
    print()
    print("🚀 Server starting...")
    print("💡 TIP: Upload a CSV file and try these enhanced queries:")
    print("   💬 'Hi, how are you?' (Conversational)")
    print("   📊 'What is the highest revenue?' (Quick Analysis)")
    print("   🔬 'Generate a 5-year sales forecast' (Full Analysis with Local Report)")  # UPDATED
    print("   📄 'Create a comprehensive report' (HTML Report Downloaded Locally)")  # NEW
    print()
    
    # Run the application
    if EVENTLET_AVAILABLE:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    else:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)