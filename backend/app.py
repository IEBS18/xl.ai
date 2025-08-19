

# try:
#     import eventlet
#     eventlet.monkey_patch()
#     EVENTLET_AVAILABLE = True
#     print("✅ Eventlet monkey patch applied successfully")
# except ImportError:
#     EVENTLET_AVAILABLE = False
#     print("⚠️  Eventlet not available, using threading mode")
# except Exception as e:
#     EVENTLET_AVAILABLE = False
#     print(f"⚠️  Eventlet monkey patch failed: {e}")
#     print("   Continuing with threading mode...")

# import logging
# import os
# import json
# import uuid
# from datetime import datetime
# import threading
# import traceback
# from pathlib import Path

# from flask import Flask, render_template, request, jsonify, session, send_file, Response
# from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
# from flask_cors import CORS
# from werkzeug.utils import secure_filename
# import pandas as pd

# # Import enhanced analyzer and utilities
# from enhanced_analyzer import EnhancedStreamingAnalyzer
# from utils import (
#     ConversationHistory,
#     generate_tailwind_table,
#     generate_simple_table,
#     stop_analysis_for_session,
#     clear_stop_signal_for_session,
#     cleanup_session_data,
#     is_session_inactive,
#     is_session_too_old,
#     update_session_activity,
#     get_session_stats,
#     validate_session_exists,
#     create_session_summary,
#     StopAnalysisException,
#     LANGCHAIN_AVAILABLE
# )

# from dotenv import load_dotenv
# from auth import auth_blueprint, init_db
# import requests
# import tempfile

# load_dotenv()

# GOTENBERG_URL = os.getenv('GOTENBERG_URL')

# app = Flask(__name__)
# app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
# app.config['UPLOAD_FOLDER'] = 'uploads'
# app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# # Register auth blueprint
# app.register_blueprint(auth_blueprint, url_prefix='/auth')

# # Initialize database on startup
# try:
#     init_db()
#     print("✅ Database initialized successfully")
# except Exception as e:
#     print(f"⚠️  Database initialization failed: {e}")
#     print("   Auth features may not work properly")

# # Comprehensive CORS configuration for multiple frontend sources
# allowed_origins = [
#     "http://localhost:5173", 
#     "http://localhost", 
#     "http://127.0.0.1:5173",
#     "https://preview--data-scope-ai-lens.lovable.app",
#     "https://*.lovable.app",
#     "http://localhost:3001",
#     "http://127.0.0.1:3001",
#     "http://20.197.12.172"
# ]

# CORS(app, origins=allowed_origins, supports_credentials=True)

# # Initialize SocketIO with robust configuration
# async_mode = 'eventlet' if EVENTLET_AVAILABLE else 'threading'

# socketio = SocketIO(
#     app, 
#     cors_allowed_origins=allowed_origins,
#     async_mode=async_mode,
#     transports=['polling', 'websocket'],
#     logger=False,
#     engineio_logger=False,
#     ping_timeout=60,
#     ping_interval=25
# )

# # Ensure upload directory exists
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# # Global storage for analyzer instances per session - NOW USING ENHANCED ANALYZER
# analyzers = {}
# session_data = {}

# # Session cleanup configuration
# SESSION_CLEANUP_ENABLED = True
# SESSION_MAX_AGE_HOURS = 24
# SESSION_MAX_INACTIVE_HOURS = 24

# # ==================== ROUTES (ALL PRESERVED) ====================

# @app.route('/')
# def index():
#     """Main chat interface."""
#     if 'session_id' not in session:
#         session['session_id'] = str(uuid.uuid4())
#     return render_template('index.html')


# @app.route('/upload', methods=['POST', 'OPTIONS'])
# def upload_file_with_session():
#     """Handle CSV file upload directly to blob storage, analyze from SAS URL - NO LOCAL STORAGE."""
#     if request.method == 'OPTIONS':
#         response = jsonify({'status': 'ok'})
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
#         response.headers.add('Access-Control-Allow-Methods', 'POST')
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
   
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file provided'}), 400
   
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'error': 'No file selected'}), 400
   
#     if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
#         return jsonify({'error': 'Please upload a CSV or Excel file'}), 400
   
#     try:
#         # Generate new session ID for this upload
#         new_session_id = str(uuid.uuid4())
        
#         # Initialize analyzer
#         analyzer = EnhancedStreamingAnalyzer(new_session_id, socketio)
        
#         # Check if blob storage is available
#         if not analyzer.blob_service_client:
#             return jsonify({'error': 'Blob storage not configured. Please check Azure credentials.'}), 500
#         logging.info("we have reached here")
#         # Upload file stream directly to blob storage and get SAS URL
#         blob_result = analyzer.upload_stream_and_get_sas_url(
#             file.stream, 
#             file.filename, 
#             expiry_hours=168  # 7 days
#         )
        
#         if not blob_result['success']:
#             return jsonify({'error': f"Failed to upload to blob storage: {blob_result.get('error')}"}), 500
        
