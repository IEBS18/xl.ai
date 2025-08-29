import time
import json
import logging
import base64
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from openai import AzureOpenAI

class StreamingAdapter:
    """
    Enhanced streaming adapter that captures ALL assistant activities.
    Streams text responses, code execution, and file generation in real-time.
    """
    
    def __init__(self, client: AzureOpenAI, emit_callback: Callable):
        self.client = client
        self.emit_callback = emit_callback
        self.should_stop = False
        self.processed_steps = set()
        self.downloaded_files = {}
    
    def stream_assistant_run(self, thread_id: str, run_id: str, session_id: str) -> Dict[str, Any]:
        """Enhanced streaming with comprehensive activity capture."""
        try:
            self.should_stop = False
            start_time = time.time()
            max_wait_time = 6000
            
            # self._emit_stream('status', '🤖 Starting assistant analysis...', session_id)
            
            last_status = None
            last_step_count = 0
            
            while time.time() - start_time < max_wait_time and not self.should_stop:
                # Get current run status
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                # Stream status changes
                if run.status != last_status:
                    self._handle_status_change(run.status, session_id)
                    last_status = run.status
                
                # Stream run steps with enhanced detail
                current_step_count = self._stream_run_steps_enhanced(
                    thread_id, run_id, last_step_count, session_id
                )
                last_step_count = current_step_count
                
                # Handle completion states
                if run.status == "completed":
                    return self._handle_completion_enhanced(thread_id, run_id, session_id)
                elif run.status == "failed":
                    return self._handle_failure(run, session_id)
                elif run.status == "cancelled":
                    return self._handle_cancellation(session_id)
                elif run.status in ["queued", "in_progress", "cancelling"]:
                    time.sleep(1)
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"Unknown run status: {run.status}",
                        "type": "unknown_status"
                    }
            
            # Timeout handling
            self._emit_stream('error', 'Analysis timed out after 10 minutes', session_id)
            return {
                "success": False,
                "error": "Assistant run timed out",
                "type": "timeout"
            }
            
        except Exception as e:
            logging.error(f"❌ Error in enhanced streaming: {e}")
            self._emit_stream('error', f'Error during analysis: {str(e)}', session_id)
            return {
                "success": False,
                "error": str(e),
                "type": "streaming_error"
            }
    
    def _stream_run_steps_enhanced(self, thread_id: str, run_id: str, last_step_count: int, session_id: str) -> int:
        """Enhanced step streaming with comprehensive content capture."""
        try:
            run_steps = self.client.beta.threads.runs.steps.list(
                thread_id=thread_id,
                run_id=run_id,
                order="asc"
            )
            
            current_step_count = len(run_steps.data)
            
            # Process new steps
            if current_step_count > last_step_count:
                new_steps = run_steps.data[last_step_count:]
                for step in new_steps:
                    self._process_step_enhanced(step, session_id)
            
            return current_step_count
            
        except Exception as e:
            logging.error(f"Error processing steps: {e}")
            return last_step_count
    
    def _process_step_enhanced(self, step, session_id: str):
        """Enhanced step processing with real-time streaming."""
        try:
            step_id = step.id
            
            # Skip if already processed
            if step_id in self.processed_steps:
                return
            
            self.processed_steps.add(step_id)
            
            # Stream step start
            self._emit_stream('step_start', {
                'step_id': step_id,
                'type': step.type,
                'status': step.status
            }, session_id)
            
            # Process tool calls
            if hasattr(step.step_details, 'tool_calls'):
                for tool_call in step.step_details.tool_calls:
                    self._process_tool_call_enhanced(tool_call, session_id)
            
            # Process message creation
            elif step.type == "message_creation":
                self._process_message_creation(step, session_id)
            
        except Exception as e:
            logging.error(f"Error processing step: {e}")
    
    def _process_tool_call_enhanced(self, tool_call, session_id: str):
        """Process tool calls with comprehensive streaming."""
        if tool_call.type == "code_interpreter":
            # Stream code input
            if hasattr(tool_call.code_interpreter, 'input') and tool_call.code_interpreter.input:
                self._emit_stream('code', tool_call.code_interpreter.input, session_id)
            
            # Stream outputs
            if hasattr(tool_call.code_interpreter, 'outputs'):
                for output in tool_call.code_interpreter.outputs:
                    if output.type == "logs":
                        self._emit_stream('output', output.logs, session_id)
                    elif output.type == "image":
                        self._handle_generated_image(output.image.file_id, session_id)
        
        elif tool_call.type == "function":
            # Handle custom function calls
            self._emit_stream('function_call', {
                'name': tool_call.function.name,
                'arguments': tool_call.function.arguments
            }, session_id)
    
    def _process_message_creation(self, step, session_id: str):
        """Process message creation to stream text responses."""
        try:
            message_id = step.step_details.message_creation.message_id
            message = self.client.beta.threads.messages.retrieve(
                thread_id=step.thread_id,
                message_id=message_id
            )
            
            # Stream message content
            for content in message.content:
                if content.type == "text":
                    self._emit_stream('response', content.text.value, session_id)
                elif content.type == "image_file":
                    self._handle_generated_image(content.image_file.file_id, session_id)
                    
        except Exception as e:
            logging.error(f"Error processing message creation: {e}")
    
    def _handle_generated_image(self, file_id: str, session_id: str):
        """Handle generated images with immediate streaming."""
        try:
            # Download file content
            file_data = self.client.files.content(file_id)
            
            # Convert to base64 for streaming
            img_base64 = base64.b64encode(file_data.content).decode('utf-8')
            
            # Stream the image
            # self._emit_stream('image', {
            #     'file_id': file_id,
            #     'data': f"data:image/png;base64,{img_base64}",
            #     'filename': f"assistant_generated_{file_id}.png",
            #     'type': 'assistant_generated'
            # }, session_id)
            
            # Store for later processing
            self.downloaded_files[file_id] = file_data.content
            
        except Exception as e:
            logging.error(f"Error handling generated image: {e}")
    
    def _handle_completion_enhanced(self, thread_id: str, run_id: str, session_id: str) -> Dict[str, Any]:
        """Enhanced completion handling with comprehensive result capture."""
        try:
            self._emit_stream('status', 'Analysis completed successfully!', session_id)
            
            # Get final messages
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=5
            )
            
            # Find latest assistant message
            assistant_response = None
            for message in messages.data:
                if message.role == "assistant":
                    assistant_response = message
                    break
            
            if not assistant_response:
                return {
                    "success": False,
                    "error": "No assistant response found",
                    "type": "no_response"
                }
            
            # Extract comprehensive response content
            response_content = ""
            generated_files = []
            
            for content in assistant_response.content:
                if content.type == "text":
                    response_content += content.text.value
                elif content.type == "image_file":
                    generated_files.append(content.image_file.file_id)
            
            # Get execution outputs from run steps
            execution_outputs = []
            generated_code = ""
            
            run_steps = self.client.beta.threads.runs.steps.list(
                thread_id=thread_id,
                run_id=run_id
            )
            
            for step in run_steps.data:
                if hasattr(step.step_details, 'tool_calls'):
                    for tool_call in step.step_details.tool_calls:
                        if tool_call.type == "code_interpreter":
                            # Capture code
                            if hasattr(tool_call.code_interpreter, 'input'):
                                generated_code += tool_call.code_interpreter.input + "\n"
                            
                            # Capture outputs
                            for output in tool_call.code_interpreter.outputs:
                                if output.type == "logs":
                                    execution_outputs.append(output.logs)
                                elif output.type == "image":
                                    if output.image.file_id not in generated_files:
                                        generated_files.append(output.image.file_id)
            
            # Stream final completion
            # self._emit_stream('completion', {
            #     'message': 'Analysis completed successfully!',
            #     'response_length': len(response_content),
            #     'files_generated': len(generated_files),
            #     'code_executed': bool(generated_code.strip())
            # }, session_id)
            
            return {
                "success": True,
                "response_content": response_content,
                "generated_code": generated_code.strip(),
                "execution_outputs": execution_outputs,
                "generated_files": generated_files,
                "downloaded_files": self.downloaded_files,
                "message_id": assistant_response.id,
                "type": "completion"
            }
            
        except Exception as e:
            logging.error(f"Error handling completion: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "completion_error"
            }
    
    def _handle_status_change(self, status: str, session_id: str):
        """Handle status changes with appropriate streaming messages."""
        status_messages = {
            "queued": "Analysis queued...",
            "in_progress": " Running analysis...",
            "cancelling": "🛑 Cancelling analysis...",
            "cancelled": "❌ Analysis cancelled",
            "failed": "❌ Analysis failed",
            "completed": "Analysis completed!"
        }
        
        message = status_messages.get(status, f"Status: {status}")
        self._emit_stream('status', message, session_id)
    
    def _handle_failure(self, run, session_id: str) -> Dict[str, Any]:
        """Handle failed run."""
        error_msg = f"Assistant run failed"
        if hasattr(run, 'last_error') and run.last_error:
            error_msg += f": {run.last_error.message}"
        
        self._emit_stream('error', error_msg, session_id)
        return {
            "success": False,
            "error": error_msg,
            "type": "run_failed"
        }
    
    def _handle_cancellation(self, session_id: str) -> Dict[str, Any]:
        """Handle cancelled run."""
        self._emit_stream('stopped', 'Analysis was cancelled', session_id)
        return {
            "success": False,
            "error": "Run was cancelled",
            "type": "cancelled",
            "stopped_by_user": True
        }
    
    def _emit_stream(self, message_type: str, data: Any, session_id: str):
        """Emit streaming data using the callback."""
        try:
            if self.emit_callback:
                self.emit_callback(message_type, {
                    'type': message_type,
                    'data': data,
                    'timestamp': datetime.now().isoformat(),
                    'session_id': session_id
                })
        except Exception as e:
            logging.error(f"Error emitting stream: {e}")
    
    def stop_streaming(self):
        """Signal to stop streaming."""
        self.should_stop = True
    
    def cancel_run(self, thread_id: str, run_id: str) -> bool:
        """Cancel an active run."""
        try:
            self.client.beta.threads.runs.cancel(
                thread_id=thread_id,
                run_id=run_id
            )
            return True
        except Exception as e:
            logging.error(f"Error cancelling run: {e}")
            return False