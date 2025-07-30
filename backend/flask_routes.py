# flask_routes.py
"""
Flask routes for the CSV Analysis application
"""

import os
import uuid
from datetime import datetime
from flask import request, jsonify, session, send_file, Response
from werkzeug.utils import secure_filename

from table_generator import generate_tailwind_table


def init_routes(app, analyzers, session_data, StreamingAnalyzer):
    """Initialize all Flask routes"""
    
    @app.route('/upload', methods=['POST', 'OPTIONS'])
    def upload_file():
        """Handle CSV file upload with CORS support."""
        if request.method == 'OPTIONS':
            # Handle preflight request
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
            # Generate session ID if not exists
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Initialize analyzer for this session
            session_id = session['session_id']
            analyzer = StreamingAnalyzer(session_id)
            
            # Load the CSV
            if analyzer.load_csv(filepath):
                analyzers[session_id] = analyzer
                session_data[session_id] = {
                    'filename': file.filename,
                    'filepath': filepath,
                    'upload_time': datetime.now().isoformat(),
                    'shape': analyzer.df.shape,
                    'columns': list(analyzer.df.columns)
                }
                
                response = jsonify({
                    'success': True,
                    'message': f'File uploaded successfully! Shape: {analyzer.df.shape}',
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
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500

    @app.route('/session-info', methods=['GET', 'OPTIONS'])
    def session_info():
        """Get current session information with CORS support."""
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'ok'})
            origin = request.headers.get('Origin', '*')
            response.headers.add('Access-Control-Allow-Origin', origin)
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response
        
        session_id = session.get('session_id')
        if session_id and session_id in session_data:
            # Get conversation history summary if analyzer exists
            history_summary = {}
            if session_id in analyzers:
                history_summary = analyzers[session_id].conversation_history.get_summary()
            
            response = jsonify({
                'connected': True,
                'data': session_data[session_id],
                'history_summary': history_summary
            })
        else:
            response = jsonify({'connected': False})
        
        origin = request.headers.get('Origin', '*')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

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

    @app.route('/langchain-status', methods=['GET', 'OPTIONS'])
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

    @app.route('/export-langchain-conversation', methods=['GET', 'OPTIONS'])
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