#         # Load and analyze file directly from SAS URL
#         file_extension = os.path.splitext(file.filename)[-1]
#         if not analyzer.load_csv_from_sas_url(blob_result['sas_url'], file_extension):
#             return jsonify({'error': 'Failed to load and analyze file from blob storage'}), 500
        
#         # Store analyzer and session data
#         analyzers[new_session_id] = analyzer
#         session_data[new_session_id] = {
#             'filename': file.filename,
#             'blob_sas_url': blob_result['sas_url'],
#             'blob_name': blob_result['blob_name'],
#             'sas_expires_at': blob_result['expires_at'],
#             'upload_time': datetime.now().isoformat(),
#             'shape': analyzer.df.shape,
#             'columns': list(analyzer.df.columns),
#             'created_by': session.get('user_id', 'anonymous'),
#             'last_activity': datetime.now().isoformat(),
#             'analyzer_type': 'enhanced',
#             'storage_type': 'blob_only'  # Indicate no local storage
#         }
           
#         # Clear any existing stop signals for this session
#         clear_stop_signal_for_session(new_session_id)
           
#         print(f"✅ Created new BLOB-ONLY session: {new_session_id} for file: {file.filename}")
#         print(f"📁 File stored and analyzed directly from blob storage")
           
#         response_data = {
#             'success': True,
#             'sessionId': new_session_id,
#             'message': f'File uploaded and analyzed from blob storage! Shape: {analyzer.df.shape}',
#             'data': {
#                 'filename': file.filename,
#                 'shape': analyzer.df.shape,
#                 'columns': list(analyzer.df.columns),
#                 'preview': generate_tailwind_table(analyzer.df.head()),
#                 'data': analyzer.df.head(100).to_dict('records'),
#                 'sessionId': new_session_id,
#                 'storage_type': 'blob_only',
#                 'blob_info': {
#                     'blob_name': blob_result['blob_name'],
#                     'expires_at': blob_result['expires_at'],
#                     'expiry_hours': blob_result['expiry_hours']
#                 },
#                 'features': {
#                     'conversational': True,
#                     'textual_analytical': True,
#                     'fully_analytical': True,
#                     'enhanced_capabilities': True,
#                     'blob_storage_only': True,
#                     'memory_efficient': True
#                 }
#             }
#         }
        
#         response = jsonify(response_data)
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
           
#     except Exception as e:
#         print(f"❌ Upload error: {str(e)}")
#         logging.exception("Detailed upload error")
#         return jsonify({'error': f'Upload failed: {str(e)}'}), 500
# # ==================== ALL OTHER ROUTES PRESERVED EXACTLY ====================
# # (The routes below are IDENTICAL to the original - no changes needed)

# @app.route("/generate-pdf", methods=["POST"])
# def generate_pdf():
#     """Generate PDF from HTML content using Gotenberg."""
#     html_content = request.data.decode("utf-8")

#     # Create a temporary HTML file
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp_html:
#         tmp_html.write(html_content)
#         tmp_html_path = tmp_html.name

#     try:
#         # Send HTML to Gotenberg
#         with open(tmp_html_path, "rb") as html_file:
#             files = {
#                 "files": ("index.html", html_file, "text/html"),
#             }

#             response = requests.post(GOTENBERG_URL, files=files)

#         if response.status_code == 200:
#             # Save PDF to temp file
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
#                 tmp_pdf.write(response.content)
#                 tmp_pdf_path = tmp_pdf.name

#             return send_file(tmp_pdf_path, as_attachment=True, download_name="output.pdf", mimetype="application/pdf")
#         else:
#             return jsonify({"error": "Gotenberg conversion failed", "details": response.text}), 500

#     finally:
#         # Clean up temp HTML (PDF will be deleted by Flask after send_file)
#         if os.path.exists(tmp_html_path):
#             os.remove(tmp_html_path)


# @app.route('/session/<session_id>/info', methods=['GET', 'OPTIONS'])
# def get_session_info(session_id):
#     """Get information about a specific session."""
#     if request.method == 'OPTIONS':
#         response = jsonify({'status': 'ok'})
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
    
#     try:
#         # Validate session exists
#         is_valid, error_msg = validate_session_exists(session_id, analyzers, session_data)
#         if not is_valid:
#             return jsonify({
#                 'success': False,
#                 'error': error_msg
#             }), 404
        
#         # Update last activity
#         update_session_activity(session_id, session_data)
        
#         # Get comprehensive session summary
#         session_summary = create_session_summary(session_id, session_data, analyzers)
        
#         # Get analyzer for data preview
#         analyzer = analyzers[session_id]
        
#         # Add enhanced analyzer capabilities info
#         enhanced_info = {}
#         if isinstance(analyzer, EnhancedStreamingAnalyzer):
#             enhanced_info = {
#                 'enhanced_analyzer': True,
#                 'capabilities': analyzer.get_analysis_capabilities(),
#                 'conversation_context': analyzer.get_conversation_context()
#             }
        
