# Enhanced handlers/enhanced_analyzer.py - Key modifications for DataFrame, Code, and Report handling

import pandas as pd
import numpy as np
import json
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import re

class EnhancedDataFrameProcessor:
    """Enhanced DataFrame processing and extraction from assistant outputs"""
    
    @staticmethod
    def extract_dataframes_from_assistant_outputs(execution_outputs: List[str], response_content: str = "") -> Dict[str, Any]:
        """
        ENHANCED: Extract actual DataFrames from assistant execution outputs
        
        Returns both DataFrame objects and their metadata for proper frontend handling
        """
        dataframes = {}
        dataframe_metadata = {}
        
        # Pattern to detect DataFrame variable assignments
        df_patterns = [
            r'(\w+)\s*=\s*pd\.DataFrame\([^)]*\)',
            r'(\w+)\s*=\s*df\.',  # DataFrame operations
            r'(\w+)\s*=\s*.*\.groupby\(',  # Groupby operations
            r'(\w+)\s*=\s*.*\.pivot\(',  # Pivot operations
            r'(\w+)\s*=\s*.*\.merge\(',  # Merge operations
            r'(\w+)_df\s*=',  # Variables ending with _df
            r'forecast.*=\s*',  # Forecast results
            r'result.*df\s*=',  # Result DataFrames
        ]
        
        # Look for DataFrame creation/manipulation in outputs
        for output in execution_outputs:
            # Check for DataFrame display outputs (df.head(), df.info(), etc.)
            if 'DataFrame' in output or 'Index:' in output or 'Columns:' in output:
                dataframes['execution_output_df'] = {
                    'type': 'display_output',
                    'content': output,
                    'extracted_from': 'execution_display'
                }
            
            # Extract variable names that likely contain DataFrames
            for pattern in df_patterns:
                matches = re.findall(pattern, output, re.IGNORECASE)
                for match in matches:
                    var_name = match if isinstance(match, str) else match[0]
                    if var_name not in dataframes:
                        dataframes[var_name] = {
                            'type': 'inferred_dataframe',
                            'variable_name': var_name,
                            'extracted_from': 'code_analysis'
                        }
        
        # Also check response content for DataFrame mentions
        if response_content:
            # Look for DataFrame descriptions in the response
            df_mentions = re.findall(r'DataFrame\s+(\w+)', response_content, re.IGNORECASE)
            for mention in df_mentions:
                if mention not in dataframes:
                    dataframes[mention] = {
                        'type': 'mentioned_dataframe',
                        'variable_name': mention,
                        'extracted_from': 'response_content'
                    }
        
        return dataframes

    @staticmethod
    def serialize_dataframe_for_api(df: pd.DataFrame, name: str = "dataframe") -> Dict[str, Any]:
        """
        ENHANCED: Serialize DataFrame for API response with complete metadata
        """
        if df is None or df.empty:
            return {
                'name': name,
                'empty': True,
                'shape': [0, 0],
                'columns': [],
                'data': [],
                'metadata': {}
            }
        
        # Limit size for API response
        max_rows = 1000
        display_df = df.head(max_rows) if len(df) > max_rows else df
        
        # Generate summary statistics for numeric columns
        numeric_summary = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            try:
                summary_stats = df[numeric_cols].describe()
                numeric_summary = summary_stats.to_dict()
            except Exception as e:
                logging.warning(f"Could not generate numeric summary: {e}")
        
        # Generate column information
        column_info = {}
        for col in df.columns:
            col_info = {
                'dtype': str(df[col].dtype),
                'null_count': int(df[col].isnull().sum()),
                'unique_count': int(df[col].nunique()),
                'sample_values': df[col].dropna().head(3).tolist()
            }
            
            # Add specific info based on data type
            if df[col].dtype in ['object']:
                col_info['most_common'] = df[col].value_counts().head(3).to_dict()
            elif np.issubdtype(df[col].dtype, np.number):
                col_info.update({
                    'min': float(df[col].min()) if not df[col].isnull().all() else None,
                    'max': float(df[col].max()) if not df[col].isnull().all() else None,
                    'mean': float(df[col].mean()) if not df[col].isnull().all() else None
                })
            
            column_info[col] = col_info
        
        return {
            'name': name,
            'shape': list(df.shape),
            'columns': list(df.columns),
            'data': display_df.to_dict('records'),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'metadata': {
                'total_rows': len(df),
                'displayed_rows': len(display_df),
                'truncated': len(df) > max_rows,
                'null_counts': df.isnull().sum().to_dict(),
                'numeric_summary': numeric_summary,
                'column_info': column_info,
                'memory_usage': df.memory_usage(deep=True).sum(),
                'created_at': datetime.now().isoformat()
            }
        }

