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
from flask_socketio import SocketIO, emit, disconnect, join_room
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

# Suppress warnings
warnings.filterwarnings('ignore')

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Comprehensive CORS configuration for multiple frontend sources
allowed_origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "https://preview--data-scope-ai-lens.lovable.app",
    "https://*.lovable.app",
    "http://localhost:3001",
    "http://127.0.0.1:3001"
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

class StreamingAnalyzer(QuadraticCSVAnalyzer):
    """Extended analyzer with streaming capabilities for Flask integration."""
    
    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id
        self.streaming_outputs = []
    
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
            print(f"🤖 Analyzing query: {user_query}")
            self.emit_stream('status', f"🤖 Analyzing query: {user_query}")
            
            # Reset generated images for this query
            self.generated_images = []
            self.streaming_outputs = []
            
            # Check if this is a report request
            is_report_request = self._is_report_request(user_query)
            
            # Extract data request type
            data_request = self._extract_data_request(user_query)
            
            # Detect if this is a forecasting query
            forecasting_keywords = ['forecast', 'predict', 'future', 'next', 'ahead', 'months', 'years', 'projection']
            is_forecasting = any(keyword in user_query.lower() for keyword in forecasting_keywords)
    
            if is_report_request:
                # Generate comprehensive report
                self.emit_stream('status', "📋 Generating comprehensive report...")
                return self._generate_comprehensive_report_streaming(user_query, is_forecasting)
            else:
                # Focus on DataFrame results
                self.emit_stream('status', "📊 Focusing on DataFrame results...")
                return self._generate_dataframe_analysis_streaming(user_query, data_request, is_forecasting)
                
        except Exception as e:
            error_msg = f"Error analyzing query: {str(e)}"
            print(error_msg)
            self.emit_stream('error', error_msg)
            return {
                "error": error_msg,
                "traceback": traceback.format_exc(),
                "type": "error"
            }
    
    def _generate_dataframe_analysis_streaming(self, user_query: str, data_request: Dict, is_forecasting: bool) -> Dict[str, Any]:
        """Generate analysis focused on returning actionable DataFrame results - EXACT COPY from test2.py"""
       
        # Enhanced prompt for DataFrame-focused analysis - EXACT COPY from test2.py
        base_requirements = f"""
Generate Python code to: {user_query} and always write code inside ```python

PRIMARY GOAL: Return actionable DataFrame results that can enhance the original dataset.

CRITICAL REQUIREMENTS:
- Use 'df' variable which contains the loaded DataFrame
- NEVER use pd.read_csv() or file paths
- Focus on creating NEW DATA that adds value to the original dataset
- Return results as DataFrames with meaningful column names
- Show before/after data previews
- If generating plots, never use plt.show() always savefig

DATA OUTPUT FOCUS:
- Create calculated columns, derived metrics, or classifications
- Generate forecasted data with future dates if requested
- Add trend indicators, performance scores, or category rankings
- Provide data that can be merged back to the original file

REQUEST TYPE: {data_request['type']}
"""
 
        if is_forecasting:
            enhanced_prompt = base_requirements + f"""
FORECASTING-SPECIFIC REQUIREMENTS:
- Create a separate DataFrame with future predictions
- Include future dates beyond the last date in dataset
- Provide confidence intervals or prediction ranges
- Return forecasted_data_df with columns: [Date, Predicted_Value, Confidence_Lower, Confidence_Upper]
- Show both historical trend analysis and future predictions

FORECASTING OUTPUT:
- Original data with trend indicators added
- Separate forecast DataFrame for future periods
- Combined visualization showing historical + predicted
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
        
        # Generate and execute the analysis code - EXACT COPY from test2.py
        response = self.openai_client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user",   "content": enhanced_prompt}
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
                        'preview': generate_tailwind_table(var_value.head()),
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
                
                captured_images.append(str(image_path))
                self.generated_images.append(image_filename)
                
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
    
    def _generate_comprehensive_report_streaming(self, user_query: str, is_forecasting: bool) -> Dict[str, Any]:
        """Generate comprehensive report when specifically requested - EXACT COPY from test2.py"""
        print("\n📋 Generating comprehensive strategic report...")
        self.emit_stream('status', "📋 Generating comprehensive strategic report...")
        
        try:
            # First run the analysis to get data - EXACT COPY from test2.py
            data_request = self._extract_data_request(user_query)
            analysis_result = self._generate_dataframe_analysis_streaming(user_query, data_request, is_forecasting)
            
            if not analysis_result.get("success"):
                return {
                    "error": "Cannot generate report - analysis failed",
                    "type": "report_error"
                }
            
            self.emit_stream('status', "📝 Generating strategic report content...")
            
            # Generate the report - EXACT COPY from test2.py
            market_topic = self._extract_market_topic(user_query)
            target_variable = self._extract_target_variable(user_query)
            forecast_periods = self._extract_forecast_periods(user_query) if is_forecasting else 6
            
            report = self.generate_forecast_report(
                forecast_results=analysis_result,
                client_name="Executive Leadership Team",
                market_topic=market_topic,
                forecast_periods=forecast_periods,
                target_variable=target_variable
            )
            
            # Stream the report to frontend
            self.emit_stream('report', report)
            
            analysis_result.update({
                "type": "comprehensive_report",
                "comprehensive_report": report,
                "report_generated": True,
                "market_topic": market_topic,
                "target_variable": target_variable,
                "forecast_periods": forecast_periods
            })
            
            print("✅ Comprehensive strategic report generated successfully!")
            self.emit_stream('success', "✅ Comprehensive strategic report generated successfully!")
            
        except Exception as report_error:
            print(f"⚠️ Report generation failed: {str(report_error)}")
            self.emit_stream('error', f"Report generation failed: {str(report_error)}")
            analysis_result.update({
                "report_error": str(report_error),
                "report_generated": False,
                "type": "report_error"
            })
        
        return analysis_result

def generate_tailwind_table(df):
    html = '<table class="w-full bg-gray-900 text-gray-100 rounded-2xl overflow-hidden shadow-lg">'
    html += '<thead><tr>'
    for col in df.columns:
        html += f'<th class="px-6 py-4 text-left font-semibold text-white border-b border-gray-700">{col}</th>'
    html += '</tr></thead><tbody>'
    for _, row in df.iterrows():
        html += '<tr class="hover:bg-gray-800">'
        for val in row:
            html += f'<td class="px-6 py-4 border-b border-gray-800">{val}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html

@app.route('/')
def index():
    """Main chat interface."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')

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
        response = jsonify({
            'connected': True,
            'data': session_data[session_id]
        })
    else:
        response = jsonify({'connected': False})
    
    origin = request.headers.get('Origin', '*')
    response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

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
    
    if EVENTLET_AVAILABLE:
        print("✅ Using eventlet for optimal WebSocket support")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    else:
        print("⚠️  Using threading mode - install eventlet for better performance")
        print("   pip install eventlet")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)