#         # Add data preview if DataFrame is available
#         data_preview = None
#         if analyzer.df is not None:
#             try:
#                 data_preview = generate_tailwind_table(analyzer.df.head())
#             except Exception as e:
#                 print(f"Failed to generate data preview: {e}")
#                 data_preview = "Preview unavailable"
        
#         # Create complete session info with preview
#         session_info = {
#             'success': True,
#             'fileInfo': {
#                 'filename': session_summary.get('filename'),
#                 'shape': session_summary.get('shape'),
#                 'columns': session_summary.get('columns'),
#                 'uploadTime': session_summary.get('uploadTime'),
#                 'lastActivity': session_summary.get('lastActivity'),
#                 'sessionId': session_id,
#                 'preview': data_preview,
#                 'data': analyzer.df.head(100).to_dict('records') if analyzer.df is not None else []
#             },
#             **session_summary,
#             **enhanced_info
#         }
        
#         response = jsonify(session_info)
        
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
        
#     except Exception as e:
#         print(f"❌ Session info error: {str(e)}")
#         return jsonify({
#             'success': False,
#             'error': f'Failed to get session info: {str(e)}'
#         }), 500


# @app.route('/session/<session_id>/upload', methods=['POST', 'OPTIONS'])
# def upload_to_existing_session(session_id):
#     """Upload a file to an existing session (replace existing file) - UPDATED FOR ENHANCED ANALYZER."""
#     if request.method == 'OPTIONS':
#         response = jsonify({'status': 'ok'})
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
#         response.headers.add('Access-Control-Allow-Methods', 'POST')
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
    
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file provided'}), 400
    
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'error': 'No file selected'}), 400
    
#     if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
#         return jsonify({'error': 'Please upload a CSV or Excel file'}), 400
    
#     try:
#         # Check if session exists
#         if session_id not in analyzers:
#             return jsonify({'error': 'Session not found'}), 404
        
#         # Save uploaded file
#         filename = secure_filename(file.filename)
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = f"{timestamp}_{filename}"
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)
        
#         # Update existing analyzer
#         analyzer = analyzers[session_id]
        
#         # Load the new CSV (this will reinitialize handlers for enhanced analyzer)
#         if analyzer.load_csv(filepath):
#             # Update session data
#             session_data[session_id].update({
#                 'filename': file.filename,
#                 'filepath': filepath,
#                 'upload_time': datetime.now().isoformat(),
#                 'shape': analyzer.df.shape,
#                 'columns': list(analyzer.df.columns),
#                 'last_activity': datetime.now().isoformat()
#             })
            
#             # Clear any existing stop signals for this session
#             clear_stop_signal_for_session(session_id)
            
#             print(f"✅ Updated session: {session_id} with new file: {file.filename}")
            
#             response_data = {
#                 'success': True,
#                 'sessionId': session_id,
#                 'message': f'File updated successfully! Shape: {analyzer.df.shape}',
#                 'data': {
#                     'filename': file.filename,
#                     'shape': analyzer.df.shape,
#                     'columns': list(analyzer.df.columns),
#                     'preview': generate_tailwind_table(analyzer.df.head())
#                 }
#             }
            
#             # Add enhanced capabilities info
#             if isinstance(analyzer, EnhancedStreamingAnalyzer):
#                 response_data['data']['features'] = {
#                     'conversational': True,
#                     'textual_analytical': True,
#                     'fully_analytical': True,
#                     'enhanced_capabilities': True
#                 }
            
#             response = jsonify(response_data)
#             origin = request.headers.get('Origin', '*')
#             response.headers.add('Access-Control-Allow-Origin', origin)
#             response.headers.add('Access-Control-Allow-Credentials', 'true')
#             return response
#         else:
#             return jsonify({'error': 'Failed to load CSV file'}), 400
            
#     except Exception as e:
#         print(f"❌ Session upload error: {str(e)}")
#         return jsonify({'error': f'Upload failed: {str(e)}'}), 500


# # ==================== ALL OTHER ROUTES REMAIN IDENTICAL ====================
# # (Including session history, stop, terminate, delete, list sessions, cleanup, etc.)
# # I'll include a few key ones to show they're preserved:

# @app.route('/session/<session_id>/history', methods=['GET', 'OPTIONS'])
# def get_session_history(session_id):
#     """Get conversation history for a specific session."""
#     if request.method == 'OPTIONS':
#         response = jsonify({'status': 'ok'})
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
    
#     try:
#         # Validate session exists
#         is_valid, error_msg = validate_session_exists(session_id, analyzers, session_data)
#         if not is_valid:
#             return jsonify({
#                 'success': False,
#                 'error': error_msg
#             }), 404
        
#         # Update last activity
#         update_session_activity(session_id, session_data)
        
