import os
import json
from datetime import datetime
from typing import Dict, Any, Tuple
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class QueryClassifier:
    """Classifies user queries into conversational, textual+analytical, or fully analytical categories."""
    
    def __init__(self):
        self.openai_client = AzureOpenAI(
            api_key=os.getenv('AZUREAPI'),
            api_version=os.getenv('AZUREVERSION'),
            azure_endpoint=os.getenv('AZUREENDPOINT')
        )
        self.MODEL = "gpt-4"
    
    def classify_query(self, user_query: str, csv_info: str = "") -> Tuple[str, Dict[str, Any]]:
        """
        Classify a user query into one of three categories:
        1. 'conversational' - General chat, greetings, jokes, etc.
        2. 'textual_analytical' - Simple questions requiring data analysis with text response
        3. 'fully_analytical' - Complex analysis requiring reports, forecasting, visualizations
        
        Returns:
            Tuple of (category, metadata)
        """
        
        classification_prompt = f"""
You are a query classifier for a CSV data analysis system. Classify the following user query into exactly ONE of these three categories:

**CATEGORY 1: conversational**
- General greetings, casual chat, jokes, system capabilities questions
- Examples: "Hi, how are you?", "Tell me a joke", "What can you do?", "Hello"
- Return: Just friendly conversational response needed

**CATEGORY 2: textual_analytical** 
- Simple data questions requiring analysis but expecting a brief text answer
- Examples: "What is the highest revenue?", "Tell me the average age", "How many rows are there?"
- Return: Generate code, run analysis, provide concise text answer

**CATEGORY 3: fully_analytical**
- Complex analysis requiring detailed reports, forecasting, multiple visualizations
- Examples: "Generate a 5-year forecast", "Create a report", "Analyze trends and patterns"
- Return: Full analysis with streaming output and detailed visualizations

CSV Data Context:
{csv_info}

User Query: "{user_query}"

Respond with a JSON object containing:
{{
    "category": "conversational|textual_analytical|fully_analytical",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of classification",
    "expected_output": "What type of output is expected",
    "requires_data": true/false,
    "complexity": "low|medium|high"
}}

Be strict about classification:
- Only use "conversational" for genuine chat/social queries
- Use "textual_analytical" for simple data questions wanting quick answers
- Use "fully_analytical" for complex analysis, reports, forecasting, or multiple insights
"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert query classifier for data analysis systems."},
                    {"role": "user", "content": classification_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_text = response_text
            
            try:
                classification_result = json.loads(json_text)
                category = classification_result.get("category", "fully_analytical")
                
                # Validate category
                valid_categories = ["conversational", "textual_analytical", "fully_analytical"]
                if category not in valid_categories:
                    category = "fully_analytical"  # Default fallback
                
                return category, classification_result
                
            except json.JSONDecodeError:
                print(f"⚠️ Failed to parse classification JSON: {json_text}")
                return "fully_analytical", {
                    "category": "fully_analytical",
                    "confidence": 0.5,
                    "reasoning": "Classification parsing failed, defaulting to full analysis",
                    "expected_output": "Complete analysis",
                    "requires_data": True,
                    "complexity": "high"
                }
        
        except Exception as e:
            print(f"❌ Query classification error: {str(e)}")
            # Default to fully analytical on error
            return "fully_analytical", {
                "category": "fully_analytical", 
                "confidence": 0.5,
                "reasoning": f"Classification failed: {str(e)}",
                "expected_output": "Complete analysis",
                "requires_data": True,
                "complexity": "high"
            }
    
    def is_conversational_query(self, user_query: str) -> bool:
        """Quick check if query is likely conversational without full classification."""
        conversational_keywords = [
            "hi", "hello", "hey", "how are you", "what's up", "good morning",
            "good afternoon", "good evening", "thanks", "thank you", "bye",
            "goodbye", "joke", "funny", "what can you do", "help me",
            "who are you", "what is your name", "nice to meet you"
        ]
        
        query_lower = user_query.lower().strip()
        
        # Check for exact matches or keywords
        for keyword in conversational_keywords:
            if keyword in query_lower:
                return True
        
        # Check for short greetings
        if len(query_lower.split()) <= 3 and any(greeting in query_lower for greeting in ["hi", "hello", "hey"]):
            return True
            
        return False
    
    def extract_analysis_intent(self, user_query: str, category: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific analysis intent from the classified query."""
        
        intent_data = {
            "category": category,
            "original_query": user_query,
            "timestamp": datetime.now().isoformat(),
            **metadata
        }
        
        if category == "conversational":
            intent_data.update({
                "response_type": "conversational",
                "requires_execution": False,
                "expected_format": "text"
            })
            
        elif category == "textual_analytical":
            # Extract specific data intent
            query_lower = user_query.lower()
            
            # Determine what type of simple analysis is needed
            if any(word in query_lower for word in ["highest", "maximum", "max", "largest"]):
                intent_data["analysis_type"] = "maximum"
            elif any(word in query_lower for word in ["lowest", "minimum", "min", "smallest"]):
                intent_data["analysis_type"] = "minimum"
            elif any(word in query_lower for word in ["average", "mean"]):
                intent_data["analysis_type"] = "average"
            elif any(word in query_lower for word in ["sum", "total"]):
                intent_data["analysis_type"] = "sum"
            elif any(word in query_lower for word in ["count", "how many", "number of"]):
                intent_data["analysis_type"] = "count"
            else:
                intent_data["analysis_type"] = "general"
            
            intent_data.update({
                "response_type": "textual_analytical",
                "requires_execution": True,
                "expected_format": "text_with_data",
                "should_stream": False,
                "show_code": False
            })
            
        else:  # fully_analytical
            # Determine if it's forecasting, reporting, or general analysis
            query_lower = user_query.lower()
            
            if any(word in query_lower for word in ["forecast", "predict", "future", "projection"]):
                intent_data["analysis_type"] = "forecasting"
            elif any(word in query_lower for word in ["report", "summary", "comprehensive"]):
                intent_data["analysis_type"] = "report"
            else:
                intent_data["analysis_type"] = "general_analysis"
            
            intent_data.update({
                "response_type": "fully_analytical",
                "requires_execution": True,
                "expected_format": "full_analysis",
                "should_stream": True,
                "show_code": True
            })
        
        return intent_data