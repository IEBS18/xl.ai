
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

# Import dashboard functions
from auth import get_db_connection
import psycopg2.extras

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
    Convert external image URLs in HTML to base64 data URLs - OPTIMIZED VERSION
    Find unique URLs first, download once, then replace all occurrences
    """
    
    # Step 1: Find ALL unique external image URLs in the HTML
    img_pattern = r'<img[^>]*?src\s*=\s*["\']([^"\']+)["\']'
    all_img_urls = re.findall(img_pattern, html_content, re.IGNORECASE)
    
    # Filter to get unique external URLs only
    unique_external_urls = list(set([
        url.strip('\'"') for url in all_img_urls 
        if url.strip('\'"').startswith(('http://', 'https://')) and not url.strip('\'"').startswith('data:')
    ]))
    
    logging.info(f"📊 Found {len(all_img_urls)} total img src attributes")
    logging.info(f"📊 Found {len(unique_external_urls)} unique external image URLs")
    
    if not unique_external_urls:
        logging.info("ℹ️ No external images to convert")
        return html_content
    
    # Step 2: Download each unique URL and convert to base64
    url_to_base64 = {}  # URL -> base64 data URL mapping
    
    for i, img_url in enumerate(unique_external_urls):
        logging.info(f"🔄 Converting image {i+1}/{len(unique_external_urls)}: {img_url[:80]}...")
        
        try:
            # Download with retry logic
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
                    
                    # Check for very large images (> 10MB) and warn
                    if len(content) > 10 * 1024 * 1024:
                        logging.warning(f"⚠️ Very large image detected: {len(content)} bytes for {img_url[:50]}...")
                        # Could optionally resize here, but for now just warn
                    
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
                continue
            
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
                
                # Check for very large base64 strings that might cause browser issues
                if len(img_base64) > 5000000:  # ~5MB base64 limit
                    logging.warning(f"⚠️ Very large base64 image: {len(img_base64)} chars for {img_url[:50]}...")
                    # Could implement image resizing here if needed
                
                # Validate the base64 image by attempting to decode it back
                try:
                    # Test decode to verify the base64 is valid
                    test_decode = base64.b64decode(img_base64)
                    if len(test_decode) != len(content):
                        raise ValueError("Base64 decode validation failed")
                    
                    # Additional validation: check if it looks like valid image data
                    image_signatures = [
                        b'\x89PNG',  # PNG
                        b'\xFF\xD8\xFF',  # JPEG
                        b'GIF87a', b'GIF89a',  # GIF
                        b'RIFF',  # WebP (starts with RIFF)
                        b'BM',  # BMP
                    ]
                    
                    is_valid_image = any(content.startswith(sig) for sig in image_signatures)
                    if not is_valid_image:
                        logging.warning(f"⚠️ Image may not have valid format signature for {img_url[:50]}...")
                        # But continue anyway - might still work
                        
                except Exception as validation_error:
                    logging.error(f"❌ Base64 validation failed for {img_url}: {validation_error}")
                    raise ValueError(f"Invalid base64 data: {validation_error}")
                
                # Store the mapping
                url_to_base64[img_url] = data_url
                
                logging.info(f"✅ Converted and validated ({len(content)} bytes) -> {len(img_base64)} base64 chars")
                
            except Exception as encode_error:
                logging.error(f"❌ Base64 encoding failed for {img_url}: {str(encode_error)}")
                continue
                
        except Exception as e:
            logging.error(f"❌ Failed to convert {img_url}: {str(e)}")
            continue
    
    # Step 3: Replace ALL occurrences of each URL with its base64 equivalent
    modified_html = html_content
    total_replacements = 0
    
    for original_url, base64_data_url in url_to_base64.items():
        # Count occurrences before replacement
        count_before = modified_html.count(original_url)
        
        # Replace all occurrences of this URL
        modified_html = modified_html.replace(original_url, base64_data_url)
        
        # Count occurrences after replacement (should be 0)
        count_after = modified_html.count(original_url)
        replacements_made = count_before - count_after
        total_replacements += replacements_made
        
        logging.info(f"🔄 Replaced {replacements_made} occurrences of: {original_url[:50]}...")
    
    logging.info(f"🎯 Conversion complete: {len(url_to_base64)} unique images downloaded")
    logging.info(f"🎯 Total URL replacements made: {total_replacements}")
    
    return modified_html


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
            
            # Inject CSS to ensure images are visible and properly sized
            await page.add_style_tag(content="""
                img {
                    max-width: 100% !important;
                    height: auto !important;
                    display: block !important;
                    page-break-inside: avoid !important;
                }
                .chart-container, .image-container {
                    page-break-inside: avoid !important;
                    margin: 10px 0 !important;
                }
            """)
            
            # Wait for all images to load (base64 images should load instantly)
            await page.wait_for_load_state('networkidle')
            
            # Force rendering of base64 images by triggering layout recalculation
            await page.evaluate("""
                () => {
                    // Force a reflow to ensure base64 images are rendered
                    document.body.offsetHeight;
                    
                    // Set explicit dimensions for any images without them
                    const images = document.querySelectorAll('img');
                    images.forEach((img, index) => {
                        if (img.src.startsWith('data:')) {
                            console.log(`Processing base64 image ${index}:`, {
                                complete: img.complete,
                                naturalWidth: img.naturalWidth,
                                naturalHeight: img.naturalHeight,
                                srcLength: img.src.length
                            });
                            
                            // Force decode base64 images
                            if (img.decode) {
                                img.decode().catch((error) => {
                                    console.warn(`Image ${index} decode failed:`, error);
                                });
                            }
                            
                            // For problematic images, try to trigger loading
                            if (!img.complete || img.naturalWidth === 0) {
                                console.warn(`Image ${index} not loaded properly, trying to fix...`);
                                
                                // Try setting the src again to trigger reload
                                const originalSrc = img.src;
                                img.src = '';
                                setTimeout(() => {
                                    img.src = originalSrc;
                                }, 10);
                                
                                // Set minimum dimensions if needed
                                if (!img.style.width && !img.style.height) {
                                    img.style.maxWidth = '100%';
                                    img.style.height = 'auto';
                                }
                            }
                        }
                        
                        // Ensure images have layout
                        if (!img.style.display || img.style.display === 'none') {
                            img.style.display = 'block';
                        }
                    });
                    
                    // Force another reflow
                    document.body.offsetHeight;
                }
            """)
            
            # Wait for image processing and potential re-loads
            await page.wait_for_timeout(10000)  # 3 seconds to allow decode operations
            
            # Give problematic images a second chance
            await page.evaluate("""
                () => {
                    const problemImages = Array.from(document.images).filter(img => 
                        img.src.startsWith('data:') && (!img.complete || img.naturalWidth === 0)
                    );
                    
                    if (problemImages.length > 0) {
                        console.log(`Found ${problemImages.length} problematic images, giving them another chance...`);
                        
                        // Force reflow again for problematic images
                        problemImages.forEach((img, index) => {
                            console.log(`Retrying problematic image ${index}...`);
                            const rect = img.getBoundingClientRect();
                            console.log(`Image rect:`, rect);
                            
                            // Force visibility
                            img.style.visibility = 'visible';
                            img.style.opacity = '1';
                        });
                        
                        document.body.offsetHeight; // Force reflow
                    }
                }
            """)
            
            # Additional short wait for the retry
            await page.wait_for_timeout(5000)
            
            # Simple check to verify base64 images are in the DOM, then proceed
            image_status = await page.evaluate("""
                () => {
                    const images = Array.from(document.images);
                    const base64Count = images.filter(img => img.src.startsWith('data:')).length;
                    return {
                        total: images.length,
                        base64Count: base64Count
                    };
                }
            """)
            
            logging.info(f"📊 DOM verification: {image_status['total']} total images, {image_status['base64Count']} are base64")
            
            # Comprehensive debugging of why images might not appear in PDF
            debug_info = await page.evaluate("""
                () => {
                    const images = Array.from(document.images);
                    const imageDetails = images.map((img, index) => ({
                        index: index,
                        isBase64: img.src.startsWith('data:'),
                        srcLength: img.src.length,
                        complete: img.complete,
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight,
                        width: img.width,
                        height: img.height,
                        displayed: img.offsetWidth > 0 && img.offsetHeight > 0,
                        visible: img.style.display !== 'none' && img.style.visibility !== 'hidden',
                        hasParent: img.parentElement !== null,
                        computedDisplay: getComputedStyle(img).display,
                        computedVisibility: getComputedStyle(img).visibility,
                        rect: img.getBoundingClientRect()
                    }));
                    
                    return {
                        total: images.length,
                        base64Count: images.filter(img => img.src.startsWith('data:')).length,
                        completeCount: images.filter(img => img.complete).length,
                        displayedCount: images.filter(img => img.offsetWidth > 0 && img.offsetHeight > 0).length,
                        visibleCount: images.filter(img => {
                            const rect = img.getBoundingClientRect();
                            return rect.width > 0 && rect.height > 0;
                        }).length,
                        details: imageDetails
                    };
                }
            """)
            
            logging.info(f"🔍 Detailed PDF-ready analysis:")
            logging.info(f"   📊 Total: {debug_info['total']}, Base64: {debug_info['base64Count']}")
            logging.info(f"   📊 Complete: {debug_info['completeCount']}, Displayed: {debug_info['displayedCount']}, Visible: {debug_info['visibleCount']}")
            
            # Log problematic images that might not render in PDF
            problematic_images = [img for img in debug_info['details'] 
                                if img['isBase64'] and (not img['displayed'] or img['rect']['width'] == 0)]
            
            if problematic_images:
                logging.warning(f"⚠️ Found {len(problematic_images)} images that might not render in PDF:")
                for img in problematic_images[:5]:  # Log first 5
                    logging.warning(f"   Image {img['index']}: complete={img['complete']}, displayed={img['displayed']}, rect=({img['rect']['width']}x{img['rect']['height']})")
                
                # Force fix problematic images for PDF rendering
                fixed_count = await page.evaluate("""
                    () => {
                        const images = Array.from(document.images);
                        let fixedCount = 0;
                        
                        images.forEach((img, index) => {
                            if (img.src.startsWith('data:')) {
                                const rect = img.getBoundingClientRect();
                                
                                // Force visibility and dimensions for PDF rendering
                                if (rect.width === 0 || rect.height === 0 || !img.offsetParent) {
                                    console.log(`Forcing visibility for image ${index}...`);
                                    
                                    // Apply aggressive styling to ensure PDF visibility
                                    img.style.cssText = `
                                        display: block !important;
                                        visibility: visible !important;
                                        opacity: 1 !important;
                                        width: auto !important;
                                        max-width: 100% !important;
                                        height: auto !important;
                                        position: static !important;
                                        margin: 10px 0 !important;
                                        page-break-inside: avoid !important;
                                    `;
                                    
                                    // Ensure parent containers are visible
                                    let parent = img.parentElement;
                                    while (parent && parent !== document.body) {
                                        if (getComputedStyle(parent).display === 'none') {
                                            parent.style.display = 'block !important';
                                        }
                                        parent = parent.parentElement;
                                    }
                                    
                                    fixedCount++;
                                }
                            }
                        });
                        
                        // Force complete DOM reflow
                        document.body.style.display = 'none';
                        document.body.offsetHeight; // Trigger reflow
                        document.body.style.display = '';
                        document.body.offsetHeight; // Trigger reflow again
                        
                        return fixedCount;
                    }
                """)
                
                logging.info(f"🔧 Applied aggressive fixes to {fixed_count} images for PDF rendering")
                
                # For problematic images, try a nuclear approach - replace with a placeholder or re-decode
                if fixed_count > 0:
                    nuclear_fixes = await page.evaluate("""
                        () => {
                            const images = Array.from(document.images);
                            let nuclearCount = 0;
                            
                            images.forEach((img, index) => {
                                if (img.src.startsWith('data:') && (!img.complete || img.getBoundingClientRect().width === 0)) {
                                    console.log(`Nuclear fix for image ${index}...`);
                                    
                                    // Try to create a new image element with the same src
                                    const newImg = document.createElement('img');
                                    newImg.src = img.src;
                                    newImg.style.cssText = `
                                        display: block !important;
                                        width: auto !important;
                                        max-width: 600px !important;
                                        height: auto !important;
                                        margin: 10px auto !important;
                                        border: 1px solid #ccc !important;
                                        page-break-inside: avoid !important;
                                    `;
                                    
                                    // Replace the problematic image
                                    if (img.parentNode) {
                                        img.parentNode.replaceChild(newImg, img);
                                        nuclearCount++;
                                    }
                                }
                            });
                            
                            return nuclearCount;
                        }
                    """)
                    
                    if nuclear_fixes > 0:
                        logging.info(f"💥 Applied nuclear fixes (element replacement) to {nuclear_fixes} images")
                        await page.wait_for_timeout(3000)  # Extra wait for new elements
                    
                # Wait for DOM to stabilize after all fixes
                await page.wait_for_timeout(2000)
            else:
                logging.info("✅ All base64 images appear to be properly positioned for PDF rendering")
            
            # Final verification after all fixes
            final_verification = await page.evaluate("""
                () => {
                    const images = Array.from(document.images);
                    const base64Images = images.filter(img => img.src.startsWith('data:'));
                    
                    const finalStats = {
                        total: images.length,
                        base64Count: base64Images.length,
                        completeCount: base64Images.filter(img => img.complete).length,
                        visibleCount: base64Images.filter(img => {
                            const rect = img.getBoundingClientRect();
                            return rect.width > 0 && rect.height > 0;
                        }).length,
                        stillProblematic: []
                    };
                    
                    base64Images.forEach((img, index) => {
                        const rect = img.getBoundingClientRect();
                        if (!img.complete || rect.width === 0) {
                            finalStats.stillProblematic.push({
                                index: index,
                                complete: img.complete,
                                rect: rect,
                                srcLength: img.src.length
                            });
                        }
                    });
                    
                    return finalStats;
                }
            """)
            
            logging.info(f"🔍 Final verification: {final_verification['completeCount']}/{final_verification['base64Count']} complete, {final_verification['visibleCount']} visible")
            
            if final_verification['stillProblematic']:
                logging.warning(f"⚠️ {len(final_verification['stillProblematic'])} images still problematic after all fixes")
                for prob in final_verification['stillProblematic'][:3]:
                    logging.warning(f"   Still problematic: index={prob['index']}, complete={prob['complete']}, srcLength={prob['srcLength']}")
            else:
                logging.info("🎉 All images are now properly loaded and visible!")
            
            # Since all images are converted to base64, they should be embedded in the PDF
            logging.info("✅ Proceeding to PDF generation - all images are base64 embedded")
            
            # Generate PDF with high quality settings optimized for images
            pdf_bytes = await page.pdf(
                format='A4',
                margin={
                    'top': '0.4in',
                    'bottom': '0.4in', 
                    'left': '0.4in',
                    'right': '0.4in'
                },
                print_background=True,  # Essential for background images and charts
                prefer_css_page_size=True,
                display_header_footer=False,
                scale=1.0,
                # Additional options for better image quality
                page_ranges='',  # All pages
                tagged=False,    # Disable tagging for smaller file size
                outline=False    # Disable outline for smaller file size
            )
            
            await browser.close()
            
            # Final validation
            if len(pdf_bytes) < 1000:  # PDF should be at least 1KB
                raise ValueError(f"Generated PDF seems too small: {len(pdf_bytes)} bytes")
            
            logging.info(f"✅ PDF generated successfully with Playwright ({len(pdf_bytes)} bytes)")
            
            # Log success metrics
            base64_images_in_original = html_content.count('data:image/')
            logging.info(f"📊 Final stats: {base64_images_in_original} base64 images in HTML, PDF size: {len(pdf_bytes)} bytes")
            
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
        
        # Convert external images to base64 before PDF generation to ensure they're embedded
        if external_images:
            logging.info(f"🖼️ Starting optimized image conversion for {len(external_images)} external image references...")
            try:
                html_content = convert_external_images_to_base64(html_content)
                logging.info("✅ Optimized image conversion completed")
                
                # Verify conversion worked by checking for base64 images
                base64_count = html_content.count('data:image/')
                logging.info(f"📈 Final result: {base64_count} base64 images embedded in HTML")
                
                # Optionally save processed HTML for debugging (only in development)
                if os.getenv('DEBUG_PDF_HTML', '').lower() == 'true':
                    import time
                    debug_path = f"/tmp/debug_pdf_{int(time.time())}.html"
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logging.info(f"🔍 Debug: Processed HTML saved to {debug_path}")
                    
                    # Also save a sample of the base64 data for verification
                    import re
                    base64_samples = re.findall(r'data:image/[^;]+;base64,([A-Za-z0-9+/]{50})', html_content)
                    if base64_samples:
                        logging.info(f"🔍 Debug: Found {len(base64_samples)} base64 image samples, first 50 chars: {base64_samples[0][:50]}...")
            except Exception as e:
                logging.error(f"❌ Image conversion failed: {e}")
                logging.warning("⚠️ Proceeding with original HTML - some images may not embed properly")
        else:
            logging.info("ℹ️ No external images found - proceeding directly to PDF generation")
        
        # Generate PDF with Playwright (images now embedded as base64)
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
        
        # Get current session data for file information
        current_session = session_data.get(session_id, {})
        
        # Add enhanced analyzer capabilities info
        enhanced_info = {}
        if isinstance(analyzer, EnhancedStreamingAnalyzer):
            # Get assistant upload status from session memory
            assistant_upload_status = analyzer.session_memory.get_assistant_upload_status()
            
            enhanced_info ={
                'enhanced_analyzer': True,
                'ai_routing_enabled': True,  # NEW
                'query_router_available': hasattr(analyzer.query_classifier, 'routers'),  # NEW
                'assistants_enabled': True,
                'thread_id': getattr(analyzer, 'thread_id', None),
                'uploaded_files_count': len(getattr(analyzer, 'current_file_ids', [])),
                'total_session_files': len(current_session.get('files', [])),
                'files_ready_for_assistant': len([f for f in current_session.get('files', []) if f.get('assistant_upload_status') == 'completed']),
                'assistant_upload_status': assistant_upload_status,  # NEW - Track upload status
                'is_assistant_upload_complete': assistant_upload_status == "completed",  # NEW - Boolean helper
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
            'data': analyzer.df.head(100).fillna('').to_dict('records') if analyzer.df is not None else []
        }
        
        # Add multiple files information if available
        if 'files' in current_session and current_session['files']:
            file_info['files'] = current_session['files']
            file_info['totalFiles'] = len(current_session['files'])
            file_info['isMultipleFiles'] = len(current_session['files']) > 1
            
            # Sync analyzer's current_file_ids with all completed uploads from session_data
            if hasattr(analyzer, 'current_file_ids'):
                # Get all completed assistant file IDs from session data
                session_file_ids = []
                for file_data in current_session['files']:
                    if file_data.get('assistant_file_id') and file_data.get('assistant_upload_status') == 'completed':
                        session_file_ids.append(file_data['assistant_file_id'])
                
                # Update analyzer's file IDs to include all uploaded files
                analyzer.current_file_ids = list(set(analyzer.current_file_ids + session_file_ids))
                logging.info(f"🔄 Synced analyzer file IDs: {len(analyzer.current_file_ids)} total files")
        
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
                'data': analyzer.df.head(100).fillna('').to_dict('records') if analyzer.df is not None else []
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


@app.route('/upload-files', methods=['POST', 'OPTIONS'])
def upload_multiple_files_with_session():
    """Handle multiple CSV file upload - ENHANCED for Assistants API support"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
   
    # Get list of files instead of single file
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files provided'}), 400
   
    # Validate all files first
    for file in files:
        if file.filename == '':
            return jsonify({'error': 'One or more files not selected'}), 400
        if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            return jsonify({'error': f'Please upload CSV or Excel files only. Invalid: {file.filename}'}), 400
   
    try:
        # Generate new session ID for this upload (same as before)
        new_session_id = str(uuid.uuid4())
        
        # Initialize ENHANCED analyzer (same as before)
        analyzer = EnhancedStreamingAnalyzer(new_session_id, socketio)
        
        # Check blob storage (same as before)
        if not analyzer.blob_service_client:
            return jsonify({'error': 'Blob storage not configured. Please check Azure credentials.'}), 500
        
        logging.info(f"Processing {len(files)} files upload with Assistants API support")
        
        # Process each file
        files_info = []
        blob_results = []
        
        for i, file in enumerate(files):
            # Upload each file stream to blob storage with indexed naming
            file.stream.seek(0)  # Reset stream position
            indexed_filename = f"{i}_{file.filename}"  # Add index to avoid conflicts
            
            blob_result = analyzer.upload_stream_and_get_sas_url(
                file.stream, 
                indexed_filename, 
                expiry_hours=168
            )
            
            if not blob_result['success']:
                return jsonify({'error': f"Failed to upload {file.filename} to blob storage: {blob_result.get('error')}"}), 500
            
            blob_results.append({
                'index': i,
                'filename': file.filename,
                'indexed_filename': indexed_filename,
                'sas_url': blob_result['sas_url'],
                'blob_name': blob_result['blob_name']
            })
            
            # Reset file stream for size calculation
            file.stream.seek(0)
            file_content = file.stream.read()
            file_size = len(file_content)
            
            files_info.append({
                'index': i,
                'filename': file.filename,
                'size': file_size,
                'upload_status': 'blob_completed',
                'assistant_upload_status': 'pending',
                'blob_name': blob_result['blob_name'],  # Add blob info for preview generation
                'sas_url': blob_result['sas_url']       # Add SAS URL for direct access
            })
        
        # Load and analyze first file (primary file) WITHOUT uploading to assistant yet
        # (Assistant upload will happen in background for ALL files including primary)
        primary_file = blob_results[0]
        
        # Load primary file data but skip assistant upload (will be done in background)
        import requests
        import tempfile
        import os
        import pandas as pd
        
        file_extension = os.path.splitext(primary_file['filename'])[-1]
        
        response = requests.get(primary_file['sas_url'])
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        try:
            if file_extension == ".csv":
                analyzer.df = pd.read_csv(temp_path, encoding="utf-8")
            else:
                analyzer.df = pd.read_excel(temp_path, engine='openpyxl')
            
            # Update conversation context
            analyzer.conversation_context.update({
                "has_data": True,
                "filename": primary_file['filename'],
                "shape": analyzer.df.shape,
                "columns": list(analyzer.df.columns)
            })
            
        finally:
            os.unlink(temp_path)
        
        # Store analyzer and session data (same as before)
        analyzers[new_session_id] = analyzer
        
        # Enhanced session data for multiple files  
        logging.info(f"📂 [UPLOAD] Creating session data for session: {new_session_id}")
        logging.info(f"📂 [UPLOAD] Files info: {files_info}")
        
        session_data[new_session_id] = {
            'session_id': new_session_id,
            'files': files_info,  # Array of file info
            'primary_file_index': 0,  # Which file is primary
            'blob_results': blob_results,
            'filename': primary_file['filename'],  # For backward compatibility
            'blob_sas_url': primary_file['sas_url'],  # For backward compatibility
            'blob_name': primary_file['blob_name'],  # For backward compatibility
            'upload_time': datetime.now().isoformat(),
            'shape': analyzer.df.shape,  # Shape of primary file
            'columns': list(analyzer.df.columns),  # Columns of primary file
            'created_by': session.get('user_id', 'anonymous'),
            'last_activity': datetime.now().isoformat(),
            'analyzer_type': 'enhanced_assistants',
            'storage_type': 'blob_only',
            'assistants_enabled': True,
            'thread_id': analyzer.thread_id,
            'assistant_upload_status': 'pending',
            'is_assistant_upload_complete': False
        }
        
        # Start background assistant upload for all files
        def background_assistant_upload():
            try:
                logging.info(f"🚀 Starting background assistant upload for {len(blob_results)} files in session {new_session_id}")
                for i, blob_info in enumerate(blob_results):
                    try:
                        logging.info(f"📂 Processing file {i+1}/{len(blob_results)}: {blob_info['filename']} (index: {blob_info['index']})")
                        
                        # Download file from blob for assistant upload
                        blob_client = analyzer.blob_service_client.get_blob_client(
                            container=analyzer.container_name, 
                            blob=blob_info['blob_name']
                        )
                        blob_data = blob_client.download_blob()
                        
                        from io import BytesIO
                        file_stream = BytesIO(blob_data.readall())
                        
                        logging.info(f"🔄 Uploading {blob_info['filename']} to assistant...")
                        file_id = analyzer.file_manager.upload_csv_from_stream(
                            file_stream, 
                            blob_info['filename'], 
                            new_session_id  # Use consistent session ID
                        )
                        logging.info(f"✅ Assistant upload complete: {blob_info['filename']} -> {file_id}")
                        
                        # Ensure we have the correct index in session_data
                        file_index = blob_info['index']
                        logging.info(f"📂 [BACKGROUND] Updating session {new_session_id}, file index {file_index} with assistant_file_id {file_id}")
                        
                        if file_index < len(session_data[new_session_id]['files']):
                            # Update session data with assistant file ID
                            session_data[new_session_id]['files'][file_index]['assistant_file_id'] = file_id
                            session_data[new_session_id]['files'][file_index]['assistant_upload_status'] = 'completed'
                            logging.info(f"📋 [BACKGROUND] Updated session_data for file index {file_index}: {session_data[new_session_id]['files'][file_index]['filename']}")
                            logging.info(f"📋 [BACKGROUND] Session now has {len([f for f in session_data[new_session_id]['files'] if f.get('assistant_upload_status') == 'completed'])} completed files")
                        else:
                            logging.error(f"❌ File index {file_index} out of range for session files array (length: {len(session_data[new_session_id]['files'])})")
                        
                        # Also update the analyzer's current_file_ids
                        if hasattr(analyzer, 'current_file_ids'):
                            analyzer.current_file_ids.append(file_id)
                            logging.info(f"📋 Added file_id {file_id} to analyzer.current_file_ids. Total: {len(analyzer.current_file_ids)}")
                        
                    except Exception as file_error:
                        logging.error(f"❌ Error processing file {blob_info['filename']}: {file_error}")
                        # Mark this specific file as failed
                        if blob_info['index'] < len(session_data[new_session_id]['files']):
                            session_data[new_session_id]['files'][blob_info['index']]['assistant_upload_status'] = 'failed'
                
                # Mark overall upload as complete
                session_data[new_session_id]['assistant_upload_status'] = 'completed'
                session_data[new_session_id]['is_assistant_upload_complete'] = True
                
                # Also update the analyzer's session memory
                if hasattr(analyzer, 'session_memory') and analyzer.session_memory:
                    analyzer.session_memory.set_assistant_upload_status('completed')
                
                logging.info(f"✅ Background assistant upload completed for session {new_session_id}")
                
            except Exception as e:
                logging.error(f"❌ Background assistant upload failed for session {new_session_id}: {e}")
                logging.exception("Detailed background upload error:")
                session_data[new_session_id]['assistant_upload_status'] = 'failed'
                
                # Also update the analyzer's session memory
                if hasattr(analyzer, 'session_memory') and analyzer.session_memory:
                    analyzer.session_memory.set_assistant_upload_status('failed')
                
                for file_info in session_data[new_session_id]['files']:
                    if file_info['assistant_upload_status'] == 'pending':
                        file_info['assistant_upload_status'] = 'failed'
        
        # Set initial session memory status
        if hasattr(analyzer, 'session_memory') and analyzer.session_memory:
            analyzer.session_memory.set_assistant_upload_status('pending')
        
        # Start background thread (same pattern as current code)
        threading.Thread(target=background_assistant_upload, daemon=True).start()
        
        # Clear any existing stop signals for this session
        clear_stop_signal_for_session(new_session_id)
        
        # Generate preview for ALL files (not just primary)
        import tempfile
        temp_dir = tempfile.gettempdir()
        
        # Add preview data to each file info
        for i, file_info in enumerate(files_info):
            try:
                # Generate unique temp file path
                temp_file_path = os.path.join(temp_dir, f"temp_{i}_{file_info['filename']}")
                
                # Download file from blob for preview generation
                blob_client = analyzer.blob_service_client.get_blob_client(
                    container=analyzer.container_name, 
                    blob=file_info['blob_name']
                )
                
                with open(temp_file_path, "wb") as temp_file:
                    blob_data = blob_client.download_blob()
                    temp_file.write(blob_data.readall())
                
                # Generate preview and handle Excel sheets properly
                file_extension = os.path.splitext(file_info['filename'])[-1].lower()
                
                if file_extension in ['.xlsx', '.xls']:
                    # For Excel files, process each sheet separately
                    try:
                        import pandas as pd
                        from openpyxl import load_workbook
                        
                        # Load workbook to get sheet information
                        wb = load_workbook(temp_file_path, data_only=True)
                        sheets_data = []
                        
                        for sheet_idx, sheet_name in enumerate(wb.sheetnames[:3]):  # Max 3 sheets
                            # Read individual sheet
                            df_sheet = pd.read_excel(temp_file_path, sheet_name=sheet_name)
                            
                            # Create temp file for individual sheet
                            base_path = os.path.splitext(temp_file_path)[0]
                            sheet_temp_path = f"{base_path}_sheet_{sheet_idx}.csv"
                            df_sheet.to_csv(sheet_temp_path, index=False)
                            
                            # Generate preview for individual sheet
                            sheet_preview = generate_sheet_images_with_highlighting(sheet_temp_path, max_sheets=1)
                            
                            sheets_data.append({
                                'name': sheet_name,
                                'preview': sheet_preview,
                                'shape': list(df_sheet.shape),
                                'columns': df_sheet.columns.tolist(),
                                'data': df_sheet.head(100).fillna('').to_dict('records')
                            })
                            
                            # Clean up individual sheet temp file
                            os.unlink(sheet_temp_path)
                        
                        # Use first sheet as main preview
                        file_info['preview'] = sheets_data[0]['preview'] if sheets_data else ''
                        file_info['sheets'] = sheets_data
                        file_info['has_preview'] = True
                        
                    except Exception as excel_error:
                        logging.error(f"❌ Excel processing failed for {file_info['filename']}: {excel_error}")
                        # Fallback to combined preview
                        file_preview_html = generate_sheet_images_with_highlighting(temp_file_path, max_sheets=3)
                        file_info['preview'] = file_preview_html
                        file_info['has_preview'] = True
                else:
                    # For CSV files, use existing logic
                    file_preview_html = generate_sheet_images_with_highlighting(temp_file_path, max_sheets=3)
                    file_info['preview'] = file_preview_html
                    file_info['has_preview'] = True
                
                # Clean up temp file
                os.unlink(temp_file_path)
                
                logging.info(f"✅ Generated preview for file {i+1}/{len(files_info)}: {file_info['filename']}")
                
            except Exception as file_error:
                logging.error(f"❌ Failed to generate preview for {file_info['filename']}: {file_error}")
                # Add fallback preview
                file_info['preview'] = f'''
                <div class="sheet-images-preview bg-gray-50 dark:bg-gray-900 p-6">
                    <div class="text-center">
                        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                            File Ready: {file_info['filename']}
                        </h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400">
                            Preview generation in progress...
                        </p>
                    </div>
                </div>
                '''
                file_info['has_preview'] = False
        
        # Use primary file preview for backward compatibility
        primary_preview = files_info[0].get('preview', 'No preview available')
        
        # Prepare response data with individual file previews
        response_data = {
            'success': True,
            'session_id': new_session_id,
            'files': files_info,  # Now includes preview data for each file
            'total_files': len(files_info),
            'primary_file': files_info[0],
            'data': {
                'filename': primary_file['filename'],
                'shape': list(analyzer.df.shape),
                'columns': list(analyzer.df.columns),
                'preview': primary_preview,  # Primary file preview for compatibility
                'files': files_info,  # Include all files with their previews
                'session_id': new_session_id,
                'upload_time': datetime.now().isoformat(),
                'total_files': len(files_info),
                'isMultipleFiles': len(files_info) > 1,
                'totalFiles': len(files_info)  # For frontend compatibility
            }
        }
        
        response = jsonify(response_data)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
           
    except Exception as e:
        print(f"❌ Multi-file upload error: {str(e)}")
        logging.exception("Detailed multi-file upload error")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/session/<session_id>/upload-files', methods=['POST', 'OPTIONS'])
