import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class AssistantManager:
    """
    Manages OpenAI Assistants for CSV analysis.
    Replaces direct chat completion calls with assistant-based interactions.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.client = self._setup_azure_client()
        self.assistant_id = None
        self.assistant_config = self._get_assistant_config()
        
    def _setup_azure_client(self) -> AzureOpenAI:
        """Setup Azure OpenAI client for assistants API"""
        return AzureOpenAI(
            api_key=os.getenv("AZUREAPI"),
            api_version=os.getenv("AZUREVERSION", "2024-05-01-preview"),  # Use preview for assistants
            azure_endpoint=os.getenv("AZUREENDPOINT")
        )
    
    def _get_assistant_config(self) -> Dict[str, Any]:
        """Get assistant configuration based on analysis type"""
        return {
            "data_analyst": {
                "name": "CSV Data Analyst",
                "instructions": self._get_data_analyst_instructions(),
                "tools": [{"type": "code_interpreter"}],
                "model": os.getenv("AZUREMODEL", "gpt-4")
            },
            "conversational": {
                "name": "Conversational Assistant", 
                "instructions": self._get_conversational_instructions(),
                "tools": [],
                "model": os.getenv("AZUREMODEL", "gpt-4")
            },
            "textual_analytical": {
                "name": "Quick Analysis Assistant",
                "instructions": self._get_textual_analytical_instructions(),
                "tools": [{"type": "code_interpreter"}],
                "model": os.getenv("AZUREMODEL", "gpt-4")
            }
        }
    
    def _get_data_analyst_instructions(self) -> str:
        """UPDATED: Instructions for assistant to save HTML reports in sandbox"""
        return """You are a Python code generator and PROFESSIONAL BUSINESS ANALYST that MUST create COMPLETE, EXECUTABLE data analysis solutions WITH professional HTML business reports.

MANDATORY REQUIREMENTS:
1. Generate COMPLETE Python code that runs from start to finish - NO PARTIAL CODE
2. ALWAYS include data exploration, analysis, modeling, AND visualization
3. NEVER stop at data exploration - always complete the full analysis
4. ALWAYS create charts/visualizations using matplotlib for EVERY analysis
5. Return results as DataFrames with meaningful column names
6. Use the 'df' variable (DataFrame is already loaded - NEVER use pd.read_csv())
7. ALWAYS generate and SAVE a PROFESSIONAL HTML BUSINESS REPORT in /mnt/data

VISUALIZATION REQUIREMENTS (MANDATORY):
- ALWAYS create at least one chart for every analysis
- Use Bar charts for comparisons, categories, rankings
- Use Line charts for trends, time series, forecasting  
- Use Pie charts for revenue/profit breakdowns by category/SKU
- Save all plots using plt.savefig() and plt.show()
- Include proper titles, labels, and legends

DATAFRAME REQUIREMENTS:
- Focus on returning ACTIONABLE DATA as DataFrames
- Create new columns, calculated fields, or enhanced datasets
- Always show what data would be ADDED or UPDATED in the original file
- Generate meaningful column names for new calculated fields

CRITICAL HTML REPORT REQUIREMENTS:
After completing your Python analysis, you MUST create and SAVE a professional HTML business report.

Use this EXACT code structure at the end of your analysis:

