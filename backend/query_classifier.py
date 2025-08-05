from datetime import datetime
import re
from typing import Dict, Any, Tuple

class SmartQueryClassifier:
    """
    FIXED Smart query classifier that properly routes queries to the right handlers.
    
    Key Changes:
    1. Better classification logic
    2. Fixed simple conversational detection
    3. Improved analysis requirement detection
    4. Better report detection
    """
    
    def __init__(self):
        # Simple conversational patterns that should NOT trigger analysis
        self.simple_conversational = [
            r'^(hi|hello|hey)(\s|!|\?)*$',
            r'^(good morning|good afternoon|good evening)(\s|!|\?)*$',
            r'^how are you(\s|!|\?)*$',
            r'^what\'?s up(\s|!|\?)*$',
            r'^(thanks|thank you|ty)(\s|!|\?)*$',
            r'^(bye|goodbye|see you later)(\s|!|\?)*$',
            r'^(yes|yeah|yep|ok|okay)(\s|!|\?)*$',
            r'^(no|nope|nah)(\s|!|\?)*$',
            r'^who are you(\s|!|\?)*$',
            r'^what are you(\s|!|\?)*$',
            r'^(help|need help)(\s|!|\?)*$'
        ]
        
        # Capability questions that need simple responses but can use AI
        self.capability_questions = [
            r'what can you do(\s|!|\?)*$',
            r'what are your capabilities(\s|!|\?)*$',
            r'how can you help(\s|!|\?)*$',
            r'what features do you have(\s|!|\?)*$',
            r'tell me about yourself',
            r'what is this(\s|!|\?)*$',
            r'how does this work(\s|!|\?)*$',
            r'what things can you do(\s|!|\?)*$'
        ]
        
        # Data analysis indicators (require analysis)
        self.analysis_indicators = [
            'analyze', 'analysis', 'data', 'csv', 'dataframe', 'df',
            'plot', 'chart', 'graph', 'visualize', 'visualization', 'show me',
            'statistics', 'stats', 'mean', 'median', 'mode', 'average',
            'correlation', 'regression', 'forecast', 'predict', 'prediction',
            'trend', 'pattern', 'filter', 'group', 'sort', 'calculate',
            'aggregate', 'sum', 'count', 'compare', 'comparison',
            'revenue', 'sales', 'profit', 'performance', 'growth',
            'top', 'bottom', 'best', 'worst', 'highest', 'lowest',
            'insights', 'breakdown', 'distribution'
        ]
        
        # Report indicators (require comprehensive analysis + HTML report)
        self.report_indicators = [
            'report', 'summary report', 'generate report', 'create report',
            'comprehensive report', 'strategic report', 'executive summary',
            'write report', 'full report', 'detailed report', 'analysis report',
            'comprehensive analysis', 'detailed analysis'
        ]
        
        # Quick question indicators (simple data lookup)
        self.quick_question_indicators = [
            'what is', 'what\'s', 'how many', 'how much', 'which', 'when',
            'where', 'who has', 'which has', 'total', 'number of'
        ]
    
    def classify_query(self, query: str, has_data: bool = True) -> Tuple[str, Dict[str, Any]]:
        """
        FIXED classification logic with better routing.
        
        Returns:
        - 'simple_conversational': No analysis needed, use simple response
        - 'capability_question': No analysis needed, but use AI for better response  
        - 'analytical': Requires data analysis
        """
        
        query_clean = query.strip().lower()
        
        # 1. Check for simple conversational patterns (highest priority)
        for pattern in self.simple_conversational:
            if re.match(pattern, query_clean):
                return 'simple_conversational', {
                    'confidence': 'high',
                    'pattern_matched': pattern,
                    'requires_analysis': False,
                    'use_ai': False  # Use simple predefined responses
                }
        
        # 2. Check for capability questions (use AI but no data analysis)
        for pattern in self.capability_questions:
            if re.search(pattern, query_clean):
                return 'capability_question', {
                    'confidence': 'high',
                    'pattern_matched': pattern,
                    'requires_analysis': False,
                    'use_ai': True  # Use AI for better response
                }
        
        # 3. Check for report requests (comprehensive analysis + HTML report)
        report_score = 0
        matched_report_indicators = []
        for indicator in self.report_indicators:
            if indicator in query_clean:
                report_score += 1
                matched_report_indicators.append(indicator)
        
        if report_score > 0:
            return 'analytical', {
                'confidence': 'high',
                'analysis_indicators': matched_report_indicators,
                'requires_analysis': True,
                'analysis_type': 'report',
                'has_data': has_data
            }
        
        # 4. Check for analysis indicators
        analysis_score = 0
        matched_indicators = []
        
        for indicator in self.analysis_indicators:
            if indicator in query_clean:
                analysis_score += 1
                matched_indicators.append(indicator)
        
        # 5. Check for quick question patterns
        quick_question_score = 0
        for indicator in self.quick_question_indicators:
            if indicator in query_clean:
                quick_question_score += 1
        
        # 6. Decision logic
        if analysis_score >= 2:
            # Multiple analysis indicators = complex analysis
            return 'analytical', {
                'confidence': 'high',
                'analysis_indicators': matched_indicators,
                'requires_analysis': True,
                'analysis_type': 'complex',
                'has_data': has_data
            }
        elif analysis_score == 1:
            # Single analysis indicator = could be simple or complex
            if quick_question_score > 0:
                # Quick question + analysis indicator = textual analytical
                return 'analytical', {
                    'confidence': 'medium',
                    'analysis_indicators': matched_indicators,
                    'requires_analysis': True,
                    'analysis_type': 'simple',
                    'has_data': has_data
                }
            else:
                # Single analysis indicator without quick question = complex
                return 'analytical', {
                    'confidence': 'medium',
                    'analysis_indicators': matched_indicators,
                    'requires_analysis': True,
                    'analysis_type': 'complex',
                    'has_data': has_data
                }
        elif quick_question_score > 0 and has_data:
            # Quick question with data available = simple textual analysis
            return 'analytical', {
                'confidence': 'medium',
                'analysis_indicators': [],
                'requires_analysis': True,
                'analysis_type': 'simple',
                'has_data': has_data,
                'reason': 'quick_question_with_data'
            }
        else:
            # No clear indicators = conversational
            return 'simple_conversational', {
                'confidence': 'low',
                'requires_analysis': False,
                'use_ai': True,  # Use AI for better conversational response
                'reason': 'no_clear_analysis_intent'
            }
    
    def should_analyze(self, query: str, has_data: bool = True) -> bool:
        """Simple boolean check if query requires analysis."""
        category, metadata = self.classify_query(query, has_data)
        return metadata.get('requires_analysis', False)
    
    def get_simple_response(self, query: str, category: str) -> str:
        """Get appropriate simple response for non-analytical queries."""
        query_lower = query.lower().strip()
        
        if category == 'simple_conversational':
            if any(greeting in query_lower for greeting in ['hi', 'hello', 'hey']):
                return "Hello! I'm your AI data analyst. I can help you analyze CSV data, create visualizations, and generate insights. Upload a CSV file and ask me questions about your data!"
            
            elif 'how are you' in query_lower:
                return "I'm doing great and ready to help you analyze your data! What would you like to explore in your dataset?"
            
            elif any(thanks in query_lower for thanks in ['thanks', 'thank you']):
                return "You're welcome! I'm here to help with any data analysis questions you have."
            
            elif any(bye in query_lower for bye in ['bye', 'goodbye']):
                return "Goodbye! Thanks for using the data analysis assistant. Come back anytime you need insights from your data!"
            
            elif query_lower in ['yes', 'yeah', 'yep', 'ok', 'okay']:
                return "Great! What would you like to analyze in your data?"
            
            elif query_lower in ['no', 'nope', 'nah']:
                return "No problem! Let me know if you'd like to explore your data in any way."
            
            else:
                return "I'm here to help you analyze your data! You can ask me to create charts, calculate statistics, find trends, or generate reports from your CSV files."
        
        elif category == 'capability_question':
            return """I'm an AI data analyst that can help you with:

• **Data Analysis**: Calculate statistics, find patterns, identify trends
• **Visualizations**: Create charts, graphs, and plots from your data  
• **Forecasting**: Predict future values and trends
• **Reports**: Generate comprehensive analytical reports with HTML output
• **Data Processing**: Clean, filter, and transform your datasets

Just upload a CSV file and ask me questions like:
- "What are the sales trends?"
- "Create a forecast for next 6 months"
- "Show me the top performing products"
- "Generate a comprehensive report"
- "What is the highest revenue?"

What would you like to explore in your data?"""
        
        else:
            return "I can help you analyze your data! What specific insights are you looking for?"
        
      
    def extract_analysis_intent(self, user_query: str, category: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific analysis intent from the classified query."""
        
        intent_data = {
            "category": category,
            "original_query": user_query,
            "timestamp": datetime.now().isoformat(),
            **metadata
        }
        
        if category == "simple_conversational" or category == "capability_question":
            intent_data.update({
                "response_type": "conversational",
                "requires_execution": False,
                "expected_format": "text"
            })
            
        elif category == "analytical":
            # Get analysis type from metadata
            analysis_type = metadata.get('analysis_type', 'general')
            
            if analysis_type == 'report':
                # Report generation
                intent_data.update({
                    "response_type": "report",
                    "requires_execution": True,
                    "expected_format": "html_report",
                    "should_stream": True,
                    "show_code": True,
                    "generate_html": True
                })
            elif analysis_type == 'simple':
                # Simple textual analysis
                query_lower = user_query.lower()
                
                # Determine specific analysis type
                if any(word in query_lower for word in ["highest", "maximum", "max", "largest"]):
                    intent_data["specific_analysis"] = "maximum"
                elif any(word in query_lower for word in ["lowest", "minimum", "min", "smallest"]):
                    intent_data["specific_analysis"] = "minimum"
                elif any(word in query_lower for word in ["average", "mean"]):
                    intent_data["specific_analysis"] = "average"
                elif any(word in query_lower for word in ["sum", "total"]):
                    intent_data["specific_analysis"] = "sum"
                elif any(word in query_lower for word in ["count", "how many", "number of"]):
                    intent_data["specific_analysis"] = "count"
                else:
                    intent_data["specific_analysis"] = "general"
                
                intent_data.update({
                    "response_type": "textual_analytical",
                    "requires_execution": True,
                    "expected_format": "text_with_data",
                    "should_stream": False,
                    "show_code": False
                })
            else:
                # Complex analysis (includes forecasting, visualization, etc.)
                query_lower = user_query.lower()
                
                if any(word in query_lower for word in ["forecast", "predict", "future", "projection"]):
                    intent_data["specific_analysis"] = "forecasting"
                elif any(word in query_lower for word in ["chart", "plot", "graph", "visualize", "show"]):
                    intent_data["specific_analysis"] = "visualization"
                else:
                    intent_data["specific_analysis"] = "general_analysis"
                
                intent_data.update({
                    "response_type": "fully_analytical",
                    "requires_execution": True,
                    "expected_format": "full_analysis",
                    "should_stream": True,
                    "show_code": True
                })
        
        return intent_data