def upload_files_to_existing_session(session_id):
    """Add multiple files to an existing session - UPDATED FOR ENHANCED ANALYZER"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files provided'}), 400
    
    # Validate files
    for file in files:
        if file.filename == '':
            return jsonify({'error': 'One or more files not selected'}), 400
        if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            return jsonify({'error': f'Invalid file type: {file.filename}'}), 400
    
    try:
        # Check if session exists (same as current logic)
        if session_id not in analyzers:
            return jsonify({'error': 'Session not found'}), 404
        
        analyzer = analyzers[session_id]
        current_session_data = session_data[session_id]
        
        # Get current file count for indexing
        existing_files = current_session_data.get('files', [])
        start_index = len(existing_files) if existing_files else 1  # Start from 1 if no files array (backward compatibility)
        
        # Process new files
        new_files_info = []
        
        for i, file in enumerate(files):
            # Save to local uploads folder (following current logic pattern)
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{start_index + i}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            new_files_info.append({
                'index': start_index + i,
                'filename': file.filename,
                'filepath': filepath,
                'size': os.path.getsize(filepath),
                'upload_status': 'completed',
                'assistant_upload_status': 'pending'
            })
        
        # Initialize files array if it doesn't exist (backward compatibility)
        if 'files' not in current_session_data:
            # Convert existing session to multi-file format
            current_session_data['files'] = [{
                'index': 0,
                'filename': current_session_data.get('filename', 'unknown'),
                'filepath': '',  # Blob storage based
                'size': 0,
                'upload_status': 'completed',
                'assistant_upload_status': 'completed'
            }]
            current_session_data['primary_file_index'] = 0
        
        # Update session data by extending files array
        current_session_data['files'].extend(new_files_info)
        current_session_data['last_activity'] = datetime.now().isoformat()
        
        # Start background assistant upload for new files
        def background_assistant_upload():
            try:
                for file_info in new_files_info:
                    with open(file_info['filepath'], 'rb') as f:
                        file_id = analyzer.file_manager.upload_csv_from_stream(
                            f, 
                            file_info['filename'], 
                            session_id  # Use consistent session ID
                        )
                        file_info['assistant_file_id'] = file_id
                        file_info['assistant_upload_status'] = 'completed'
                        
                        # Also update the analyzer's current_file_ids
                        if hasattr(analyzer, 'current_file_ids'):
                            analyzer.current_file_ids.append(file_id)
                        
                logging.info(f"✅ Background assistant upload completed for new files in session {session_id}")
                        
            except Exception as e:
                logging.error(f"Background assistant upload failed: {e}")
                for file_info in new_files_info:
                    if file_info['assistant_upload_status'] == 'pending':
                        file_info['assistant_upload_status'] = 'failed'
        
        threading.Thread(target=background_assistant_upload, daemon=True).start()
        
        # Clear any existing stop signals
        clear_stop_signal_for_session(session_id)
        
        response_data = {
            'success': True,
            'message': f'Successfully added {len(files)} files to session',
            'session_id': session_id,
            'files': new_files_info,
            'total_files': len(current_session_data['files']),
            'data': {
                'session_id': session_id,
                'filename': new_files_info[0]['filename'],
                'shape': analyzer.df.shape if hasattr(analyzer, 'df') and analyzer.df is not None else [0, 0],
                'columns': list(analyzer.df.columns) if hasattr(analyzer, 'df') and analyzer.df is not None else [],
                'total_files': len(current_session_data['files'])
            }
        }
        
        response = jsonify(response_data)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Multi-file add error: {str(e)}")
        return jsonify({'error': f'Failed to add files: {str(e)}'}), 500


@app.route('/session/<session_id>/debug', methods=['GET', 'OPTIONS'])
def debug_session_files(session_id):
    """Debug endpoint to check file status and analyzer state"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        # Check session data
        current_session = session_data.get(session_id, {})
        analyzer = analyzers.get(session_id)
        
        debug_info = {
            'session_id': session_id,
            'session_exists': session_id in session_data,
            'analyzer_exists': session_id in analyzers,
            'session_data': {
                'files': current_session.get('files', []),
                'assistant_upload_status': current_session.get('assistant_upload_status'),
                'is_assistant_upload_complete': current_session.get('is_assistant_upload_complete')
            },
            'analyzer_state': {},
            'file_manager_state': {}
        }
        
        if analyzer:
            debug_info['analyzer_state'] = {
                'current_file_ids': getattr(analyzer, 'current_file_ids', []),
                'current_file_ids_count': len(getattr(analyzer, 'current_file_ids', [])),
                'thread_id': getattr(analyzer, 'thread_id', None),
                'session_id': analyzer.session_id,
                'has_df': analyzer.df is not None,
                'has_file_manager': hasattr(analyzer, 'file_manager'),
                'has_assistant_manager': hasattr(analyzer, 'assistant_manager')
            }
            
            if hasattr(analyzer, 'file_manager') and analyzer.file_manager:
                debug_info['file_manager_state'] = {
                    'uploaded_files': analyzer.file_manager.uploaded_files,
                    'session_files': analyzer.file_manager.list_session_files(session_id)
                }
        
        response = jsonify(debug_info)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# DATABASE CONNECTION ENDPOINTS