```python
# Generate Professional HTML Report
import base64
from io import BytesIO
from datetime import datetime

# Convert matplotlib figures to base64 for embedding
def get_figure_as_base64(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    return f"data:image/png;base64,{img_base64}"

# Get all matplotlib figures as base64
import matplotlib.pyplot as plt
figure_images = []
for fig_num in plt.get_fignums():
    fig = plt.figure(fig_num)
    img_data = get_figure_as_base64(fig)
    figure_images.append(img_data)

# Create the HTML report with embedded images
html_report = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Professional Title Based on Your Analysis]</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: #f8f9fa;
        }}
        .report-container {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .report-header {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 2rem;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 2rem;
        }}
        .report-header h1 {{ color: white; margin: 0; font-size: 2rem; }}
        .meta {{ color: #6b7280; font-size: 0.9rem; text-align: center; margin-bottom: 2rem; }}
        h2 {{ color: #1e40af; border-bottom: 2px solid #3b82f6; padding-bottom: 0.5rem; margin-top: 2rem; }}
        h3 {{ color: #374151; margin-top: 1.5rem; }}
        .executive-summary {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 1.5rem; margin: 1.5rem 0; border-radius: 0 8px 8px 0; }}
        .key-finding {{ background: #f0f9ff; border-left: 4px solid #10b981; padding: 1rem; margin: 1rem 0; border-radius: 0 6px 6px 0; }}
        .recommendation {{ background: #fefce8; border-left: 4px solid #f59e0b; padding: 1rem; margin: 1rem 0; border-radius: 0 6px 6px 0; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
        .stat-card {{ background: #f8fafc; padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid #e2e8f0; }}
        .stat-number {{ font-size: 1.5rem; font-weight: bold; color: #1e40af; }}
        .stat-label {{ color: #64748b; font-size: 0.875rem; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }}
        th {{ background: #f8fafc; padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #e2e8f0; }}
        td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; }}
        tr:nth-child(even) {{ background: #f8fafc; }}
        .image-container {{ text-align: center; margin: 2rem 0; background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .image-container img {{ max-width: 100%; height: auto; border-radius: 8px; }}
        .image-caption {{ margin-top: 1rem; color: #6b7280; font-size: 0.875rem; font-style: italic; }}
        ul {{ list-style-type: disc; padding-left: 2rem; }}
        li {{ margin: 0.5rem 0; }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>[Write a professional title based on your specific analysis]</h1>
        </div>
        
        <div class="meta">
            <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | <strong>Report Type:</strong> Executive Data Analysis</p>
            <p><strong>Dataset:</strong> {df.shape[0]:,} records × {df.shape[1]} variables</p>
        </div>

        <div class="executive-summary">
            <h2>Executive Summary</h2>
            <p>[Write 2-3 specific paragraphs summarizing your key findings with actual numbers, percentages, and business impact from your analysis. Include the most important insights that executives need to know.]</p>
        </div>

        <h2>Data Overview</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{df.shape[0]:,}</div>
                <div class="stat-label">Total Records</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{df.shape[1]}</div>
                <div class="stat-label">Variables Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">[Actual key metric from your analysis]</div>
                <div class="stat-label">Key Performance Indicator</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">[Actual data quality percentage]</div>
                <div class="stat-label">Data Completeness</div>
            </div>
        </div>
        <p>[Describe the dataset characteristics, analysis methodology, and data quality assessment with actual findings]</p>

        <h2>Key Findings</h2>
        <div class="key-finding">
            <h3>[Finding 1: Write actual finding from your analysis]</h3>
            <p>[Describe the specific finding with numbers and percentages from your analysis]</p>
        </div>
        <div class="key-finding">
            <h3>[Finding 2: Write actual finding from your analysis]</h3>
            <p>[Describe another specific finding with metrics from your analysis]</p>
        </div>
        <div class="key-finding">
            <h3>[Finding 3: Write actual finding from your analysis]</h3>
            <p>[Describe third specific finding with quantitative results]</p>
        </div>

        <h2>Detailed Analysis Results</h2>
        <p>The following tables present the comprehensive analytical findings:</p>
        
        <h3>1. [Name of first DataFrame variable you created]</h3>
        <p><strong>Purpose:</strong> [Explain what business question this DataFrame answers]</p>
        <p><strong>Key Insights:</strong> [List 3-5 specific insights from this DataFrame]</p>
        <table>
            <thead>
                <tr>
                    [Write the actual column headers from your first DataFrame using: {''.join(f'<th>{col}</th>' for col in first_dataframe.columns)}]
                </tr>
            </thead>
            <tbody>
                [Write actual rows of data from your first DataFrame using: {''.join(f'<tr>{''.join(f'<td>{val}</td>' for val in row)}</tr>' for idx, row in first_dataframe.head(15).iterrows())}]
            </tbody>
        </table>

        <h3>2. [Name of second DataFrame variable you created]</h3>
        <p><strong>Purpose:</strong> [Explain what this DataFrame shows]</p>
        <table>
            <thead>
                <tr>
                    [Write actual column headers from your second DataFrame]
                </tr>
            </thead>
            <tbody>
                [Write actual data rows from your second DataFrame]
            </tbody>
        </table>

        [Continue for each DataFrame you created in your analysis]

        <h2>Data Visualizations</h2>
        <p>The following charts provide visual insights into the analytical findings:</p>'''

# Add embedded images to the HTML
for i, img_data in enumerate(figure_images, 1):
    html_report += f'''
        <div class="image-container">
            <h3>Figure {i}: [Write actual title describing this chart based on what you created]</h3>
            <img src="{img_data}" alt="Analysis Chart {i}" />
            <div class="image-caption">
                <strong>Chart Type:</strong> [Bar chart/Line chart/Pie chart - whatever you used]<br>
                <strong>Key Insights:</strong> [Describe what patterns, trends, or outliers this chart reveals and their business significance]
            </div>
        </div>'''

html_report += '''
        <h2>Business Implications</h2>
        <p><strong>Strategic Impact:</strong> [How your findings impact business strategy, operations, revenue, costs - be specific]</p>
        <p><strong>Competitive Advantage:</strong> [Opportunities identified for competitive positioning]</p>
        <p><strong>Risk Assessment:</strong> [Potential risks or concerns revealed by the analysis]</p>
        <p><strong>Financial Impact:</strong> [Quantified financial implications where possible - revenue, cost savings, ROI]</p>

        <h2>Recommendations and Action Items</h2>
        
        <div class="recommendation">
            <h3>Immediate Actions (0-30 days)</h3>
            <ul>
                <li>[Specific, actionable recommendation with timeline and expected impact based on your analysis]</li>
                <li>[Specific, actionable recommendation with timeline and expected impact based on your analysis]</li>
                <li>[Specific, actionable recommendation with timeline and expected impact based on your analysis]</li>
            </ul>
        </div>

        <div class="recommendation">
            <h3>Strategic Initiatives (1-6 months)</h3>
            <ul>
                <li>[Medium-term recommendation with business impact and resource requirements based on findings]</li>
                <li>[Medium-term recommendation with business impact and resource requirements based on findings]</li>
            </ul>
        </div>

        <h2>Technical Summary</h2>
        <p><strong>Analysis Methods:</strong> [List the analytical techniques you actually used in your code]</p>
        <p><strong>Data Quality:</strong> [Comment on data completeness and reliability based on your analysis]</p>
        <p><strong>Statistical Confidence:</strong> [Discuss confidence in your results - R-squared, p-values, etc.]</p>
        <p><strong>Limitations:</strong> [Any limitations or assumptions in your analysis]</p>

        <h2>Conclusion</h2>
        <p>[Write a comprehensive conclusion that synthesizes all your findings into clear, actionable insights for executives. Include the most important takeaways and next steps based on your actual analysis results.]</p>

        <div style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #e2e8f0; text-align: center; color: #64748b; font-size: 0.875rem;">
            <p>This professional business report was generated through advanced AI-powered data analysis.</p>
            <p>All findings and recommendations are based on comprehensive statistical analysis of the provided dataset.</p>
        </div>
    </div>
</body>
</html>'''

# Save the HTML report to sandbox
report_filename = "professional_analysis_report.html"
with open(report_filename, 'w', encoding='utf-8') as f:
    f.write(html_report)

print(f"✅ Professional HTML report saved as: {report_filename}")
print(f"📊 Report includes {len(figure_images)} embedded visualizations")
print(f"📄 Report contains detailed analysis of {df.shape[0]:,} records")
```

