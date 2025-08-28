# assistants/query_router.py - UPDATED VERSION

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from assistants.query_check import OpenAIQueryCategorizer, QueryCategory

class RuleBasedQueryRouter:
    """
    NEW: Rule-based query router using OpenAIQueryCategorizer from query_check.py
    
    Replaces the AI-based AssistantQueryRouter with classification logic from query_check.py
    Handles sequential execution for DATA_ANALYSIS_AND_REPORT queries.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.categorizer = OpenAIQueryCategorizer()
        
    def route_query(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route query using OpenAI classification and return routing decision.
        
        Args:
            user_query: The user's question/request
            context: Additional context (has_data, filename, etc.)
            
        Returns:
            Routing decision with assistant type and metadata
        """
        try:
            # Step 1: Classify query using OpenAI
            classification_result = self.categorizer.categorize_query(user_query)
            
            if not classification_result.get('success'):
                logging.error(f"Classification failed: {classification_result.get('reasoning')}")
                return self._get_fallback_decision(user_query, context)
            
            # Step 2: Map category to assistant routing decision
            category_enum = classification_result.get('category_enum')
            category_text = classification_result.get('category', 'conversational')
            
            routing_decision = self._map_category_to_routing(
                category_enum, category_text, user_query, context, classification_result
            )
            
            # Step 3: Add classification metadata
            routing_decision.update({
                'original_query': user_query,
                'timestamp': datetime.now().isoformat(),
                'router_used': True,
                'session_id': self.session_id,
                'context': context or {},
                'classification_result': classification_result,
                'openai_reasoning': classification_result.get('reasoning', 'No reasoning provided'),
                'confidence': classification_result.get('confidence', 0.0)
            })
            
            logging.info(f"🎯 Query classified: {user_query} → {routing_decision.get('assistant_type')} (confidence: {classification_result.get('confidence'):.1%})")
            return routing_decision
            
        except Exception as e:
            logging.error(f"❌ Router error: {e}")
            return self._get_fallback_decision(user_query, context)
    
    def _map_category_to_routing(self, category_enum: QueryCategory, category_text: str, 
                               user_query: str, context: Dict[str, Any], 
                               classification_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map OpenAI classification categories to assistant routing decisions.
        """
        
        if category_enum == QueryCategory.CONVERSATIONAL:
            assistant_type='conversational'
            # data_source_type = context.get('data_source_type', 'files')
            # assistant_type = 'database_analyst' if data_source_type == 'database' else 'conversational'
            
            return {
                'assistant_type': assistant_type,
                'execution_mode': 'single',
                'confidence': 'high',
                'reasoning': 'General conversation or capability question',
                'query_complexity': 'simple',
                'expected_output': 'text',
                'requires_data': False,
                'business_analysis': False
            }
            
        elif category_enum == QueryCategory.SIMPLE_CALCULATION:
        # Check if this is a database session
            # data_source_type = context.get('data_source_type', 'files')
            
            # if data_source_type == 'database':
            #     # For database sessions, simple queries should use database_analyst
            #     return {
            #         'assistant_type': 'database_analyst',
            #         'execution_mode': 'single',
            #         'confidence': 'high',
            #         'reasoning': 'Simple database query requiring SQL execution',
            #         'query_complexity': 'simple',
            #         'expected_output': 'text',
            #         'requires_data': True,
            #         'business_analysis': False,
            #         'database_simple_query': True  # Flag for simple database queries
            #     }
            # else:
                # File-based sessions use textual_analytical as before
                return {
                    'assistant_type': 'textual_analytical',
                    'execution_mode': 'single', 
                    'confidence': 'high',
                    'reasoning': 'Simple calculation or direct data question',
                    'query_complexity': 'simple',
                    'expected_output': 'text',
                    'requires_data': True,
                    'business_analysis': False
                }
                
        elif category_enum == QueryCategory.DATA_ANALYSIS:
            # Check if this is a database session
            data_source_type = context.get('data_source_type', 'files')
            assistant_type = 'database_analyst' if data_source_type == 'database' else 'data_analyst'
            
            return {
                'assistant_type': assistant_type,
                'execution_mode': 'single',
                'confidence': 'high', 
                'reasoning': f'Complex data analysis with visualizations required (data source: {data_source_type})',
                'query_complexity': 'complex',
                'expected_output': 'visualization',
                'requires_data': True,
                'business_analysis': True
            }
            
        elif category_enum == QueryCategory.REPORT:
            data_source_type = context.get('data_source_type', 'files')
            assistant_type = 'database_analyst' if data_source_type == 'database' else 'data_analyst'
            
            return {
                'assistant_type': 'report_generator',
                'execution_mode': 'single',
                'confidence': 'high',
                'reasoning': 'Report generation requested',
                'query_complexity': 'complex',
                'expected_output': 'report',
                'requires_data': True,
                'business_analysis': True
            }
            
        elif category_enum == QueryCategory.DATA_ANALYSIS_AND_REPORT:

            data_source_type = context.get('data_source_type', 'files')
            assistant_type = 'database_analyst' if data_source_type == 'database' else 'data_analyst'
            # 🎯 KEY: Sequential execution mode
            return {
                'assistant_type': assistant_type,  # Start with data analysis
                'execution_mode': 'sequential',    # NEW: Indicates sequential execution
                'sequence': [assistant_type, 'report_generator'],  # NEW: Execution sequence
                'confidence': 'high',
                'reasoning': 'Requires both data analysis and report generation',
                'query_complexity': 'complex',
                'expected_output': 'report_with_analysis',
                'requires_data': True,
                'business_analysis': True,
                'sequential_execution': True  # Flag for enhanced analyzer
            }
            
        else:
            # Unknown category - fallback to conversational
            return {
                'assistant_type': 'conversational',
                'execution_mode': 'single',
                'confidence': 'low',
                'reasoning': f'Unknown category: {category_text}, defaulting to conversational',
                'query_complexity': 'simple',
                'expected_output': 'text',
                'requires_data': False,
                'business_analysis': False,
                'fallback_used': True
            }
    
    def _get_fallback_decision(self, user_query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide fallback routing decision when classification fails.
        """
        query_lower = user_query.lower().strip()
        
        # Simple rule-based fallback
        if any(greeting in query_lower for greeting in ['hi', 'hello', 'hey', 'how are you']):
            assistant_type = 'conversational'
            reasoning = 'Greeting detected in fallback'
        elif any(calc in query_lower for calc in ['what is', 'how many', 'total', 'count']):
            assistant_type = 'textual_analytical'
            reasoning = 'Simple question detected in fallback'
        elif any(report in query_lower for report in ['report', 'summary', 'comprehensive']):
            assistant_type = 'report_generator'
            reasoning = 'Report request detected in fallback'
        else:
            assistant_type = 'data_analyst'
            reasoning = 'Default to data analysis in fallback'
        
        return {
            'assistant_type': assistant_type,
            'execution_mode': 'single',
            'confidence': 'low',
            'reasoning': reasoning,
            'query_complexity': 'moderate',
            'expected_output': 'text',
            'requires_data': True,
            'business_analysis': False,
            'fallback_used': True,
            'original_query': user_query,
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'context': context or {}
        }

class EnhancedQueryClassifier:
    """
    UPDATED: Enhanced query classifier that uses RuleBasedQueryRouter
    
    Maintains compatibility with existing code while using the new router.
    """
    
    def __init__(self, assistant_manager=None, thread_manager=None):
        self.assistant_manager = assistant_manager
        self.thread_manager = thread_manager
        self.routers = {}  # Store routers per session
        
    def classify_query(self, query: str, has_data: bool = True, session_id: str = None, 
                      context: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Classify query using rule-based routing with OpenAI classification.
        
        Returns:
        - category: For backward compatibility ('conversational' or 'analytical')
        - metadata: Enhanced metadata from OpenAI classification
        """
        
        if session_id:
            # Get or create router for this session
            if session_id not in self.routers:
                self.routers[session_id] = RuleBasedQueryRouter(session_id)
            
            router = self.routers[session_id]
            
            # Prepare context
            routing_context = context or {}
            routing_context.update({
                'has_data': has_data,
                'session_id': session_id
            })
            
            # Get routing decision
            decision = router.route_query(query, routing_context)
            
            # Convert to old format for compatibility
            assistant_type = decision.get("assistant_type", "conversational")
            
            # Map new categories to old categories for compatibility
            if assistant_type == "conversational":
                old_category = "conversational"
                analysis_type = "conversational"
            else:
                old_category = "analytical"
                if assistant_type == "textual_analytical":
                    analysis_type = "simple"
                elif assistant_type == "data_analyst":
                    analysis_type = "complex"
                elif assistant_type == "report_generator":
                    analysis_type = "report"
                else:
                    analysis_type = "general"
            
            # Enhanced metadata with OpenAI classification
            enhanced_metadata = {
                'confidence': decision.get('confidence', 'medium'),
                'requires_analysis': assistant_type != "conversational",
                'analysis_type': analysis_type,
                'has_data': has_data,
                'assistant_type': assistant_type,
                'query_complexity': decision.get('query_complexity', 'moderate'),
                'expected_output': decision.get('expected_output', 'text'),
                'ai_reasoning': decision.get('openai_reasoning', ''),
                'router_used': True,
                'execution_mode': decision.get('execution_mode', 'single'),  # NEW
                'sequential_execution': decision.get('sequential_execution', False),  # NEW
                'sequence': decision.get('sequence', []),  # NEW
                'original_decision': decision
            }
            
            logging.info(f"🎯 OpenAI Classification: '{query}' → {assistant_type} ({analysis_type})")
            return old_category, enhanced_metadata
            
        else:
            # Fallback to simple classification if no session_id
            return self._simple_classification(query, has_data)
    
    def _simple_classification(self, query: str, has_data: bool) -> Tuple[str, Dict[str, Any]]:
        """Simple fallback classification when no session ID is provided"""
        query_lower = query.lower().strip()
        
        if any(pattern in query_lower for pattern in ['hi', 'hello', 'how are you']):
            return 'conversational', {
                'confidence': 'medium',
                'requires_analysis': False,
                'analysis_type': 'conversational',
                'has_data': has_data,
                'assistant_type': 'conversational',
                'execution_mode': 'single',
                'sequential_execution': False,
                'fallback_used': True
            }
        else:
            return 'analytical', {
                'confidence': 'low',
                'requires_analysis': True,
                'analysis_type': 'general',
                'has_data': has_data,
                'assistant_type': 'data_analyst',
                'execution_mode': 'single',
                'sequential_execution': False,
                'fallback_used': True
            }
    
    def cleanup_session(self, session_id: str):
        """Clean up router for a specific session"""
        if session_id in self.routers:
            del self.routers[session_id]
            logging.info(f"🧹 Cleaned up router for session: {session_id}")
    
    def cleanup_all(self):
        """Clean up all routers"""
        for session_id in list(self.routers.keys()):
            self.cleanup_session(session_id)