# =============================================================================

@app.route('/database/test-connection', methods=['POST', 'OPTIONS'])
def test_database_connection():
    """Test database connection before creating session"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        connection_params = request.json
        
        # Validate required parameters
        required_params = ['connection_type', 'host', 'database', 'username', 'password']
        missing_params = [param for param in required_params if not connection_params.get(param)]
        if missing_params:
            return jsonify({
                'success': False,
                'message': f'Missing required parameters: {", ".join(missing_params)}'
            }), 400
        
        # Import and use database connector
        from utils.database_connector import DatabaseConnector
        
        connector = DatabaseConnector()
        result = connector.test_connection(connection_params)
        
        return jsonify({
            'success': result['status'] == 'success',
            'message': result['message'],
            'tables_count': result.get('tables_count', 0)
        })
        
    except Exception as e:
        logging.error(f"Database connection test failed: {e}")
        return jsonify({
            'success': False,
            'message': f'Connection test failed: {str(e)}'
        }), 500


@app.route('/database/connect', methods=['POST', 'OPTIONS'])
def connect_database():
    """Create session with database connection (mirrors file upload flow)"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        connection_params = request.json
        
        # Validate required parameters
        required_params = ['connection_type', 'host', 'database', 'username', 'password']
        missing_params = [param for param in required_params if not connection_params.get(param)]
        if missing_params:
            return jsonify({
                'success': False,
                'error': f'Missing required parameters: {", ".join(missing_params)}'
            }), 400
        
        # Generate session ID (same as file upload)
        session_id = str(uuid.uuid4())
        
        # Initialize database analyzer
        analyzer = EnhancedStreamingAnalyzer(session_id, socketio)
        success = analyzer.load_database_connection(connection_params)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to database'
            }), 400
        
        # Store session data (mirrors file upload session structure)
        session_data[session_id] = {
            'data_source_type': 'database',
            'database_connection': {
                'connection_params': connection_params,
                'connection_status': 'connected'
            },
            'created_at': datetime.now().isoformat(),
            'files': [],  # Empty for database sessions
            'last_activity': datetime.now().isoformat(),
            'message_count': 0,
            'assistant_upload_status': 'completed'  # Database schema uploaded to assistants
        }
        
        # Store analyzer
        analyzers[session_id] = analyzer
        
        logging.info(f"✅ Database session created: {session_id} ({connection_params['connection_type']})")
        
        response = jsonify({
            'success': True,
            'session_id': session_id,
            'message': f'Connected to {connection_params["connection_type"]} database successfully'
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to connect to database: {str(e)}'
        }), 500


