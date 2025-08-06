import pandas as pd
import numpy as np
import re
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
import logging

class SmartQueryRouter:
    """
    Intelligent query routing that decides the optimal response path
    without always generating complex code or charts.
    """
    
    def __init__(self, df: pd.DataFrame, metadata: Dict[str, Any]):
        self.df = df
        self.metadata = metadata
        self.stats_cache = {}
        self.precomputed_summaries = {}
        
        # Pre-compute common statistics during initialization
        self._precompute_statistics()
    
    def _precompute_statistics(self):
        """Pre-compute common statistics to enable instant responses."""
        try:
            # Basic counts and shapes
            self.stats_cache['row_count'] = len(self.df)
            self.stats_cache['column_count'] = len(self.df.columns)
            self.stats_cache['columns'] = list(self.df.columns)
            
            # Numeric column statistics
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                col_data = self.df[col].dropna()
                if len(col_data) > 0:
                    self.stats_cache[f"{col}_max"] = col_data.max()
                    self.stats_cache[f"{col}_min"] = col_data.min()
                    self.stats_cache[f"{col}_mean"] = col_data.mean()
                    self.stats_cache[f"{col}_sum"] = col_data.sum()
                    self.stats_cache[f"{col}_count"] = len(col_data)
            
            # Categorical summaries
            categorical_cols = self.df.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                col_data = self.df[col].dropna()
                if len(col_data) > 0:
                    self.stats_cache[f"{col}_unique_count"] = col_data.nunique()
                    self.stats_cache[f"{col}_mode"] = col_data.mode().iloc[0] if len(col_data.mode()) > 0 else None
                    self.stats_cache[f"{col}_value_counts"] = col_data.value_counts().to_dict()
            
            logging.info(f"Pre-computed statistics for {len(numeric_cols)} numeric and {len(categorical_cols)} categorical columns")
            
        except Exception as e:
            logging.warning(f"Error pre-computing statistics: {e}")
    
    def route_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main routing function that determines how to handle the query.
        Returns response_plan with execution strategy.
        """
        
        # Analyze the query
        query_analysis = self._analyze_query_intent(user_query)
        
        # Determine optimal response path
        response_plan = self._determine_response_path(query_analysis, user_query)
        
        return response_plan
    
    def _analyze_query_intent(self, user_query: str) -> Dict[str, Any]:
        """Analyze query to understand intent and requirements."""
        
        query_lower = user_query.lower().strip()
        
        analysis = {
            'query_type': 'unknown',
            'entities': [],
            'operations': [],
            'output_format': 'text',
            'complexity': 'low',
            'requires_visualization': False,
            'requires_code_execution': False,
            'can_use_cached_data': False,
            'scope': 'single_value'  # single_value, summary, analysis, comprehensive
        }
        
        # Extract entities (column names, values)
        analysis['entities'] = self._extract_entities(query_lower)
        
        # Identify operations
        analysis['operations'] = self._identify_operations(query_lower)
        
        # Determine query type
        analysis['query_type'] = self._classify_query_type(query_lower, analysis)
        
        # Assess complexity
        analysis['complexity'] = self._assess_complexity(query_lower, analysis)
        
        # Check if visualization is needed
        analysis['requires_visualization'] = self._should_generate_visualization(query_lower, analysis)
        
        # Check if we can use cached data
        analysis['can_use_cached_data'] = self._can_use_cached_response(query_lower, analysis)
        
        # Determine scope
        analysis['scope'] = self._determine_query_scope(query_lower, analysis)
        
        return analysis
    
    def _extract_entities(self, query_lower: str) -> List[Dict[str, str]]:
        """Extract entities like column names, values, time periods."""
        entities = []
        
        # Extract column names
        for col in self.df.columns:
            if col.lower() in query_lower:
                entities.append({
                    'type': 'column',
                    'value': col,
                    'confidence': 'high'
                })
        
        # Extract numeric values
        numeric_matches = re.findall(r'\d+(?:\.\d+)?', query_lower)
        for match in numeric_matches:
            entities.append({
                'type': 'number',
                'value': float(match),
                'confidence': 'medium'
            })
        
        # Extract time periods
        time_patterns = [
            (r'(\d+)\s*(?:months?|years?|weeks?|days?)', 'time_period'),
            (r'next\s+(\d+)', 'future_period'),
            (r'last\s+(\d+)', 'past_period')
        ]
        
        for pattern, entity_type in time_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                entities.append({
                    'type': entity_type,
                    'value': int(match),
                    'confidence': 'high'
                })
        
        return entities
    
    def _identify_operations(self, query_lower: str) -> List[str]:
        """Identify what operations are requested."""
        operations = []
        
        operation_keywords = {
            'aggregate': ['sum', 'total', 'average', 'mean', 'count', 'max', 'maximum', 'min', 'minimum'],
            'filter': ['where', 'filter', 'only', 'exclude', 'remove'],
            'sort': ['sort', 'order', 'rank', 'top', 'bottom', 'highest', 'lowest'],
            'group': ['group', 'by', 'category', 'segment'],
            'compare': ['compare', 'vs', 'versus', 'difference', 'between'],
            'trend': ['trend', 'over time', 'pattern', 'growth', 'decline'],
            'forecast': ['forecast', 'predict', 'future', 'projection', 'ahead'],
            'visualize': ['chart', 'graph', 'plot', 'show', 'visualize', 'display'],
            'report': ['report', 'analysis', 'summary', 'comprehensive', 'detailed']
        }
        
        for operation, keywords in operation_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                operations.append(operation)
        
        return operations
    
    def _classify_query_type(self, query_lower: str, analysis: Dict) -> str:
        """Classify the type of query."""
        
        # Conversational queries
        conversational_patterns = [
            r'^(hi|hello|hey|good morning)',
            r'how are you',
            r'what can you do',
            r'thank you',
            r'goodbye'
        ]
        
        for pattern in conversational_patterns:
            if re.search(pattern, query_lower):
                return 'conversational'
        
        # Simple lookup queries
        if any(op in analysis['operations'] for op in ['aggregate']) and len(analysis['entities']) == 1:
            return 'simple_lookup'
        
        # Complex analysis queries
        if any(op in analysis['operations'] for op in ['forecast', 'report']):
            return 'complex_analysis'
        
        # Visualization queries
        if 'visualize' in analysis['operations']:
            return 'visualization_focused'
        
        # Data exploration queries
        if any(op in analysis['operations'] for op in ['filter', 'group', 'compare']):
            return 'data_exploration'
        
        return 'general_analytical'
    
    def _assess_complexity(self, query_lower: str, analysis: Dict) -> str:
        """Assess query complexity level."""
        
        complexity_indicators = {
            'low': ['count', 'sum', 'max', 'min', 'average'],
            'medium': ['group by', 'filter', 'sort', 'compare'],
            'high': ['forecast', 'predict', 'trend analysis', 'correlation'],
            'very_high': ['comprehensive report', 'strategic analysis', 'modeling']
        }
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                return level
        
        # Additional heuristics
        if len(analysis['operations']) > 2:
            return 'high'
        elif len(analysis['entities']) > 3:
            return 'medium'
        
        return 'low'
    
    def _should_generate_visualization(self, query_lower: str, analysis: Dict) -> bool:
        """Intelligently determine if visualization would add value."""
        
        # Explicit visualization requests
        viz_keywords = ['chart', 'graph', 'plot', 'show', 'visualize', 'display']
        if any(keyword in query_lower for keyword in viz_keywords):
            return True
        
        # Trend analysis (benefits from line charts)
        if any(op in analysis['operations'] for op in ['trend', 'forecast']):
            return True
        
        # Comparisons between categories (benefits from bar charts)
        if 'compare' in analysis['operations'] and len(analysis['entities']) > 1:
            return True
        
        # Distribution questions (benefits from histograms)
        distribution_keywords = ['distribution', 'spread', 'range', 'frequency']
        if any(keyword in query_lower for keyword in distribution_keywords):
            return True
        
        # Time series data with temporal questions
        date_columns = self.metadata['data_summary']['date_columns']
        if date_columns and any(keyword in query_lower for keyword in ['over time', 'trend', 'pattern']):
            return True
        
        # Multiple categories or segments
        if 'group' in analysis['operations'] or 'segment' in query_lower:
            return True
        
        # Don't generate charts for simple factual queries
        simple_query_patterns = [
            r'what is the (max|min|average|sum|total|count)',
            r'how many',
            r'what\'s the highest',
            r'what\'s the lowest'
        ]
        
        for pattern in simple_query_patterns:
            if re.search(pattern, query_lower):
                return False
        
        return False
    
    def _can_use_cached_response(self, query_lower: str, analysis: Dict) -> bool:
        """Check if we can answer using pre-computed statistics."""
        
        # Simple aggregation queries with single entity
        if (analysis['query_type'] == 'simple_lookup' and 
            len(analysis['entities']) == 1 and 
            len(analysis['operations']) == 1):
            
            entity = analysis['entities'][0]
            operation = analysis['operations'][0]
            
            if entity['type'] == 'column' and operation == 'aggregate':
                # Check if we have cached stats for this column
                col_name = entity['value']
                
                # Check for common statistics in cache
                cache_patterns = [
                    f"{col_name}_max",
                    f"{col_name}_min", 
                    f"{col_name}_mean",
                    f"{col_name}_sum",
                    f"{col_name}_count"
                ]
                
                return any(pattern in self.stats_cache for pattern in cache_patterns)
        
        # Row/column count queries
        count_patterns = [
            r'how many rows',
            r'how many columns',
            r'what is the shape',
            r'size of (?:the )?data'
        ]
        
        for pattern in count_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def _determine_query_scope(self, query_lower: str, analysis: Dict) -> str:
        """Determine the scope of analysis needed."""
        
        # Single value responses
        single_value_patterns = [
            r'what is the (max|min|average|sum|total)',
            r'how many',
            r'what\'s the (highest|lowest)'
        ]
        
        for pattern in single_value_patterns:
            if re.search(pattern, query_lower):
                return 'single_value'
        
        # Summary level
        summary_keywords = ['summary', 'overview', 'breakdown', 'distribution']
        if any(keyword in query_lower for keyword in summary_keywords):
            return 'summary'
        
        # Analysis level
        analysis_keywords = ['analyze', 'analysis', 'pattern', 'trend', 'relationship']
        if any(keyword in query_lower for keyword in analysis_keywords):
            return 'analysis'
        
        # Comprehensive level
        comprehensive_keywords = ['report', 'comprehensive', 'detailed', 'strategic', 'forecast']
        if any(keyword in query_lower for keyword in comprehensive_keywords):
            return 'comprehensive'
        
        return 'summary'
    
    def _determine_response_path(self, query_analysis: Dict, user_query: str) -> Dict[str, Any]:
        """Determine the optimal response path based on query analysis."""
        
        response_plan = {
            'strategy': 'unknown',
            'execution_method': 'cached',  # cached, minimal_code, full_analysis
            'requires_charts': query_analysis['requires_visualization'],
            'estimated_time': 'instant',
            'response_type': 'text',
            'confidence': 0.0,
            'fallback_strategy': 'full_analysis'
        }
        
        # Route based on query type and analysis
        if query_analysis['query_type'] == 'conversational':
            response_plan.update({
                'strategy': 'conversational',
                'execution_method': 'direct_response',
                'estimated_time': 'instant',
                'response_type': 'text',
                'confidence': 0.9
            })
        
        elif query_analysis['can_use_cached_data']:
            response_plan.update({
                'strategy': 'cached_response',
                'execution_method': 'cached',
                'estimated_time': 'instant',
                'response_type': 'text',
                'confidence': 0.95
            })
        
        elif (query_analysis['query_type'] == 'simple_lookup' and 
              query_analysis['complexity'] == 'low'):
            response_plan.update({
                'strategy': 'direct_calculation',
                'execution_method': 'minimal_code',
                'estimated_time': 'fast',
                'response_type': 'text_with_data',
                'confidence': 0.8
            })
        
        elif query_analysis['scope'] in ['analysis', 'comprehensive']:
            response_plan.update({
                'strategy': 'full_analysis',
                'execution_method': 'full_analysis',
                'estimated_time': 'moderate',
                'response_type': 'comprehensive',
                'confidence': 0.7
            })
        
        else:
            response_plan.update({
                'strategy': 'standard_analysis',
                'execution_method': 'minimal_code',
                'estimated_time': 'fast',
                'response_type': 'text_with_data',
                'confidence': 0.6
            })
        
        # Add specific execution details
        response_plan['execution_details'] = self._create_execution_details(
            query_analysis, user_query, response_plan
        )
        
        return response_plan
    
    def _create_execution_details(self, query_analysis: Dict, user_query: str, 
                                response_plan: Dict) -> Dict[str, Any]:
        """Create specific execution details for the chosen strategy."""
        
        details = {
            'target_columns': [],
            'required_operations': query_analysis['operations'],
            'entities': query_analysis['entities'],
            'chart_types': [],
            'code_template': None,
            'cache_keys': []
        }
        
        # Extract target columns from entities
        for entity in query_analysis['entities']:
            if entity['type'] == 'column':
                details['target_columns'].append(entity['value'])
        
        # Determine chart types if visualization is needed
        if response_plan['requires_charts']:
            details['chart_types'] = self._suggest_chart_types(query_analysis)
        
        # Create cache keys for cached responses
        if response_plan['execution_method'] == 'cached':
            details['cache_keys'] = self._generate_cache_keys(query_analysis)
        
        # Generate code template for minimal code execution
        if response_plan['execution_method'] == 'minimal_code':
            details['code_template'] = self._generate_minimal_code_template(query_analysis)
        
        return details
    
    def _suggest_chart_types(self, query_analysis: Dict) -> List[str]:
        """Suggest appropriate chart types based on query analysis."""
        chart_types = []
        
        operations = query_analysis['operations']
        entities = query_analysis['entities']
        
        # Time series / trends
        if 'trend' in operations or 'forecast' in operations:
            chart_types.append('line_chart')
        
        # Comparisons between categories
        if 'compare' in operations and len(entities) > 1:
            chart_types.append('bar_chart')
        
        # Part-to-whole relationships
        if any(keyword in str(operations) for keyword in ['breakdown', 'distribution', 'percentage']):
            chart_types.append('pie_chart')
        
        # Correlations or relationships
        if 'correlation' in str(operations) or 'relationship' in str(operations):
            chart_types.append('scatter_plot')
        
        # Default to bar chart for general comparisons
        if not chart_types and len(entities) > 1:
            chart_types.append('bar_chart')
        
        return chart_types
    
    def _generate_cache_keys(self, query_analysis: Dict) -> List[str]:
        """Generate cache keys for retrieving pre-computed results."""
        cache_keys = []
        
        for entity in query_analysis['entities']:
            if entity['type'] == 'column':
                col_name = entity['value']
                
                # Add relevant cache keys based on operations
                for operation in query_analysis['operations']:
                    if operation == 'aggregate':
                        cache_keys.extend([
                            f"{col_name}_max",
                            f"{col_name}_min",
                            f"{col_name}_mean",
                            f"{col_name}_sum",
                            f"{col_name}_count"
                        ])
        
        # Add general cache keys
        cache_keys.extend(['row_count', 'column_count', 'columns'])
        
        return cache_keys
    
    def _generate_minimal_code_template(self, query_analysis: Dict) -> str:
        """Generate minimal code template for targeted analysis."""
        
        if not query_analysis['entities']:
            return "# No specific entities identified\nresult = 'Please specify which column or data you want to analyze'"
        
        # Focus on the primary entity (usually a column)
        primary_entity = None
        for entity in query_analysis['entities']:
            if entity['type'] == 'column':
                primary_entity = entity
                break
        
        if not primary_entity:
            return "# No column entities identified\nresult = 'Please specify which column you want to analyze'"
        
        col_name = primary_entity['value']
        operations = query_analysis['operations']
        
        # Generate targeted code based on operations
        code_lines = [
            "# Targeted analysis - minimal code approach",
            f"target_column = '{col_name}'",
            "results = {}",
            "",
            "try:",
            f"    col_data = df['{col_name}'].dropna()",
            "    if len(col_data) == 0:",
            "        results['error'] = f'Column {target_column} has no valid data'",
            "    else:"
        ]
        
        # Add specific calculations based on operations
        if 'aggregate' in operations:
            code_lines.extend([
                "        results['count'] = len(col_data)",
                "        if pd.api.types.is_numeric_dtype(col_data):",
                "            results['max'] = col_data.max()",
                "            results['min'] = col_data.min()",
                "            results['mean'] = col_data.mean()",
                "            results['sum'] = col_data.sum()",
                "        else:",
                "            results['unique_count'] = col_data.nunique()",
                "            results['most_common'] = col_data.mode().iloc[0] if len(col_data.mode()) > 0 else None"
            ])
        
        if 'group' in operations:
            code_lines.extend([
                "        if pd.api.types.is_numeric_dtype(col_data):",
                "            results['value_counts'] = col_data.value_counts().head(10).to_dict()",
                "        else:",
                "            results['value_counts'] = col_data.value_counts().to_dict()"
            ])
        
        code_lines.extend([
            "",
            "except Exception as e:",
            "    results['error'] = f'Error analyzing {target_column}: {str(e)}'",
            "",
            "# Format result for user",
            "if 'error' in results:",
            "    result = results['error']",
            "else:",
            "    result_parts = []"
        ])
        
        # Add result formatting based on what was calculated
        if 'aggregate' in operations:
            code_lines.extend([
                "    if 'max' in results:",
                f"        result_parts.append(f'Highest {col_name}: {{results[\"max\"]:.2f}}')",
                "    if 'min' in results:",
                f"        result_parts.append(f'Lowest {col_name}: {{results[\"min\"]:.2f}}')",
                "    if 'mean' in results:",
                f"        result_parts.append(f'Average {col_name}: {{results[\"mean\"]:.2f}}')",
                "    if 'sum' in results:",
                f"        result_parts.append(f'Total {col_name}: {{results[\"sum\"]:.2f}}')",
                "    if 'count' in results:",
                f"        result_parts.append(f'Count: {{results[\"count\"]}}')"
            ])
        
        code_lines.extend([
            "    result = ' | '.join(result_parts) if result_parts else 'Analysis completed'"
        ])
        
        return '\n'.join(code_lines)


class MetadataBasedResponder:
    """
    Responds to queries using pre-computed metadata and statistics
    without executing complex code.
    """
    
    def __init__(self, df: pd.DataFrame, metadata: Dict[str, Any], stats_cache: Dict[str, Any]):
        self.df = df
        self.metadata = metadata
        self.stats_cache = stats_cache
    
    def generate_cached_response(self, user_query: str, cache_keys: List[str]) -> Dict[str, Any]:
        """Generate response using cached statistics."""
        
        try:
            query_lower = user_query.lower()
            response_parts = []
            
            # Handle specific query patterns
            if re.search(r'how many rows', query_lower):
                row_count = self.stats_cache.get('row_count', len(self.df))
                response_parts.append(f"📊 The dataset has {row_count:,} rows")
            
            if re.search(r'how many columns', query_lower):
                col_count = self.stats_cache.get('column_count', len(self.df.columns))
                response_parts.append(f"📊 The dataset has {col_count} columns")
            
            # Handle column-specific queries
            for col in self.df.columns:
                if col.lower() in query_lower:
                    response_parts.extend(self._get_column_summary(col, query_lower))
            
            # Handle general statistics requests
            if any(keyword in query_lower for keyword in ['summary', 'overview', 'info']):
                response_parts.extend(self._get_dataset_overview())
            
            if response_parts:
                return {
                    "query": user_query,
                    "type": "cached_response",
                    "success": True,
                    "response": '\n'.join(response_parts),
                    "generated_images": [],
                    "dataframes": {},
                    "execution_time": "instant",
                    "method": "cached_statistics"
                }
            else:
                return {
                    "query": user_query,
                    "type": "cached_response",
                    "success": False,
                    "error": "Could not find relevant cached information",
                    "fallback_required": True
                }
        
        except Exception as e:
            return {
                "query": user_query,
                "type": "cached_response", 
                "success": False,
                "error": str(e),
                "fallback_required": True
            }
    
    def _get_column_summary(self, col_name: str, query_lower: str) -> List[str]:
        """Get summary information for a specific column."""
        summary_parts = []
        
        # Check what statistics are available for this column
        if f"{col_name}_max" in self.stats_cache:
            if any(keyword in query_lower for keyword in ['max', 'maximum', 'highest']):
                max_val = self.stats_cache[f"{col_name}_max"]
                summary_parts.append(f"📈 Highest {col_name}: {max_val:,.2f}")
        
        if f"{col_name}_min" in self.stats_cache:
            if any(keyword in query_lower for keyword in ['min', 'minimum', 'lowest']):
                min_val = self.stats_cache[f"{col_name}_min"]
                summary_parts.append(f"📉 Lowest {col_name}: {min_val:,.2f}")
        
        if f"{col_name}_mean" in self.stats_cache:
            if any(keyword in query_lower for keyword in ['average', 'mean']):
                mean_val = self.stats_cache[f"{col_name}_mean"]
                summary_parts.append(f"📊 Average {col_name}: {mean_val:,.2f}")
        
        if f"{col_name}_sum" in self.stats_cache:
            if any(keyword in query_lower for keyword in ['sum', 'total']):
                sum_val = self.stats_cache[f"{col_name}_sum"]
                summary_parts.append(f"🔢 Total {col_name}: {sum_val:,.2f}")
        
        if f"{col_name}_count" in self.stats_cache:
            if any(keyword in query_lower for keyword in ['count', 'how many']):
                count_val = self.stats_cache[f"{col_name}_count"]
                summary_parts.append(f"📋 Count of {col_name}: {count_val:,}")
        
        return summary_parts
    
    def _get_dataset_overview(self) -> List[str]:
        """Get general dataset overview."""
        overview = []
        
        # Basic info
        row_count = self.stats_cache.get('row_count', 0)
        col_count = self.stats_cache.get('column_count', 0)
        overview.append(f"📊 Dataset Overview: {row_count:,} rows × {col_count} columns")
        
        # Column types
        numeric_cols = self.metadata['data_summary']['numeric_columns']
        categorical_cols = self.metadata['data_summary']['categorical_columns']
        
        if numeric_cols:
            overview.append(f"🔢 Numeric columns ({len(numeric_cols)}): {', '.join(numeric_cols[:5])}")
        
        if categorical_cols:
            overview.append(f"📝 Text columns ({len(categorical_cols)}): {', '.join(categorical_cols[:5])}")
        
        # Data quality
        quality_score = self.metadata['quality_metrics']['completeness']
        overview.append(f"✅ Data completeness: {quality_score:.1%}")
        
        return overview


class ContextAwareChunker:
    """
    Manages large files by creating intelligent chunks while maintaining
    context awareness for cross-chunk queries.
    """
    
    def __init__(self, df: pd.DataFrame, metadata: Dict[str, Any], max_chunk_size: int = 1000):
        self.df = df
        self.metadata = metadata
        self.max_chunk_size = max_chunk_size
        self.chunks = []
        self.chunk_summaries = []
        self.cross_chunk_index = {}
        
        # Create chunks if needed
        if len(df) > max_chunk_size:
            self._create_intelligent_chunks()
        else:
            # Single chunk
            self.chunks = [df]
            self.chunk_summaries = [self._create_chunk_summary(df, 0)]
    
    def _create_intelligent_chunks(self):
        """Create chunks based on logical data boundaries."""
        
        # Strategy 1: Chunk by natural groups if categorical columns exist
        categorical_cols = self.metadata['data_summary']['categorical_columns']
        
        if categorical_cols:
            # Use the first categorical column for grouping
            group_col = categorical_cols[0]
            self._chunk_by_category(group_col)
        else:
            # Strategy 2: Sequential chunking with overlap
            self._chunk_sequentially()
    
    def _chunk_by_category(self, group_col: str):
        """Chunk data by categories in a column."""
        try:
            grouped = self.df.groupby(group_col)
            
            current_chunk = []
            current_size = 0
            
            for name, group in grouped:
                if current_size + len(group) > self.max_chunk_size and current_chunk:
                    # Save current chunk
                    chunk_df = pd.concat(current_chunk, ignore_index=True)
                    self.chunks.append(chunk_df)
                    self.chunk_summaries.append(
                        self._create_chunk_summary(chunk_df, len(self.chunks) - 1)
                    )
                    
                    # Start new chunk
                    current_chunk = [group]
                    current_size = len(group)
                else:
                    current_chunk.append(group)
                    current_size += len(group)
            
            # Add final chunk
            if current_chunk:
                chunk_df = pd.concat(current_chunk, ignore_index=True)
                self.chunks.append(chunk_df)
                self.chunk_summaries.append(
                    self._create_chunk_summary(chunk_df, len(self.chunks) - 1)
                )
        
        except Exception as e:
            logging.warning(f"Category-based chunking failed: {e}, falling back to sequential")
            self._chunk_sequentially()
    
    def _chunk_sequentially(self):
        """Create sequential chunks with overlap."""
        overlap_size = 50  # Overlap between chunks for context
        
        start_idx = 0
        chunk_idx = 0
        
        while start_idx < len(self.df):
            end_idx = min(start_idx + self.max_chunk_size, len(self.df))
            
            chunk_df = self.df.iloc[start_idx:end_idx].copy()
            self.chunks.append(chunk_df)
            self.chunk_summaries.append(self._create_chunk_summary(chunk_df, chunk_idx))
            
            # Move start with overlap
            start_idx = end_idx - overlap_size
            chunk_idx += 1
            
            if end_idx >= len(self.df):
                break
    
    def _create_chunk_summary(self, chunk_df: pd.DataFrame, chunk_idx: int) -> Dict[str, Any]:
        """Create summary for a chunk."""
        
        summary = {
            'chunk_index': chunk_idx,
            'row_range': (chunk_df.index.min(), chunk_df.index.max()),
            'shape': chunk_df.shape,
            'columns': list(chunk_df.columns),
            'numeric_summaries': {},
            'categorical_summaries': {},
            'date_range': None
        }
        
        # Numeric summaries
        numeric_cols = chunk_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            col_data = chunk_df[col].dropna()
            if len(col_data) > 0:
                summary['numeric_summaries'][col] = {
                    'min': col_data.min(),
                    'max': col_data.max(),
                    'mean': col_data.mean(),
                    'count': len(col_data)
                }
        
        # Categorical summaries
        categorical_cols = chunk_df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            col_data = chunk_df[col].dropna()
            if len(col_data) > 0:
                summary['categorical_summaries'][col] = {
                    'unique_count': col_data.nunique(),
                    'most_common': col_data.mode().iloc[0] if len(col_data.mode()) > 0 else None,
                    'top_values': col_data.value_counts().head(5).to_dict()
                }
        
        # Date range if date columns exist
        date_cols = self.metadata['data_summary']['date_columns']
        if date_cols:
            for col in date_cols:
                if col in chunk_df.columns:
                    try:
                        date_data = pd.to_datetime(chunk_df[col], errors='coerce').dropna()
                        if len(date_data) > 0:
                            summary['date_range'] = {
                                'column': col,
                                'start': date_data.min(),
                                'end': date_data.max()
                            }
                            break
                    except:
                        continue
        
        return summary
    
    def find_relevant_chunks(self, query_analysis: Dict) -> List[int]:
        """Find chunks relevant to the query."""
        relevant_chunks = []
        
        # If query mentions specific columns, find chunks with those columns
        target_columns = [entity['value'] for entity in query_analysis['entities'] 
                         if entity['type'] == 'column']
        
        if target_columns:
            for idx, summary in enumerate(self.chunk_summaries):
                if any(col in summary['columns'] for col in target_columns):
                    relevant_chunks.append(idx)
        
        # If no specific columns, include all chunks
        if not relevant_chunks:
            relevant_chunks = list(range(len(self.chunks)))
        
        return relevant_chunks
    
    def get_combined_chunk_data(self, chunk_indices: List[int]) -> pd.DataFrame:
        """Combine data from specified chunks."""
        if not chunk_indices:
            return pd.DataFrame()
        
        selected_chunks = [self.chunks[i] for i in chunk_indices]
        return pd.concat(selected_chunks, ignore_index=True)


class CompatibilityWrapper:
    """
    Wrapper that maintains backward compatibility with existing code
    while providing enhanced functionality.
    """
    
    def __init__(self, original_analyzer_class):
        self.original_analyzer_class = original_analyzer_class
        self.structure_detector = EnhancedFileStructureDetector()
    
    def create_enhanced_analyzer(self, session_id: str, socketio=None):
        """Create analyzer with enhanced capabilities while maintaining compatibility."""
        
        # Create original analyzer instance
        analyzer = self.original_analyzer_class(session_id, socketio)
        
        # Add enhanced components
        analyzer.structure_detector = self.structure_detector
        analyzer.query_router = None  # Will be initialized after CSV load
        analyzer.metadata_responder = None
        analyzer.context_chunker = None
        
        # Override the load_csv method
        original_load_csv = analyzer.load_csv
        
        def enhanced_load_csv(file_path: str) -> bool:
            try:
                # Use enhanced structure detection
                clean_df, file_metadata = self.structure_detector.detect_and_load_file(file_path)
                
                # Set the cleaned DataFrame
                analyzer.df = clean_df
                analyzer.original_df = clean_df.copy()
                analyzer.original_file_path = file_path
                
                # Generate CSV info using cleaned data
                analyzer.csv_info = analyzer._generate_csv_info()
                
                # Initialize enhanced components
                analyzer.query_router = SmartQueryRouter(clean_df, file_metadata)
                analyzer.metadata_responder = MetadataBasedResponder(
                    clean_df, file_metadata, analyzer.query_router.stats_cache
                )
                
                # Initialize chunker for large files
                if len(clean_df) > 5000:
                    analyzer.context_chunker = ContextAwareChunker(clean_df, file_metadata)
                
                # Store file metadata
                analyzer.file_metadata = file_metadata
                
                logging.info("✅ Enhanced CSV loading completed")
                logging.info(f"📊 Structure confidence: {file_metadata['quality_metrics']['structure_confidence']:.2f}")
                
                if file_metadata['processing_notes']:
                    logging.info("📝 Processing notes:")
                    for note in file_metadata['processing_notes']:
                        logging.info(f"   - {note}")
                
                return True
                
            except Exception as e:
                logging.error(f"Enhanced CSV loading failed: {e}")
                # Fallback to original method
                return original_load_csv(file_path)
        
        # Replace the load_csv method
        analyzer.load_csv = enhanced_load_csv
        
        # Override analyze_query_streaming to add smart routing
        original_analyze = analyzer.analyze_query_streaming
        
        def enhanced_analyze_query_streaming(user_query: str):
            try:
                # Use smart routing if available
                if hasattr(analyzer, 'query_router') and analyzer.query_router:
                    response_plan = analyzer.query_router.route_query(user_query)
                    
                    # Execute based on response plan
                    if response_plan['strategy'] == 'cached_response':
                        cache_keys = response_plan['execution_details']['cache_keys']
                        result = analyzer.metadata_responder.generate_cached_response(user_query, cache_keys)
                        
                        if result['success']:
                            # Stream the cached response
                            if hasattr(analyzer, 'emit_stream'):
                                analyzer.emit_stream('status', '⚡ Using cached response for instant answer')
                                analyzer.emit_stream('output', result['response'])
                                analyzer.emit_stream('completion', 'Instant response complete!')
                            return result
                        else:
                            # Fallback to original method
                            if hasattr(analyzer, 'emit_stream'):
                                analyzer.emit_stream('status', '🔄 Cached response unavailable, using full analysis')
                    
                    elif response_plan['strategy'] == 'direct_calculation':
                        # Use minimal code execution
                        if hasattr(analyzer, 'emit_stream'):
                            analyzer.emit_stream('status', '⚡ Using targeted analysis for quick answer')
                        
                        # Execute minimal code
                        code_template = response_plan['execution_details']['code_template']
                        if code_template:
                            result = analyzer._execute_minimal_code(code_template, user_query)
                            if result['success']:
                                return result
                
                # Fallback to original analysis for complex queries
                if hasattr(analyzer, 'emit_stream'):
                    analyzer.emit_stream('status', '🔬 Using comprehensive analysis approach')
                
                return original_analyze(user_query)
                
            except Exception as e:
                logging.error(f"Enhanced query analysis failed: {e}")
                # Always fallback to original method
                return original_analyze(user_query)
        
        # Add minimal code execution method
        def execute_minimal_code(code: str, user_query: str) -> Dict[str, Any]:
            """Execute minimal code for targeted analysis."""
            try:
                exec_globals = {
                    'df': analyzer.df,
                    'pd': pd,
                    'np': np,
                    'len': len,
                    'str': str,
                    'float': float,
                    'int': int
                }
                
                exec_locals = {}
                exec(code, exec_globals, exec_locals)
                
                result_text = exec_locals.get('result', 'Analysis completed')
                
                # Stream the result
                if hasattr(analyzer, 'emit_stream'):
                    analyzer.emit_stream('output', result_text)
                    analyzer.emit_stream('completion', 'Quick analysis complete!')
                
                return {
                    "query": user_query,
                    "type": "minimal_analysis",
                    "success": True,
                    "response": result_text,
                    "generated_images": [],
                    "dataframes": {},
                    "execution_method": "minimal_code",
                    "execution_result": {
                        "success": True,
                        "output": result_text
                    }
                }
                
            except Exception as e:
                return {
                    "query": user_query,
                    "type": "minimal_analysis",
                    "success": False,
                    "error": str(e),
                    "fallback_required": True
                }
        
        analyzer._execute_minimal_code = execute_minimal_code
        
        # Replace the analyze_query_streaming method
        analyzer.analyze_query_streaming = enhanced_analyze_query_streaming
        
        return analyzer