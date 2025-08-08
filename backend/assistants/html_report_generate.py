import os
import json
import base64
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
from jinja2 import Template

class HTMLReportGenerator:
    """
    Generates dynamic HTML reports for data analysis results.
    Combines images, dataframes, code, and analysis text into comprehensive reports.
    """
    
    def __init__(self, session_id: str, output_dir: str = "reports"):
        self.session_id = session_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_report(self, analysis_results: Dict[str, Any], 
                       user_query: str, file_manager=None) -> str:
        """
        Generate HTML report from analysis results.
        
        Args:
            analysis_results: Results from assistant analysis
            user_query: Original user query
            file_manager: FileManager instance for downloading images
            
        Returns:
            Path to generated HTML report
        """
        try:
            # Extract components from analysis results
            report_data = self._extract_report_components(analysis_results, file_manager)
            
            # Generate HTML content
            html_content = self._generate_html_content(
                report_data, user_query, analysis_results.get('response_content', '')
            )
            
            # Save report
            report_path = self._save_report(html_content)
            
            logging.info(f"✅ Generated HTML report: {report_path}")
            return report_path
            
        except Exception as e:
            logging.error(f"❌ Error generating HTML report: {e}")
            raise
    
    def _extract_report_components(self, analysis_results: Dict[str, Any], 
                                 file_manager=None) -> Dict[str, Any]:
        """Extract and process components for the report"""
        
        components = {
            'images': [],
            'dataframes': [],
            'code': analysis_results.get('generated_code', ''),
            'execution_outputs': analysis_results.get('execution_outputs', []),
            'summary': analysis_results.get('response_content', ''),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Process generated images
        generated_images = analysis_results.get('generated_images', [])
        for image_id in generated_images:
            if file_manager:
                try:
                    # Download image to temporary location
                    temp_dir = self.output_dir / "temp_images"
                    temp_dir.mkdir(exist_ok=True)
                    
                    image_path = file_manager.download_generated_file(
                        image_id, str(temp_dir), f"chart_{image_id}.png"
                    )
                    
                    # Convert to base64 for embedding
                    image_base64 = self._image_to_base64(image_path)
                    components['images'].append({
                        'id': image_id,
                        'base64': image_base64,
                        'path': image_path
                    })
                    
                except Exception as e:
                    logging.warning(f"⚠️ Could not process image {image_id}: {e}")
        
        # Extract dataframes from execution outputs
        components['dataframes'] = self._extract_dataframes_from_outputs(
            components['execution_outputs']
        )
        
        return components
    
    def _extract_dataframes_from_outputs(self, execution_outputs: List[str]) -> List[Dict[str, Any]]:
        """Extract dataframe representations from execution outputs"""
        dataframes = []
        
        for i, output in enumerate(execution_outputs):
            # Look for dataframe-like outputs
            if any(keyword in output.lower() for keyword in ['dataframe', 'df', '|', 'index']):
                # Try to parse as dataframe representation
                dataframes.append({
                    'id': f"df_{i}",
                    'content': output,
                    'type': 'text_representation'
                })
        
        return dataframes
    
    def _image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string"""
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            logging.warning(f"⚠️ Could not convert image to base64: {e}")
            return ""
    
    def _generate_html_content(self, report_data: Dict[str, Any], 
                              user_query: str, analysis_summary: str) -> str:
        """Generate HTML content using template"""
        
        template_str = self._get_html_template()
        template = Template(template_str)
        
        return template.render(
            session_id=self.session_id,
            user_query=user_query,
            analysis_summary=analysis_summary,
            timestamp=report_data['timestamp'],
            images=report_data['images'],
            dataframes=report_data['dataframes'],
            code=report_data['code'],
            execution_outputs=report_data['execution_outputs']
        )
    
    def _get_html_template(self) -> str:
        """Get HTML template for the report"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Analysis Report - {{ session_id }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .report-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .report-header h1 {
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .report-meta {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }
        
        .report-content {
            padding: 30px;
        }
        
        .section {
            margin-bottom: 40px;
            border-bottom: 1px solid #eee;
            padding-bottom: 30px;
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        .section-title {
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }
        
        .query-box {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            font-style: italic;
            color: #495057;
        }
        
        .summary-box {
            background: #e8f5e8;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }
        
        .code-block {
            background: #f4f4f4;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .image-container {
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 8px;
        }
        
        .chart-image {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .dataframe-container {
            margin: 20px 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .dataframe-title {
            background: #f8f9fa;
            padding: 15px;
            font-weight: bold;
            border-bottom: 1px solid #ddd;
        }
        
        .dataframe-content {
            padding: 20px;
            font-family: monospace;
            white-space: pre-wrap;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .execution-output {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 14px;
            white-space: pre-wrap;
        }
        
        .timestamp {
            color: #6c757d;
            font-size: 0.9em;
        }
        
        .no-content {
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 20px;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .report-header h1 {
                font-size: 2em;
            }
            
            .report-content {
                padding: 20px;
            }
            
            .section-title {
                font-size: 1.5em;
            }
        }
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>📊 Data Analysis Report</h1>
            <div class="report-meta">
                <div><strong>Session ID:</strong> {{ session_id }}</div>
                <div class="timestamp"><strong>Generated:</strong> {{ timestamp }}</div>
            </div>
        </div>
        
        <div class="report-content">
            <!-- User Query Section -->
            <div class="section">
                <h2 class="section-title">🔍 Analysis Query</h2>
                <div class="query-box">
                    "{{ user_query }}"
                </div>
            </div>
            
            <!-- Summary Section -->
            {% if analysis_summary %}
            <div class="section">
                <h2 class="section-title">📋 Analysis Summary</h2>
                <div class="summary-box">
                    {{ analysis_summary | replace('\n', '<br>') | safe }}
                </div>
            </div>
            {% endif %}
            
            <!-- Visualizations Section -->
            {% if images %}
            <div class="section">
                <h2 class="section-title">📈 Visualizations</h2>
                {% for image in images %}
                <div class="image-container">
                    <img src="data:image/png;base64,{{ image.base64 }}" 
                         alt="Analysis Chart {{ loop.index }}" 
                         class="chart-image">
                    <div style="margin-top: 10px; color: #666; font-size: 0.9em;">
                        Chart {{ loop.index }}
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="section">
                <h2 class="section-title">📈 Visualizations</h2>
                <div class="no-content">No visualizations generated for this analysis.</div>
            </div>
            {% endif %}
            
            <!-- Data Results Section -->
            {% if dataframes %}
            <div class="section">
                <h2 class="section-title">📊 Data Results</h2>
                {% for df in dataframes %}
                <div class="dataframe-container">
                    <div class="dataframe-title">Dataset {{ loop.index }}</div>
                    <div class="dataframe-content">{{ df.content }}</div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="section">
                <h2 class="section-title">📊 Data Results</h2>
                <div class="no-content">No structured data results generated.</div>
            </div>
            {% endif %}
            
            <!-- Code Section -->
            {% if code %}
            <div class="section">
                <h2 class="section-title">💻 Generated Code</h2>
                <div class="code-block">{{ code }}</div>
            </div>
            {% endif %}
            
            <!-- Execution Outputs Section -->
            {% if execution_outputs %}
            <div class="section">
                <h2 class="section-title">🖥️ Execution Results</h2>
                {% for output in execution_outputs %}
                <div class="execution-output">{{ output }}</div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
        """
    
    def _save_report(self, html_content: str) -> str:
        """Save HTML report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_report_{self.session_id}_{timestamp}.html"
        report_path = self.output_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_path)
    
    def create_report_from_assistant_result(self, assistant_result: Dict[str, Any], 
                                          user_query: str, file_manager=None) -> str:
        """
        Convenience method to create report directly from assistant result.
        
        Args:
            assistant_result: Result from AssistantManager.run_assistant_analysis()
            user_query: Original user query
            file_manager: FileManager instance
            
        Returns:
            Path to generated HTML report
        """
        if not assistant_result.get('success', False):
            raise ValueError("Cannot generate report from failed assistant result")
        
        return self.generate_report(assistant_result, user_query, file_manager)
    
    @staticmethod
    def is_analytical_query(user_query: str) -> bool:
        """
        Determine if a query is analytical and should generate a report.
        
        Args:
            user_query: User's query text
            
        Returns:
            True if query appears to be analytical
        """
        analytical_keywords = [
            'analyze', 'analysis', 'report', 'compare', 'trend', 'correlation',
            'statistics', 'summarize', 'insights', 'pattern', 'distribution',
            'forecast', 'predict', 'model', 'regression', 'visualization',
            'chart', 'graph', 'plot', 'dashboard', 'metrics', 'performance',
            'breakdown', 'segment', 'group by', 'aggregate', 'calculate'
        ]
        
        query_lower = user_query.lower()
        return any(keyword in query_lower for keyword in analytical_keywords)
    
    def cleanup_temp_files(self):
        """Clean up temporary image files"""
        try:
            temp_dir = self.output_dir / "temp_images"
            if temp_dir.exists():
                for file_path in temp_dir.iterdir():
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logging.warning(f"⚠️ Could not delete temp file {file_path}: {e}")
                temp_dir.rmdir()
        except Exception as e:
            logging.warning(f"⚠️ Error cleaning up temp files: {e}")