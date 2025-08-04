import os
import json
import traceback
from datetime import datetime
from typing import Dict, Any
import pandas as pd
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class AnalyticalHandler:
    """Handles complex analytical queries requiring full analysis with streaming and visualizations."""
    
    def __init__(self, session_id: str, analyzer_instance, socketio=None):
        self.session_id = session_id
        self.analyzer = analyzer_instance  # Reference to the original StreamingAnalyzer
        self.socketio = socketio
        self.df = analyzer_instance.df
        self.csv_info = analyzer_instance.csv_info
        self.generated_images = analyzer_instance.generated_images
        self.openai_client = AzureOpenAI(
            api_key=os.getenv('AZUREAPI'),
            api_version=os.getenv('AZUREVERSION'),
            azure_endpoint=os.getenv('AZUREENDPOINT'),
            # azure_model=os.getenv('AZURE_OPENAI_MODEL')
        )
        self.MODEL =os.getenv('AZUREMODEL')
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
            print(f"Error emitting analytical stream: {e}")
    
    def handle_fully_analytical_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle complex analytical queries using the existing full analysis pipeline.
        
        Args:
            user_query: The user's complex analysis request
            intent_data: Classification metadata about the query
            
        Returns:
            Dict containing the full analysis result
        """
        
        try:
            self.emit_stream('status', f"🔬 Starting comprehensive analysis for: {user_query}")
            
            # Extract analysis details from intent
            analysis_type = intent_data.get("analysis_type", "general_analysis")
            
            # Use the existing analysis pipeline from the original StreamingAnalyzer
            if analysis_type == "forecasting":
                return self._handle_forecasting_query(user_query, intent_data)
            elif analysis_type == "report":
                return self._handle_report_query(user_query, intent_data)
            else:
                return self._handle_general_analysis_query(user_query, intent_data)
                
        except Exception as e:
            error_msg = f"Error in full analysis: {str(e)}"
            print(error_msg)
            print(f"Traceback: {traceback.format_exc()}")
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
    
    def _handle_forecasting_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle forecasting queries using existing forecasting logic."""
        
        self.emit_stream('status', '📈 Preparing forecasting analysis...')
        
        # Extract data request using existing analyzer method
        data_request = self.analyzer._extract_data_request(user_query)
        is_forecasting = True
        
        # Determine if a comprehensive report is needed
        is_report_request = self.analyzer._is_report_request(user_query)
        
        if is_report_request:
            # Use existing comprehensive report generation
            return self.analyzer._generate_comprehensive_report_streaming(user_query, is_forecasting)
        else:
            # Use existing dataframe analysis with forecasting
            return self.analyzer._generate_dataframe_analysis_streaming_with_fallback(
                user_query, data_request, is_forecasting
            )
    
    def _handle_report_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report generation queries using existing report logic."""
        
        self.emit_stream('status', '📊 Generating comprehensive report...')
        
        # Extract forecasting intent
        is_forecasting = any(
            kw in user_query.lower()
            for kw in ['forecast', 'predict', 'future', 'next', 'ahead', 'months', 'years', 'projection']
        )
        
        # Use existing comprehensive report generation
        return self.analyzer._generate_comprehensive_report_streaming(user_query, is_forecasting)
    
    def _handle_general_analysis_query(self, user_query: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general complex analysis queries using existing analysis logic."""
        
        self.emit_stream('status', '🔍 Performing detailed analysis...')
        
        # Extract data request and forecasting intent
        data_request = self.analyzer._extract_data_request(user_query)
        is_forecasting = any(
            kw in user_query.lower()
            for kw in ['forecast', 'predict', 'future', 'next', 'ahead', 'months', 'years', 'projection']
        )
        
        # Use existing dataframe analysis with fallback
        result = self.analyzer._generate_dataframe_analysis_streaming_with_fallback(
            user_query, data_request, is_forecasting
        )
        
        # Add analytical handler metadata
        result.update({
            "handled_by": "analytical_handler",
            "analysis_complexity": "high",
            "intent_data": intent_data
        })
        
        return result
    
    def _enhance_analysis_with_context(self, user_query: str, base_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance the analysis result with additional context and insights."""
        
        try:
            # Check if we should add additional insights
            if base_result.get("success") and base_result.get("dataframes"):
                
                self.emit_stream('status', '💡 Generating additional insights...')
                
                # Generate summary insights using AI
                insights = self._generate_analysis_insights(user_query, base_result)
                
                if insights:
                    base_result["ai_insights"] = insights
                    self.emit_stream('output', f"\n🔍 **Key Insights:**\n{insights}")
            
            return base_result
            
        except Exception as e:
            print(f"Failed to enhance analysis with context: {e}")
            return base_result
    
    def _generate_analysis_insights(self, user_query: str, analysis_result: Dict[str, Any]) -> str:
        """Generate AI-powered insights about the analysis results."""
        
        try:
            # Prepare context about the analysis
            dataframes = analysis_result.get("dataframes", {})
            execution_output = analysis_result.get("execution_result", {}).get("output", "")
            
            context_summary = f"""
Analysis performed for query: "{user_query}"

Dataset information:
- Shape: {self.df.shape}
- Columns: {list(self.df.columns)[:10]}{'...' if len(self.df.columns) > 10 else ''}

Analysis results:
- Generated {len(dataframes)} result DataFrames
- Execution output: {execution_output[:500]}{'...' if len(execution_output) > 500 else ''}

Generated {len(analysis_result.get('generated_images', []))} visualizations
"""
            
            insight_prompt = f"""
Based on the data analysis performed, provide 2-3 key business insights or takeaways that would be valuable to the user. Focus on:

1. What the data reveals about patterns or trends
2. Actionable insights for decision making  
3. Notable findings or anomalies

Keep insights concise and business-focused. Format as bullet points.

Context:
{context_summary}

Key Insights:
"""
            
            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are a business analyst providing key insights from data analysis results."},
                    {"role": "user", "content": insight_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Failed to generate analysis insights: {e}")
            return ""
    
    def _check_stop_signal(self):
        """Check for stop signals - delegate to analyzer."""
        if hasattr(self.analyzer, 'check_stop_signal'):
            self.analyzer.check_stop_signal()
    
    def _create_enhanced_analysis_result(self, base_result: Dict[str, Any], intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance the base analysis result with additional metadata."""
        
        enhanced_result = base_result.copy()
        enhanced_result.update({
            "handler_type": "analytical",
            "query_complexity": intent_data.get("complexity", "high"),
            "analysis_intent": intent_data.get("analysis_type", "general"),
            "processing_timestamp": datetime.now().isoformat(),
            "metadata": {
                "classification_confidence": intent_data.get("confidence", 0.0),
                "expected_output": intent_data.get("expected_output", "full_analysis"),
                "requires_streaming": True,
                "complexity_level": "high"
            }
        })
        
        return enhanced_result