class EnhancedCodeProcessor:
    """Enhanced code extraction and formatting from assistant responses"""
    
    @staticmethod
    def extract_all_code_from_response(response_content: str, execution_outputs: List[str] = None) -> Dict[str, Any]:
        """
        ENHANCED: Extract all code from assistant response with proper formatting
        """
        extracted_code = {
            'main_code': '',
            'code_blocks': [],
            'execution_snippets': [],
            'imports': [],
            'functions': [],
            'variables': [],
            'formatted_code': '',
            'metadata': {}
        }
        
        # Extract main code blocks
        code_patterns = [
            r'```python\n(.*?)\n```',
            r'```\n(.*?)\n```',
            r'<code>(.*?)</code>',
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, response_content, re.DOTALL)
            for match in matches:
                cleaned_code = match.strip()
                if cleaned_code:
                    extracted_code['code_blocks'].append(cleaned_code)
                    if not extracted_code['main_code']:
                        extracted_code['main_code'] = cleaned_code
        
        # Extract from execution outputs if available
        if execution_outputs:
            for output in execution_outputs:
                # Look for code execution indicators
                if any(indicator in output for indicator in ['>>>', 'In [', 'pandas', 'import', 'def ', 'plt.']):
                    extracted_code['execution_snippets'].append(output)
        
        # Analyze code structure
        if extracted_code['main_code']:
            code = extracted_code['main_code']
            
            # Extract imports
            import_pattern = r'import\s+[\w\.,\s]+|from\s+[\w\.]+\s+import\s+[\w\.,\s\*]+'
            extracted_code['imports'] = re.findall(import_pattern, code)
            
            # Extract function definitions
            function_pattern = r'def\s+(\w+)\s*\([^)]*\):'
            extracted_code['functions'] = re.findall(function_pattern, code)
            
            # Extract variable assignments
            variable_pattern = r'(\w+)\s*=\s*[^=]'
            extracted_code['variables'] = list(set(re.findall(variable_pattern, code)))
            
            # Format code with line numbers
            lines = code.split('\n')
            formatted_lines = []
            for i, line in enumerate(lines, 1):
                formatted_lines.append(f"{i:3d} | {line}")
            extracted_code['formatted_code'] = '\n'.join(formatted_lines)
        
        # Add metadata
        extracted_code['metadata'] = {
            'total_blocks': len(extracted_code['code_blocks']),
            'total_lines': len(extracted_code['main_code'].split('\n')) if extracted_code['main_code'] else 0,
            'has_imports': len(extracted_code['imports']) > 0,
            'has_functions': len(extracted_code['functions']) > 0,
            'has_visualization': any(viz in extracted_code['main_code'] for viz in ['plt.', 'sns.', 'plotly']) if extracted_code['main_code'] else False,
            'extracted_at': datetime.now().isoformat()
        }
        
        return extracted_code