@app.route('/database/schema/<session_id>', methods=['GET', 'OPTIONS'])
def get_database_schema(session_id):
    """Get database schema information for a session"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        # Validate session exists and is database type
        if session_id not in session_data:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        session = session_data[session_id]
        if session.get('data_source_type') != 'database':
            return jsonify({'success': False, 'error': 'Not a database session'}), 400
        
        # Get database info
        db_connection = session.get('database_connection', {})
        analyzer = analyzers.get(session_id)
        
        schema_info = {}
        if analyzer and hasattr(analyzer, 'db_schema'):
            schema_info = analyzer.db_schema
        
        return jsonify({
            'success': True,
            'connection_status': db_connection.get('connection_status', 'unknown'),
            'connection_type': db_connection.get('connection_params', {}).get('connection_type', 'unknown'),
            'database_name': db_connection.get('connection_params', {}).get('database', 'unknown'),
            'tables': schema_info,
            'tables_count': len(schema_info)
        })
        
    except Exception as e:
        logging.error(f"Error getting database schema: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
                'data': 'Session terminated by user',
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

# ==================== DASHBOARD ROUTES ====================

@app.route('/dashboards', methods=['GET', 'OPTIONS'])
def get_user_dashboards():
    """Get all dashboards for the current user"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        user_id = request.cookies.get('user_insipredict_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid user session'
            }), 401
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get dashboards with visualization count
        cursor.execute('''
            SELECT d.*, COUNT(dv.id) as visualization_count 
            FROM dashboards d 
            LEFT JOIN dashboard_visualizations dv ON d.id = dv.dashboard_id 
            WHERE d.user_id = %s
            GROUP BY d.id 
            ORDER BY d.updated_at DESC
        ''', (user_id,))
        
        dashboards = []
        for row in cursor.fetchall():
            dashboards.append({
                'id': str(row['id']),
                'name': row['name'],
                'description': row['description'],
                'created_at': row['created_at'].isoformat(),
                'updated_at': row['updated_at'].isoformat(),
                'visualization_count': row['visualization_count']
            })
        
        cursor.close()
        conn.close()
        
        response = jsonify({
            'success': True,
            'dashboards': dashboards
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Error getting dashboards: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get dashboards: {str(e)}'
        }), 500

