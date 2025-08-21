# assistants/query_router.py

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from openai import AzureOpenAI
# from assistant_manager import AssistantManager
# from thread_manager import ThreadManager
class AssistantQueryRouter:
    """
    NEW: Assistant-based query router that replaces hardcoded classification.
    
    This router uses an OpenAI Assistant to intelligently analyze queries and 
    decide which specific assistant should handle the request.
    """
    
    def __init__(self, assistant_manager, thread_manager, session_id: str):
        self.assistant_manager = assistant_manager
        self.thread_manager = thread_manager
        self.session_id = session_id
        self.router_assistant_id = None
        
    def get_router_assistant_config(self) -> Dict[str, Any]:
        """Configuration for the router assistant"""
        return {
            "name": "Query Router Assistant",
            "instructions": self._get_router_instructions(),
            "tools": [],  # No tools needed, just decision making
            "model": os.getenv("AZUREMODEL", "gpt-4")
        }
    
    def _get_router_instructions(self) -> str:
        """Enhanced instructions for the router assistant to classify and route queries with focus on intent detection"""
        return """You are an EXPERT QUERY ROUTER for a comprehensive data analysis platform. Your PRIMARY GOAL is to distinguish between users who want SPECIFIC VALUES/NUMBERS versus those who want to UNDERSTAND PATTERNS/RELATIONSHIPS.

🎯 CORE DECISION FRAMEWORK:

**USER INTENT ANALYSIS - WHAT DOES THE USER WANT?**
1. **SPECIFIC VALUE/NUMBER** → textual_analytical
   - User wants a direct answer: "$2.5M", "150 customers", "23% growth"
   - Question can be answered with a single number or simple fact
   - Focus is on "what is" rather than "why" or "how"

2. **UNDERSTANDING PATTERNS** → data_analyst  
   - User wants to understand relationships, factors, or patterns
   - Requires exploring data to find insights, correlations, trends
   - Focus is on "why", "how", "what factors", "what patterns"

3. **FORMATTED REPORT** → report_generator
   - User explicitly wants a comprehensive document or report
   - Needs professional formatting and multiple insights combined

4. **CASUAL CONVERSATION** → conversational
   - Greetings, capability questions, general chat

📊 AVAILABLE SPECIALIST ASSISTANTS:

**textual_analytical** - VALUE-SEEKING QUERIES
✅ Perfect for: Direct questions wanting specific numbers/values
🎯 Intent: User wants "THE ANSWER" (a number, total, count, name, etc.)
📝 Examples:
   - "What is the total sales?" → Wants: "$2.5M" 
   - "How many customers?" → Wants: "150 customers"
   - "What's the highest revenue?" → Wants: "$45,000"
   - "Which product sold most?" → Wants: "Product A"
🔑 KEY INDICATORS: "what is", "how many", "total", "highest", "lowest", "which", "when"

**data_analyst** - PATTERN-SEEKING QUERIES  
✅ Perfect for: Understanding relationships, factors, trends, patterns
🎯 Intent: User wants to UNDERSTAND something complex about their data
📝 Examples:
   - "What factors affect sales?" → Wants: Analysis of multiple variables
   - "Analyze pricing trends" → Wants: Pattern identification over time
   - "Why did revenue drop?" → Wants: Root cause analysis
   - "How do regions compare?" → Wants: Comparative analysis
🔑 KEY INDICATORS: "factors", "why", "how", "analyze", "understand", "patterns", "trends", "compare", "relationship"

**report_generator** - COMPREHENSIVE REPORTING
✅ Perfect for: Formatted business reports and documents
🎯 Intent: User wants a professional document with multiple insights
📝 Examples: "Generate report", "Create executive summary", "Comprehensive analysis"

**conversational** - NON-ANALYTICAL INTERACTION
✅ Perfect for: Greetings, capability questions, general chat
📝 Examples: "Hi", "What can you do?", "How are you?"

🚨 CRITICAL DISTINCTION - VALUE vs PATTERN:

❌ WRONG: "What is the total sales?" → data_analyst (This wants a VALUE, not analysis!)
✅ RIGHT: "What is the total sales?" → textual_analytical (User wants the number)

❌ WRONG: "Analyze sales factors" → textual_analytical (This wants UNDERSTANDING!)  
✅ RIGHT: "Analyze sales factors" → data_analyst (User wants to understand patterns)

⚡ ENHANCED DECISION TREE:

1. **Is it casual conversation?** → conversational
2. **Does user want a specific value/number?** 
   - Look for: "what is", "total", "how many", "highest", "which"
   - If YES → textual_analytical
3. **Does user want to understand patterns/relationships?**
   - Look for: "analyze", "factors", "why", "how", "understand", "patterns"  
   - If YES → data_analyst
4. **Does user want a comprehensive report?** → report_generator
5. **Default** → conversational

🧠 ENHANCED VALIDATION CHECKS:

**VALUE-SEEKING PATTERNS** (→ textual_analytical):
- Questions starting with "What is", "How many", "Which", "When"
- Requests for totals, counts, maximums, minimums, averages
- Single-fact requests that can be answered directly
- Length typically < 15 words

**PATTERN-SEEKING PATTERNS** (→ data_analyst):
- Questions about "factors", "variables", "relationships", "correlations"
- Requests to "analyze", "understand", "explore", "investigate"
- Business case studies with context and objectives
- Complex queries requiring multi-step analysis
- Length typically > 20 words or contains business context

OUTPUT FORMAT - Return ONLY valid JSON:
{
    "assistant_type": "conversational|textual_analytical|data_analyst|report_generator",
    "confidence": "high|medium|low", 
    "reasoning": "Brief explanation focusing on user intent (max 40 words)",
    "user_intent": "value_seeking|pattern_seeking|reporting|conversational",
    "query_complexity": "simple|moderate|complex",
    "expected_output": "text|data|visualization|report|modeling",
    "requires_data": true|false,
    "keywords_detected": ["key", "words", "that", "influenced", "decision"]
}

🎯 REMEMBER: Focus on USER INTENT - do they want a specific answer or do they want to understand something complex about their data?"""

    def route_query(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route a user query to the appropriate assistant using AI decision making with enhanced pre-analysis.
        
        Args:
            user_query: The user's question/request
            context: Additional context (has_data, filename, etc.)
            
        Returns:
            Routing decision with assistant type and metadata
        """
        try:
            # Create router assistant if needed
            if not self.router_assistant_id:
                self.router_assistant_id = self._create_router_assistant()
            
            # Perform pre-query analysis
            pre_analysis = self._enhanced_query_analysis(user_query, context)
            
            # Prepare routing query with enhanced context
            routing_query = self._prepare_routing_query(user_query, context, pre_analysis)
            
            # Get routing decision from assistant
            routing_result = self.assistant_manager.run_assistant_analysis(
                self.thread_manager.create_or_get_thread(f"{self.session_id}_router"),
                routing_query
            )
            
            if routing_result.get("success"):
                # Parse assistant's decision
                decision = self._parse_routing_decision(routing_result.get("response_content", ""))
                
                # Validate and potentially correct the decision
                validated_decision = self._validate_and_correct_decision(decision, user_query, pre_analysis)
                
                # Add metadata
                validated_decision.update({
                    "original_query": user_query,
                    "timestamp": datetime.now().isoformat(),
                    "router_used": True,
                    "session_id": self.session_id,
                    "context": context or {},
                    "pre_analysis": pre_analysis
                })
                
                logging.info(f"🧭 Router decision: {user_query} → {validated_decision.get('assistant_type')} (confidence: {validated_decision.get('confidence')})")
                return validated_decision
            else:
                # Fallback to simple classification
                return self._fallback_classification(user_query, context)
                
        except Exception as e:
            logging.error(f"❌ Router error: {e}")
            return self._fallback_classification(user_query, context)
    
    def _enhanced_query_analysis(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform enhanced pre-analysis of the query to provide better context to the AI router.
        
        Analyzes query patterns before sending to AI router to improve classification accuracy.
        """
        import re
        
        query_lower = user_query.lower().strip()
        analysis = {
            "query_length": len(user_query.split()),
            "character_count": len(user_query),
            "question_type": None,
            "value_seeking_indicators": [],
            "pattern_seeking_indicators": [],
            "business_context_indicators": [],
            "complexity_score": 0,
            "intent_prediction": None
        }
        
        # Value-seeking indicators
        value_patterns = [
            r'\bwhat is\b', r'\bwhat\'s\b', r'\bhow many\b', r'\bhow much\b',
            r'\btotal\b', r'\bsum\b', r'\bcount\b', r'\bnumber of\b',
            r'\bhighest\b', r'\blowest\b', r'\bmaximum\b', r'\bminimum\b',
            r'\baverage\b', r'\bmean\b', r'\bwhich\b', r'\bwhen\b'
        ]
        
        for pattern in value_patterns:
            if re.search(pattern, query_lower):
                analysis["value_seeking_indicators"].append(pattern.replace(r'\b', ''))
        
        # Pattern-seeking indicators  
        pattern_patterns = [
            r'\banalyze\b', r'\banalysis\b', r'\bfactor\b', r'\bfactors\b',
            r'\bunderstood?\b', r'\bunderstand\b', r'\bwhy\b', r'\bhow\b',
            r'\btrend\b', r'\btrends\b', r'\bpattern\b', r'\bpatterns\b',
            r'\brelationship\b', r'\brelationships\b', r'\bcorrelation\b',
            r'\bcompare\b', r'\bcomparison\b', r'\bimpact\b', r'\binfluence\b',
            r'\bdriv\w+\b', r'\baffect\b', r'\bvariable\b', r'\bvariables\b'
        ]
        
        for pattern in pattern_patterns:
            if re.search(pattern, query_lower):
                analysis["pattern_seeking_indicators"].append(pattern.replace(r'\b', ''))
        
        # Business context indicators
        business_patterns = [
            r'\bbusiness\b', r'\bmarket\b', r'\bstrateg\w+\b', r'\bpricing\b',
            r'\brevenue\b', r'\bsales\b', r'\bprofit\b', r'\bcustomer\b',
            r'\bperformance\b', r'\bgrowth\b', r'\bcompetit\w+\b',
            r'\bcase study\b', r'\bobjective\b', r'\bgoal\b'
        ]
        
        for pattern in business_patterns:
            if re.search(pattern, query_lower):
                analysis["business_context_indicators"].append(pattern.replace(r'\b', ''))
        
        # Determine question type
        if query_lower.startswith(('what', 'which', 'when', 'where', 'who')):
            analysis["question_type"] = "direct_question"
        elif query_lower.startswith(('how', 'why')):
            analysis["question_type"] = "explanatory_question"
        elif any(word in query_lower for word in ['analyze', 'study', 'examine', 'investigate']):
            analysis["question_type"] = "analytical_request"
        else:
            analysis["question_type"] = "statement_or_command"
        
        # Calculate complexity score
        analysis["complexity_score"] = (
            len(analysis["value_seeking_indicators"]) +
            len(analysis["pattern_seeking_indicators"]) * 2 +  # Pattern seeking gets more weight
            len(analysis["business_context_indicators"]) +
            (analysis["query_length"] // 10)  # Longer queries tend to be more complex
        )
        
        # Predict intent based on analysis
        value_score = len(analysis["value_seeking_indicators"])
        pattern_score = len(analysis["pattern_seeking_indicators"])
        
        if value_score > pattern_score and analysis["question_type"] == "direct_question":
            analysis["intent_prediction"] = "value_seeking"
        elif pattern_score > 0 or analysis["question_type"] in ["explanatory_question", "analytical_request"]:
            analysis["intent_prediction"] = "pattern_seeking"
        elif analysis["query_length"] < 5:
            analysis["intent_prediction"] = "conversational"
        else:
            analysis["intent_prediction"] = "unclear"
        
        # Add data context if available
        if context:
            analysis["has_data"] = context.get('has_data', False)
            analysis["data_columns"] = context.get('columns', [])
            analysis["data_shape"] = context.get('shape', None)
        
        return analysis
    
    def _create_router_assistant(self) -> str:
        """Create the router assistant"""
        try:
            config = self.get_router_assistant_config()
            
            assistant = self.assistant_manager.client.beta.assistants.create(
                name=f"{config['name']} - {self.session_id}",
                instructions=config["instructions"],
                tools=config["tools"],
                model=config["model"],
                metadata={
                    "session_id": self.session_id,
                    "assistant_type": "query_router",
                    "created_at": datetime.now().isoformat()
                }
            )
            
            logging.info(f"✅ Created router assistant: {assistant.id}")
            return assistant.id
            
        except Exception as e:
            logging.error(f"❌ Error creating router assistant: {e}")
            raise
    
    def _prepare_routing_query(self, user_query: str, context: Dict[str, Any] = None, pre_analysis: Dict[str, Any] = None) -> str:
        """Prepare the routing query with enhanced context and pre-analysis for the assistant"""
        
        # Build context information
        context_info = []
        if context:
            has_data = context.get('has_data', False)
            if has_data:
                context_info.append(f"✅ User has uploaded data")
                filename = context.get('filename')
                if filename:
                    context_info.append(f"📁 Filename: {filename}")
                shape = context.get('shape')
                if shape:
                    context_info.append(f"📊 Data shape: {shape[0]:,} rows × {shape[1]} columns")
                columns = context.get('columns', [])
                if columns:
                    context_info.append(f"📋 Columns: {', '.join(columns[:8])}")
                    if len(columns) > 8:
                        context_info.append(f"   ... and {len(columns) - 8} more columns")
            else:
                context_info.append("❌ No data uploaded yet")
        
        # Add pre-analysis insights
        analysis_info = []
        if pre_analysis:
            analysis_info.append(f"📏 Query Length: {pre_analysis.get('query_length', 0)} words")
            analysis_info.append(f"❓ Question Type: {pre_analysis.get('question_type', 'unknown')}")
            analysis_info.append(f"🧠 Intent Prediction: {pre_analysis.get('intent_prediction', 'unclear')}")
            analysis_info.append(f"📊 Complexity Score: {pre_analysis.get('complexity_score', 0)}")
            
            if pre_analysis.get('value_seeking_indicators'):
                analysis_info.append(f"🎯 Value-seeking indicators: {', '.join(pre_analysis['value_seeking_indicators'])}")
            
            if pre_analysis.get('pattern_seeking_indicators'):  
                analysis_info.append(f"🔍 Pattern-seeking indicators: {', '.join(pre_analysis['pattern_seeking_indicators'])}")
            
            if pre_analysis.get('business_context_indicators'):
                analysis_info.append(f"💼 Business context: {', '.join(pre_analysis['business_context_indicators'])}")
        
        context_str = "\n".join(context_info) if context_info else "No data context"
        analysis_str = "\n".join(analysis_info) if analysis_info else "No pre-analysis available"
        
        routing_query = f"""
CLASSIFY THIS USER QUERY WITH ENHANCED CONTEXT:

User Query: "{user_query}"

📊 DATA CONTEXT:
{context_str}

🔍 PRE-ANALYSIS INSIGHTS:
{analysis_str}

🎯 CLASSIFICATION TASK:
Based on the query and analysis above, determine the user's PRIMARY INTENT:

1. VALUE-SEEKING: Does the user want a specific number, count, or direct answer?
   - Look for pre-analysis showing value-seeking indicators
   - Direct questions starting with "what is", "how many", "total", etc.
   - If YES → textual_analytical

2. PATTERN-SEEKING: Does the user want to understand relationships, trends, or complex patterns?
   - Look for pre-analysis showing pattern-seeking indicators  
   - Questions about "factors", "why", "how", "analyze", "understand"
   - If YES → data_analyst

3. REPORTING: Does the user want a comprehensive formatted report?
   - Explicit requests for reports, summaries, or comprehensive analysis
   - If YES → report_generator

4. CONVERSATIONAL: Simple greetings or capability questions?
   - Short queries with low complexity scores
   - If YES → conversational

⚠️ CRITICAL: Pay special attention to the pre-analysis intent prediction and indicators detected.

Provide your routing decision as JSON only.
"""
        
        return routing_query
    
    def _parse_routing_decision(self, response_content: str) -> Dict[str, Any]:
        """Parse the assistant's routing decision from response"""
        try:
            # Try to extract JSON from response
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                decision = json.loads(json_str)
                
                # Validate required fields
                if "assistant_type" in decision:
                    # Ensure valid assistant type
                    valid_types = ["conversational", "textual_analytical", "data_analyst", "report_generator"]
                    if decision["assistant_type"] not in valid_types:
                        decision["assistant_type"] = "conversational"
                    
                    # Set defaults for missing fields
                    decision.setdefault("confidence", "medium")
                    decision.setdefault("reasoning", "Assistant decision")
                    decision.setdefault("query_complexity", "moderate")
                    decision.setdefault("expected_output", "text")
                    decision.setdefault("requires_data", True)
                    
                    return decision
            
            # If JSON parsing fails, try to extract assistant type from text
            response_lower = response_content.lower()
            if "textual_analytical" in response_lower:
                assistant_type = "textual_analytical"
            elif "data_analyst" in response_lower:
                assistant_type = "data_analyst"
            elif "report_generator" in response_lower:
                assistant_type = "report_generator"
            elif "conversational" in response_lower:
                assistant_type = "conversational"
            else:
                assistant_type = "conversational"
            
            return {
                "assistant_type": assistant_type,
                "confidence": "low",
                "reasoning": "Extracted from non-JSON response",
                "query_complexity": "moderate",
                "expected_output": "text",
                "requires_data": True
            }
            
        except Exception as e:
            logging.error(f"❌ Error parsing routing decision: {e}")
            return self._get_default_decision()
    
    def _validate_and_correct_decision(self, decision: Dict[str, Any], user_query: str, pre_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and potentially correct AI routing decisions based on clear patterns.
        
        This method catches obvious misrouting and applies correction rules to improve accuracy.
        """
        original_assistant_type = decision.get("assistant_type", "conversational")
        corrected = False
        correction_reason = None
        
        query_lower = user_query.lower().strip()
        intent_prediction = pre_analysis.get("intent_prediction", "unclear")
        value_indicators = pre_analysis.get("value_seeking_indicators", [])
        pattern_indicators = pre_analysis.get("pattern_seeking_indicators", [])
        query_length = pre_analysis.get("query_length", 0)
        
        # Rule 1: Clear value-seeking queries routed incorrectly to data_analyst
        if (original_assistant_type == "data_analyst" and 
            intent_prediction == "value_seeking" and 
            len(value_indicators) >= 2 and 
            len(pattern_indicators) == 0 and
            query_length < 12):
            
            decision["assistant_type"] = "textual_analytical"
            corrected = True
            correction_reason = f"Clear value-seeking query with {len(value_indicators)} indicators, too simple for complex analysis"
        
        # Rule 2: Clear pattern-seeking queries routed incorrectly to textual_analytical  
        elif (original_assistant_type == "textual_analytical" and
              (intent_prediction == "pattern_seeking" or
               len(pattern_indicators) >= 2 or
               any(word in query_lower for word in ['analyze', 'factors', 'why', 'understand', 'relationship']))):
            
            decision["assistant_type"] = "data_analyst"
            corrected = True
            correction_reason = f"Pattern-seeking query with analysis indicators: {pattern_indicators}"
        
        # Rule 3: Very short greetings routed to analytical assistants
        elif (original_assistant_type in ["textual_analytical", "data_analyst"] and
              query_length <= 3 and
              any(greeting in query_lower for greeting in ['hi', 'hello', 'hey', 'thanks', 'bye'])):
            
            decision["assistant_type"] = "conversational"
            corrected = True
            correction_reason = "Short greeting detected, should be conversational"
        
        # Rule 4: Business case studies or complex questions routed to textual_analytical
        elif (original_assistant_type == "textual_analytical" and
              (query_length > 20 or
               len(pre_analysis.get("business_context_indicators", [])) >= 2 or
               any(phrase in query_lower for phrase in ['business case', 'case study', 'problem statement', 'objective']))):
            
            decision["assistant_type"] = "data_analyst" 
            corrected = True
            correction_reason = "Complex business context requires analytical capabilities"
        
        # Rule 5: Enhanced report detection (broader patterns)
        report_keywords = ['report', 'detailed', 'comprehensive', 'summary', 'insights', 'analysis']
        report_actions = ['give me', 'provide', 'generate', 'create', 'make', 'show me']
        
        has_report_keyword = any(keyword in query_lower for keyword in report_keywords)
        has_report_action = any(action in query_lower for action in report_actions)
        
        if (has_report_keyword and has_report_action and 
            original_assistant_type != "report_generator"):
            
            decision["assistant_type"] = "report_generator"
            corrected = True
            correction_reason = f"Report request detected: {[k for k in report_keywords if k in query_lower]} + {[a for a in report_actions if a in query_lower]}"
        
        # Rule 6: Override for specific value-seeking patterns regardless of other indicators
        value_seeking_patterns = [
            r'\bwhat is the (total|sum|count|number|highest|lowest|maximum|minimum|average)',
            r'\bhow many\b.*\?',
            r'\bwhich\b.*(highest|lowest|best|worst|most|least)',
            r'\btotal (sales|revenue|profit|cost|price)'
        ]
        
        import re
        for pattern in value_seeking_patterns:
            if re.search(pattern, query_lower) and original_assistant_type != "textual_analytical":
                decision["assistant_type"] = "textual_analytical"
                corrected = True
                correction_reason = f"Strong value-seeking pattern detected: {pattern}"
                break
        
        # Update metadata if correction was made
        if corrected:
            decision["confidence"] = "high"  # High confidence in corrections
            decision["corrected"] = True
            decision["original_assistant_type"] = original_assistant_type
            decision["correction_reason"] = correction_reason
            decision["reasoning"] = f"CORRECTED: {correction_reason}"
            
            logging.info(f"🔧 Decision corrected: {original_assistant_type} → {decision['assistant_type']} | {correction_reason}")
        else:
            decision["corrected"] = False
        
        # Ensure all required fields are present
        decision.setdefault("confidence", "medium")
        decision.setdefault("reasoning", "AI decision")
        decision.setdefault("query_complexity", "moderate")
        decision.setdefault("expected_output", "text")
        decision.setdefault("requires_data", True)
        decision.setdefault("user_intent", intent_prediction)
        
        return decision
    
    def _fallback_classification(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """ENHANCED fallback classification with improved intent detection and tiered decision logic"""
        
        query_lower = user_query.lower().strip()
        query_words = query_lower.split()
        word_count = len(query_words)
        
        # Perform mini-analysis for fallback (simplified version of enhanced analysis)
        fallback_analysis = self._mini_query_analysis(user_query)
        
        # TIER 1: Clear conversational patterns (highest priority)
        conversational_patterns = [
            r'^(hi|hello|hey)(\s|!|\?)*$',
            r'^(how are you|what\'?s up)(\s|!|\?)*$', 
            r'^(thanks|thank you|bye|goodbye)(\s|!|\?)*$',
            r'^(yes|no|ok|okay)(\s|!|\?)*$'
        ]
        
        import re
        for pattern in conversational_patterns:
            if re.match(pattern, query_lower):
                return {
                    "assistant_type": "conversational",
                    "confidence": "high",
                    "reasoning": "Clear conversational pattern matched",
                    "query_complexity": "simple",
                    "expected_output": "text",
                    "requires_data": False,
                    "user_intent": "conversational",
                    "fallback_used": True,
                    "pattern_matched": pattern
                }
        
        # TIER 2: Strong value-seeking patterns (direct answers)
        strong_value_patterns = [
            r'\bwhat is the (total|sum|count|highest|lowest|maximum|minimum|average)',
            r'\bhow many\b.*\?',
            r'\bwhich\b.*(highest|lowest|best|worst|most|least)',
            r'\btotal (sales|revenue|profit|price|cost)',
            r'^what is\b.*\?',
            r'^which\b.*\?'
        ]
        
        for pattern in strong_value_patterns:
            if re.search(pattern, query_lower) and word_count <= 15:
                return {
                    "assistant_type": "textual_analytical",
                    "confidence": "high",
                    "reasoning": f"Strong value-seeking pattern: wants direct answer",
                    "query_complexity": "simple",
                    "expected_output": "text",
                    "requires_data": True,
                    "user_intent": "value_seeking",
                    "fallback_used": True,
                    "pattern_matched": pattern
                }
        
        # TIER 3: Strong pattern-seeking indicators (complex analysis)
        strong_pattern_keywords = [
            'analyze', 'analysis', 'factors affecting', 'understand factors',
            'why', 'relationship', 'correlation', 'model', 'predict',
            'understand how', 'what factors', 'depends on', 'influences'
        ]
        
        pattern_score = sum(1 for keyword in strong_pattern_keywords if keyword in query_lower)
        
        if pattern_score >= 2 or (pattern_score >= 1 and word_count > 15):
            return {
                "assistant_type": "data_analyst",
                "confidence": "high",
                "reasoning": f"Strong pattern-seeking indicators ({pattern_score} detected)",
                "query_complexity": "complex",
                "expected_output": "modeling",
                "requires_data": True,
                "user_intent": "pattern_seeking",
                "business_analysis": True,
                "fallback_used": True
            }
        
        # TIER 4: Business context detection
        business_indicators = [
            'business case', 'case study', 'problem statement', 'objective',
            'market analysis', 'business goal', 'strategy', 'performance analysis',
            'competitive analysis', 'pricing strategy'
        ]
        
        business_score = sum(1 for indicator in business_indicators if indicator in query_lower)
        
        if business_score >= 1 or word_count > 25:  # Long queries likely complex
            return {
                "assistant_type": "data_analyst",
                "confidence": "medium",
                "reasoning": "Business context or complex query detected",
                "query_complexity": "complex",
                "expected_output": "modeling",
                "requires_data": True,
                "user_intent": "pattern_seeking",
                "business_analysis": True,
                "fallback_used": True
            }
        
        # TIER 5: Enhanced report requests detection
        report_indicators = ['report', 'summary', 'comprehensive', 'executive summary', 'document', 'detailed', 'insights', 'overview']
        report_actions = ['give me', 'provide', 'show me', 'generate', 'create', 'make']
        
        has_report_indicator = any(keyword in query_lower for keyword in report_indicators)
        has_report_action = any(action in query_lower for action in report_actions)
        
        # More aggressive report detection
        if has_report_indicator and (has_report_action or word_count > 8):
            return {
                "assistant_type": "report_generator", 
                "confidence": "high",
                "reasoning": f"Report request detected: {[r for r in report_indicators if r in query_lower]}",
                "query_complexity": "complex",
                "expected_output": "report",
                "requires_data": True,
                "user_intent": "reporting",
                "fallback_used": True,
                "report_indicators_found": [r for r in report_indicators if r in query_lower]
            }
        
        # TIER 6: Simple value-seeking patterns (less specific)
        simple_value_indicators = [
            'what is', 'how many', 'total', 'sum', 'count', 'average',
            'highest', 'lowest', 'maximum', 'minimum', 'which'
        ]
        
        value_score = sum(1 for indicator in simple_value_indicators if indicator in query_lower)
        
        if value_score >= 1 and word_count <= 12 and context and context.get('has_data', False):
            return {
                "assistant_type": "textual_analytical",
                "confidence": "medium",
                "reasoning": "Simple value-seeking query with data available",
                "query_complexity": "simple",
                "expected_output": "text",
                "requires_data": True,
                "user_intent": "value_seeking",
                "fallback_used": True
            }
        
        # TIER 7: General analytical terms 
        analytical_terms = [
            'analyze', 'analysis', 'data', 'chart', 'plot', 'visualize',
            'trend', 'pattern', 'insight', 'calculate', 'compute', 'examine'
        ]
        
        analytical_score = sum(1 for term in analytical_terms if term in query_lower)
        
        if analytical_score >= 1:
            # Decide between textual_analytical and data_analyst based on complexity
            if word_count <= 8 and analytical_score == 1:
                assistant_type = "textual_analytical"
                complexity = "simple"
                intent = "value_seeking"
            else:
                assistant_type = "data_analyst"
                complexity = "moderate"
                intent = "pattern_seeking"
            
            return {
                "assistant_type": assistant_type,
                "confidence": "medium",
                "reasoning": f"Analytical terms detected, complexity: {complexity}",
                "query_complexity": complexity,
                "expected_output": "data" if assistant_type == "textual_analytical" else "visualization",
                "requires_data": True,
                "user_intent": intent,
                "fallback_used": True
            }
        
        # TIER 8: Default based on query characteristics
        if word_count <= 4:
            # Very short queries default to conversational
            return {
                "assistant_type": "conversational",
                "confidence": "low",
                "reasoning": "Very short query, likely conversational",
                "query_complexity": "simple",
                "expected_output": "text",
                "requires_data": False,
                "user_intent": "conversational",
                "fallback_used": True
            }
        else:
            # Longer unclear queries default to data_analyst for safety
            return {
                "assistant_type": "data_analyst",
                "confidence": "low",
                "reasoning": "Unclear query, defaulting to analytical capabilities",
                "query_complexity": "moderate",
                "expected_output": "data",
                "requires_data": True,
                "user_intent": "unclear",
                "fallback_used": True
            }
    
    def _mini_query_analysis(self, user_query: str) -> Dict[str, Any]:
        """Simplified query analysis for fallback classification"""
        query_lower = user_query.lower().strip()
        
        value_words = ['what', 'which', 'how many', 'total', 'count', 'highest', 'lowest']
        pattern_words = ['analyze', 'why', 'how', 'understand', 'factors', 'relationship']
        
        return {
            "value_indicators": sum(1 for word in value_words if word in query_lower),
            "pattern_indicators": sum(1 for word in pattern_words if word in query_lower),
            "word_count": len(user_query.split()),
            "has_question_mark": '?' in user_query
        }
    
    def _get_default_decision(self) -> Dict[str, Any]:
        """Get default routing decision when all else fails"""
        return {
            "assistant_type": "conversational",
            "confidence": "low",
            "reasoning": "Default fallback decision",
            "query_complexity": "simple",
            "expected_output": "text", 
            "requires_data": False,
            "error_fallback": True
        }
    
    def cleanup(self):
        """Clean up router assistant resources"""
        try:
            if self.router_assistant_id:
                self.assistant_manager.client.beta.assistants.delete(self.router_assistant_id)
                logging.info(f"🗑️ Deleted router assistant: {self.router_assistant_id}")
        except Exception as e:
            logging.error(f"⚠️ Error cleaning up router assistant: {e}")


class EnhancedQueryClassifier:
    """
    UPDATED: Enhanced query classifier that uses AssistantQueryRouter
    
    This replaces the hardcoded SmartQueryClassifier with an AI-powered approach
    while maintaining the same interface for backward compatibility.
    """
    
    def __init__(self, assistant_manager=None, thread_manager=None):
        self.assistant_manager = assistant_manager
        self.thread_manager = thread_manager
        self.routers = {}  # Store routers per session
        
    def classify_query(self, query: str, has_data: bool = True, session_id: str = None, 
                      context: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        ENHANCED: Classify query using assistant-based routing
        
        Returns:
        - category: 'conversational', 'textual_analytical', 'data_analyst', 'report_generator'  
        - metadata: Enhanced metadata from AI decision
        """
        
        # Use assistant routing if available
        if self.assistant_manager and self.thread_manager and session_id:
            try:
                # Get or create router for this session
                if session_id not in self.routers:
                    self.routers[session_id] = AssistantQueryRouter(
                        self.assistant_manager, 
                        self.thread_manager, 
                        session_id
                    )
                
                router = self.routers[session_id]
                
                # Prepare context
                routing_context = context or {}
                routing_context.update({
                    'has_data': has_data,
                    'session_id': session_id
                })
                
                # Get AI routing decision
                decision = router.route_query(query, routing_context)
                
                # Convert to old format for compatibility
                category = decision.get("assistant_type", "conversational")
                
                # Map new categories to old categories for compatibility
                if category == "textual_analytical":
                    old_category = "analytical"
                    analysis_type = "simple"
                elif category == "data_analyst":
                    old_category = "analytical"  
                    analysis_type = "complex"
                elif category == "report_generator":
                    old_category = "analytical"
                    analysis_type = "report"
                else:
                    old_category = "conversational"
                    analysis_type = "conversational"
                
                # Enhanced metadata
                enhanced_metadata = {
                    'confidence': decision.get('confidence', 'medium'),
                    'requires_analysis': category != "conversational",
                    'analysis_type': analysis_type,
                    'has_data': has_data,
                    'assistant_type': category,  # New field
                    'query_complexity': decision.get('query_complexity', 'moderate'),
                    'expected_output': decision.get('expected_output', 'text'),
                    'ai_reasoning': decision.get('reasoning', ''),
                    'router_used': True,
                    'original_decision': decision
                }
                
                logging.info(f"🎯 AI Classification: '{query}' → {category} ({analysis_type})")
                return old_category, enhanced_metadata
                
            except Exception as e:
                logging.error(f"❌ AI classification failed: {e}")
                # Fall back to rule-based classification
        
        # Fallback to rule-based classification
        return self._rule_based_classification(query, has_data)
    
    def _rule_based_classification(self, query: str, has_data: bool) -> Tuple[str, Dict[str, Any]]:
        """Fallback rule-based classification (simplified version of original)"""
        
        query_lower = query.lower().strip()
        
        # Simple conversational
        simple_patterns = ['hi', 'hello', 'hey', 'how are you', 'what can you do', 'thanks', 'thank you']
        if any(pattern in query_lower for pattern in simple_patterns):
            return 'conversational', {
                'confidence': 'high',
                'requires_analysis': False,
                'analysis_type': 'conversational',
                'has_data': has_data,
                'assistant_type': 'conversational',
                'fallback_used': True
            }
        
        # Report requests
        if any(word in query_lower for word in ['report', 'summary', 'comprehensive']):
            return 'analytical', {
                'confidence': 'high',
                'requires_analysis': True, 
                'analysis_type': 'report',
                'has_data': has_data,
                'assistant_type': 'report_generator',
                'fallback_used': True
            }
        
        # Simple data questions
        simple_data = ['what is', 'how many', 'total', 'count', 'average', 'highest', 'lowest']
        if any(pattern in query_lower for pattern in simple_data):
            return 'analytical', {
                'confidence': 'medium',
                'requires_analysis': True,
                'analysis_type': 'simple', 
                'has_data': has_data,
                'assistant_type': 'textual_analytical',
                'fallback_used': True
            }
        
        # Complex analysis
        complex_indicators = ['chart', 'plot', 'visualize', 'forecast', 'predict', 'trend', 'analysis']
        if any(word in query_lower for word in complex_indicators):
            return 'analytical', {
                'confidence': 'medium',
                'requires_analysis': True,
                'analysis_type': 'complex',
                'has_data': has_data,
                'assistant_type': 'data_analyst',
                'fallback_used': True
            }
        
        # Default to conversational
        return 'conversational', {
            'confidence': 'low',
            'requires_analysis': False,
            'analysis_type': 'conversational',
            'has_data': has_data,
            'assistant_type': 'conversational',
            'fallback_used': True
        }
    
    def cleanup_session(self, session_id: str):
        """Clean up router for a specific session"""
        if session_id in self.routers:
            try:
                self.routers[session_id].cleanup()
                del self.routers[session_id]
                logging.info(f"🧹 Cleaned up router for session: {session_id}")
            except Exception as e:
                logging.error(f"⚠️ Error cleaning up router for session {session_id}: {e}")
    
    def cleanup_all(self):
        """Clean up all routers"""
        for session_id in list(self.routers.keys()):
            self.cleanup_session(session_id)