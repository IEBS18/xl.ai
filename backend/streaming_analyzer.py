"""
Enhanced Streaming Analyzer with NLP integration and AI conversational features
"""
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
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# Import your existing analyzer
from legacy_codes.test2 import QuadraticCSVAnalyzer

# Import NLP processor
try:
    from nlp_query_processor import EnhancedNLPQueryProcessor, ProcessedQuery
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

# Import conversation manager
from conversation_manager import ConversationHistory, ConversationalManager

# Import utilities
from session_utils import (
    generate_tailwind_table,
    stop_signals,
    StopAnalysisException
)

class StreamingAnalyzer(QuadraticCSVAnalyzer):
    """Extended analyzer with streaming capabilities, NLP integration, and AI conversation features."""
    
    def __init__(self, session_id, socketio=None):
        super().__init__()
        self.session_id = session_id
        self.streaming_outputs = []
        self.conversation_history = ConversationHistory(session_id, self.output_dir)
        self.socketio = socketio
        self.is_analyzing = False
        
        # Initialize NLP components
        self.nlp_processor = None
        self.query_history = []
        
        # Initialize conversational manager
        self.conversational_manager = ConversationalManager(
            self.openai_client, 
            self.df
        )
    
    def initialize_nlp_processor(self):
        """Initialize NLP processor after CSV is loaded"""
        if not NLP_AVAILABLE:
            print("⚠️ NLP components not available")
            return
            
        try:
            if self.df is not None:
                self.nlp_processor = EnhancedNLPQueryProcessor(self.df)
                self.emit_stream('status', "🧠 NLP Query Processor initialized successfully")
                print("✅ NLP Query Processor initialized successfully")
                
                # Update conversational manager with new dataframe
                self.conversational_manager.df = self.df
            else:
                print("⚠️ Cannot initialize NLP processor - no DataFrame loaded")
        except Exception as e:
            print(f"⚠️ NLP Processor initialization failed: {e}")
            self.emit_stream('error', f"NLP initialization failed: {str(e)}")
            self.nlp_processor = None

    def emit_stream(self, message_type, data):
        """Emit streaming data to the frontend."""
        try:
            if self.socketio:
                self.socketio.emit('stream_data', {
                    'type': message_type,
                    'data': data,
                    'timestamp': datetime.now().isoformat(),
                    'sessionId': self.session_id  # CRITICAL: Always include sessionId
                }, room=self.session_id)
                
                # Check for stop signal
                if self.session_id in stop_signals and stop_signals[self.session_id]:
                    print(f"🛑 Analysis stopped by user for session: {self.session_id}")
                    self.socketio.emit('stream_data', {
                        'type': 'stopped',
                        'data': 'Analysis stopped by user',
                        'timestamp': datetime.now().isoformat(),
                        'sessionId': self.session_id
                    }, room=self.session_id)
                    raise StopAnalysisException("Analysis stopped by user")
                
                # Small delay for smooth streaming
                try:
                    # Try eventlet sleep first
                    import eventlet
                    eventlet.sleep(0.05)
                except ImportError:
                    # Fallback to regular sleep
                    time.sleep(0.05)
        except StopAnalysisException:
            raise  # Re-raise stop exception
        except Exception as e:
            print(f"Error emitting stream: {e}")
    
    def check_stop_signal(self):
        """Check if user has requested to stop analysis"""
        if self.session_id in stop_signals and stop_signals[self.session_id]:
            print(f"🛑 Stop signal detected for session: {self.session_id}")
            raise StopAnalysisException("Analysis stopped by user")
    
    def analyze_query_streaming(self, user_query: str):
        """Enhanced analyze_query with AI-powered conversational handling and NLP preprocessing"""
        if self.df is None:
            # If no data loaded and it's a casual conversation, provide conversational response
            if self.conversational_manager.is_casual_conversation(user_query):
                response = self.generate_conversational_response(user_query)
                # Store in conversation history
                if hasattr(self, 'conversation_history'):
                    self.conversation_history.add_conversation(user_query, response)
                return response
            else:
                # If no data but user seems to want analysis, provide AI guidance
                response = self.conversational_manager.handle_no_data_query(user_query)
                # Store in conversation history
                if hasattr(self, 'conversation_history'):
                    self.conversation_history.add_conversation(user_query, response)
                self.emit_stream('guidance', response['response'])
                return response

        # Check if this is casual conversation rather than data analysis
        if self.conversational_manager.is_casual_conversation(user_query):
            response = self.generate_conversational_response(user_query)
            # Store in conversation history
            if hasattr(self, 'conversation_history'):
                self.conversation_history.add_conversation(user_query, response)
            return response

        # Initialize NLP processor if not done yet
        if self.nlp_processor is None and NLP_AVAILABLE:
            self.initialize_nlp_processor()

        try:
            # Set analyzing flag
            self.is_analyzing = True
            
            # Clear any existing stop signal
            if self.session_id in stop_signals:
                stop_signals[self.session_id] = False
            
            # announce incoming query
            self.emit_stream('status', f"Analyzing query: {user_query}")
            self.check_stop_signal()

            # reset per‑query state
            self.generated_images = []
            self.streaming_outputs = []

            # Use NLP processing if available
            if self.nlp_processor is not None:
                result = self.analyze_query_with_nlp(user_query)
            else:
                # Fallback to original method
                result = self.analyze_query_original(user_query)

            # record in history
            self.conversation_history.add_conversation(user_query, result)
            
            # Clear analyzing flag
            self.is_analyzing = False
            
            return result

        except StopAnalysisException:
            # Handle stop signal gracefully
            self.is_analyzing = False
            stop_result = {
                "error": "Analysis stopped by user",
                "type": "stopped",
                "success": False,
                "stopped_by_user": True,
                "sessionId": self.session_id
            }
            self.conversation_history.add_conversation(user_query, stop_result)
            return stop_result
            
        except Exception as e:
            # capture full traceback
            self.is_analyzing = False
            full_trace = traceback.format_exc()
            error_msg = f"Error analyzing query:\n{full_trace}"
            print(error_msg)
            self.emit_stream('error', error_msg)

            # record failure in history
            self.conversation_history.add_conversation(user_query, {
                "error": str(e),
                "traceback": full_trace,
                "type": "error",
                "success": False,
                "sessionId": self.session_id
            })

            return {
                "error": str(e),
                "traceback": full_trace,
                "type": "error",
                "success": False,
                "sessionId": self.session_id
            }
    
    def analyze_query_with_nlp(self, user_query: str):
        """NLP-enhanced query analysis"""
        try:
            # Process query with NLP
            self.emit_stream('status', "🧠 Processing query with NLP...")
            processed_query = self.nlp_processor.process_query(user_query)
            
            # Store in query history
            self.query_history.append({
                'timestamp': datetime.now().isoformat(),
                'original_query': user_query,
                'intent': processed_query.intent.primary_intent,
                'confidence': processed_query.intent.confidence,
                'complexity': processed_query.intent.complexity_level,
                'urgency': processed_query.urgency_level
            })
            
            # Emit NLP insights to frontend
            self.emit_nlp_insights(processed_query)
            
            # Determine analysis path based on intent
            return self.execute_intent_based_analysis(processed_query)
            
        except Exception as e:
            print(f"⚠️ NLP analysis failed, falling back to original: {e}")
            return self.analyze_query_original(user_query)
    
    def execute_intent_based_analysis(self, processed_query: ProcessedQuery):
        """Execute analysis based on detected intent while maintaining original flow"""
        intent = processed_query.intent.primary_intent
        
        self.emit_stream('status', f"🎯 Executing {intent} analysis...")
        
        try:
            # Generate enhanced prompt
            enhanced_prompt = self.nlp_processor.generate_enhanced_prompt(processed_query)
            
            # Add column suggestions if found
            if processed_query.column_references:
                enhanced_prompt += f"\n\nSUGGESTED RELEVANT COLUMNS: {', '.join(processed_query.column_references)}"
            
            # Add temporal context if available
            if processed_query.temporal_expressions['has_temporal']:
                enhanced_prompt += f"\n\nTEMPORAL CONTEXT DETECTED: Use time-based analysis"
                if processed_query.temporal_expressions.get('forecast_periods'):
                    fp = processed_query.temporal_expressions['forecast_periods']
                    enhanced_prompt += f"\nForecast requirement: {fp['quantity']} {fp['unit']}"
            
            # Add urgency context
            if processed_query.urgency_level == 'high':
                enhanced_prompt += f"\n\nHIGH PRIORITY REQUEST: Focus on key insights and efficiency"
            
            # Decide analysis path based on intent - keeping original logic
            is_report_request = intent == 'reporting' or self._is_report_request(processed_query.original_query)
            
            # Extract data request info
            data_request = {
                'type': intent,
                'enhanced': True,
                'confidence': processed_query.intent.confidence,
                'complexity': processed_query.intent.complexity_level
            }
            
            # Check if forecasting - keeping original logic
            is_forecasting = intent == 'forecasting' or any(
                kw in processed_query.original_query.lower()
                for kw in ['forecast','predict','future','next','ahead','months','years','projection']
            )
            
            if is_report_request:
                self.emit_stream('status', "📋 Generating comprehensive report with NLP insights...")
                return self._generate_comprehensive_report_streaming(
                    processed_query.original_query,
                    is_forecasting
                )
            else:
                # Use enhanced prompt with existing DataFrame analysis method
                return self._generate_dataframe_analysis_streaming_with_fallback(
                    processed_query.original_query,
                    enhanced_prompt,
                    data_request,
                    is_forecasting
                )
                
        except Exception as e:
            print(f"⚠️ Intent-based analysis failed for {intent}: {e}")
            return self.analyze_query_original(processed_query.original_query)
    
    def analyze_query_original(self, user_query: str):
        """Fallback to original analysis method - KEEPING EXACT ORIGINAL LOGIC"""
        self.emit_stream('status', f"🤖 Analyzing query: {user_query}")
        
        self.generated_images = []
        self.streaming_outputs = []
        
        is_report_request = self._is_report_request(user_query)
        data_request = self._extract_data_request(user_query)
        is_forecasting = any(
            kw in user_query.lower()
            for kw in ['forecast','predict','future','next','ahead','months','years','projection']
        )

        if is_report_request:
            self.emit_stream('status', "📋 Generating comprehensive report…")
            result = self._generate_comprehensive_report_streaming(
                user_query,
                is_forecasting
            )
        else:
            self.emit_stream('status', "📊 Focusing on DataFrame results…")
            result = self._generate_dataframe_analysis_streaming_with_fallback(
                user_query,
                user_query,  # Use original query as prompt
                data_request,
                is_forecasting
            )

        return result
    
    def generate_conversational_response(self, user_query: str) -> Dict[str, Any]:
        """Generate AI-powered conversational response"""
        self.emit_stream('status', "💬 Generating conversational response...")
        
        # Generate AI response using conversational manager
        ai_response = self.conversational_manager.generate_ai_conversational_response(
            user_query, 
            self.conversation_history
        )
        
        # Emit the conversational response
        self.emit_stream('conversation', ai_response)
        
        return {
            "query": user_query,
            "type": "conversational_response",
            "success": True,
            "response": ai_response,
            "sessionId": self.session_id,
            "is_conversation": True,
            "generated_images": [],
            "dataframes": {},
            "data_update_available": False
        }
    
    def emit_nlp_insights(self, processed_query: ProcessedQuery):
        """Emit NLP insights to frontend"""
        try:
            insights = {
                'intent': {
                    'primary': processed_query.intent.primary_intent,
                    'confidence': round(processed_query.intent.confidence, 2),
                    'complexity': processed_query.intent.complexity_level,
                    'secondary': processed_query.intent.secondary_intents
                },
                'entities': {
                    'columns_found': processed_query.column_references,
                    'temporal_info': processed_query.temporal_expressions['has_temporal'],
                    'operations': processed_query.intent.data_operations,
                    'named_entities': processed_query.named_entities
                },
                'requirements': {
                    'needs_visualization': processed_query.intent.requires_visualization,
                    'urgency': processed_query.urgency_level,
                    'sentiment': processed_query.sentiment
                },
                'understanding': {
                    'cleaned_query': processed_query.cleaned_query,
                    'key_tokens': processed_query.tokens[:10],
                    'forecast_periods': processed_query.temporal_expressions.get('forecast_periods')
                }
            }
            
            self.emit_stream('nlp_insights', insights)
            
        except Exception as e:
            print(f"⚠️ Failed to emit NLP insights: {e}")
    
    def get_nlp_statistics(self) -> Dict[str, Any]:
        """Get NLP processing statistics"""
        if not self.query_history:
            return {
                'total_queries': 0,
                'nlp_enabled': self.nlp_processor is not None
            }
        
        from collections import Counter
        
        intents = [q['intent'] for q in self.query_history]
        complexities = [q['complexity'] for q in self.query_history]
        urgencies = [q['urgency'] for q in self.query_history]
        
        avg_confidence = np.mean([q['confidence'] for q in self.query_history])
        
        return {
            'total_queries': len(self.query_history),
            'nlp_enabled': self.nlp_processor is not None,
            'intent_distribution': dict(Counter(intents)),
            'complexity_distribution': dict(Counter(complexities)),
            'urgency_distribution': dict(Counter(urgencies)),
            'average_confidence': round(avg_confidence, 2),
            'most_common_intent': Counter(intents).most_common(1)[0] if intents else None,
            'recent_queries': self.query_history[-5:] if self.query_history else []
        }
    
    def _streaming_print(self, *args, **kwargs):
        """Custom print function that streams output to frontend."""
        output_text = ' '.join(str(arg) for arg in args)
        self.streaming_outputs.append(output_text)
        self.emit_stream('output', output_text)
        print(*args, **kwargs)  # Also print to console
    
    def _generate_dataframe_analysis_streaming_with_fallback(self, user_query: str, enhanced_prompt: str, data_request: Dict, is_forecasting: bool) -> Dict[str, Any]:
        """Enhanced version with automatic fallback on failure and stop checking"""
        
        # Check for stop signal before major operations
        self.check_stop_signal()
        
        # First, try the enhanced generation logic
        original_result = self._generate_dataframe_analysis_streaming(user_query, enhanced_prompt, data_request, is_forecasting)
        
        # If original execution was successful, return it
        if original_result.get("success"):
            return original_result
        
        # Check for stop signal before fallback
        self.check_stop_signal()
        
        # If original execution failed, trigger fallback
        self.emit_stream('warning', "Initial code generation failed. Attempting regeneration with error context...")
        
        failed_code = original_result.get("generated_code", "")
        error_message = original_result.get("execution_result", {}).get("error", "Unknown error")
        
        # Call the fallback function
        fallback_result = self._regenerate_code_with_fallback(
            user_query=user_query,
            data_request=data_request,
            is_forecasting=is_forecasting,
            failed_code=failed_code,
            error_message=error_message,
            max_retries=3
        )
        
        return fallback_result
    
    def _generate_dataframe_analysis_streaming(self, user_query: str, enhanced_prompt: str, data_request: Dict, is_forecasting: bool) -> Dict[str, Any]:
        """Generate analysis focused on returning actionable DataFrame results with stop checking"""
        
        # Check for stop signal before major operations
        self.check_stop_signal()
        
        # Use the enhanced prompt if provided, otherwise create base requirements
        if enhanced_prompt == user_query:  # Original query used as fallback
            base_requirements = f"""
Generate Python code to: {user_query}
 
PRIMARY GOAL: Return actionable DataFrame results that can enhance the original dataset.
 
CRITICAL REQUIREMENTS:
- Use 'df' variable which contains the loaded DataFrame
- NEVER use pd.read_csv() or file paths
- Focus on creating NEW DATA that adds value to the original dataset
- Return results as DataFrames with meaningful column names
- Show before/after data previews
- Always give charts using matplotlib for visualization using Bar-Charts, Line Graphs, Pie Chart. 
- Use Line charts for forecastings and Trend analysis.
- Use PieChart for Revenue per Product or Category or SKU 
- Use Bar Chart for other types of viualisation
 
DATA OUTPUT FOCUS:
- Create calculated columns, derived metrics, or classifications
- Generate forecasted data with future dates if requested
- Add trend indicators, performance scores, or category rankings
- Provide data that can be merged back to the original file
- Provide the charts for the visualisations for tasks such as trend, revenue, forecast, predictions, analyzation, best products, performance.
 
RESULT STRUCTURE:
1. Examine original data structure
2. Perform calculations/analysis
3. Create enhanced DataFrame with new columns
4. Show preview of original vs enhanced data
5. Save results that can update the original file
6. Return the chart
 
REQUEST TYPE: {data_request['type']}
"""
        else:
            base_requirements = enhanced_prompt
        
        # Check for stop signal before generating code
        self.check_stop_signal()
        
        self.emit_stream('status', "Generating analysis code...")
        
        # Get conversation context for AI
        context = self.conversation_history.get_context_for_ai()
        
        # Generate and execute the analysis code - Enhanced with context
        prompt_with_context = base_requirements + context
        
        # Check for stop signal before API call
        self.check_stop_signal()
        
        response = self.openai_client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user",   "content": prompt_with_context}
            ],
        )
        
        generated_code = response.choices[0].message.content
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0].strip()
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0].strip()
        
        print(" Generated code:")
        print(generated_code)
        print("-" * 50)
        self.emit_stream('code', generated_code)
        
        # Check for stop signal before execution
        self.check_stop_signal()
        
        self.emit_stream('status', "Executing generated code...")
        result = self._execute_code_streaming(generated_code)
        
        # Process results to extract DataFrames
        dataframes_found = {}
        if result.get("success") and result.get("variables"):
            for var_name, var_value in result["variables"].items():
                if isinstance(var_value, pd.DataFrame):
                    dataframes_found[var_name] = var_value
                    print(f"Found DataFrame: {var_name} (Shape: {var_value.shape})")
                    
                    # Stream the dataframe data
                    self.emit_stream('dataframe', {
                        'name': var_name,
                        'shape': var_value.shape,
                        'columns': list(var_value.columns),
                        'preview': generate_tailwind_table(var_value),
                        'data': var_value.to_dict('records')[:100] if len(var_value) > 0 else [],
                        'sessionId': self.session_id
                    })
        
        # Prepare the result
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
            "data_update_available": len(dataframes_found) > 0,
            "sessionId": self.session_id,
            "nlp_enhanced": True if enhanced_prompt != user_query else False
        }
        
        # Show data updates if successful
        if result.get("success") and dataframes_found:
            print(f"\nAnalysis completed successfully!")
            print(f"📊 Generated {len(dataframes_found)} result DataFrames")
            self.emit_stream('success', f"Analysis completed successfully! Generated {len(dataframes_found)} result DataFrames")
            
            # Save the main result DataFrame
            main_df_name = list(dataframes_found.keys())[0]
            main_df = dataframes_found[main_df_name]
            
            if len(main_df) > 0:
                # Show preview
                self.show_data_preview(self.original_df, main_df)
                
                # Save for potential file update
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
            # Check for stop signal before execution
            self.check_stop_signal()
            
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
            
            # Add sklearn libraries
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
            
            # Add statsmodels for time series
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
            
            # Add XGBoost
            try:
                import xgboost as xgb
                from xgboost import XGBRegressor
                exec_globals.update({'xgb': xgb, 'XGBRegressor': XGBRegressor})
            except ImportError:
                self.emit_stream('output', "⚠️ XGBoost not available. Install with: pip install xgboost")
            
            self.emit_stream('status', "▶️ Executing code...")
            
            exec_locals = {}
            
            # Execute with timeout and stop checking
            try:
                # Split code into lines for periodic stop checking
                code_lines = code.split('\n')
                current_code = ""
                
                for i, line in enumerate(code_lines):
                    # Check for stop signal every few lines
                    if i % 5 == 0:
                        self.check_stop_signal()
                    
                    current_code += line + '\n'
                    
                    # Execute in chunks for better stop responsiveness
                    if i % 10 == 9 or i == len(code_lines) - 1:
                        if platform.system() != 'Windows':
                            with timeout_context(30):  # 30 second timeout per chunk
                                exec(current_code, exec_globals, exec_locals)
                        else:
                            exec(current_code, exec_globals, exec_locals)
                        current_code = ""
                        
            except TimeoutError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Code execution timed out"
                }
            except StopAnalysisException:
                raise  # Re-raise stop exception
            
            self.emit_stream('status', "Capturing visualizations...")
            
            # Capture images with timeout protection
            try:
                captured_images = self._capture_matplotlib_plots_streaming()
                plt.close('all')
            except Exception as img_error:
                self.emit_stream('output', f"Image capture failed: {img_error}")
                captured_images = []
                plt.close('all')
            
            # Result processing
            result_vars = {k: v for k, v in exec_locals.items() if not k.startswith('_')}
            
            return {
                "success": True,
                "output": "Code executed successfully!",
                "variables": result_vars,
                "captured_images": captured_images,
                "message": f"Execution completed successfully! Captured {len(captured_images)} images."
            }
            
        except StopAnalysisException:
            raise  # Re-raise stop exception
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
                "message": f"Execution failed: {str(e)}"
            }
    
    def _capture_matplotlib_plots_streaming(self) -> List[str]:
        """Capture any matplotlib plots that were created during code execution with streaming"""
        captured_images = []
        
        fig_nums = plt.get_fignums()
        
        for i, fig_num in enumerate(fig_nums):
            try:
                # Check for stop signal
                self.check_stop_signal()
                
                fig = plt.figure(fig_num)
                
                timestamp = datetime.now().strftime("%H%M%S")
                image_filename = f"plot_{timestamp}_{i+1}.png"
                image_path = self.images_dir / image_filename
                
                # Save the image
                fig.savefig(image_path, dpi=300, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
                
                public_url = self._upload_image_to_blob(str(image_path))
                if public_url:
                    captured_images.append(public_url)
                    self.generated_images.append(public_url)
                else:
                    captured_images.append(str(image_path))
                    self.generated_images.append(image_filename)
                
                # Convert to base64 and stream to frontend
                try:
                    with open(image_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                    
                    self.emit_stream('image', {
                        'filename': image_filename,
                        'data': f"data:image/png;base64,{img_data}",
                        'path': str(image_path),
                        'sessionId': self.session_id
                    })
                    
                    print(f"Saved and streamed plot: {image_filename}")
                    
                except Exception as stream_error:
                    print(f"Failed to stream image {image_filename}: {stream_error}")
                
            except StopAnalysisException:
                raise  # Re-raise stop exception
            except Exception as e:
                print(f"Failed to save plot {i+1}: {str(e)}")
        
        return captured_images
    
    def _convert_images_to_base64(self) -> Dict[str, str]:
        """Convert all generated images to base64 for HTML embedding."""
        base64_images = {}
        
        # Convert existing saved images
        for i, img_filename in enumerate(self.generated_images):
            try:
                # Check for stop signal
                self.check_stop_signal()
                
                img_path = self.images_dir / img_filename
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                        base64_images[f"image_{i+1}"] = img_data
                        print(f"Converted {img_filename} to base64")
            except StopAnalysisException:
                raise  # Re-raise stop exception
            except Exception as e:
                print(f"Failed to convert {img_filename}: {e}")
        
        # Also capture any currently open matplotlib figures
        fig_nums = plt.get_fignums()
        for i, fig_num in enumerate(fig_nums):
            try:
                # Check for stop signal
                self.check_stop_signal()
                
                fig = plt.figure(fig_num)
                buffer = BytesIO()
                fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                        facecolor='white', edgecolor='none')
                buffer.seek(0)
                img_data = base64.b64encode(buffer.read()).decode('utf-8')
                base64_images[f"figure_{i+1}"] = img_data
                buffer.close()
                print(f"Converted matplotlib figure {fig_num} to base64")
            except StopAnalysisException:
                raise  # Re-raise stop exception
            except Exception as e:
                print(f"Failed to convert figure {fig_num}: {e}")
        
        return base64_images

    def _generate_comprehensive_report_streaming(self, user_query: str, is_forecasting: bool) -> Dict[str, Any]:
        """Generate comprehensive report when specifically requested"""
        print("\nGenerating comprehensive strategic report...")
        self.emit_stream('status', "📋 Generating comprehensive strategic report...")
        
        try:
            # First run the analysis to get data
            data_request = self._extract_data_request(user_query)
            analysis_result = self._generate_dataframe_analysis_streaming_with_fallback(user_query, user_query, data_request, is_forecasting)
            
            if not analysis_result.get("success"):
                return {
                    "error": "Cannot generate report - analysis failed",
                    "type": "report_error",
                    "sessionId": self.session_id
                }
            
            self.emit_stream('status', "📝 Converting images and generating report...")
            
            # Convert all images to base64
            base64_images = self._convert_images_to_base64()
            print(f"Converted {len(base64_images)} images to base64")
            
            # Check for stop signal
            self.check_stop_signal()
            
            # Generate the report
            market_topic = self._extract_market_topic(user_query)
            target_variable = self._extract_target_variable(user_query)
            forecast_periods = self._extract_forecast_periods(user_query) if is_forecasting else 6
            
            # Prepare data context
            data_context = self._prepare_report_data_context(analysis_result, target_variable)
            
            report = self.generate_forecast_report(
                data_context=data_context,
                forecast_results=analysis_result,
                client_name="Executive Leadership Team",
                market_topic=market_topic,
                forecast_periods=forecast_periods,
                target_variable=target_variable,
            )
            
            # Stream the report to frontend
            self.emit_stream('report', report)
            
            analysis_result.update({
                "type": "comprehensive_report",
                "comprehensive_report": report,
                "report_generated": True,
                "market_topic": market_topic,
                "target_variable": target_variable,
                "forecast_periods": forecast_periods,
                "sessionId": self.session_id
            })
            
            print("Comprehensive strategic report generated successfully!")
            self.emit_stream('success', "Comprehensive strategic report generated successfully!")
            
        except StopAnalysisException:
            raise  # Re-raise stop exception
        except Exception as report_error:
            print(f"⚠️ Report generation failed: {str(report_error)}")
            print(f"Traceback: {traceback.format_exc()}")
            self.emit_stream('error', f"Report generation failed: {str(report_error)}")
            analysis_result.update({
                "report_error": str(report_error),
                "report_generated": False,
                "type": "report_error",
                "sessionId": self.session_id
            })
        
        return analysis_result
    
    def _regenerate_code_with_fallback(self, user_query: str, data_request: Dict, is_forecasting: bool, 
                                   failed_code: str, error_message: str, max_retries: int = 2) -> Dict[str, Any]:
        """Fallback function to regenerate code when execution fails with stop checking"""
        
        self.emit_stream('status', f"🔄 Code execution failed. Attempting to regenerate...")
        
        # Check for stop signal
        self.check_stop_signal()
        
        # Create enhanced prompt with error context
        error_context_prompt = f"""
PREVIOUS ATTEMPT FAILED - PLEASE FIX THE ISSUES:

ORIGINAL REQUEST: {user_query}
REQUEST TYPE: {data_request['type']}

FAILED CODE:
```python
{failed_code}
```

ERROR MESSAGE:
{error_message}

CRITICAL FIXES NEEDED:
1. Analyze the error message above and fix the root cause
2. Ensure all required libraries are properly imported
3. Handle missing columns gracefully with proper error checking
4. Use proper data type conversions and null handling
5. Validate data structure before processing

COMMON ERROR PATTERNS TO AVOID:
- KeyError: Check if columns exist before accessing them
- ValueError: Validate data types and handle conversion errors
- IndexError: Check DataFrame length before indexing
- AttributeError: Verify DataFrame methods and attributes exist
- TypeError: Ensure proper data type matching

FALLBACK STRATEGIES:
- Use try-except blocks for risky operations
- Provide alternative column names if primary ones don't exist
- Use .get() method for dictionary-like access
- Add data validation steps before processing
- Include fallback methods if primary analysis fails
"""
        
        # Attempt regeneration with retries
        for attempt in range(max_retries):
            try:
                # Check for stop signal before each attempt
                self.check_stop_signal()
                
                self.emit_stream('status', f"Regeneration attempt {attempt + 1}/{max_retries}")
                
                # Generate new code with error context
                context = self.conversation_history.get_context_for_ai()
                prompt_with_context = error_context_prompt + context
                
                response = self.openai_client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": self._create_system_prompt()},
                        {"role": "user", "content": prompt_with_context}
                    ],
                )
                
                regenerated_code = response.choices[0].message.content
                if "```python" in regenerated_code:
                    regenerated_code = regenerated_code.split("```python")[1].split("```")[0].strip()
                elif "```" in regenerated_code:
                    regenerated_code = regenerated_code.split("```")[1].split("```")[0].strip()
                
                print(f"Regenerated code (attempt {attempt + 1}):")
                print(regenerated_code)
                print("-" * 50)
                
                self.emit_stream('code', f"Regenerated code (attempt {attempt + 1}):\n{regenerated_code}")
                
                # Check for stop signal before execution
                self.check_stop_signal()
                
                # Execute the regenerated code
                self.emit_stream('status', f"Executing regenerated code...")
                result = self._execute_code_streaming(regenerated_code)
                
                # If successful, process and return results
                if result.get("success"):
                    self.emit_stream('success', f"Code regeneration successful on attempt {attempt + 1}!")
                    
                    # Process results same as original function
                    dataframes_found = {}
                    if result.get("variables"):
                        for var_name, var_value in result["variables"].items():
                            if isinstance(var_value, pd.DataFrame):
                                dataframes_found[var_name] = var_value
                                print(f"Found DataFrame: {var_name} (Shape: {var_value.shape})")
                                
                                self.emit_stream('dataframe', {
                                    'name': var_name,
                                    'shape': var_value.shape,
                                    'columns': list(var_value.columns),
                                    'preview': generate_tailwind_table(var_value),
                                    'data': var_value.to_dict('records')[:100] if len(var_value) > 0 else [],
                                    'sessionId': self.session_id
                                })
                    
                    analysis_result = {
                        "query": user_query,
                        "type": "dataframe_analysis",
                        "request_type": data_request['type'],
                        "generated_code": regenerated_code,
                        "execution_result": result,
                        "success": True,
                        "is_forecasting": is_forecasting,
                        "generated_images": self.generated_images.copy(),
                        "dataframes": dataframes_found,
                        "data_update_available": len(dataframes_found) > 0,
                        "regenerated": True,
                        "regeneration_attempt": attempt + 1,
                        "sessionId": self.session_id
                    }
                    
                    # Add the same post-processing as the original function
                    if result.get("success") and dataframes_found:
                        print(f"\nAnalysis completed successfully!")
                        print(f"📊 Generated {len(dataframes_found)} result DataFrames")
                        self.emit_stream('success', f"Analysis completed successfully! Generated {len(dataframes_found)} result DataFrames")
                        
                        # Save the main result DataFrame
                        main_df_name = list(dataframes_found.keys())[0]
                        main_df = dataframes_found[main_df_name]
                        
                        if len(main_df) > 0:
                            # Show preview
                            self.show_data_preview(self.original_df, main_df)
                            
                            # Save for potential file update
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
                
                else:
                    # Update error message for next attempt
                    error_message = result.get("error", "Unknown error occurred")
                    failed_code = regenerated_code
                    self.emit_stream('error', f"Regeneration attempt {attempt + 1} failed: {error_message}")
                    continue
                    
            except StopAnalysisException:
                raise  # Re-raise stop exception
            except Exception as e:
                error_message = str(e)
                self.emit_stream('error', f"Regeneration attempt {attempt + 1} failed with exception: {error_message}")
                continue
        
        # If all retries failed, return failure result
        self.emit_stream('error', f"All regeneration attempts failed after {max_retries} tries")
        
        return {
            "query": user_query,
            "type": "dataframe_analysis",
            "request_type": data_request['type'],
            "generated_code": failed_code,
            "execution_result": {"success": False, "error": error_message},
            "success": False,
            "is_forecasting": is_forecasting,
            "generated_images": [],
            "dataframes": {},
            "data_update_available": False,
            "regenerated": False,
            "regeneration_failed": True,
            "final_error": error_message,
            "sessionId": self.session_id
        }