@app.route('/dashboards', methods=['POST'])
def create_dashboard():
    """Create a new dashboard"""
    try:
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Dashboard name is required'
            }), 400
        
        user_id = request.cookies.get('user_insipredict_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid user session'
            }), 401
            
        name = data.get('name')
        description = data.get('description', '')
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cursor.execute('''
            INSERT INTO dashboards (name, description, user_id) 
            VALUES (%s, %s, %s) 
            RETURNING id, name, description, created_at, updated_at
        ''', (name, description, user_id))
        
        dashboard = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        response_data = {
            'success': True,
            'dashboard': {
                'id': str(dashboard['id']),
                'name': dashboard['name'],
                'description': dashboard['description'],
                'created_at': dashboard['created_at'].isoformat(),
                'updated_at': dashboard['updated_at'].isoformat(),
                'visualization_count': 0
            }
        }
        
        response = jsonify(response_data)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Error creating dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to create dashboard: {str(e)}'
        }), 500

@app.route('/dashboards/<dashboard_id>/visualizations', methods=['POST'])
def add_visualization_to_dashboard(dashboard_id):
    """Add a visualization to a dashboard"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Visualization data is required'
            }), 400
        
        user_id = request.cookies.get('user_insipredict_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid user session'
            }), 401
        
        # Verify dashboard belongs to user
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cursor.execute('SELECT id FROM dashboards WHERE id = %s AND user_id = %s', 
                      (dashboard_id, user_id))
        dashboard = cursor.fetchone()
        
        if not dashboard:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Dashboard not found'
            }), 404
        
        # Add visualization
        title = data.get('title', 'Untitled Visualization')
        chart_data = data.get('chart_data', '')
        filename = data.get('filename', '')
        chart_type = data.get('chart_type', 'unknown')
        position = data.get('position', {})
        
        cursor.execute('''
            INSERT INTO dashboard_visualizations 
            (dashboard_id, title, chart_data, filename, chart_type, position_x, position_y, width, height) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
            RETURNING id, title, chart_data, filename, chart_type, position_x, position_y, width, height, created_at
        ''', (
            dashboard_id, title, chart_data, filename, chart_type,
            position.get('x', 0), position.get('y', 0), 
            position.get('width', 400), position.get('height', 300)
        ))
        
        visualization = cursor.fetchone()
        
        # Update dashboard updated_at
        cursor.execute('UPDATE dashboards SET updated_at = CURRENT_TIMESTAMP WHERE id = %s', (dashboard_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        response_data = {
            'success': True,
            'visualization': {
                'id': str(visualization['id']),
                'title': visualization['title'],
                'chart_data': visualization['chart_data'],
                'filename': visualization['filename'],
                'chart_type': visualization['chart_type'],
                'position': {
                    'x': visualization['position_x'],
                    'y': visualization['position_y'],
                    'width': visualization['width'],
                    'height': visualization['height']
                },
                'created_at': visualization['created_at'].isoformat()
            }
        }
        
        response = jsonify(response_data)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Error adding visualization to dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to add visualization: {str(e)}'
        }), 500

@app.route('/dashboards/<dashboard_id>', methods=['GET', 'OPTIONS'])
def get_dashboard_with_visualizations(dashboard_id):
    """Get a dashboard with all its visualizations"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        user_id = request.cookies.get('user_insipredict_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid user session'
            }), 401
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get dashboard
        cursor.execute('SELECT * FROM dashboards WHERE id = %s AND user_id = %s', 
                      (dashboard_id, user_id))
        dashboard = cursor.fetchone()
        
        if not dashboard:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Dashboard not found'
            }), 404
        
        # Get visualizations
        cursor.execute('''
            SELECT * FROM dashboard_visualizations 
            WHERE dashboard_id = %s 
            ORDER BY created_at ASC
        ''', (dashboard_id,))
        
        visualizations = []
        for viz in cursor.fetchall():
            visualizations.append({
                'id': str(viz['id']),
                'title': viz['title'],
                'chart_data': viz['chart_data'],
                'filename': viz['filename'],
                'chart_type': viz['chart_type'],
                'position': {
                    'x': viz['position_x'],
                    'y': viz['position_y'],
                    'width': viz['width'],
                    'height': viz['height']
                },
                'created_at': viz['created_at'].isoformat()
            })
        
        cursor.close()
        conn.close()
        
        dashboard_data = {
            'id': str(dashboard['id']),
            'name': dashboard['name'],
            'description': dashboard['description'],
            'created_at': dashboard['created_at'].isoformat(),
            'updated_at': dashboard['updated_at'].isoformat(),
            'visualizations': visualizations
        }
        
        response = jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Error getting dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get dashboard: {str(e)}'
        }), 500