#         analyzer = analyzers[session_id]
#         history = analyzer.conversation_history.history
#         summary = analyzer.conversation_history.get_summary()
        
#         response = jsonify({
#             'success': True,
#             'sessionId': session_id,
#             'history': history,
#             'summary': summary,
#             'totalQueries': len(history)
#         })
        
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
        
#     except Exception as e:
#         print(f"❌ Session history error: {str(e)}")
#         return jsonify({
#             'success': False,
#             'error': f'Failed to get session history: {str(e)}'
#         }), 500


# @app.route('/session/<session_id>/stop', methods=['POST', 'OPTIONS'])
# def stop_session_analysis(session_id):
#     """Stop current analysis for a specific session."""
#     if request.method == 'OPTIONS':
#         response = jsonify({'status': 'ok'})
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Methods', 'POST')
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
    
#     try:
#         # Get stop type from request body
#         data = request.get_json() or {}
#         stop_type = data.get('type', 'query')  # 'query' or 'session'
        
#         # Validate session exists
#         is_valid, error_msg = validate_session_exists(session_id, analyzers, session_data)
#         if not is_valid:
#             return jsonify({
#                 'success': False,
#                 'error': error_msg
#             }), 404
        
#         if stop_type == 'session':
#             # TERMINATE ENTIRE SESSION
#             print(f"🛑 Terminating entire session: {session_id}")
            
#             # Set stop signal first
#             stop_analysis_for_session(session_id)
            
#             # Emit session termination signal
#             socketio.emit('stream_data', {
#                 'type': 'session_terminated',
#                 'data': '🛑 Session terminated by user',
#                 'timestamp': datetime.now().isoformat()
#             }, room=session_id)
            
#             # Clean up session after a brief delay to allow message delivery
#             def delayed_cleanup():
#                 import time
#                 time.sleep(1)  # Allow WebSocket message to be sent
#                 cleanup_session_data(session_id, session_data, analyzers)
#                 print(f"🗑️ Session {session_id} terminated and cleaned up")
            
#             cleanup_thread = threading.Thread(target=delayed_cleanup)
#             cleanup_thread.daemon = True
#             cleanup_thread.start()
            
#             response_data = {
#                 'success': True,
#                 'sessionId': session_id,
#                 'message': 'Session terminated',
#                 'action': 'session_terminated',
#                 'timestamp': datetime.now().isoformat()
#             }
            
#         else:
#             # STOP CURRENT QUERY ONLY (default behavior)
#             print(f"🛑 Stopping current query for session: {session_id}")
            
#             # Set stop signal
#             stop_analysis_for_session(session_id)
            
#             # Update last activity
#             update_session_activity(session_id, session_data)
            
#             # Emit stop signal via WebSocket
#             socketio.emit('stream_data', {
#                 'type': 'stop_requested',
#                 'data': 'Stop requested by user...',
#                 'timestamp': datetime.now().isoformat()
#             }, room=session_id)
            
#             response_data = {
#                 'success': True,
#                 'sessionId': session_id,
#                 'message': 'Analysis stop requested',
#                 'action': 'query_stopped',
#                 'timestamp': datetime.now().isoformat()
#             }
        
#         response = jsonify(response_data)
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
        
#     except Exception as e:
#         print(f"❌ Stop analysis error: {str(e)}")
#         return jsonify({
#             'success': False,
#             'error': f'Failed to stop analysis: {str(e)}'
#         }), 500


# # [All other routes like terminate, delete, list sessions, cleanup, etc. remain identical]
# # Adding the essential ones for completeness:

# @app.route('/sessions', methods=['GET', 'OPTIONS'])
# def list_sessions():
#     """List all active sessions with comprehensive information."""
#     if request.method == 'OPTIONS':
#         response = jsonify({'status': 'ok'})
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
    
#     try:
#         sessions = []
        
#         for session_id in list(analyzers.keys()):
#             if session_id in session_data:
#                 session_summary = create_session_summary(session_id, session_data, analyzers)
                
#                 # Add enhanced analyzer info
#                 if isinstance(analyzers[session_id], EnhancedStreamingAnalyzer):
#                     session_summary['enhanced_analyzer'] = True
                
#                 sessions.append(session_summary)
        
#         # Sort by last activity (most recent first)
#         sessions.sort(key=lambda x: x.get('lastActivity', ''), reverse=True)
        
#         # Get overall statistics
#         stats = get_session_stats(session_data, analyzers)
        
#         # Add enhanced analyzer stats
#         enhanced_count = sum(1 for analyzer in analyzers.values() 
#                            if isinstance(analyzer, EnhancedStreamingAnalyzer))
#         stats['enhanced_analyzers_count'] = enhanced_count
        
#         response = jsonify({
#             'success': True,
#             'sessions': sessions,
#             'statistics': stats
#         })
        
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
        
#     except Exception as e:
#         print(f"❌ Sessions listing error: {str(e)}")
#         return jsonify({
#             'success': False,
#             'error': f'Failed to list sessions: {str(e)}'
#         }), 500


