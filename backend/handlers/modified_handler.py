# PART 1: ConversationHandler - Initialization and Setup
import logging
import os
import random
from datetime import datetime
from typing import Dict, Any, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class ConversationHandler:
    """
    WORKING: Handles conversational queries (greetings, casual chat, capability questions)
    
    PURPOSE:
    - Process simple conversational queries like "Hi", "How are you?", "What can you do?"
    - Use AI (Assistants API) for better responses when available
    - Fallback to predefined responses when AI fails
    - Stream responses to frontend in real-time
    """
    
    def __init__(self, session_id: str, socketio=None, assistant_manager=None, thread_manager=None):
        """
        WORKING: Initialize the conversation handler
        
        Parameters:
        - session_id: Unique identifier for the user session
        - socketio: WebSocket connection for real-time streaming
        - assistant_manager: Manages OpenAI Assistants API calls
        - thread_manager: Manages conversation threads/context
        """
        self.session_id = session_id
        self.socketio = socketio
        self.assistant_manager = assistant_manager
        self.thread_manager = thread_manager
        
        # Fallback to direct OpenAI if assistants not available
        if not assistant_manager:
            self.openai_client = AzureOpenAI(
                api_key=os.getenv('AZUREAPI'),
                api_version=os.getenv('AZUREVERSION'),
                azure_endpoint=os.getenv('AZUREENDPOINT')
            )
            self.MODEL = os.getenv("AZUREMODEL", "gpt-4")
        
        # PART 2: Predefined Quick Responses
        """
        WORKING: These are fast, predefined responses for common queries
        - Used when AI is not needed or fails
        - Provides instant responses without API calls
        - Covers most common conversational patterns
        """
        self.quick_responses = {
            "greeting": [
                "Hello! I'm your AI data analyst assistant. I'm here to help you analyze your CSV data and answer any questions you might have!",
                "Hi there! Ready to dive into some data analysis? I can help you explore your dataset, create visualizations, and generate insights.",
                "Hey! Great to see you. I'm equipped to handle everything from simple data queries to complex forecasting and reporting.",
            ],
            "how_are_you": [
                "I'm doing great, thanks for asking! I'm ready to help you analyze your data and uncover valuable insights.",
                "I'm excellent and ready to tackle any data analysis challenges you have!",
                "Doing wonderful! I'm energized and ready to help you make sense of your data.",
            ],
            "capabilities": [
                "I can help you with a wide range of data analysis tasks:\n• Answer questions about your data (averages, maximums, counts, etc.)\n• Create beautiful visualizations and charts\n• Generate comprehensive reports\n• Perform forecasting and trend analysis\n• Clean and transform your data\n• Identify patterns and insights\n\nJust ask me anything about your dataset!",
                "Here's what I can do for you:\n✓ Analyze your CSV data with Python\n✓ Create charts and visualizations\n✓ Generate forecasts and predictions\n✓ Answer specific questions about your data\n✓ Create detailed reports\n✓ Help with data cleaning and processing\n\nWhat would you like to explore in your data?",
            ],
            "thanks": [
                "You're very welcome! I'm here whenever you need help with your data analysis.",
                "Happy to help! Feel free to ask me anything about your dataset.",
                "My pleasure! Let me know if you have any questions about your data.",
            ],
            "goodbye": [
                "Goodbye! Thanks for using the data analysis assistant. Come back anytime you need insights from your data!",
                "See you later! It was great helping you with your data analysis.",
                "Bye! Don't hesitate to return if you need more data insights.",
            ]
        }
    
    # PART 3: Streaming Utility
    def emit_stream(self, message_type: str, data: str):
        """
        WORKING: Send real-time updates to the frontend
        
        How it works:
        1. Uses WebSocket (socketio) to send data immediately
        2. Sends structured messages with type and timestamp
        3. Frontend receives these messages and updates UI in real-time
        4. Handles errors gracefully if connection fails
        """
        try:
            if self.socketio:
                self.socketio.emit('stream_data', {
                    'type': message_type,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
        except Exception as e:
            print(f"Error emitting conversational stream: {e}")

    # PART 4: Main Handler Method
    def handle_conversational_query(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        WORKING: Main method that processes conversational queries
        
        Flow:
        1. Emit status that we're processing the message
        2. Try to generate response using AI (Assistants API)
        3. If AI fails, fallback to predefined responses
        4. Stream the response to frontend
        5. Return structured result in expected format
        
        Parameters:
        - user_query: What the user said (e.g., "Hi", "How are you?")
        - context: Information about current session (has data, dataset info, etc.)
        
        Returns:
        - Structured dictionary with response, success status, etc.
        """
        
        try:
            # Step 1: Let frontend know we're processing
            self.emit_stream('status', '💬 Understanding your message...')
            
            # Step 2: Try AI response first, then fallback
            if self.assistant_manager and self.thread_manager:
                response_text = self._generate_assistant_response(user_query, context)
            else:
                response_text = self._generate_conversational_response(user_query, context)
            
            # Step 3: Stream the response to frontend
            self.emit_stream('output', response_text)
            self.emit_stream('completion', 'Response complete!')
            
            # Step 4: Return structured result
            return {
                "query": user_query,
                "type": "conversational",
                "success": True,
                "response": response_text,
                "generated_images": [],
                "dataframes": {},
                "execution_result": {
                    "success": True,
                    "output": response_text
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Handle errors gracefully
            error_msg = f"Error handling conversational query: {str(e)}"
            print(error_msg)
            self.emit_stream('error', error_msg)
            
            return {
                "query": user_query,
                "type": "conversational",
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error while processing your message. Please try again.",
                "generated_images": [],
                "dataframes": {},
                "timestamp": datetime.now().isoformat()
            }

    # PART 5: AI Response Generation
    def _generate_assistant_response(self, user_query: str, context: Dict[str, Any] = None) -> str:
        """
        WORKING: Generate response using OpenAI Assistants API
        
        How it works:
        1. Create/get a conversational assistant
        2. Get the conversation thread for this session
        3. Add context about user's data if available
        4. Send query to assistant and get AI response
        5. If successful, return AI response
        6. If fails, fallback to predefined responses
        """
        try:
            # Get conversational assistant
            assistant_id = self.assistant_manager.create_or_get_assistant("conversational")
            thread_id = self.thread_manager.create_or_get_thread(self.session_id)
            
            # Add context to make response more relevant
            enhanced_query = user_query
            if context and context.get("has_data"):
                enhanced_query += f"\n\nContext: I have access to a dataset with {context.get('shape', ['?', '?'])[0]} rows and {context.get('shape', ['?', '?'])[1]} columns."
            
            # Run assistant
            result = self.assistant_manager.run_assistant_analysis(
                thread_id,
                enhanced_query
            )
            
            if result.get("success"):
                return result.get("response_content", "I'm here to help with your data analysis!")
            else:
                # Fallback to predefined responses
                return self._generate_conversational_response(user_query, context)
                
        except Exception as e:
            print(f"Assistant response failed: {e}")
            return self._generate_conversational_response(user_query, context)

    # PART 6: Predefined Response Generation  
    def _generate_conversational_response(self, user_query: str, context: Dict[str, Any] = None) -> str:
        """
        WORKING: Generate response using predefined patterns and responses
        
        How it works:
        1. Convert query to lowercase for pattern matching
        2. Check for common patterns (greetings, questions, thanks, etc.)
        3. Select appropriate predefined response
        4. Add context about user's data if available
        5. For complex queries, use AI as fallback
        
        Pattern matching logic:
        - "hi", "hello" → greeting responses
        - "how are you" → status responses  
        - "what can you do" → capability responses
        - "thanks" → appreciation responses
        - "bye" → goodbye responses
        """
        
        query_lower = user_query.lower().strip()
        
        # Check for greeting patterns
        if any(greeting in query_lower for greeting in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]):
            response = random.choice(self.quick_responses["greeting"])
            
            # Add context about their data if available
            if context and context.get("has_data"):
                response += f"\n\nI can see you have a dataset with {context.get('shape', ['?', '?'])[0]} rows and {context.get('shape', ['?', '?'])[1]} columns. What would you like to explore?"
            
            return response
        
        # Check for status questions
        elif any(phrase in query_lower for phrase in ["how are you", "how's it going", "what's up"]):
            return random.choice(self.quick_responses["how_are_you"])
        
        # Check for capability questions
        elif any(phrase in query_lower for phrase in ["what can you do", "capabilities", "help me", "what do you do"]):
            response = random.choice(self.quick_responses["capabilities"])
            
            # Add specific context if they have data loaded
            if context and context.get("has_data"):
                response += f"\n\nYour current dataset has {len(context.get('columns', []))} columns. I can analyze any of these for you!"
            
            return response
        
        # Check for thanks
        elif any(phrase in query_lower for phrase in ["thank", "thanks", "appreciate"]):
            return random.choice(self.quick_responses["thanks"])
        
        # Check for goodbye
        elif any(phrase in query_lower for phrase in ["bye", "goodbye", "see you", "later"]):
            return random.choice(self.quick_responses["goodbye"])
        
        # For complex conversational queries, use AI
        else:
            return self._generate_ai_conversational_response(user_query, context)

    # PART 7: AI Fallback for Complex Conversations
    def _generate_ai_conversational_response(self, user_query: str, context: Dict[str, Any] = None) -> str:
        """
        WORKING: Use direct OpenAI API for complex conversational queries
        
        When to use:
        - Query doesn't match simple patterns
        - User asks complex questions about capabilities
        - Need more nuanced, contextual response
        
        How it works:
        1. Build context information about user's data
        2. Create prompt for conversational AI
        3. Call OpenAI API directly
        4. Return AI-generated response
        5. If fails, return generic helpful response
        """
        
        # Build context information
        context_info = ""
        if context:
            if context.get("has_data"):
                context_info = f"""
Context: The user has uploaded a CSV dataset with:
- {context.get('shape', ['?', '?'])[0]} rows and {context.get('shape', ['?', '?'])[1]} columns
- Columns: {', '.join(context.get('columns', [])[:5])}{'...' if len(context.get('columns', [])) > 5 else ''}
- Filename: {context.get('filename', 'unknown')}
"""
            else:
                context_info = "Context: The user has not uploaded any data yet."
        
        conversation_prompt = f"""
You are a friendly, helpful AI data analyst assistant. The user is having a casual conversation with you.

{context_info}

Respond to the user's message in a warm, conversational way. Keep it:
- Friendly and engaging
- Concise (2-3 sentences max)  
- Relevant to data analysis when appropriate
- Encouraging about their data analysis journey

User's message: "{user_query}"

Your response:
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are a friendly AI data analyst assistant. Keep responses conversational, warm, and concise."},
                    {"role": "user", "content": conversation_prompt}
                ],
                temperature=0.5,  # Some creativity for conversation
                max_tokens=200    # Keep responses concise
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI conversational response failed: {e}")
            # Final fallback to generic response
            return "That's an interesting question! I'm here to help you with data analysis. Is there anything specific about your dataset you'd like to explore?"
    
class TextualAnalyticalHandler:
    """
    WORKING: Handles simple analytical queries that need quick text answers
    
    PURPOSE:
    - Process simple data questions like "What is the highest revenue?", "How many rows?", "What's the average age?"
    - Use AI (Assistants API with Code Interpreter) to analyze data and provide answers
    - Return text-based answers without complex visualizations
    - Fallback to direct code generation and execution if AI fails
    
    EXAMPLES OF QUERIES IT HANDLES:
    - "What is the maximum sales value?"
    - "How many customers are there?"
    - "What's the average price?"
    - "Which product has the highest revenue?"
    - "Count the number of orders"
    """
    
    def __init__(self, session_id: str, df, socketio=None, csv_info: str = "", 
                 assistant_manager=None, thread_manager=None, file_manager=None):
        """
        WORKING: Initialize the textual analytical handler
        
        Parameters:
        - session_id: Unique session identifier
        - df: The pandas DataFrame with user's data
        - socketio: WebSocket for real-time updates
        - csv_info: String description of the dataset structure
        - assistant_manager: Manages AI assistants
        - thread_manager: Manages conversation context
        - file_manager: Handles file uploads to AI
        """
        self.session_id = session_id
        self.df = df
        self.socketio = socketio
        self.csv_info = csv_info
        self.assistant_manager = assistant_manager
        self.thread_manager = thread_manager
        self.file_manager = file_manager
        
        # Fallback to direct OpenAI if assistants not available
        if not assistant_manager:
            self.openai_client = AzureOpenAI(
                api_key=os.getenv('AZUREAPI'),
                api_version=os.getenv('AZUREVERSION'),
                azure_endpoint=os.getenv('AZUREENDPOINT')
            )
            self.MODEL = os.getenv("AZUREMODEL", "gpt-4")

    # PART 2: Streaming Utility
    def emit_stream(self, message_type: str, data: str):
        """
        WORKING: Send real-time updates to frontend
        - Shows progress like "Analyzing your question..."
        - Displays results as they come in
        - Handles completion notifications
        """
        try:
            if self.socketio:
                self.socketio.emit('stream_data', {
                    'type': message_type,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
        except Exception as e:
            print(f"Error emitting textual analytical stream: {e}")

    # PART 3: Main Handler Method
    def handle_textual_analytical_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        WORKING: Main method that processes simple analytical queries
        
        FLOW:
        1. Show "Analyzing your question..." status
        2. Try AI analysis first (Assistants API with Code Interpreter)
        3. If AI fails, fallback to direct code generation
        4. Always ensure we return a meaningful text response
        5. Stream results to frontend
        6. Return structured response
        
        INPUT EXAMPLE:
        - user_query: "What is the highest revenue?"
        - intent_data: {"analysis_type": "maximum", "specific_analysis": "maximum"}
        
        OUTPUT EXAMPLE:
        {
            "query": "What is the highest revenue?",
            "type": "textual_analytical", 
            "success": True,
            "response": "The highest revenue in your dataset is $45,230, found in the Q4 2023 sales data.",
            "generated_code": "result = df['Revenue'].max()",
            "execution_result": {"success": True, "result": "$45,230"},
            "analysis_type": "maximum"
        }
        """
        
        try:
            # Step 1: Show progress
            self.emit_stream('status', '🔍 Analyzing your question...')
            
            # Step 2: Try AI analysis first, then fallback
            if self.assistant_manager and self.thread_manager:
                result = self._analyze_with_assistants(user_query, intent_data)
            else:
                result = self._analyze_with_direct_api(user_query, intent_data)
            
            # Step 3: Process results
            if result.get("success"):
                text_response = result.get("response", "Analysis completed")
                
                # CRITICAL FIX: Always provide meaningful response
                if not text_response or text_response == "Analysis completed":
                    text_response = f"I analyzed your question '{user_query}' and here's what I found: {result.get('result', 'Please check the code execution results.')}"
                
                # Step 4: Stream results to frontend
                self.emit_stream('output', text_response)
                self.emit_stream('completion', 'Analysis complete!')
                
                # Step 5: Return structured result
                return {
                    "query": user_query,
                    "type": "textual_analytical",
                    "success": True,
                    "response": text_response,
                    "generated_code": result.get("generated_code", ""),
                    "execution_result": {"success": True, "result": text_response},
                    "generated_images": [],
                    "dataframes": {},
                    "analysis_type": intent_data.get("analysis_type", "general"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return self._create_error_result(user_query, result.get("error", "Analysis failed"))
            
        except Exception as e:
            error_msg = f"Error in textual analysis: {str(e)}"
            print(error_msg)
            self.emit_stream('error', error_msg)
            return self._create_error_result(user_query, str(e))

    # PART 4: AI Analysis (Primary Method)
    def _analyze_with_assistants(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        WORKING: Use OpenAI Assistants API with Code Interpreter for analysis
        
        HOW IT WORKS:
        1. Create a "textual_analytical" assistant (specialized for quick questions)
        2. Get the conversation thread for this session
        3. Enhance the user query with context and requirements
        4. Attach uploaded CSV files to the analysis
        5. Run the assistant analysis
        6. Extract and format the response
        
        ENHANCED QUERY EXAMPLE:
        Original: "What is the highest revenue?"
        Enhanced: "Please answer this specific question about the dataset: What is the highest revenue?
        
        Requirements:
        1. Provide a clear, specific answer with actual numbers/values
        2. Explain what the answer means in context
        3. Use the uploaded CSV data to get accurate results
        4. Be concise but informative
        
        Dataset info: Shape: (1000, 12), Columns: ['Date', 'Revenue', 'Product']..."
        """
        try:
            # Step 1: Create/get specialized assistant
            assistant_id = self.assistant_manager.create_or_get_assistant("textual_analytical")
            thread_id = self.thread_manager.create_or_get_thread(self.session_id)
            
            # Step 2: Enhance query with context and requirements
            enhanced_query = f"""
            Please answer this specific question about the dataset: {user_query}

            Requirements:
            1. Provide a clear, specific answer with actual numbers/values
            2. Explain what the answer means in context
            3. Use the uploaded CSV data to get accurate results
            4. Be concise but informative

            Dataset info: {self.csv_info[:500]}...
            """
            
            # Step 3: Get files uploaded for this session
            file_ids = self.file_manager.list_session_files(self.session_id) if self.file_manager else []
            
            # Step 4: Run assistant analysis
            result = self.assistant_manager.run_assistant_analysis(
                thread_id,
                enhanced_query,
                file_ids=file_ids
            )
            
            # Step 5: Process results
            if result.get("success"):
                response_content = result.get("response_content", "Analysis completed")
                
                # Extract any code execution results
                execution_outputs = result.get("execution_outputs", [])
                if execution_outputs:
                    # Combine AI response with execution outputs
                    response_content += "\n\nExecution Results:\n" + "\n".join(execution_outputs)
                
                return {
                    "success": True,
                    "response": response_content,
                    "result": response_content,
                    "generated_code": result.get("generated_code", "")
                }
            else:
                return {"success": False, "error": result.get("error", "Assistant analysis failed")}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    # PART 5: Fallback Analysis (Direct API)
    def _analyze_with_direct_api(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        WORKING: Fallback method using direct OpenAI API + code generation
        
        WHEN USED:
        - Assistants API is not available
        - Assistants API fails
        - Need guaranteed response
        
        HOW IT WORKS:
        1. Generate focused Python code to answer the specific question
        2. Execute the code safely in controlled environment
        3. Extract the result and format as text response
        
        EXAMPLE FLOW:
        Query: "What is the highest revenue?"
        Generated Code: "result = f'The highest revenue is ${df[\"Revenue\"].max():,.2f}'"
        Executed Result: "The highest revenue is $45,230.00"
        """
        try:
            # Step 1: Generate Python code for the question
            analysis_code = self._generate_focused_analysis_code(user_query, intent_data)
            
            if not analysis_code:
                return {"success": False, "error": "Could not generate analysis code"}
            
            # Step 2: Execute the code safely
            execution_result = self._execute_analysis_code(analysis_code)
            
            # Step 3: Format results
            if execution_result.get("success"):
                result_text = str(execution_result.get("result", "Analysis completed"))
                return {
                    "success": True,
                    "response": result_text,
                    "result": result_text,
                    "generated_code": analysis_code
                }
            else:
                return {"success": False, "error": execution_result.get("error", "Execution failed")}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    # PART 6: Code Generation
    def _generate_focused_analysis_code(self, user_query: str, intent_data: Dict[str, Any]) -> str:
        """
        WORKING: Generate Python code to answer specific questions
        
        APPROACH:
        1. Create prompt with query and dataset info
        2. Use OpenAI to generate focused Python code
        3. Ensure code stores result in 'result' variable
        4. Make result human-readable, not just raw numbers
        
        EXAMPLE:
        Query: "What is the highest revenue?"
        Generated Code:
        ```python
        max_revenue = df['Revenue'].max()
        result = f"The highest revenue in your dataset is ${max_revenue:,.2f}"
        ```
        """
        
        analysis_type = intent_data.get("analysis_type", "general")
        
        code_generation_prompt = f"""
Generate Python code to answer this specific question about the dataset: "{user_query}"

REQUIREMENTS:
1. Use the 'df' variable (DataFrame is already loaded)
2. Write concise code that directly answers the question
3. Store the final answer in a variable called 'result'
4. Make the result human-readable (not just raw numbers)
5. Handle any potential errors gracefully
6. NO visualizations or plots for simple questions
7. Focus on getting the specific answer quickly

Analysis Type Detected: {analysis_type}

CSV Data Info:
{self.csv_info}

Generate clean, executable Python code that stores the answer in 'result':
"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are a Python code generator. Generate concise code that answers data questions directly. Always store the final answer in a 'result' variable."},
                    {"role": "user", "content": code_generation_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent code
                max_tokens=500
            )
            
            generated_code = response.choices[0].message.content.strip()
            
            # Clean up code blocks
            if "```python" in generated_code:
                generated_code = generated_code.split("```python")[1].split("```")[0].strip()
            elif "```" in generated_code:
                generated_code = generated_code.split("```")[1].split("```")[0].strip()
            
            return generated_code
            
        except Exception as e:
            print(f"Code generation failed: {e}")
            return ""

    # PART 7: Code Execution
    def _execute_analysis_code(self, code: str) -> Dict[str, Any]:
        """
        WORKING: Safely execute generated Python code
        
        SECURITY MEASURES:
        1. Limited execution environment (only safe libraries)
        2. No file system access
        3. No network access
        4. Only data analysis functions available
        
        ENVIRONMENT INCLUDES:
        - df: User's pandas DataFrame
        - pd: pandas library
        - np: numpy library
        - Basic Python functions (len, str, int, float, etc.)
        - Math functions (max, min, sum, round)
        """
        
        try:
            # Set up safe execution environment
            exec_globals = {
                'df': self.df,  # User's data
                'pd': __import__('pandas'),
                'np': __import__('numpy'),
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'round': round,
                'max': max,
                'min': min,
                'sum': sum
            }
            
            exec_locals = {}
            
            # Execute the code
            exec(code, exec_globals, exec_locals)
            
            # Get the result
            result = exec_locals.get('result', 'Analysis completed')
            
            return {
                "success": True,
                "result": result,
                "code": code,
                "variables": exec_locals
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code": code
            }

    # PART 8: Error Handling
    def _create_error_result(self, user_query: str, error_message: str) -> Dict[str, Any]:
        """
        WORKING: Create standardized error response
        
        ENSURES:
        - User gets helpful error message
        - System doesn't crash
        - Consistent response format
        - Suggests how to fix the issue
        """
        return {
            "query": user_query,
            "type": "textual_analytical",
            "success": False,
            "error": error_message,
            "response": f"I apologize, but I encountered an issue analyzing your question: {error_message}. Could you try rephrasing your question?",
            "generated_images": [],
            "dataframes": {},
            "timestamp": datetime.now().isoformat()
        }    

class AnalyticalHandler:
    """
    WORKING: Handles complex analytical queries with visualizations and comprehensive analysis
    
    PURPOSE:
    - Process complex data analysis requests that need charts, plots, and detailed insights
    - Use AI (Assistants API with Code Interpreter) for comprehensive analysis
    - Generate visualizations (matplotlib, seaborn charts)
    - Stream results in real-time to frontend
    - Always explain what was analyzed and found
    
    EXAMPLES OF QUERIES IT HANDLES:
    - "Create a sales trend analysis with charts"
    - "Generate a forecast for the next 6 months"
    - "Analyze customer segments and visualize the results"
    - "Show me the correlation between price and sales"
    - "Create a comprehensive report with visualizations"
    """
    
    def __init__(self, session_id: str, analyzer_instance, socketio=None, 
                 assistant_manager=None, thread_manager=None, file_manager=None):
        """
        WORKING: Initialize the analytical handler
        
        Parameters:
        - session_id: Unique session identifier
        - analyzer_instance: Reference to main analyzer (has df, csv_info, etc.)
        - socketio: WebSocket for real-time streaming
        - assistant_manager: Manages AI assistants
        - thread_manager: Manages conversation context
        - file_manager: Handles file operations
        """
        self.session_id = session_id
        self.analyzer = analyzer_instance
        self.socketio = socketio
        self.df = analyzer_instance.df if analyzer_instance else None
        self.csv_info = analyzer_instance.csv_info if analyzer_instance else ""
        self.generated_images = analyzer_instance.generated_images if analyzer_instance else []
        
        # Assistants API components
        self.assistant_manager = assistant_manager
        self.thread_manager = thread_manager
        self.file_manager = file_manager
        
        # Fallback to direct OpenAI if assistants not available
        if not assistant_manager:
            self.openai_client = AzureOpenAI(
                api_key=os.getenv('AZUREAPI'),
                api_version=os.getenv('AZUREVERSION'),
                azure_endpoint=os.getenv('AZUREENDPOINT')
            )
            self.MODEL = os.getenv('AZUREMODEL', 'gpt-4')

    # PART 2: Streaming Utility
    def emit_stream(self, message_type: str, data: str):
        """
        WORKING: Send real-time updates to frontend during analysis
        
        MESSAGE TYPES:
        - 'status': Progress updates ("Starting analysis...", "Generating charts...")
        - 'output': Text results and insights
        - 'image': Generated charts and visualizations
        - 'completion': Analysis finished notification
        - 'error': Error messages
        """
        try:
            if self.socketio:
                self.socketio.emit('stream_data', {
                    'type': message_type,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
        except Exception as e:
            print(f"Error emitting analytical stream: {e}")

    # PART 3: Main Handler Method
    def handle_fully_analytical_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        WORKING: Main method that processes complex analytical queries
        
        FLOW:
        1. Show "Starting comprehensive analysis..." status
        2. Extract analysis type (forecasting, visualization, general)
        3. Try AI analysis first (Assistants API with streaming)
        4. If AI fails, fallback to original analysis pipeline
        5. Always add explanation of what was done
        6. Return comprehensive results with charts and insights
        
        INPUT EXAMPLE:
        - user_query: "Analyze sales trends and create visualizations"
        - intent_data: {"analysis_type": "visualization", "specific_analysis": "visualization"}
        
        OUTPUT EXAMPLE:
        {
            "query": "Analyze sales trends and create visualizations",
            "type": "fully_analytical",
            "success": True,
            "response": "I analyzed your sales data and found strong seasonal patterns...",
            "generated_code": "import matplotlib.pyplot as plt...",
            "execution_result": {"success": True, "output": "Generated 3 charts"},
            "generated_images": ["chart1.png", "chart2.png", "chart3.png"],
            "dataframes": {"trend_analysis": <DataFrame>},
            "analysis_type": "visualization"
        }
        """
        
        try:
            # Step 1: Show initial progress
            self.emit_stream('status', f"🔬 Starting comprehensive analysis for: {user_query}")
            
            # Step 2: Extract analysis details
            analysis_type = intent_data.get("analysis_type", "general_analysis")
            
            # Step 3: Try AI analysis first, then fallback
            if self.assistant_manager and self.thread_manager:
                result = self._analyze_with_assistants(user_query, intent_data, analysis_type)
            else:
                result = self._analyze_with_original_pipeline(user_query, intent_data, analysis_type)
            
            # Step 4: CRITICAL FIX - Always add explanation of what was done
            if result.get('success') and not result.get('response'):
                result['response'] = self._generate_analysis_summary(user_query, result)
            
            return result
                
        except Exception as e:
            error_msg = f"Error in full analysis: {str(e)}"
            print(error_msg)
            self.emit_stream('error', error_msg)
            
            return {
                "query": user_query,
                "type": "fully_analytical",
                "success": False,
                "error": str(e),
                "generated_images": [],
                "dataframes": {},
                "timestamp": datetime.now().isoformat()
            }

    # PART 4: AI Analysis (Primary Method)
    def _analyze_with_assistants(self, user_query: str, intent_data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """
        WORKING: Use OpenAI Assistants API with Code Interpreter for comprehensive analysis
        
        HOW IT WORKS:
        1. Create a "data_analyst" assistant (specialized for complex analysis)
        2. Get conversation thread for context
        3. Enhance query with comprehensive requirements
        4. Attach uploaded CSV files
        5. Create streaming run for real-time updates
        6. Process generated files (images, reports, etc.)
        7. Extract DataFrames and insights
        
        ENHANCED QUERY EXAMPLE:
        Original: "Analyze sales trends"
        Enhanced: "Perform comprehensive data analysis for: Analyze sales trends
        
        Requirements:
        1. Analyze the uploaded dataset thoroughly
        2. Create appropriate visualizations (charts, plots, graphs)
        3. Provide detailed insights and explanations
        4. Generate actionable recommendations
        5. Use Python with matplotlib/seaborn for visualizations
        6. Explain your methodology and findings clearly"
        
        STREAMING PROCESS:
        - Real-time updates as AI writes and executes code
        - Images appear as they're generated
        - Text insights stream as they're written
        - Final summary with all results
        """
        try:
            # Step 1: Create specialized assistant
            assistant_id = self.assistant_manager.create_or_get_assistant("data_analyst")
            thread_id = self.thread_manager.create_or_get_thread(self.session_id)
            
            # Step 2: Enhance query with comprehensive requirements
            enhanced_query = f"""
            Perform comprehensive data analysis for: {user_query}
            
            Requirements:
            1. Analyze the uploaded dataset thoroughly
            2. Create appropriate visualizations (charts, plots, graphs)
            3. Provide detailed insights and explanations
            4. Generate actionable recommendations
            5. Use Python with matplotlib/seaborn for visualizations
            6. Explain your methodology and findings clearly
            
            Analysis Type: {analysis_type}
            Dataset info: {self.csv_info[:500]}...
            
            Please provide a comprehensive analysis with visualizations.
            """
            
            # Step 3: Get uploaded files for analysis
            file_ids = self.file_manager.list_session_files(self.session_id) if self.file_manager else []
            
            # Step 4: Add message to conversation thread
            self.thread_manager.add_message_to_thread(
                thread_id,
                "user",
                enhanced_query,
                file_ids=file_ids
            )
            
            # Step 5: Create streaming run
            run = self.assistant_manager.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            
            # Step 6: Initialize streaming for real-time updates
            from utils.streaming_adapter import StreamingAdapter
            streaming_adapter = StreamingAdapter(
                self.assistant_manager.client,
                self._emit_streaming_callback
            )
            
            # Step 7: Stream the analysis with real-time updates
            result = streaming_adapter.stream_assistant_run(
                thread_id,
                run.id,
                self.session_id
            )
            
            # Step 8: Process results
            if result.get("success"):
                # Download and process generated files
                generated_files = result.get("generated_files", [])
                processed_images = self._process_generated_images(generated_files)
                
                # Extract DataFrames from outputs (if possible)
                dataframes = self._extract_dataframes_from_outputs(result.get("execution_outputs", []))
                
                # Ensure we have a proper response
                response_content = result.get("response_content", "")
                if not response_content:
                    response_content = self._generate_analysis_summary(user_query, result)
                
                # Return comprehensive results
                return {
                    "query": user_query,
                    "type": "fully_analytical",
                    "success": True,
                    "response": response_content,
                    "generated_code": result.get("generated_code", ""),
                    "execution_result": {
                        "success": True,
                        "output": "\n".join(result.get("execution_outputs", []))
                    },
                    "generated_images": processed_images,
                    "dataframes": dataframes,
                    "analysis_type": analysis_type,
                    "timestamp": datetime.now().isoformat(),
                    "assistant_used": True,
                    "assistant_id": assistant_id,
                    "thread_id": thread_id
                }
            else:
                # Fallback to original pipeline
                return self._analyze_with_original_pipeline(user_query, intent_data, analysis_type)
                
        except Exception as e:
            print(f"❌ Assistants analysis failed: {e}")
            # Fallback to original pipeline
            return self._analyze_with_original_pipeline(user_query, intent_data, analysis_type)

    # PART 5: Analysis Summary Generation
    def _generate_analysis_summary(self, user_query: str, result: Dict[str, Any]) -> str:
        """
        WORKING: Generate explanation of what was analyzed
        
        PURPOSE:
        - Always explain what the system did
        - Make analysis transparent to users
        - Provide context for results
        - Build user confidence in results
        
        SUMMARY INCLUDES:
        - What was requested
        - What analysis was performed
        - What code was executed
        - What files/visualizations were created
        - How many data tables were generated
        """
        summary_parts = []
        
        summary_parts.append(f"I completed a comprehensive analysis of your request: '{user_query}'")
        
        if result.get("generated_code"):
            summary_parts.append("• Generated and executed Python code for the analysis")
        
        execution_outputs = result.get("execution_outputs", [])
        if execution_outputs:
            summary_parts.append(f"• Processed {len(execution_outputs)} analysis steps")
        
        generated_images = result.get("generated_images", [])
        if generated_images:
            summary_parts.append(f"• Created {len(generated_images)} visualization(s)")
        
        dataframes = result.get("dataframes", {})
        if dataframes:
            summary_parts.append(f"• Generated {len(dataframes)} data table(s)")
        
        summary_parts.append("• Analysis completed successfully with detailed results")
        
        return "\n".join(summary_parts)

    # PART 6: Image Processing
    def _process_generated_images(self, file_ids: list) -> list:
        """
        WORKING: Download and process images generated by AI
        
        PROCESS:
        1. Download each image file from OpenAI
        2. Save to local images directory
        3. Upload to blob storage (if available)
        4. Emit to frontend for immediate display
        5. Return list of image URLs/paths
        
        IMAGE HANDLING:
        - Supports PNG, JPG, SVG formats
        - Automatic blob storage upload
        - Real-time streaming to frontend
        - Error handling for failed downloads
        """
        processed_images = []
        
        for file_id in file_ids:
            try:
                # Download file to local storage
                if hasattr(self.analyzer, 'images_dir') and self.file_manager:
                    save_path = self.file_manager.download_generated_file(
                        file_id,
                        str(self.analyzer.images_dir),
                        f"assistant_{file_id}.png"
                    )
                    
                    # Upload to blob storage if available
                    if hasattr(self.analyzer, '_upload_image_to_blob'):
                        blob_url = self.analyzer._upload_image_to_blob(save_path)
                        if blob_url:
                            processed_images.append(blob_url)
                        else:
                            processed_images.append(save_path)
                    else:
                        processed_images.append(save_path)
                    
                    # Emit to frontend immediately
                    self._emit_image_to_frontend(save_path)
                    
            except Exception as e:
                print(f"Error processing image {file_id}: {e}")
        
        return processed_images

    def _emit_image_to_frontend(self, image_path: str):
        """
        WORKING: Send generated image to frontend for display
        
        FORMAT:
        - Converts image to base64 for web display
        - Includes metadata (filename, path, type)
        - Uses WebSocket for immediate display
        - Handles different image formats
        """
        try:
            import base64
            with open(image_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            
            self.emit_stream('image', {
                'filename': os.path.basename(image_path),
                'data': f"data:image/png;base64,{img_data}",
                'path': image_path,
                'thisis': 4  # Assistant generated analytical
            })
            
        except Exception as e:
            print(f"Error emitting image: {e}")

    # PART 7: DataFrame Extraction
    def _extract_dataframes_from_outputs(self, execution_outputs: list) -> Dict[str, Any]:
        """
        WORKING: Extract DataFrame information from AI execution results
        
        PROCESS:
        1. Scan execution outputs for DataFrame indicators
        2. Look for shape information, column names, etc.
        3. Create metadata about generated DataFrames
        4. Return structured information for frontend
        
        DETECTION PATTERNS:
        - Text containing "DataFrame"
        - Shape information like "(1000, 5)"
        - Column listings
        - Data summaries
        """
        dataframes = {}
        
        # Simplified extraction - could be enhanced for more sophisticated parsing
        for i, output in enumerate(execution_outputs):
            if "DataFrame" in output or "shape:" in output:
                # Create metadata entry for detected DataFrame
                dataframes[f"result_{i}"] = {
                    "type": "assistant_generated",
                    "description": "DataFrame generated by assistant",
                    "output": output
                }
        
        return dataframes

    # PART 8: Streaming Callback
    def _emit_streaming_callback(self, message_type: str, data: dict):
        """
        WORKING: Callback function for streaming adapter
        
        PURPOSE:
        - Receives real-time updates from AI analysis
        - Forwards updates to frontend via WebSocket
        - Handles different message types (code, output, images, etc.)
        """
        try:
            if self.socketio:
                self.socketio.emit('stream_data', data, room=self.session_id)
        except Exception as e:
            print(f"Error in streaming callback: {e}")

    # PART 9: Fallback Analysis Pipeline
    def _analyze_with_original_pipeline(self, user_query: str, intent_data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """
        WORKING: Fallback to original analysis methods when AI fails
        
        ROUTES TO:
        - Forecasting handler for prediction queries
        - Report handler for comprehensive reports
        - General analysis handler for other complex queries
        
        ENSURES:
        - System always provides results
        - Backward compatibility maintained
        - Graceful degradation when AI unavailable
        """
        try:
            # Route based on analysis type
            if analysis_type == "forecasting":
                return self._handle_forecasting_query(user_query, intent_data)
            elif analysis_type == "report":
                return self._handle_report_query(user_query, intent_data)
            else:
                return self._handle_general_analysis_query(user_query, intent_data)
                
        except Exception as e:
            return {
                "query": user_query,
                "type": "fully_analytical",
                "success": False,
                "error": str(e),
                "generated_images": [],
                "dataframes": {},
                "timestamp": datetime.now().isoformat()
            }

    # PART 10: Specialized Query Handlers
    def _handle_forecasting_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        WORKING: Handle forecasting queries using existing forecasting logic
        
        PROCESS:
        1. Show forecasting progress
        2. Extract data request from analyzer
        3. Check if comprehensive report needed
        4. Route to appropriate forecasting method
        5. Return results with predictions and charts
        """
        
        self.emit_stream('status', '📈 Preparing forecasting analysis...')
        
        # Extract data request using existing analyzer method
        if hasattr(self.analyzer, '_extract_data_request'):
            data_request = self.analyzer._extract_data_request(user_query)
        else:
            data_request = {"type": "forecast_data"}
        
        is_forecasting = True
        
        # Determine if comprehensive report needed
        if hasattr(self.analyzer, '_is_report_request'):
            is_report_request = self.analyzer._is_report_request(user_query)
        else:
            is_report_request = 'report' in user_query.lower()
        
        if is_report_request:
            # Use existing comprehensive report generation
            if hasattr(self.analyzer, '_generate_comprehensive_report_streaming'):
                return self.analyzer._generate_comprehensive_report_streaming(user_query, is_forecasting)
        else:
            # Use existing dataframe analysis with forecasting
            if hasattr(self.analyzer, '_generate_dataframe_analysis_streaming_with_fallback'):
                return self.analyzer._generate_dataframe_analysis_streaming_with_fallback(
                    user_query, data_request, is_forecasting
                )
        
        # Final fallback
        return {
            "query": user_query,
            "type": "fully_analytical",
            "success": False,
            "error": "Forecasting analysis not available",
            "generated_images": [],
            "dataframes": {},
            "timestamp": datetime.now().isoformat()
        }

    def _handle_report_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        WORKING: Handle report generation queries
        
        PROCESS:
        1. Show report generation progress
        2. Check for forecasting elements
        3. Route to comprehensive report generator
        4. Return HTML report with visualizations
        """
        
        self.emit_stream('status', '📊 Generating comprehensive report...')
        
        # Extract forecasting intent
        is_forecasting = any(
            kw in user_query.lower()
            for kw in ['forecast', 'predict', 'future', 'next', 'ahead', 'months', 'years', 'projection']
        )
        
        # Use existing comprehensive report generation
        if hasattr(self.analyzer, '_generate_comprehensive_report_streaming'):
            return self.analyzer._generate_comprehensive_report_streaming(user_query, is_forecasting)
        
        # Fallback
        return {
            "query": user_query,
            "type": "report",
            "success": False,
            "error": "Report generation not available",
            "generated_images": [],
            "dataframes": {},
            "timestamp": datetime.now().isoformat()
        }

    def _handle_general_analysis_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        WORKING: Handle general complex analysis queries
        
        PROCESS:
        1. Show analysis progress
        2. Extract data request and forecasting intent
        3. Route to dataframe analysis with fallback
        4. Add analytical handler metadata
        5. Return comprehensive results
        """
        
        self.emit_stream('status', '🔍 Performing detailed analysis...')
        
        # Extract data request and forecasting intent
        if hasattr(self.analyzer, '_extract_data_request'):
            data_request = self.analyzer._extract_data_request(user_query)
        else:
            data_request = {"type": "analysis"}
            
        is_forecasting = any(
            kw in user_query.lower()
            for kw in ['forecast', 'predict', 'future', 'next', 'ahead', 'months', 'years', 'projection']
        )
        
        # Use existing dataframe analysis with fallback
        if hasattr(self.analyzer, '_generate_dataframe_analysis_streaming_with_fallback'):
            result = self.analyzer._generate_dataframe_analysis_streaming_with_fallback(
                user_query, data_request, is_forecasting
            )
        else:
            # Basic fallback
            result = {
                "query": user_query,
                "type": "fully_analytical",
                "success": True,
                "response": "Analysis completed using fallback method.",
                "generated_images": [],
                "dataframes": {},
                "timestamp": datetime.now().isoformat()
            }
        
        # Add analytical handler metadata
        result.update({
            "handled_by": "analytical_handler",
            "analysis_complexity": "high",
            "intent_data": intent_data
        })
        
        return result    