class EnhancedReportGenerator:
    """Enhanced dynamic report generation for business analysts"""
    
    def __init__(self):
        self.report_templates = {
            'executive': self._get_executive_template(),
            'technical': self._get_technical_template(),
            'comprehensive': self._get_comprehensive_template()
        }
    
    def generate_dynamic_report(self, 
                              query: str,
                              analysis_results: Dict[str, Any],
                              dataframes: Dict[str, Any],
                              images: List[str],
                              code: Dict[str, Any]) -> str:
        """
        ENHANCED: Generate dynamic, business-quality reports
        """
        
        # Analyze the query and results to determine report type
        report_type = self._determine_report_type(query, analysis_results)
        
        # Generate report sections dynamically
        sections = self._generate_report_sections(query, analysis_results, dataframes, images, code)
        
        # Create executive summary
        executive_summary = self._generate_executive_summary(query, analysis_results, dataframes)
        
        # Generate business insights
        insights = self._generate_business_insights(dataframes, analysis_results)
        
        # Create the final report
        report_html = self._compile_report(
            report_type=report_type,
            query=query,
            executive_summary=executive_summary,
            sections=sections,
            insights=insights,
            dataframes=dataframes,
            images=images,
            code=code
        )
        
        return report_html
    
    def _determine_report_type(self, query: str, results: Dict[str, Any]) -> str:
        """Determine the appropriate report type based on query and results"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['executive', 'summary', 'overview', 'strategic']):
            return 'executive'
        elif any(word in query_lower for word in ['technical', 'detailed', 'analysis', 'comprehensive']):
            return 'comprehensive'
        elif results.get('type') == 'forecasting':
            return 'comprehensive'
        else:
            return 'technical'
    
    def _generate_report_sections(self, query: str, results: Dict[str, Any], 
                                dataframes: Dict[str, Any], images: List[str], 
                                code: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate dynamic sections based on analysis content"""
        sections = []
        
        # Data Overview Section
        if dataframes:
            sections.append({
                'title': 'Data Overview',
                'type': 'data_overview',
                'content': self._generate_data_overview(dataframes),
                'priority': 1
            })
        
        # Analysis Results Section
        if results.get('success'):
            sections.append({
                'title': 'Analysis Results',
                'type': 'analysis_results',
                'content': self._generate_analysis_results_content(results),
                'priority': 2
            })
        
        # Visualizations Section
        if images:
            sections.append({
                'title': 'Data Visualizations',
                'type': 'visualizations',
                'content': self._generate_visualizations_content(images),
                'priority': 3
            })
        
        # Data Tables Section
        if dataframes:
            sections.append({
                'title': 'Generated Data Tables',
                'type': 'data_tables',
                'content': self._generate_data_tables_content(dataframes),
                'priority': 4
            })
        
        # Technical Details Section
        if code.get('main_code'):
            sections.append({
                'title': 'Technical Implementation',
                'type': 'technical',
                'content': self._generate_technical_content(code),
                'priority': 5
            })
        
        return sorted(sections, key=lambda x: x['priority'])
    
    def _generate_executive_summary(self, query: str, results: Dict[str, Any], 
                                  dataframes: Dict[str, Any]) -> str:
        """Generate executive summary with key findings"""
        summary_parts = []
        
        # Query context
        summary_parts.append(f"**Analysis Objective:** {query}")
        
        # Key findings from dataframes
        if dataframes:
            for name, df_data in dataframes.items():
                if isinstance(df_data, dict) and 'metadata' in df_data:
                    metadata = df_data['metadata']
                    summary_parts.append(
                        f"**{name.replace('_', ' ').title()}:** "
                        f"{metadata.get('total_rows', 0):,} records across "
                        f"{len(df_data.get('columns', []))} variables"
                    )
        
        # Analysis success indicator
        if results.get('success'):
            summary_parts.append("**Status:** Analysis completed successfully with actionable insights generated")
        
        # Key metrics (if available)
        numeric_insights = self._extract_numeric_insights(dataframes)
        if numeric_insights:
            summary_parts.append(f"**Key Metrics:** {numeric_insights}")
        
        return "\n\n".join(summary_parts)
    
    def _generate_business_insights(self, dataframes: Dict[str, Any], 
                                  results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate business insights from data analysis"""
        insights = []
        
        # Insights from dataframes
        for name, df_data in dataframes.items():
            if isinstance(df_data, dict) and 'metadata' in df_data:
                metadata = df_data['metadata']
                
                # Data quality insights
                null_counts = metadata.get('null_counts', {})
                high_null_cols = [col for col, count in null_counts.items() if count > 0]
                if high_null_cols:
                    insights.append({
                        'type': 'data_quality',
                        'title': 'Data Quality Considerations',
                        'content': f"Found missing values in {len(high_null_cols)} columns: {', '.join(high_null_cols[:3])}{'...' if len(high_null_cols) > 3 else ''}. Consider data cleaning strategies."
                    })
                
                # Size insights
                total_rows = metadata.get('total_rows', 0)
                if total_rows > 10000:
                    insights.append({
                        'type': 'data_scale',
                        'title': 'Large Dataset Detected',
                        'content': f"Dataset contains {total_rows:,} records, indicating substantial data volume suitable for robust statistical analysis."
                    })
                
                # Numeric insights
                numeric_summary = metadata.get('numeric_summary', {})
                if numeric_summary:
                    insights.append({
                        'type': 'statistical',
                        'title': 'Statistical Patterns',
                        'content': f"Analysis of {len(numeric_summary)} numeric variables reveals patterns suitable for trend analysis and forecasting."
                    })
        
        # Analysis type insights
        if results.get('is_forecasting'):
            insights.append({
                'type': 'forecasting',
                'title': 'Forecasting Capability',
                'content': "Time series forecasting models have been applied to predict future trends based on historical patterns."
            })
        
        return insights
    
    def _compile_report(self, report_type: str, query: str, executive_summary: str,
                       sections: List[Dict[str, Any]], insights: List[Dict[str, str]],
                       dataframes: Dict[str, Any], images: List[str], 
                       code: Dict[str, Any]) -> str:
        """Compile the final HTML report"""
        
        # Get base template
        template = self.report_templates.get(report_type, self.report_templates['comprehensive'])
        
        # Generate dynamic content
        sections_html = self._render_sections(sections)
        insights_html = self._render_insights(insights)
        dataframes_html = self._render_dataframes(dataframes)
        images_html = self._render_images(images)
        
        # Compile final report
        report_html = template.format(
            title=self._generate_report_title(query),
            query=query,
            executive_summary=executive_summary,
            sections_content=sections_html,
            insights_content=insights_html,
            dataframes_content=dataframes_html,
            images_content=images_html,
            generated_date=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            code_content=self._render_code(code) if code.get('main_code') else ''
        )
        
        return report_html
    
    def _get_comprehensive_template(self) -> str:
        """Get comprehensive report template for business analysts"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
            margin-top: 0.5rem;
        }}
        .content {{
            padding: 2rem;
        }}
        .section {{
            margin-bottom: 3rem;
            padding: 1.5rem;
            border-radius: 8px;
            background: #f8f9fa;
            border-left: 5px solid #667eea;
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }}
        .executive-summary {{
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            border-left: 5px solid #ff6b6b;
        }}
        .insight-card {{
            background: white;
            padding: 1.5rem;
            margin: 1rem 0;
            border-radius: 8px;
            border-left: 4px solid #28a745;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .insight-card h4 {{
            color: #28a745;
            margin-top: 0;
        }}
        .dataframe-container {{
            margin: 2rem 0;
            overflow-x: auto;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .dataframe-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}
        .dataframe-table th {{
            background: #667eea;
            color: white;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
        }}
        .dataframe-table td {{
            padding: 0.8rem 1rem;
            border-bottom: 1px solid #e9ecef;
        }}
        .dataframe-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        .dataframe-table tr:hover {{
            background: #e3f2fd;
        }}
        .image-gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }}
        .image-card {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .image-card img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        .image-card .caption {{
            padding: 1rem;
            background: #f8f9fa;
            font-weight: 500;
            color: #666;
        }}
        .code-block {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 1.5rem;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.4;
        }}
        .metadata {{
            background: #e8f5e8;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
            font-size: 0.9em;
            color: #2d5a2d;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 2rem;
            text-align: center;
            color: #666;
            border-top: 1px solid #e9ecef;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
            .header {{ background: #333; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">Generated on {generated_date}</div>
        </div>
        
        <div class="content">
            <div class="executive-summary">
                <h2>Executive Summary</h2>
                {executive_summary}
            </div>
            
            <div class="section">
                <h2>Analysis Query</h2>
                <p><strong>"{query}"</strong></p>
            </div>
            
            {sections_content}
            
            {insights_content}
            
            {dataframes_content}
            
            {images_content}
            
            {code_content}
        </div>
        
        <div class="footer">
            <p>Report generated by Enhanced Data Analysis Platform | {generated_date}</p>
        </div>
    </div>
</body>
</html>
        '''
    
    def _get_executive_template(self) -> str:
        """Executive-focused template"""
        # Similar structure but more concise, focus on insights
        return self._get_comprehensive_template()  # Can be customized further
    
    def _get_technical_template(self) -> str:
        """Technical-focused template"""
        # Similar structure but more emphasis on code and methodology
        return self._get_comprehensive_template()  # Can be customized further
    
    def _render_sections(self, sections: List[Dict[str, Any]]) -> str:
        """Render dynamic sections"""
        sections_html = ""
        for section in sections:
            sections_html += f'''
            <div class="section">
                <h2>{section['title']}</h2>
                {section['content']}
            </div>
            '''
        return sections_html
    
    def _render_insights(self, insights: List[Dict[str, str]]) -> str:
        """Render business insights"""
        if not insights:
            return ""
        
        insights_html = '<div class="section"><h2>Business Insights</h2>'
        for insight in insights:
            insights_html += f'''
            <div class="insight-card">
                <h4>{insight['title']}</h4>
                <p>{insight['content']}</p>
            </div>
            '''
        insights_html += '</div>'
        return insights_html
    
    def _render_dataframes(self, dataframes: Dict[str, Any]) -> str:
        """Render DataFrames as professional tables"""
        if not dataframes:
            return ""
        
        dataframes_html = '<div class="section"><h2>Data Analysis Results</h2>'
        
        for name, df_data in dataframes.items():
            if isinstance(df_data, dict) and 'data' in df_data:
                dataframes_html += f'''
                <h3>{name.replace('_', ' ').title()}</h3>
                <div class="metadata">
                    <strong>Shape:</strong> {df_data.get('shape', [0, 0])[0]:,} rows × {df_data.get('shape', [0, 0])[1]} columns |
                    <strong>Columns:</strong> {', '.join(df_data.get('columns', [])[:5])}{'...' if len(df_data.get('columns', [])) > 5 else ''}
                </div>
                <div class="dataframe-container">
                    <table class="dataframe-table">
                        <thead>
                            <tr>
                '''
                
                # Add column headers
                for col in df_data.get('columns', []):
                    dataframes_html += f'<th>{col}</th>'
                
                dataframes_html += '''
                            </tr>
                        </thead>
                        <tbody>
                '''
                
                # Add data rows (limit to first 20 for readability)
                for row in df_data.get('data', [])[:20]:
                    dataframes_html += '<tr>'
                    for col in df_data.get('columns', []):
                        value = row.get(col, '')
                        # Format numeric values
                        if isinstance(value, (int, float)):
                            if isinstance(value, float):
                                formatted_value = f"{value:,.2f}" if abs(value) < 1000000 else f"{value:.2e}"
                            else:
                                formatted_value = f"{value:,}"
                        else:
                            formatted_value = str(value)[:50] + ('...' if len(str(value)) > 50 else '')
                        dataframes_html += f'<td>{formatted_value}</td>'
                    dataframes_html += '</tr>'
                
                dataframes_html += '''
                        </tbody>
                    </table>
                </div>
                '''
                
                # Add metadata if available
                if 'metadata' in df_data:
                    metadata = df_data['metadata']
                    dataframes_html += f'''
                    <div class="metadata">
                        <strong>Total Records:</strong> {metadata.get('total_rows', 0):,} |
                        <strong>Memory Usage:</strong> {metadata.get('memory_usage', 0):,} bytes |
                        <strong>Null Values:</strong> {sum(metadata.get('null_counts', {}).values())} |
                        <strong>Generated:</strong> {metadata.get('created_at', 'Unknown')}
                    </div>
                    '''
        
        dataframes_html += '</div>'
        return dataframes_html
    
    def _render_images(self, images: List[str]) -> str:
        """Render images in a professional gallery"""
        if not images:
            return ""
        
        images_html = '''
        <div class="section">
            <h2>Data Visualizations</h2>
            <div class="image-gallery">
        '''
        
        for i, image in enumerate(images, 1):
            # Handle both base64 and URL images
            if image.startswith('data:image'):
                img_src = image
            elif image.startswith('http'):
                img_src = image
            else:
                # Assume it's a base64 string without the data URL prefix
                img_src = f"data:image/png;base64,{image}"
            
            images_html += f'''
            <div class="image-card">
                <img src="{img_src}" alt="Analysis Visualization {i}">
                <div class="caption">
                    Figure {i}: Generated visualization from data analysis
                </div>
            </div>
            '''
        
        images_html += '''
            </div>
        </div>
        '''
        return images_html
    
    def _render_code(self, code: Dict[str, Any]) -> str:
        """Render code in a professional format"""
        if not code.get('main_code'):
            return ""
        
        code_html = f'''
        <div class="section">
            <h2>Technical Implementation</h2>
            <p>The following Python code was executed to perform the analysis:</p>
            <div class="code-block">
{code.get('formatted_code', code.get('main_code', ''))}
            </div>
        '''
        
        # Add code metadata
        metadata = code.get('metadata', {})
        if metadata:
            code_html += f'''
            <div class="metadata">
                <strong>Code Statistics:</strong> 
                {metadata.get('total_lines', 0)} lines | 
                {metadata.get('total_blocks', 0)} blocks | 
                {'Includes visualizations' if metadata.get('has_visualization') else 'No visualizations'} |
                {'Has functions' if metadata.get('has_functions') else 'No custom functions'}
            </div>
            '''
        
        code_html += '</div>'
        return code_html
    
    def _generate_report_title(self, query: str) -> str:
        """Generate dynamic report title based on query"""
        query_lower = query.lower()
        
        if 'forecast' in query_lower:
            return "Forecasting Analysis Report"
        elif 'trend' in query_lower:
            return "Trend Analysis Report"
        elif 'performance' in query_lower:
            return "Performance Analysis Report"
        elif 'revenue' in query_lower or 'sales' in query_lower:
            return "Sales & Revenue Analysis Report"
        elif 'customer' in query_lower:
            return "Customer Analytics Report"
        elif 'report' in query_lower:
            return "Comprehensive Data Analysis Report"
        else:
            return "Data Analysis Report"
    
    def _generate_data_overview(self, dataframes: Dict[str, Any]) -> str:
        """Generate data overview content"""
        overview = "<p>The analysis processed the following datasets:</p><ul>"
        
        for name, df_data in dataframes.items():
            if isinstance(df_data, dict) and 'metadata' in df_data:
                metadata = df_data['metadata']
                overview += f'''
                <li><strong>{name.replace('_', ' ').title()}</strong>: 
                {metadata.get('total_rows', 0):,} records with 
                {len(df_data.get('columns', []))} variables</li>
                '''
        
        overview += "</ul>"
        return overview
    
    def _generate_analysis_results_content(self, results: Dict[str, Any]) -> str:
        """Generate analysis results content"""
        content = f"<p><strong>Analysis Status:</strong> {'Successful' if results.get('success') else 'Failed'}</p>"
        
        if results.get('type'):
            content += f"<p><strong>Analysis Type:</strong> {results['type'].replace('_', ' ').title()}</p>"
        
        if results.get('response'):
            content += f"<p><strong>Key Findings:</strong> {results['response']}</p>"
        
        return content
    
    def _generate_visualizations_content(self, images: List[str]) -> str:
        """Generate visualizations content"""
        return f"<p>Generated {len(images)} data visualization(s) to support the analysis findings.</p>"
    
    def _generate_data_tables_content(self, dataframes: Dict[str, Any]) -> str:
        """Generate data tables content"""
        return f"<p>Created {len(dataframes)} data table(s) with processed results ready for further analysis.</p>"
    
    def _generate_technical_content(self, code: Dict[str, Any]) -> str:
        """Generate technical content"""
        metadata = code.get('metadata', {})
        content = f"<p>Executed {metadata.get('total_lines', 0)} lines of Python code "
        
        if metadata.get('has_visualization'):
            content += "including data visualization components "
        
        if metadata.get('has_functions'):
            content += "with custom function definitions "
        
        content += "to perform the requested analysis.</p>"
        
        return content
    
    def _extract_numeric_insights(self, dataframes: Dict[str, Any]) -> str:
        """Extract key numeric insights from dataframes"""
        insights = []
        
        for name, df_data in dataframes.items():
            if isinstance(df_data, dict) and 'metadata' in df_data:
                numeric_summary = df_data['metadata'].get('numeric_summary', {})
                if numeric_summary:
                    # Find the most interesting metrics
                    max_values = []
                    for col, stats in numeric_summary.items():
                        if isinstance(stats, dict) and 'max' in stats:
                            max_values.append(f"{col}: {stats['max']:,.0f}")
                    
                    if max_values:
                        insights.append(f"Peak values - {', '.join(max_values[:2])}")
        
        return "; ".join(insights) if insights else "Statistical analysis completed"

# Integration enhancements for enhanced_analyzer.py main class
class DataFrameIntegrationMixin:
    """Mixin to enhance the main analyzer with improved DataFrame handling"""
    
    def __init__(self):
        self.dataframe_processor = EnhancedDataFrameProcessor()
        self.code_processor = EnhancedCodeProcessor()
        self.report_generator = EnhancedReportGenerator()
    
    def _process_analysis_results_enhanced(self, user_query: str, data_request: Dict, 
                                         is_forecasting: bool, generated_code: str, 
                                         result: Dict, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        ENHANCED version of _process_analysis_results with proper DataFrame handling
        """
        
        # Extract DataFrames from variables (actual DataFrame objects)
        dataframes_found = {}
        dataframes_serialized = {}
        
        if result.get("success") and variables:
            for var_name, var_value in variables.items():
                if isinstance(var_value, pd.DataFrame) and not var_value.empty:
                    # Store the actual DataFrame
                    dataframes_found[var_name] = var_value
                    
                    # Serialize for API response
                    dataframes_serialized[var_name] = self.dataframe_processor.serialize_dataframe_for_api(
                        var_value, var_name
                    )
                    
                    logging.info(f"📊 Found and serialized DataFrame: {var_name} (Shape: {var_value.shape})")
                    
                    # Stream the dataframe data to frontend
                    self.emit_stream('dataframe', {
                        'name': var_name,
                        'shape': list(var_value.shape),
                        'columns': list(var_value.columns),
                        'preview': self._generate_dataframe_preview(var_value),
                        'data': var_value.head(100).to_dict('records'),
                        'metadata': dataframes_serialized[var_name]['metadata'],
                        'thisis': "enhanced_dataframe"
                    })
        
        # Enhanced code processing
        code_data = self.code_processor.extract_all_code_from_response(
            generated_code, 
            result.get("execution_outputs", [])
        )
        
        # Stream code to frontend
        if code_data.get('main_code'):
            self.emit_stream('code_enhanced', {
                'code': code_data['main_code'],
                'formatted_code': code_data['formatted_code'],
                'metadata': code_data['metadata'],
                'type': 'enhanced_code'
            })
        
        # Prepare the enhanced result
        analysis_result = {
            "query": user_query,
            "type": "dataframe_analysis",
            "request_type": data_request['type'],
            "generated_code": generated_code,
            "code_data": code_data,  # Enhanced code information
            "execution_result": result,
            "success": result.get("success", False),
            "is_forecasting": is_forecasting,
            "generated_images": self.generated_images.copy(),
            "dataframes": dataframes_serialized,  # Serialized for API
            "dataframes_objects": dataframes_found,  # Actual DataFrame objects
            "data_update_available": len(dataframes_found) > 0,
            "enhanced_features": {
                "dataframe_count": len(dataframes_found),
                "code_analysis": code_data['metadata'],
                "has_visualizations": len(self.generated_images) > 0
            }
        }
        
        # Generate enhanced insights
        if dataframes_found:
            analysis_result["data_insights"] = self._generate_data_insights(dataframes_found)
        
        return analysis_result
    
    def _generate_comprehensive_report_enhanced(self, user_query: str, is_forecasting: bool) -> Dict[str, Any]:
        """
        ENHANCED comprehensive report generation with dynamic content
        """
        print("\n📋 Generating enhanced comprehensive report...")
        self.emit_stream('status', "📋 Generating enhanced comprehensive report...")
        
        try:
            # First run the analysis to get data
            data_request = self._extract_data_request(user_query)
            analysis_result = self._generate_dataframe_analysis_streaming_with_fallback(
                user_query, data_request, is_forecasting
            )
            
            if not analysis_result.get("success"):
                return {
                    "error": "Cannot generate report - analysis failed",
                    "type": "report_error"
                }
            
            self.emit_stream('status', "📝 Generating dynamic business report...")
            
            # Enhanced report generation
            report_html = self.report_generator.generate_dynamic_report(
                query=user_query,
                analysis_results=analysis_result,
                dataframes=analysis_result.get('dataframes', {}),
                images=analysis_result.get('generated_images', []),
                code=analysis_result.get('code_data', {})
            )
            
            # Stream the enhanced report
            self.emit_stream('report_enhanced', {
                'html': report_html,
                'metadata': {
                    'dataframes_included': len(analysis_result.get('dataframes', {})),
                    'images_included': len(analysis_result.get('generated_images', [])),
                    'has_code': bool(analysis_result.get('code_data', {}).get('main_code')),
                    'report_type': 'comprehensive_enhanced'
                }
            })
            
            # Update result with enhanced report
            analysis_result.update({
                "type": "comprehensive_report",
                "comprehensive_report": report_html,
                "report_generated": True,
                "report_enhanced": True,
                "market_topic": self._extract_market_topic(user_query),
                "target_variable": self._extract_target_variable(user_query),
                "forecast_periods": self._extract_forecast_periods(user_query) if is_forecasting else 6,
            })
            
            print("✅ Enhanced comprehensive report generated successfully!")
            self.emit_stream('success', "✅ Enhanced comprehensive report generated successfully!")
            
        except Exception as report_error:
            print(f"⚠️ Enhanced report generation failed: {str(report_error)}")
            self.emit_stream('error', f"Enhanced report generation failed: {str(report_error)}")
            analysis_result.update({
                "report_error": str(report_error),
                "report_generated": False,
                "type": "report_error"
            })
        
        return analysis_result
    
    def _generate_dataframe_preview(self, df: pd.DataFrame, max_rows: int = 5) -> str:
        """Generate HTML preview of DataFrame"""
        if df is None or df.empty:
            return "<p>No data available</p>"
        
        # Create a simple HTML table
        preview_df = df.head(max_rows)
        html = '<div class="dataframe-preview">'
        html += f'<div class="df-info">Shape: {df.shape[0]:,} rows × {df.shape[1]} columns</div>'
        html += preview_df.to_html(classes='preview-table', table_id=None, escape=False)
        html += '</div>'
        
        return html
    
    def _generate_data_insights(self, dataframes: Dict[str, pd.DataFrame]) -> List[Dict[str, str]]:
        """Generate business insights from actual DataFrames"""
        insights = []
        
        for name, df in dataframes.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Basic insights
                insights.append({
                    'dataframe': name,
                    'type': 'size',
                    'insight': f"Dataset contains {len(df):,} records across {len(df.columns)} variables"
                })
                
                # Null value insights
                null_counts = df.isnull().sum()
                high_null_cols = null_counts[null_counts > 0]
                if len(high_null_cols) > 0:
                    insights.append({
                        'dataframe': name,
                        'type': 'data_quality',
                        'insight': f"Found missing values in {len(high_null_cols)} columns: {', '.join(high_null_cols.index[:3].tolist())}"
                    })
                
                # Numeric insights
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    insights.append({
                        'dataframe': name,
                        'type': 'numeric',
                        'insight': f"Contains {len(numeric_cols)} numeric variables suitable for statistical analysis"
                    })
        
        return insights