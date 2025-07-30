# socketio_handlers.py
"""
SocketIO event handlers for real-time communication
"""

import uuid
import threading
from datetime import datetime
from flask import session
from flask_socketio import emit, join_room


def init_socketio_handlers(socketio, analyzers, session_data):
    """Initialize all SocketIO event handlers"""
    
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
                analyzer.socketio = socketio  # Set socketio instance for streaming
                
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