@app.route('/dashboards/<dashboard_id>/visualizations/<visualization_id>', methods=['DELETE', 'OPTIONS'])
def remove_visualization_from_dashboard(dashboard_id, visualization_id):
    """Remove a visualization from a dashboard"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        user_id = request.cookies.get('user_insipredict_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid user session'
            }), 401
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verify dashboard belongs to user
        cursor.execute('SELECT id FROM dashboards WHERE id = %s AND user_id = %s', 
                      (dashboard_id, user_id))
        dashboard = cursor.fetchone()
        
        if not dashboard:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Dashboard not found'
            }), 404
        
        # Remove visualization
        cursor.execute('DELETE FROM dashboard_visualizations WHERE id = %s AND dashboard_id = %s', 
                      (visualization_id, dashboard_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Visualization not found'
            }), 404
        
        # Update dashboard updated_at
        cursor.execute('UPDATE dashboards SET updated_at = CURRENT_TIMESTAMP WHERE id = %s', (dashboard_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        response = jsonify({
            'success': True,
            'message': 'Visualization removed successfully'
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Error removing visualization: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to remove visualization: {str(e)}'
        }), 500

@app.route('/dashboards/<dashboard_id>', methods=['DELETE', 'OPTIONS'])
def delete_dashboard(dashboard_id):
    """Delete a dashboard and all its visualizations"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        user_id = request.cookies.get('user_insipredict_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid user session'
            }), 401
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verify dashboard belongs to user
        cursor.execute('SELECT id FROM dashboards WHERE id = %s AND user_id = %s', 
                      (dashboard_id, user_id))
        dashboard = cursor.fetchone()
        
        if not dashboard:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Dashboard not found'
            }), 404
        
        # Delete dashboard (cascade will delete visualizations)
        cursor.execute('DELETE FROM dashboards WHERE id = %s', (dashboard_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        response = jsonify({
            'success': True,
            'message': 'Dashboard deleted successfully'
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Error deleting dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete dashboard: {str(e)}'
        }), 500

@app.route('/dashboards/<dashboard_id>/visualizations/<visualization_id>/position', methods=['PUT', 'OPTIONS'])
def update_visualization_position(dashboard_id, visualization_id):
    """Update the position and size of a visualization in a dashboard"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Methods', 'PUT')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Position data is required'
            }), 400
        
        user_id = request.cookies.get('user_insipredict_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid user session'
            }), 401
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verify dashboard belongs to user
        cursor.execute('SELECT id FROM dashboards WHERE id = %s AND user_id = %s', 
                      (dashboard_id, user_id))
        dashboard = cursor.fetchone()
        
        if not dashboard:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Dashboard not found'
            }), 404
        
        # Update visualization position
        cursor.execute('''
            UPDATE dashboard_visualizations 
            SET position_x = %s, position_y = %s, width = %s, height = %s 
            WHERE id = %s AND dashboard_id = %s
        ''', (
            data.get('x', 0), data.get('y', 0), 
            data.get('width', 400), data.get('height', 300),
            visualization_id, dashboard_id
        ))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Visualization not found'
            }), 404
        
        # Update dashboard updated_at
        cursor.execute('UPDATE dashboards SET updated_at = CURRENT_TIMESTAMP WHERE id = %s', (dashboard_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        response = jsonify({
            'success': True,
            'message': 'Position updated successfully'
        })
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"❌ Error updating visualization position: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to update position: {str(e)}'
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
    """ENHANCED Handle chat messages with sequential execution support"""
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
                'data': f'Processing your message: {query}',
                'timestamp': datetime.now().isoformat(),
                'sessionId': session_id
            }, room=session_id)
            
            # Start the ENHANCED analysis with sequential support
            result = analyzer.analyze_query_streaming(user_query=query)

            if result is None:
                result = {}
            
            # Handle different result types including NEW sequential type
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
                analysis_summary = result.get('analysis_summary', '')
                
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
                        'code_lines': _count_code_lines(generated_code),
                        'has_summary': bool(analysis_summary),
                        'summary_generated': result.get('summary_generated', False)
                    }
                }
                
                # Emit DataFrames and code
                _emit_dataframes_to_frontend(dataframes, session_id, socketio)
                _emit_code_to_frontend(generated_code, session_id, socketio)
                _emit_summary_to_frontend(analysis_summary, session_id, socketio, result)

            elif result.get("type") == "sequential_analysis_and_report":
                # 🎯 NEW: Sequential execution result (data analysis + report)
                dataframes = result.get('dataframes', {})
                generated_code = result.get('generated_code', '')
                comprehensive_report = result.get('comprehensive_report', '')
                embedded_images = result.get('embedded_images', [])
                analysis_summary = result.get('analysis_summary', '')
                
                completion_data = {
                    'type': 'completion',
                    'data': 'Sequential analysis and report completed successfully!',
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': session_id,
                    'result': {
                        'success': result.get('success', False),
                        'type': 'sequential_analysis_and_report',
                        'response': result.get('response', ''),
                        'report_content': comprehensive_report,
                        'report_type': result.get('report_type', 'sequential_html_report'),
                        'embedded_images_count': len(embedded_images),
                        'embedded_images': embedded_images,
                        'report_generated': result.get('report_generated', True),
                        'sequential_execution': True,
                        'execution_sequence': result.get('execution_sequence', []),
                        'phases_completed': result.get('phases_completed', []),
                        'phases_successful': result.get('phases_successful', 0),
                        'images_count': len(result.get('generated_images', [])),
                        'files_generated': result.get('generated_files', {}),
                        'dataframes_count': len(dataframes),
                        'has_dataframes': len(dataframes) > 0,
                        'has_code': bool(_extract_code_string(generated_code)),
                        'code_lines': _count_code_lines(generated_code),
                        'session_based_report': result.get('session_based_report', False),
                        'has_summary': bool(analysis_summary),
                        'summary_generated': result.get('summary_generated', False),
                        'analysis_phase_result': result.get('analysis_phase_result', {}),
                        'report_phase_result': result.get('report_phase_result', {})
                    }
                }
                
                # Emit the comprehensive report
                socketio.emit('stream_data', {
                    'type': 'sequential_report',
                    'data': {
                        'content': comprehensive_report,
                        'embedded_images': embedded_images,
                        'report_type': result.get('report_type', 'sequential_html_report'),
                        'generated_by': 'sequential_execution',
                        'execution_sequence': result.get('execution_sequence', []),
                        'phases_completed': result.get('phases_completed', [])
                    },
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': session_id
                }, room=session_id)
                
                # Emit DataFrames and code from analysis phase
                _emit_dataframes_to_frontend(dataframes, session_id, socketio)
                _emit_code_to_frontend(generated_code, session_id, socketio)
                _emit_summary_to_frontend(analysis_summary, session_id, socketio, result)

            elif result.get("type") == "report":
                # Regular report type with plain text report and embedded images
                dataframes = result.get('dataframes', {})
                generated_code = result.get('generated_code', '')
                plain_text_report = result.get('comprehensive_report', '')
                embedded_images = result.get('embedded_images', [])
                analysis_summary = result.get('analysis_summary', '')
                
                completion_data = {
                    'type': 'completion',
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
                        'has_summary': bool(analysis_summary),
                        'summary_generated': result.get('summary_generated', False)
                    }
                }
                
                # Emit the plain text report with embedded image URLs
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
                        'has_summary': bool(analysis_summary),
                        'summary_generated': result.get('summary_generated', False)
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
                analysis_summary = result.get('analysis_summary', '')
                
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
                        'has_summary': bool(analysis_summary),
                        'summary_generated': result.get('summary_generated', False)
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
                print(f"Failed to emit summary: {e}")
 
 
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
    
    print(f"Stop analysis requested for session: {session_id}")
    
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
    
    print(f"Session termination requested: {session_id}")
    
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
        print(f"Error during session termination: {e}")
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
        print(f"Error getting session status: {e}")
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