# # ==================== SOCKET HANDLERS (ALL PRESERVED) ====================

# @socketio.on('connect')
# def handle_connect():
#     """Handle client connection with improved session management."""
#     # Generate session ID if not exists
#     if 'session_id' not in session:
#         session['session_id'] = str(uuid.uuid4())
    
#     session_id = session['session_id']
#     join_room(session_id)
    
#     print(f"Client connected with session: {session_id}")
#     emit('status', {
#         'message': 'Connected to enhanced analysis server',
#         'sessionId': session_id,
#         'timestamp': datetime.now().isoformat(),
#         'features': {
#             'conversational': True,
#             'textual_analytical': True,
#             'fully_analytical': True
#         }
#     })


# @socketio.on('disconnect')
# def handle_disconnect():
#     """Handle client disconnection."""
#     session_id = session.get('session_id')
#     if session_id:
#         print(f'🔌 Client disconnected: {session_id}')
#         # Update last activity when disconnecting
#         update_session_activity(session_id, session_data)


# @socketio.on('join_session')
# def handle_join_session(data):
#     """Handle client joining a specific session room."""
#     session_id = data.get('sessionId')
#     if session_id:
#         join_room(session_id)
#         print(f"Client joined session room: {session_id}")
        
#         # Update last activity
#         update_session_activity(session_id, session_data)
        
#         # Clear any existing stop signals when joining
#         clear_stop_signal_for_session(session_id)
        
#         # Check if this is an enhanced analyzer session
#         enhanced_features = {}
#         if session_id in analyzers and isinstance(analyzers[session_id], EnhancedStreamingAnalyzer):
#             enhanced_features = {
#                 'conversational': True,
#                 'textual_analytical': True,
#                 'fully_analytical': True,
#                 'enhanced_capabilities': True
#             }
        
#         emit('status', {
#             'message': f'Joined session {session_id}',
#             'sessionId': session_id,
#             'timestamp': datetime.now().isoformat(),
#             'features': enhanced_features
#         })
#     else:
#         print("No session ID provided for join_session")
#         emit('error', {'message': 'No session ID provided'})


# @socketio.on('send_message_with_session')
# def handle_message_with_session(data):
#     """Handle chat messages for a specific session - USING ENHANCED ANALYZER."""
#     session_id = data.get('sessionId')
#     query = data.get('message', '').strip()
    
#     if not session_id:
#         emit('stream_data', {
#             'type': 'error',
#             'data': 'No session ID provided. Please refresh and try again.',
#             'timestamp': datetime.now().isoformat()
#         })
#         return
    
#     if not query:
#         emit('stream_data', {
#             'type': 'error',
#             'data': 'Please provide a message to analyze.',
#             'timestamp': datetime.now().isoformat()
#         })
#         return
    
#     print(f"Processing message for session: {session_id}")
#     print(f"Query: {query}")
    
#     # Validate session exists
#     is_valid, error_msg = validate_session_exists(session_id, analyzers, session_data)
#     if not is_valid:
#         emit('stream_data', {
#             'type': 'error',
#             'data': f'{error_msg}. Please go back to home and upload a file.',
#             'timestamp': datetime.now().isoformat()
#         })
#         return
    
#     # Update last activity
#     update_session_activity(session_id, session_data)
    
#     # Clear any existing stop signals
#     clear_stop_signal_for_session(session_id)
    
#     # Process the query with ENHANCED analyzer
#     def process_query():
#         try:
#             analyzer = analyzers[session_id]
#             analyzer.session_id = session_id
            
#             # Emit starting analysis
#             socketio.emit('stream_data', {
#                 'type': 'analysis_started',
#                 'data': f'🤖 Processing your message: {query}',
#                 'timestamp': datetime.now().isoformat(),
#                 'sessionId': session_id
#             }, room=session_id)
            
#             # Start the ENHANCED analysis (with query classification)
#             result = analyzer.analyze_query_streaming(query)
            
#             # Check if analysis was stopped
#             if result.get("stopped_by_user"):
#                 socketio.emit('stream_data', {
#                     'type': 'stopped',
#                     'data': 'Analysis stopped by user',
#                     'timestamp': datetime.now().isoformat(),
#                     'sessionId': session_id
#                 }, room=session_id)
#             else:
#                 # Send completion signal to the specific session room
#                 completion_data = {
#                     'type': 'completion',
#                     'data': 'Analysis completed successfully!',
#                     'timestamp': datetime.now().isoformat(),
#                     'sessionId': session_id,
#                     'result': {
#                         'success': result.get('success', False),
#                         'type': result.get('type', 'unknown'),
#                         'dataframes_count': len(result.get('dataframes', {})),
#                         'images_count': len(result.get('generated_images', []))
#                     }
#                 }
                
