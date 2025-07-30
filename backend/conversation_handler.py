import os
import random
from datetime import datetime
from typing import Dict, Any
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class ConversationHandler:
    """Handles conversational queries with friendly, context-aware responses."""
    
    def __init__(self, session_id: str, socketio=None):
        self.session_id = session_id
        self.socketio = socketio
        self.openai_client = AzureOpenAI(
            api_key=os.getenv('AZUREAPI'),
            api_version=os.getenv('AZUREVERSION'),
            azure_endpoint=os.getenv('AZUREENDPOINT')
        )
        self.MODEL = "gpt-4"
        
        # Predefined responses for common conversational queries
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
    
    def emit_stream(self, message_type: str, data: str):
        """Emit streaming data to the frontend."""
        try:
            if self.socketio:
                self.socketio.emit('stream_data', {
                    'type': message_type,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
        except Exception as e:
            print(f"Error emitting conversational stream: {e}")
    
    def handle_conversational_query(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle conversational queries with appropriate friendly responses.
        
        Args:
            user_query: The user's conversational query
            context: Additional context about the session (CSV info, etc.)
            
        Returns:
            Dict containing the conversational response result
        """
        
        try:
            # Emit that we're handling a conversational query
            self.emit_stream('status', '💬 Understanding your message...')
            
            # Get the conversational response
            response_text = self._generate_conversational_response(user_query, context)
            
            # Emit the response
            self.emit_stream('output', response_text)
            self.emit_stream('completion', 'Response complete!')
            
            # Return result in the expected format
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
    
    def _generate_conversational_response(self, user_query: str, context: Dict[str, Any] = None) -> str:
        """Generate an appropriate conversational response."""
        
        query_lower = user_query.lower().strip()
        
        # Check for quick response patterns first
        if any(greeting in query_lower for greeting in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]):
            response = random.choice(self.quick_responses["greeting"])
            
            # Add context about their data if available
            if context and context.get("has_data"):
                response += f"\n\nI can see you have a dataset with {context.get('shape', ['?', '?'])[0]} rows and {context.get('shape', ['?', '?'])[1]} columns. What would you like to explore?"
            
            return response
        
        elif any(phrase in query_lower for phrase in ["how are you", "how's it going", "what's up"]):
            return random.choice(self.quick_responses["how_are_you"])
        
        elif any(phrase in query_lower for phrase in ["what can you do", "capabilities", "help me", "what do you do"]):
            response = random.choice(self.quick_responses["capabilities"])
            
            # Add specific context if they have data loaded
            if context and context.get("has_data"):
                response += f"\n\nYour current dataset has {context.get('columns', [])} columns. I can analyze any of these for you!"
            
            return response
        
        elif any(phrase in query_lower for phrase in ["thank", "thanks", "appreciate"]):
            return random.choice(self.quick_responses["thanks"])
        
        elif any(phrase in query_lower for phrase in ["bye", "goodbye", "see you", "later"]):
            return random.choice(self.quick_responses["goodbye"])
        
        # For more complex conversational queries, use AI
        else:
            return self._generate_ai_conversational_response(user_query, context)
    
    def _generate_ai_conversational_response(self, user_query: str, context: Dict[str, Any] = None) -> str:
        """Use AI to generate contextual conversational responses."""
        
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
                temperature=0.5,
                # max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI conversational response failed: {e}")
            # Fallback to a generic friendly response
            return "That's an interesting question! I'm here to help you with data analysis. Is there anything specific about your dataset you'd like to explore?"
    
    def _detect_conversation_type(self, user_query: str) -> str:
        """Detect the type of conversational query for better response handling."""
        
        query_lower = user_query.lower().strip()
        
        if any(greeting in query_lower for greeting in ["hi", "hello", "hey"]):
            return "greeting"
        elif any(phrase in query_lower for phrase in ["how are you", "how's it going"]):
            return "wellbeing"
        elif any(phrase in query_lower for phrase in ["what can you do", "capabilities", "help"]):
            return "capabilities"
        elif any(phrase in query_lower for phrase in ["thank", "thanks"]):
            return "gratitude"
        elif any(phrase in query_lower for phrase in ["bye", "goodbye"]):
            return "farewell"
        elif "joke" in query_lower or "funny" in query_lower:
            return "humor"
        else:
            return "general"
    
    def generate_context_aware_greeting(self, has_data: bool = False, filename: str = None, shape: tuple = None) -> str:
        """Generate a context-aware greeting based on user's current state."""
        
        if has_data:
            return f"Hello! I can see you've uploaded '{filename}' with {shape[0]} rows and {shape[1]} columns. I'm ready to help you analyze this data. What would you like to explore first?"
        else:
            return "Hi there! I'm your AI data analyst assistant. Upload a CSV file and I'll help you uncover insights, create visualizations, and answer questions about your data. What can I help you with today?"