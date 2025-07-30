# app_refactored.py
"""
Refactored and modularized Flask CSV Analysis application
"""

# Fix for eventlet - MUST be the first import
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
import uuid
from flask import Flask, render_template, session
from flask_socketio import SocketIO
from flask_cors import CORS
from dotenv import load_dotenv

# Import modularized components
from config import Config, get_config
from streaming_analyzer import StreamingAnalyzer
from flask_routes import init_routes
from socketio_handlers import init_socketio_handlers
from auth import auth_blueprint, init_db

# Load environment variables
load_dotenv()


def create_app(config_name="development"):
    """Create and configure the Flask application"""
    
    # Get configuration
    config_class = get_config(config_name)
    print(config_name)
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Create necessary directories
    config_class.create_directories()
    
    # Validate Azure configuration
    if not config_class.validate_azure_config():
        raise ValueError("Invalid Azure OpenAI configuration")
    
    # Initialize database and auth
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        print("   Auth features may not work properly")

    # Setup CORS
    CORS(app, origins=config_class.ALLOWED_ORIGINS, supports_credentials=True)

    # Initialize SocketIO
    async_mode = 'eventlet' if EVENTLET_AVAILABLE else 'threading'
    socketio = SocketIO(
        app, 
        cors_allowed_origins=config_class.ALLOWED_ORIGINS,
        async_mode=async_mode,
        transports=config_class.SOCKETIO_TRANSPORTS,
        logger=getattr(config_class, 'SOCKETIO_LOGGER', False),
        engineio_logger=getattr(config_class, 'SOCKETIO_ENGINEIO_LOGGER', False),
        ping_timeout=config_class.SOCKETIO_PING_TIMEOUT,
        ping_interval=config_class.SOCKETIO_PING_INTERVAL
    )

    # Global storage for analyzer instances per session
    analyzers = {}
    session_data = {}

    # Custom StreamingAnalyzer that accepts socketio instance
    class AppStreamingAnalyzer(StreamingAnalyzer):
        def __init__(self, session_id):
            super().__init__(session_id, socketio)

    # Initialize routes and socketio handlers
    init_routes(app, analyzers, session_data, AppStreamingAnalyzer)
    init_socketio_handlers(socketio, analyzers, session_data)

    @app.route('/')
    def index():
        """Main chat interface."""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        return render_template('index.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {"error": "Endpoint not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error"}, 500

    return app, socketio


def print_startup_info(config_class, socketio):
    """Print application startup information"""
    print("\n" + "="*60)
    print("🚀 Flask CSV Analysis Chatbot Started")
    print("="*60)
    print(f"📊 Backend running on: http://localhost:5000")
    print(f"🔗 Frontend origins: {', '.join(config_class.ALLOWED_ORIGINS[:2])}...")
    print(f"⚙️  SocketIO mode: {socketio.async_mode}")
    print(f"🗂️  Upload directory: {config_class.UPLOADS_DIR}")
    print(f"💾 Output directory: {config_class.OUTPUTS_DIR}")
    
    # Check for optional dependencies
    try:
        from langchain.memory import ConversationBufferWindowMemory
        print("✅ LangChain: Available for enhanced conversation history")
    except ImportError:
        print("⚠️  LangChain: Not available - using basic conversation history")
    
    try:
        import xgboost
        print("✅ XGBoost: Available for advanced forecasting")
    except ImportError:
        print("⚠️  XGBoost: Not available - limited forecasting capabilities")
    
    try:
        import statsmodels
        print("✅ Statsmodels: Available for time series analysis")
    except ImportError:
        print("⚠️  Statsmodels: Not available - limited time series features")
    
    if EVENTLET_AVAILABLE:
        print("✅ Eventlet: Optimal WebSocket support enabled")
    else:
        print("⚠️  Eventlet: Using threading mode")
        print("   💡 Install eventlet for better performance: pip install eventlet")
    
    print("="*60)
    print("🎯 Ready to analyze CSV files!")
    print("="*60 + "\n")


def main():
    """Main application entry point"""
    
    try:
        # Create app and socketio
        app, socketio = create_app()
        
        # Get config for startup info
        config_class = get_config()
        
        # Print startup information
        print_startup_info(config_class, socketio)
        
        # Run the application
        if EVENTLET_AVAILABLE:
            socketio.run(
                app, 
                host='0.0.0.0', 
                port=5000, 
                debug=config_class.DEBUG, 
                use_reloader=False
            )
        else:
            socketio.run(
                app, 
                host='0.0.0.0', 
                port=5000, 
                debug=config_class.DEBUG, 
                use_reloader=False
            )
            
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Please check your environment variables:")
        print("   - AZUREAPI: Your Azure OpenAI API key")
        print("   - AZUREVERSION: API version (e.g., '2024-02-01')")
        print("   - AZUREENDPOINT: Your Azure OpenAI endpoint")
        exit(1)
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        exit(1)


if __name__ == '__main__':
    main()