#                 # Add enhanced analyzer specific completion info
#                 if isinstance(analyzer, EnhancedStreamingAnalyzer):
#                     completion_data['result']['query_category'] = result.get('type', 'unknown')
#                     completion_data['result']['enhanced_analysis'] = True
                
#                 socketio.emit('stream_data', completion_data, room=session_id)
            
#         except StopAnalysisException:
#             print(f"Analysis stopped by user for session {session_id}")
            
#         except Exception as e:
#             print(f"Analysis error for session {session_id}: {str(e)}")
#             print(f"Traceback: {traceback.format_exc()}")
#             socketio.emit('stream_data', {
#                 'type': 'error',
#                 'data': f'Analysis failed: {str(e)}',
#                 'timestamp': datetime.now().isoformat(),
#                 'sessionId': session_id
#             }, room=session_id)
    
#     # Run in a daemon thread
#     thread = threading.Thread(target=process_query)
#     thread.daemon = True
#     thread.start()


# # [All other socket handlers remain identical - stop_analysis, terminate_session, etc.]

# # ==================== BACKGROUND TASKS (ALL PRESERVED) ====================

# def periodic_cleanup():
#     """Periodic cleanup of old sessions (runs in background)."""
#     if not SESSION_CLEANUP_ENABLED:
#         return
    
#     try:
#         print("🧹 Running periodic session cleanup...")
        
#         sessions_to_delete = []
#         current_time = datetime.now()
        
#         for session_id in list(analyzers.keys()):
#             if session_id in session_data:
#                 session_info = session_data[session_id]
                
#                 if (is_session_too_old(session_info, SESSION_MAX_AGE_HOURS) or 
#                     is_session_inactive(session_info, SESSION_MAX_INACTIVE_HOURS)):
#                     sessions_to_delete.append(session_id)
        
#         # Clean up old sessions
#         cleaned_count = 0
#         for session_id in sessions_to_delete:
#             try:
#                 deleted_items = cleanup_session_data(session_id, session_data, analyzers)
#                 if deleted_items:
#                     cleaned_count += 1
#                     print(f"🗑️  Auto-cleaned session: {session_id}")
#             except Exception as e:
#                 print(f"⚠️  Failed to auto-clean session {session_id}: {e}")
        
#         if cleaned_count > 0:
#             print(f"🧹 Periodic cleanup completed: {cleaned_count} sessions cleaned")
        
#     except Exception as e:
#         print(f"❌ Periodic cleanup error: {e}")


# def schedule_periodic_cleanup():
#     """Schedule periodic cleanup to run every 30 minutes."""
#     import threading
#     import time
    
#     def cleanup_loop():
#         while True:
#             time.sleep(1800)  # 30 minutes
#             periodic_cleanup()
    
#     cleanup_thread = threading.Thread(target=cleanup_loop)
#     cleanup_thread.daemon = True
#     cleanup_thread.start()
#     print("🕐 Scheduled periodic cleanup every 30 minutes")


# # ==================== MAIN APPLICATION ====================

# if __name__ == '__main__':
#     # Verify environment variables
#     required_vars = ["AZUREAPI", "AZUREVERSION", "AZUREENDPOINT"]
#     missing_vars = [var for var in required_vars if not os.getenv(var)]
    
#     if missing_vars:
#         print(f"❌ Missing environment variables: {missing_vars}")
#         print("Please set the following:")
#         print("- AZUREAPI: Your Azure OpenAI API key")
#         print("- AZUREVERSION: API version (e.g., '2024-02-01')")
#         print("- AZUREENDPOINT: Your Azure OpenAI endpoint")
#         exit(1)
    
#     print("🚀 Starting Enhanced Flask CSV Analysis Chatbot...")
#     print("🤖 NEW FEATURES:")
#     print("   💬 Conversational queries (Hi, how are you?, What can you do?)")
#     print("   📊 Textual analytical queries (What's the highest revenue?)")
#     print("   🔬 Fully analytical queries (Generate forecast, Create report)")
#     print()
#     print("📊 Backend running on http://localhost:5000")
#     print("🔗 Connect your React frontend to this backend")
#     print(f"⚙️  Using {async_mode} async mode")
#     print(f"🧹 Session cleanup: {'Enabled' if SESSION_CLEANUP_ENABLED else 'Disabled'}")
#     print(f"⏰ Max session age: {SESSION_MAX_AGE_HOURS} hours")
#     print(f"💤 Max inactive time: {SESSION_MAX_INACTIVE_HOURS} hours")
    
#     if LANGCHAIN_AVAILABLE:
#         print("✅ LangChain available for enhanced conversation history")
#     else:
#         print("⚠️  LangChain not available - using basic conversation history")
    
#     if EVENTLET_AVAILABLE:
#         print("✅ Using eventlet for optimal WebSocket support")
#     else:
#         print("⚠️  Using threading mode - install eventlet for better performance")
#         print("   pip install eventlet")
    
#     # Start periodic cleanup if enabled
#     if SESSION_CLEANUP_ENABLED:
#         schedule_periodic_cleanup()
    