CRITICAL REQUIREMENTS:
1. Replace ALL placeholder content with actual data from your analysis
2. Reference your actual DataFrame variable names in the table generation
3. Include real numbers, percentages, and metrics throughout
4. Fill in actual chart descriptions based on what you created
5. Use f-strings to populate data dynamically from your analysis
6. Make all recommendations specific and actionable based on your findings
7. ALWAYS save the HTML file at the end of your analysis

EXECUTION FLOW:
1. Perform complete Python analysis with DataFrames and visualizations
2. Convert matplotlib figures to base64 for embedding
3. Generate HTML report with actual data from your analysis
4. Save HTML report to sandbox file system
5. The system will automatically download and serve the report

You MUST complete the entire analysis, generate the professional HTML report with embedded images, and save it to the sandbox."""
    def _get_conversational_instructions(self) -> str:
        """Instructions for conversational assistant"""
        return """You are a friendly AI assistant for a data analysis platform. You are currently in a chat session where users can upload CSV files and ask questions about their data.

Your role:
- Respond naturally to greetings, questions about yourself, and casual conversation
- Be helpful and friendly
- If users ask what you can do, mention you can analyze CSV data, create visualizations, and generate reports
- Keep responses concise but warm
- Don't generate code or perform data analysis for conversational queries
- If the conversation shifts to data analysis, encourage them to ask specific questions about their data

