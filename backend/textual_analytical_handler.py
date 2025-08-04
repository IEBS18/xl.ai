import os
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class TextualAnalyticalHandler:
    """Handles simple analytical queries that require code execution but return concise text responses."""
    
    def __init__(self, session_id: str, df: pd.DataFrame, socketio=None, csv_info: str = ""):
        self.session_id = session_id
        self.df = df
        self.socketio = socketio
        self.csv_info = csv_info
        self.openai_client = AzureOpenAI(
            api_key=os.getenv('AZUREAPI'),
            api_version=os.getenv('AZUREVERSION'),
            azure_endpoint=os.getenv('AZUREENDPOINT')
        )
        self.MODEL = os.getenv("AZUREMODEL")
        # self.MODEL='gpt-4o-mini'
    
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
            print(f"Error emitting textual analytical stream: {e}")
    
    def handle_textual_analytical_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle simple analytical queries that need quick text responses.
        
        Args:
            user_query: The user's question about the data
            intent_data: Classification metadata about the query
            
        Returns:
            Dict containing the analysis result with text response
        """
        
        try:
            self.emit_stream('status', '🔍 Analyzing your question...')
            
            # Generate focused Python code for the specific question
            analysis_code = self._generate_focused_analysis_code(user_query, intent_data)
            
            if not analysis_code:
                return self._create_error_result(user_query, "Could not generate analysis code for your question.")
            
            self.emit_stream('status', '⚙️ Running analysis...')
            
            # Execute the code
            execution_result = self._execute_analysis_code(analysis_code)
            
            if not execution_result.get("success"):
                # Try a simplified approach
                return self._handle_fallback_analysis(user_query, intent_data)
            
            # Generate human-readable response from the results
            text_response = self._generate_text_response(user_query, execution_result, intent_data)
            
            self.emit_stream('output', text_response)
            self.emit_stream('completion', 'Analysis complete!')
            
            return {
                "query": user_query,
                "type": "textual_analytical",
                "success": True,
                "response": text_response,
                "generated_code": analysis_code,
                "execution_result": execution_result,
                "generated_images": [],  # Usually no images for simple queries
                "dataframes": {},
                "analysis_type": intent_data.get("analysis_type", "general"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error in textual analysis: {str(e)}"
            print(error_msg)
            print(f"Traceback: {traceback.format_exc()}")
            self.emit_stream('error', error_msg)
            
            return self._create_error_result(user_query, str(e))
    
    def _generate_focused_analysis_code(self, user_query: str, intent_data: Dict[str, Any]) -> str:
        """Generate Python code focused on answering the specific question concisely."""
        
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

Example code patterns:
- For maximum: result = f"The highest value is {{df['column'].max()}}"
- For average: result = f"The average is {{df['column'].mean():.2f}}"
- For count: result = f"There are {{len(df)}} total records"

Generate clean, executable Python code that stores the answer in 'result':
"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are a Python code generator. Generate concise code that answers data questions directly. Always store the final answer in a 'result' variable."},
                    {"role": "user", "content": code_generation_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            generated_code = response.choices[0].message.content.strip()
            
            # Clean up the code
            if "```python" in generated_code:
                generated_code = generated_code.split("```python")[1].split("```")[0].strip()
            elif "```" in generated_code:
                generated_code = generated_code.split("```")[1].split("```")[0].strip()
            
            return generated_code
            
        except Exception as e:
            print(f"Code generation failed: {e}")
            return ""
    
    def _execute_analysis_code(self, code: str) -> Dict[str, Any]:
        """Execute the generated analysis code safely."""
        
        try:
            # Set up execution environment
            exec_globals = {
                'df': self.df,
                'pd': pd,
                'np': np,
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
                "traceback": traceback.format_exc(),
                "code": code
            }
    
    def _generate_text_response(self, user_query: str, execution_result: Dict[str, Any], intent_data: Dict[str, Any]) -> str:
        """Generate a human-readable text response from the analysis results."""
        
        result = execution_result.get("result", "")
        
        # If result is already a string, use it directly
        if isinstance(result, str):
            return result
        
        # If result is a number or other data type, format it nicely
        analysis_type = intent_data.get("analysis_type", "general")
        
        try:
            if analysis_type == "maximum":
                return f"📈 {result}"
            elif analysis_type == "minimum":
                return f"📉 {result}"
            elif analysis_type == "average":
                return f"📊 {result}"
            elif analysis_type == "sum":
                return f"🔢 {result}"
            elif analysis_type == "count":
                return f"📋 {result}"
            else:
                return f"✅ {result}"
                
        except:
            return str(result)
    
    def _handle_fallback_analysis(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analysis when the main approach fails - use direct pandas operations."""
        
        try:
            self.emit_stream('status', '🔄 Trying alternative analysis approach...')
            
            analysis_type = intent_data.get("analysis_type", "general")
            query_lower = user_query.lower()
            
            # Try to extract column names from the query
            potential_columns = []
            for col in self.df.columns:
                if col.lower() in query_lower:
                    potential_columns.append(col)
            
            # Simple fallback analyses based on query patterns
            if analysis_type == "count" or "how many" in query_lower:
                result = f"The dataset contains {len(self.df)} rows."
                
            elif analysis_type == "maximum" and potential_columns:
                col = potential_columns[0]
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    max_val = self.df[col].max()
                    result = f"The maximum value in {col} is {max_val}"
                else:
                    result = f"Cannot find maximum for non-numeric column {col}"
                    
            elif analysis_type == "minimum" and potential_columns:
                col = potential_columns[0]
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    min_val = self.df[col].min()
                    result = f"The minimum value in {col} is {min_val}"
                else:
                    result = f"Cannot find minimum for non-numeric column {col}"
                    
            elif analysis_type == "average" and potential_columns:
                col = potential_columns[0]
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    avg_val = self.df[col].mean()
                    result = f"The average value in {col} is {avg_val:.2f}"
                else:
                    result = f"Cannot calculate average for non-numeric column {col}"
                    
            else:
                # Generic response
                result = f"I found {len(self.df)} rows and {len(self.df.columns)} columns in your dataset. Could you please rephrase your question to be more specific?"
            
            self.emit_stream('output', result)
            self.emit_stream('completion', 'Fallback analysis complete!')
            
            return {
                "query": user_query,
                "type": "textual_analytical",
                "success": True,
                "response": result,
                "generated_code": "# Fallback analysis used",
                "execution_result": {"success": True, "result": result},
                "generated_images": [],
                "dataframes": {},
                "analysis_type": analysis_type,
                "fallback_used": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return self._create_error_result(user_query, f"Fallback analysis failed: {str(e)}")
    
    def _create_error_result(self, user_query: str, error_message: str) -> Dict[str, Any]:
        """Create a standardized error result."""
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
        
    def _detect_numeric_columns(self) -> list:
        """Detect numeric columns in the dataset."""
        return list(self.df.select_dtypes(include=[np.number]).columns)
    
    def _detect_categorical_columns(self) -> list:
        """Detect categorical columns in the dataset."""
        return list(self.df.select_dtypes(include=['object', 'category']).columns)
    
    def _get_column_info(self, column_name: str) -> Dict[str, Any]:
        """Get information about a specific column."""
        if column_name not in self.df.columns:
            return {"exists": False}
        
        col_data = self.df[column_name]
        info = {
            "exists": True,
            "dtype": str(col_data.dtype),
            "null_count": col_data.isnull().sum(),
            "unique_count": col_data.nunique()
        }
        
        if pd.api.types.is_numeric_dtype(col_data):
            info.update({
                "is_numeric": True,
                "min": col_data.min(),
                "max": col_data.max(),
                "mean": col_data.mean(),
                "median": col_data.median()
            })
        else:
            info.update({
                "is_numeric": False,
                "most_common": col_data.mode().iloc[0] if len(col_data.mode()) > 0 else None
            })
        
        return info