#     # Run the application
#     if EVENTLET_AVAILABLE:
#         socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
#     else:
#         socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)



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

import logging
import os
import json
import uuid
from datetime import datetime
import threading
import traceback
from pathlib import Path

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
           
        response_data = {
            'success': True,
            'sessionId': new_session_id,
            'message': f'File uploaded and analyzed with Assistants API! Shape: {analyzer.df.shape}',
            'data': {
                'filename': file.filename,
                'shape': analyzer.df.shape,
                'columns': list(analyzer.df.columns),
                'preview': generate_tailwind_table(analyzer.df.head()),
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
        
        response = jsonify(response_data)
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
           
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        logging.exception("Detailed upload error")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    """Generate PDF from HTML content using Gotenberg."""
    html_content = request.data.decode("utf-8")

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

 # SESSION MANAGEMENT ROUTES
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
            enhanced_info = {
                'enhanced_analyzer': True,
                'assistants_enabled': True,  # New
                'thread_id': getattr(analyzer, 'thread_id', None),  # New
                'uploaded_files_count': len(getattr(analyzer, 'current_file_ids', [])),  # New
                'capabilities': analyzer.get_analysis_capabilities(),
                'conversation_context': analyzer.get_conversation_context()
            }
        
        # Add data preview if DataFrame is available
        data_preview = None
        if analyzer.df is not None:
            try:
                data_preview = generate_tailwind_table(analyzer.df.head())
            except Exception as e:
                print(f"Failed to generate data preview: {e}")
                data_preview = "Preview unavailable"
        
        # Create complete session info with preview
        session_info = {
            'success': True,
            'fileInfo': {
                'filename': session_summary.get('filename'),
                'shape': session_summary.get('shape'),
                'columns': session_summary.get('columns'),
                'uploadTime': session_summary.get('uploadTime'),
                'lastActivity': session_summary.get('lastActivity'),
                'sessionId': session_id,
                'preview': data_preview,
                'data': analyzer.df.head(100).to_dict('records') if analyzer.df is not None else []
            },
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
            
            response_data = {
                'success': True,
                'sessionId': session_id,
                'message': f'File updated successfully! Shape: {analyzer.df.shape}',
                'data': {
                    'filename': file.filename,
                    'shape': analyzer.df.shape,
                    'columns': list(analyzer.df.columns),
                    'preview': generate_tailwind_table(analyzer.df.head())
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
        stats['enhanced_analyzers_count'] = enhanced_count
        stats['assistants_enabled_count'] = assistants_count
        
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


# Add this route after the existing routes and before the socket handlers

# @app.route('/reports/<filename>', methods=['GET'])
# def serve_html_report(filename):
#     """Serve HTML reports from backend/output directory"""
#     try:
#         # Security: Ensure filename is safe (no directory traversal)
#         safe_filename = secure_filename(filename)
#         if not safe_filename.endswith('.html'):
#             return jsonify({'error': 'Only HTML files are allowed'}), 400
        
#         # Construct path to report file
#         reports_dir = os.path.join(os.getcwd(), 'backend', 'output')
#         report_path = os.path.join(reports_dir, safe_filename)
        
#         # Check if file exists
#         if not os.path.exists(report_path):
#             return jsonify({'error': 'Report not found'}), 404
        
#         # Security: Ensure the file is within the reports directory
#         if not os.path.abspath(report_path).startswith(os.path.abspath(reports_dir)):
#             return jsonify({'error': 'Invalid file path'}), 400
        
#         # Serve the HTML file
#         return send_file(
#             report_path,
#             mimetype='text/html',
#             as_attachment=False,
#             download_name=safe_filename
#         )
        
#     except Exception as e:
#         print(f"❌ Error serving report {filename}: {e}")
#         return jsonify({'error': f'Failed to serve report: {str(e)}'}), 500


# @app.route('/reports', methods=['GET'])
# def list_html_reports():
#     """List all available HTML reports"""
#     try:
#         reports_dir = os.path.join(os.getcwd(), 'backend', 'output')
        
#         if not os.path.exists(reports_dir):
#             return jsonify({
#                 'success': True,
#                 'reports': [],
#                 'message': 'No reports directory found'
#             })
        
#         reports = []
#         for filename in os.listdir(reports_dir):
#             if filename.endswith('.html'):
#                 try:
#                     file_path = os.path.join(reports_dir, filename)
#                     stat_info = os.stat(file_path)
                    
#                     reports.append({
#                         'filename': filename,
#                         'url': f'/reports/{filename}',
#                         'size': stat_info.st_size,
#                         'created': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
#                         'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
#                     })
#                 except Exception as file_error:
#                     print(f"⚠️ Error reading file info for {filename}: {file_error}")
        
#         # Sort by creation time (newest first)
#         reports.sort(key=lambda x: x['created'], reverse=True)
        
#         response_data = {
#             'success': True,
#             'reports': reports,
#             'total': len(reports),
#             'directory': reports_dir
#         }
        
#         response = jsonify(response_data)
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
        
#     except Exception as e:
#         print(f"❌ Error listing reports: {e}")
#         return jsonify({
#             'success': False,
#             'error': f'Failed to list reports: {str(e)}'
#         }), 500
    
# @app.route('/reports/cleanup', methods=['POST', 'OPTIONS'])
# def cleanup_old_reports():
#     """Clean up old HTML reports, keeping only the latest N files"""
#     if request.method == 'OPTIONS':
#         response = jsonify({'status': 'ok'})
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Methods', 'POST')
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
    
#     try:
#         # Get cleanup parameters from request
#         data = request.get_json() or {}
#         keep_last_n = data.get('keepLastN', 10)  # Default: keep last 10 reports
        
#         reports_dir = os.path.join(os.getcwd(), 'backend', 'output')
        
#         if not os.path.exists(reports_dir):
#             return jsonify({
#                 'success': True,
#                 'deleted_count': 0,
#                 'message': 'No reports directory found'
#             })
        
#         # Get all HTML files with their creation times
#         reports = []
#         for filename in os.listdir(reports_dir):
#             if filename.endswith('.html'):
#                 try:
#                     file_path = os.path.join(reports_dir, filename)
#                     stat_info = os.stat(file_path)
#                     reports.append({
#                         'filename': filename,
#                         'path': file_path,
#                         'created': stat_info.st_ctime
#                     })
#                 except Exception as file_error:
#                     print(f"⚠️ Error reading file info for {filename}: {file_error}")
        
#         # Sort by creation time (newest first)
#         reports.sort(key=lambda x: x['created'], reverse=True)
        
#         # Delete old reports
#         deleted_count = 0
#         deleted_files = []
        
#         if len(reports) > keep_last_n:
#             reports_to_delete = reports[keep_last_n:]
            
#             for report in reports_to_delete:
#                 try:
#                     os.remove(report['path'])
#                     deleted_count += 1
#                     deleted_files.append(report['filename'])
#                     print(f"🗑️ Deleted old report: {report['filename']}")
#                 except Exception as delete_error:
#                     print(f"⚠️ Could not delete {report['filename']}: {delete_error}")
        
#         response_data = {
#             'success': True,
#             'deleted_count': deleted_count,
#             'deleted_files': deleted_files,
#             'kept_count': min(len(reports), keep_last_n),
#             'total_reports_before': len(reports),
#             'total_reports_after': len(reports) - deleted_count,
#             'cleanup_params': {
#                 'keepLastN': keep_last_n
#             },
#             'timestamp': datetime.now().isoformat()
#         }
        
#         response = jsonify(response_data)
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
        
#     except Exception as e:
#         print(f"❌ Reports cleanup error: {e}")
#         return jsonify({
#             'success': False,
#             'error': f'Cleanup failed: {str(e)}'
#         }), 500


# @app.route('/reports/<filename>', methods=['DELETE', 'OPTIONS'])
# def delete_specific_report(filename):
#     """Delete a specific HTML report"""
#     if request.method == 'OPTIONS':
#         response = jsonify({'status': 'ok'})
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Methods', 'DELETE')
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
    
#     try:
#         # Security: Ensure filename is safe
#         safe_filename = secure_filename(filename)
#         if not safe_filename.endswith('.html'):
#             return jsonify({'error': 'Only HTML files can be deleted'}), 400
        
#         # Construct path to report file
#         reports_dir = os.path.join(os.getcwd(), 'backend', 'output')
#         report_path = os.path.join(reports_dir, safe_filename)
        
#         # Check if file exists
#         if not os.path.exists(report_path):
#             return jsonify({'error': 'Report not found'}), 404
        
#         # Security: Ensure the file is within the reports directory
#         if not os.path.abspath(report_path).startswith(os.path.abspath(reports_dir)):
#             return jsonify({'error': 'Invalid file path'}), 400
        
#         # Delete the file
#         os.remove(report_path)
#         print(f"🗑️ Deleted report: {safe_filename}")
        
#         response_data = {
#             'success': True,
#             'filename': safe_filename,
#             'message': f'Report {safe_filename} deleted successfully',
#             'timestamp': datetime.now().isoformat()
#         }
        
#         response = jsonify(response_data)
#         origin = request.headers.get('Origin', '*')
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         return response
        
#     except Exception as e:
#         print(f"❌ Error deleting report {filename}: {e}")
#         return jsonify({
#             'success': False,
#             'error': f'Failed to delete report: {str(e)}'
#         }), 500    
# ==================== SOCKET HANDLERS (ALL PRESERVED) ====================

# ==================== SOCKET HANDLERS ====================

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
            except Exception as e:
                print(f"⚠️ Error cleaning up assistants resources: {e}")
        
        # Original cleanup
        if hasattr(analyzer, 'cleanup'):
            analyzer.cleanup()
        
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