Respond in a natural, conversational way."""
    
    def _get_textual_analytical_instructions(self) -> str:
        """Instructions for quick textual analysis assistant"""
        return """You are a Python code generator for quick data analysis questions.

REQUIREMENTS:
1. Use the 'df' variable (DataFrame is already loaded)
2. Write concise code that directly answers the question
3. Store the final answer in a variable called 'result'
4. Make the result human-readable (not just raw numbers)
5. Handle any potential errors gracefully
6. NO visualizations for simple questions
7. Focus on getting the specific answer quickly

Generate clean, executable Python code that stores the answer in 'result'."""
    
    def create_or_get_assistant(self, assistant_type: str = "data_analyst") -> str:
        """Create or retrieve an assistant for the session"""
        try:
            config = self.assistant_config.get(assistant_type, self.assistant_config["data_analyst"])
            
            # Try to get existing assistant for this session type
            existing_assistant_id = self._get_existing_assistant(assistant_type)
            if existing_assistant_id:
                self.assistant_id = existing_assistant_id
                return self.assistant_id
            logging.info(config['tools'])
            # Create new assistant
            assistant = self.client.beta.assistants.create(
                name=f"{config['name']} - {self.session_id}",
                instructions=config["instructions"],
                tools=config["tools"],
                model=config["model"],
                metadata={
                    "session_id": self.session_id,
                    "assistant_type": assistant_type,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            self.assistant_id = assistant.id
            self._store_assistant_id(assistant_type, self.assistant_id)
            
            logging.info(f"✅ Created {assistant_type} assistant: {self.assistant_id}")
            return self.assistant_id
            
        except Exception as e:
            logging.error(f"❌ Error creating assistant: {e}")
            raise
    
    def _get_existing_assistant(self, assistant_type: str) -> Optional[str]:
        """Check if we already have an assistant for this session and type"""
        try:
            # You could store assistant IDs in a file or database
            # For now, we'll create new assistants each time
            return None
        except Exception:
            return None
    
    def _store_assistant_id(self, assistant_type: str, assistant_id: str):
        """Store assistant ID for reuse (implement based on your storage preference)"""
        # Could store in file, database, or memory
        pass
    
    def run_assistant_analysis(self, thread_id: str, user_message: str, 
                             file_ids: List[str] = None) -> Dict[str, Any]:
        """
        Run assistant analysis and return results in the same format as chat completion.
        This method preserves the existing output format.
        """
        try:
            # Add user message to thread
            message_data = {
                "thread_id": thread_id,
                "role": "user",
                "content": user_message
            }
            
            if file_ids:
                message_data["attachments"] = [
                    {"file_id": file_id, "tools": [{"type": "code_interpreter"}]}
                    for file_id in file_ids
                ]
            
            self.client.beta.threads.messages.create(**message_data)
            
            # Create and run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
                # stream=True
            )
            # for event in run:
            #     logging.info(event)
            
            # Wait for completion and get results
            return self._wait_and_process_run(thread_id, run.id)
            
        except Exception as e:
            logging.error(f"❌ Assistant run failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "assistant_error"
            }
    
    def _wait_and_process_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Wait for run completion and process results"""
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            logging.info(run)
            
            if run.status == "completed":
                return self._extract_run_results(thread_id, run_id)
            elif run.status == "failed":
                return {
                    "success": False,
                    "error": f"Assistant run failed: {run.last_error}",
                    "type": "run_failed"
                }
            elif run.status == "cancelled":
                return {
                    "success": False,
                    "error": "Run was cancelled",
                    "type": "run_cancelled"
                }
            elif run.status in ["queued", "in_progress", "cancelling"]:
                time.sleep(2)
                continue
            else:
                return {
                    "success": False,
                    "error": f"Unknown run status: {run.status}",
                    "type": "unknown_status"
                }
        
        return {
            "success": False,
            "error": "Run timed out",
            "type": "timeout"
        }
    
    def _extract_run_results(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Extract results from completed run in compatible format"""
        try:
            # Get messages from thread
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=10
            )
            
            # Get the latest assistant message
            assistant_message = None
            for message in messages.data:
                if message.role == "assistant":
                    assistant_message = message
                    break
            
            if not assistant_message:
                return {
                    "success": False,
                    "error": "No assistant response found",
                    "type": "no_response"
                }
            
            # Extract content
            response_content = ""
            generated_images = []
            
            for content in assistant_message.content:
                if content.type == "text":
                    response_content += content.text.value
                elif content.type == "image_file":
                    # Handle generated images
                    generated_images.append(content.image_file.file_id)
            
            # Extract code from response if present
            generated_code = self._extract_code_from_response(response_content)
            
            # Get run steps for additional outputs
            run_steps = self.client.beta.threads.runs.steps.list(
                thread_id=thread_id,
                run_id=run_id
            )
            
            execution_outputs = []
            for step in run_steps.data:
                if hasattr(step.step_details, 'tool_calls'):
                    for tool_call in step.step_details.tool_calls:
                        if tool_call.type == "code_interpreter":
                            for output in tool_call.code_interpreter.outputs:
                                if output.type == "logs":
                                    execution_outputs.append(output.logs)
                                elif output.type == "image":
                                    generated_images.append(output.image.file_id)
            
            # Return in compatible format
            return {
                "success": True,
                "response_content": response_content,
                "generated_code": generated_code,
                "execution_outputs": execution_outputs,
                "generated_images": generated_images,
                "message_id": assistant_message.id,
                "type": "assistant_completion"
            }
            
        except Exception as e:
            logging.error(f"❌ Error extracting results: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "extraction_error"
            }
    
    def _extract_code_from_response(self, response_content: str) -> str:
        """Extract Python code from assistant response"""
        if "```python" in response_content:
            return response_content.split("```python")[1].split("```")[0].strip()
        elif "```" in response_content:
            return response_content.split("```")[1].split("```")[0].strip()
        return ""
    
    def download_file(self, file_id: str, save_path: str) -> bool:
        """Download a file generated by the assistant"""
        try:
            file_data = self.client.files.content(file_id)
            with open(save_path, 'wb') as f:
                f.write(file_data.content)
            return True
        except Exception as e:
            logging.error(f"❌ Error downloading file {file_id}: {e}")
            return False
    
    def cleanup_assistant(self):
        """Clean up assistant resources"""
        try:
            if self.assistant_id:
                self.client.beta.assistants.delete(self.assistant_id)
                logging.info(f"🗑️ Deleted assistant: {self.assistant_id}")
        except Exception as e:
            logging.error(f"⚠️ Error cleaning up assistant: {e}")