# streaming_analyzer.py
"""
Streaming Analyzer module for real-time CSV analysis with Flask integration
"""

import logging
import os
import json
import base64
import traceback
import warnings
import re
import time
import platform
from io import BytesIO
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from contextlib import contextmanager
import threading

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from legacy_codes.test2 import QuadraticCSVAnalyzer
from conversation_history import ConversationHistory
from prompt_loader import PromptLoader
from table_generator import generate_tailwind_table


class StreamingAnalyzer(QuadraticCSVAnalyzer):
    """Extended analyzer with streaming capabilities for Flask integration."""
    
    def __init__(self, session_id, socketio_instance=None):
        super().__init__()
        self.session_id = session_id
        self.socketio = socketio_instance
        self.streaming_outputs = []
        self.conversation_history = ConversationHistory(session_id, self.output_dir)
        self.prompt_loader = PromptLoader()
        
        # Initialize simple memory - no need for complex chat history initialization
        self.memory = None  # Will be set up later if needed
    
    def emit_stream(self, message_type, data):
        """Emit streaming data to the frontend."""
        if not self.socketio:
            return
            
        try:
            self.socketio.emit('stream_data', {
                'type': message_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            
            # Add delay for smooth streaming
            time.sleep(0.05)
        except Exception as e:
            print(f"Error emitting stream: {e}")

    def analyze_query_streaming(self, user_query: str):
        """Enhanced analyze_query with real-time streaming that matches original behavior."""
        if self.df is None:
            self.emit_stream('error', "No CSV file loaded. Please upload a CSV first.")
            return {"error": "No CSV file loaded. Please load a CSV first."}

        try:
            # announce incoming query
            self.emit_stream('status', f"🤖 Analyzing query: {user_query}")

            # reset per‑query state
            self.generated_images = []
            self.streaming_outputs = []

            # decide path
            is_report_request = self._is_report_request(user_query)
            data_request      = self._extract_data_request(user_query)
            is_forecasting   = any(
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
                    data_request,
                    is_forecasting
                )

            # record in history
            self.conversation_history.add_conversation(user_query, result)
            return result

        except Exception as e:
            # capture full traceback
            full_trace = traceback.format_exc()
            error_msg  = f"Error analyzing query:\n{full_trace}"
            print(error_msg)
            self.emit_stream('error', error_msg)

            # record failure in history
            self.conversation_history.add_conversation(user_query, {
                "error": str(e),
                "traceback": full_trace,
                "type": "error",
                "success": False
            })

            return {
                "error": str(e),
                "traceback": full_trace,
                "type": "error",
                "success": False
            }
    
    def _create_system_prompt(self) -> str:
        """Create system prompt using the PromptLoader."""
        return self.prompt_loader.get_system_prompt(self.csv_info)
    
    def _generate_dataframe_analysis_streaming(self, user_query: str, data_request: Dict, is_forecasting: bool) -> Dict[str, Any]:
        """Generate analysis focused on returning actionable DataFrame results."""
        
        # Get base prompt
        base_requirements = self.prompt_loader.get_base_analysis_prompt(user_query, data_request)
        
        # Add specific requirements based on type
        if is_forecasting:
            enhanced_prompt = base_requirements + self.prompt_loader.get_forecasting_prompt()
        else:
            enhanced_prompt = base_requirements + self.prompt_loader.get_analysis_prompt()
        
        self.emit_stream('status', "🤖 Generating analysis code...")
        
        # Get conversation context for AI
        context = self.conversation_history.get_context_for_ai()
        
        # Generate and execute the analysis code - Enhanced with context
        prompt_with_context = enhanced_prompt + context
        
        response = self.openai_client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user",   "content": prompt_with_context}
            ],
        )
        
        generated_code = self._extract_code_from_response(response.choices[0].message.content)
        
        print("📝 Generated code:")
        print(generated_code)
        print("-" * 50)
        self.emit_stream('code', generated_code)
        
        self.emit_stream('status', "⚡ Executing generated code...")
        result = self._execute_code_streaming(generated_code)
        
        return self._process_analysis_results(user_query, data_request, is_forecasting, generated_code, result)
    
    def _extract_code_from_response(self, response_content: str) -> str:
        """Extract Python code from response content."""
        if "```python" in response_content:
            return response_content.split("```python")[1].split("```")[0].strip()
        elif "```" in response_content:
            return response_content.split("```")[1].split("```")[0].strip()
        return response_content
    
    def _process_analysis_results(self, user_query: str, data_request: Dict, is_forecasting: bool, 
                                generated_code: str, result: Dict) -> Dict[str, Any]:
        """Process and return analysis results."""
        
        # Process results to extract DataFrames
        dataframes_found = {}
        if result.get("success") and result.get("variables"):
            for var_name, var_value in result["variables"].items():
                if isinstance(var_value, pd.DataFrame):
                    dataframes_found[var_name] = var_value
                    logging.info(f"📊 Found DataFrame: {var_name} (Shape: {var_value.shape})")
                    
                    # Stream the dataframe data
                    self.emit_stream('dataframe', {
                        'name': var_name,
                        'shape': var_value.shape,
                        'columns': list(var_value.columns),
                        'preview': generate_tailwind_table(var_value.head()),
                        'data': var_value.to_dict('records')[:100] if len(var_value) > 0 else [],
                        'thisis': "4"
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
            "data_update_available": len(dataframes_found) > 0
        }
        
        # Show data updates if successful
        if result.get("success") and dataframes_found:
            print(f"\n✅ Analysis completed successfully!")
            print(f"📊 Generated {len(dataframes_found)} result DataFrames")
            self.emit_stream('success', f"✅ Analysis completed successfully! Generated {len(dataframes_found)} result DataFrames")
            
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
        
        try:
            from scipy import stats
            
            # Set matplotlib to non-interactive mode and use Agg backend
            plt.switch_backend('Agg')
            plt.ioff()
            
            exec_globals = self._setup_execution_globals()
            exec_locals = {}
            
            self.emit_stream('status', "▶️ Executing code...")
            
            # Execute with timeout protection
            try:
                self._execute_with_timeout(code, exec_globals, exec_locals)
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
            
            # Process results
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

    def _setup_execution_globals(self) -> Dict:
        """Setup global variables for code execution."""
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
            'datetime': datetime,
            'timedelta': timedelta,
            'Path': Path,
            'images_dir': str(self.images_dir)
        }
        
        # Add optional libraries
        self._add_optional_libraries(exec_globals)
        
        return exec_globals
    
    def _add_optional_libraries(self, exec_globals: Dict):
        """Add optional libraries to execution globals if available."""
        
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
        
        # Add scipy
        try:
            from scipy import stats
            exec_globals['stats'] = stats
        except ImportError:
            self.emit_stream('output', "⚠️ Scipy not available")

    @contextmanager
    def _timeout_context(self, seconds):
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

    def _execute_with_timeout(self, code: str, exec_globals: Dict, exec_locals: Dict):
        """Execute code with timeout protection."""
        if platform.system() != 'Windows':
            with self._timeout_context(60):  # 1 minute timeout on Unix
                exec(code, exec_globals, exec_locals)
        else:
            # On Windows, execute without signal-based timeout
            exec(code, exec_globals, exec_locals)

    def _generate_dataframe_analysis_streaming_with_fallback(self, user_query: str, data_request: Dict, is_forecasting: bool) -> Dict[str, Any]:
        """Enhanced version with automatic fallback on failure."""
        
        # First, try the original generation logic
        original_result = self._generate_dataframe_analysis_streaming(user_query, data_request, is_forecasting)
        
        # If original execution was successful, return it
        if original_result.get("success"):
            return original_result
        
        # If original execution failed, trigger fallback
        self.emit_stream('warning', "⚠️ Initial code generation failed. Attempting regeneration with error context...")
        
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

    def _regenerate_code_with_fallback(self, user_query: str, data_request: Dict, is_forecasting: bool, 
                                   failed_code: str, error_message: str, max_retries: int = 2) -> Dict[str, Any]:
        """Fallback function to regenerate code when execution fails."""
        
        self.emit_stream('status', f"🔄 Code execution failed. Attempting to regenerate...")
        
        # Get error context prompt
        error_context_prompt = self.prompt_loader.get_error_context_prompt(
            user_query, data_request, failed_code, error_message, is_forecasting
        )
    
        # Attempt regeneration with retries
        for attempt in range(max_retries):
            try:
                self.emit_stream('status', f"🔄 Regeneration attempt {attempt + 1}/{max_retries}")
                
                # Include conversation context for better error fixing
                context = self.conversation_history.get_context_for_ai()
                prompt_with_context = error_context_prompt + context
                
                response = self.openai_client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": self._create_system_prompt()},
                        {"role": "user", "content": prompt_with_context}
                    ],
                )
                
                regenerated_code = self._extract_code_from_response(response.choices[0].message.content)
                
                print(f"🔄 Regenerated code (attempt {attempt + 1}):")
                print(regenerated_code)
                print("-" * 50)
                
                self.emit_stream('code', f"Regenerated code (attempt {attempt + 1}):\n{regenerated_code}")
                
                # Execute the regenerated code
                self.emit_stream('status', f"⚡ Executing regenerated code...")
                result = self._execute_code_streaming(regenerated_code)
                
                # If successful, process and return results
                if result.get("success"):
                    self.emit_stream('success', f"✅ Code regeneration successful on attempt {attempt + 1}!")
                    
                    # Process results same as original function
                    analysis_result = self._process_analysis_results(
                        user_query, data_request, is_forecasting, regenerated_code, result
                    )
                    
                    analysis_result.update({
                        "regenerated": True,
                        "regeneration_attempt": attempt + 1
                    })
                    
                    return analysis_result
                
                else:
                    # Update error message for next attempt
                    error_message = result.get("error", "Unknown error occurred")
                    failed_code = regenerated_code
                    self.emit_stream('error', f"❌ Regeneration attempt {attempt + 1} failed: {error_message}")
                    continue
                    
            except Exception as e:
                error_message = str(e)
                self.emit_stream('error', f"❌ Regeneration attempt {attempt + 1} failed with exception: {error_message}")
                continue
        
        # If all retries failed, return failure result
        self.emit_stream('error', f"❌ All regeneration attempts failed after {max_retries} tries")
        
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
            "final_error": error_message
        }
    
    def _streaming_print(self, *args, **kwargs):
        """Custom print function that streams output to frontend."""
        output_text = ' '.join(str(arg) for arg in args)
        self.streaming_outputs.append(output_text)
        self.emit_stream('output', output_text)
        print(*args, **kwargs)  # Also print to console
    
    def _capture_matplotlib_plots_streaming(self) -> List[str]:
        """Capture any matplotlib plots that were created during code execution with streaming"""
        captured_images = []
        
        fig_nums = plt.get_fignums()
        
        for i, fig_num in enumerate(fig_nums):
            try:
                fig = plt.figure(fig_num)
                
                timestamp = datetime.now().strftime("%H%M%S")
                image_filename = f"plot_{timestamp}_{i+1}.png"
                image_path = self.images_dir / image_filename
                
                # Save the image
                fig.savefig(image_path, dpi=300, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
                
                # Try to upload to blob storage if available
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
                        'thisis': 1
                    })
                    
                    print(f"📸 Saved and streamed plot: {image_filename}")
                    
                except Exception as stream_error:
                    print(f"⚠️ Failed to stream image {image_filename}: {stream_error}")
                
            except Exception as e:
                print(f"⚠️ Failed to save plot {i+1}: {str(e)}")
        
        return captured_images
    
    def _convert_images_to_base64(self) -> Dict[str, str]:
        """Convert all generated images to base64 for HTML embedding."""
        base64_images = {}
        
        # Convert existing saved images
        for i, img_filename in enumerate(self.generated_images):
            try:
                img_path = self.images_dir / img_filename
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                        base64_images[f"image_{i+1}"] = img_data
                        print(f"📸 Converted {img_filename} to base64")
            except Exception as e:
                print(f"⚠️ Failed to convert {img_filename}: {e}")
        
        # Also capture any currently open matplotlib figures
        fig_nums = plt.get_fignums()
        for i, fig_num in enumerate(fig_nums):
            try:
                fig = plt.figure(fig_num)
                buffer = BytesIO()
                fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                        facecolor='white', edgecolor='none')
                buffer.seek(0)
                img_data = base64.b64encode(buffer.read()).decode('utf-8')
                base64_images[f"figure_{i+1}"] = img_data
                buffer.close()
                print(f"📸 Converted matplotlib figure {fig_num} to base64")
            except Exception as e:
                print(f"⚠️ Failed to convert figure {fig_num}: {e}")
        
        return base64_images

    def _generate_comprehensive_report_streaming(self, user_query: str, is_forecasting: bool) -> Dict[str, Any]:
        """Generate comprehensive report when specifically requested."""
        print("\n📋 Generating comprehensive strategic report...")
        self.emit_stream('status', "📋 Generating comprehensive strategic report...")
        
        try:
            # First run the analysis to get data
            data_request = self._extract_data_request(user_query)
            analysis_result = self._generate_dataframe_analysis_streaming_with_fallback(user_query, data_request, is_forecasting)
            
            if not analysis_result.get("success"):
                return {
                    "error": "Cannot generate report - analysis failed",
                    "type": "report_error"
                }
            
            self.emit_stream('status', "📝 Converting images and generating report...")
            
            # Convert all images to base64
            base64_images = self._convert_images_to_base64()
            print(f"📸 Converted {len(base64_images)} images to base64")
            
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
            })
            
            print("✅ Comprehensive strategic report generated successfully!")
            self.emit_stream('success', "✅ Comprehensive strategic report generated successfully!")
            
        except Exception as report_error:
            print(f"⚠️ Report generation failed: {str(report_error)}")
            print(f"Traceback: {traceback.format_exc()}")
            self.emit_stream('error', f"Report generation failed: {str(report_error)}")
            analysis_result.update({
                "report_error": str(report_error),
                "report_generated": False,
                "type": "report_error"
            })
        
        return analysis_result