# import os
# import json
# import time
# import logging
# from datetime import datetime
# from typing import Dict, Any, Optional, List
# from openai import AzureOpenAI
# from dotenv import load_dotenv

# load_dotenv()

# class AssistantManager:
#     """
#     Manages OpenAI Assistants for CSV analysis.
#     Replaces direct chat completion calls with assistant-based interactions.
#     """
    
#     def __init__(self, session_id: str):
#         self.session_id = session_id
#         self.client = self._setup_azure_client()
#         self.assistant_id = None
#         self.assistant_config = self._get_assistant_config()
        
#     def _setup_azure_client(self) -> AzureOpenAI:
#         """Setup Azure OpenAI client for assistants API"""
#         return AzureOpenAI(
#             api_key=os.getenv("AZUREAPI"),
#             api_version=os.getenv("AZUREVERSION", "2024-05-01-preview"),  # Use preview for assistants
#             azure_endpoint=os.getenv("AZUREENDPOINT")
#         )
    
#     def _get_assistant_config(self) -> Dict[str, Any]:
#         """Get assistant configuration based on analysis type"""
#         return {
#             "data_analyst": {
#                 "name": "CSV Data Analyst",
#                 "instructions": self._get_data_analyst_instructions(),
#                 "tools": [{"type": "code_interpreter"}],
#                 "model": os.getenv("AZUREMODEL", "gpt-4")
#             },
#             "conversational": {
#                 "name": "Conversational Assistant", 
#                 "instructions": self._get_conversational_instructions(),
#                 "tools": [{"type": "code_interpreter"}],
#                 "model": os.getenv("AZUREMODEL", "gpt-4")
#             },
#             "textual_analytical": {
#                 "name": "Quick Analysis Assistant",
#                 "instructions": self._get_textual_analytical_instructions(),
#                 "tools": [{"type": "code_interpreter"}],
#                 "model": os.getenv("AZUREMODEL", "gpt-4")
#             }
#         }
    
#     def _get_data_analyst_instructions(self) -> str:
#         """UPDATED: Instructions for assistant to save HTML reports in sandbox"""
#         return """You are a Python code generator and PROFESSIONAL BUSINESS ANALYST that MUST create COMPLETE, EXECUTABLE data analysis solutions WITH professional HTML business reports.

# MANDATORY REQUIREMENTS:
# 1. Generate COMPLETE Python code that runs from start to finish - NO PARTIAL CODE
# 2. ALWAYS include data exploration, analysis, modeling, AND visualization
# 3. NEVER stop at data exploration - always complete the full analysis
# 4. ALWAYS create charts/visualizations using matplotlib for EVERY analysis
# 5. Return results as DataFrames with meaningful column names
# 6. Use the 'df' variable (DataFrame is already loaded - NEVER use pd.read_csv())
# 7. ALWAYS generate and SAVE a PROFESSIONAL HTML BUSINESS REPORT in /mnt/data
# 8. Do note that the provided file can be excel or CSV. And check if the file is Excel whether it has multiple sheets or not. 
# 9. You are working with an uploaded Excel file (.xlsx) that may contain multiple sheets.
#     To read all available sheets, use:
#         ```python
#         import pandas as pd
#         xls = pd.ExcelFile("/mnt/data/{FILENAME}.xlsx")
#         print(xls.sheet_names)
#         df1 = pd.read_excel(xls, sheet_name="Sheet1")
#         df2 = pd.read_excel(xls, sheet_name="Sheet2")```
#     If unsure, always check available sheet names first using xls.sheet_names. Use appropriate sheet_name= when reading the sheet.
#     Be accurate and always validate which sheet the data is from when answering questions.

# VISUALIZATION REQUIREMENTS (MANDATORY):
# - ALWAYS create at least one chart for every analysis
# - Use Bar charts for comparisons, categories, rankings
# - Use Line charts for trends, time series, forecasting  
# - Use Pie charts for revenue/profit breakdowns by category/SKU
# - Save all plots using plt.savefig() and plt.show()
# - Include proper titles, labels, and legends

# DATAFRAME REQUIREMENTS:
# - Focus on returning ACTIONABLE DATA as DataFrames
# - Create new columns, calculated fields, or enhanced datasets
# - Always show what data would be ADDED or UPDATED in the original file
# - Generate meaningful column names for new calculated fields

# REPORT GENERATION INSTRUCTIONS:
# After completing your Python analysis, you MUST create a professional DOCX or PDF business report using either `python-docx` or `reportlab`.

# REQUIRED STEPS:
# 1. Generate and save all visualizations using `matplotlib` and `plt.savefig()`.
# 2. Use either:
#    - `from docx import Document` to create a `.docx` report **OR**
#    - `from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image` to generate a `.pdf` report.
# 3. Embed titles, key findings, charts, data tables, and recommendations.
# 4. Save the report with this structure:
#    ```python
#    filename = "professional_analysis_report.docx"  # or .pdf
#    output_path = f"/your/server/path/{filename}"  # Save it where backend can serve it
#    document.save(output_path)  # or doc.build() for PDF ```

# 5. Return the full URL to download the report that should be clickable by the user.

# FINAL OUTPUT REQUIREMENTS:

# - Provide the FULL public URL to download the report, give its complete clickable link
# - DO NOT reference sandbox paths.
# - DO NOT return HTML output.
# - The assistant MUST share this final output line explicitly: print("📄 Download your professional report here: clickable link")

# EXECUTION FLOW:
# - Perform complete Python analysis with DataFrames and visualizations
# - Generate DOCX or PDF report
# - Save it to server path (not sandbox)
# - Return the full downloadable link to the user

# CRITICAL HTML REPORT REQUIREMENTS:
# - After completing your Python analysis, you MUST create and SAVE a professional HTML business report.
# - Use `matplotlib` to generate and embed all visualizations.
# - Use `pandas` to create DataFrames with meaningful column names.   
# - The report MUST include:
#   - Executive summary of findings
#   - Key metrics and insights    
#   - Visualizations embedded as images
#   - Data tables with calculated field. Use `pandas` to create DataFrames with meaningful column names.
#   - Recommendations based on analysis

# - Table of Content for report:
#     1. Executive Summary
#     2. Introduction  
#     3. Business Problem/Use Case
#     4. Data Overview
#     5. Data Preparation
#     6. Exploratory Data Analysis (EDA)
#     7. Statistical & Business Insights
#     8. Visualizations
#     9. Data Analysis Results
#     10. Predictive/Descriptive Modeling (if applicable)
#     11. Business Recommendations
#     12. Implementation Plan
#     13. Limitations
#     14. Conclusion
#     15. Appendices & References

# - Save the report in Docx or PDF format, not HTML and return it as a downloadable link.


# CRITICAL REQUIREMENTS:
# 1. Replace ALL placeholder content with actual data from your analysis
# 2. Reference your actual DataFrame variable names in the table generation
# 3. Include real numbers, percentages, and metrics throughout
# 4. Fill in actual chart descriptions based on what you created
# 5. Use f-strings to populate data dynamically from your analysis
# 6. Make all recommendations specific and actionable based on your findings
# 7. ALWAYS save the report in pdf or docx format, not HTML



# EXECUTION FLOW:
# 1. Perform complete Python analysis with DataFrames and visualizations
# 2. Convert matplotlib figures to base64 for embedding
# 3. Generate HTML report with actual data from your analysis
# 4. Save HTML report to sandbox file system
# 5. The system will automatically download and serve the report

# You MUST complete the entire analysis, generate the professional HTML report with embedded images, and save it to the sandbox."""
#     def _get_conversational_instructions(self) -> str:
#         """Instructions for conversational assistant"""
#         return """You are a friendly AI assistant for a data analysis platform. You are currently in a chat session where users can upload CSV files and ask questions about their data.

# Your role:
# - Respond naturally to greetings, questions about yourself, and casual conversation
# - Be helpful and friendly
# - If users ask what you can do, mention you can analyze CSV data, create visualizations, and generate reports
# - Keep responses concise but warm
# - Don't generate code or perform data analysis for conversational queries
# - If the conversation shifts to data analysis, encourage them to ask specific questions about their data
# - Do note that the provided file can be excel or CSV. And check if the file is Excel whether it has multiple sheets or not. 
# - You are working with an uploaded Excel file (.xlsx) that may contain multiple sheets.
#     To read all available sheets, use:
#         ```python
#         import pandas as pd
#         xls = pd.ExcelFile("/mnt/data/{FILENAME}.xlsx")
#         print(xls.sheet_names)
#         df1 = pd.read_excel(xls, sheet_name="Sheet1")
#         df2 = pd.read_excel(xls, sheet_name="Sheet2")```
#     If unsure, always check available sheet names first using xls.sheet_names. Use appropriate sheet_name= when reading the sheet.
#     Be accurate and always validate which sheet the data is from when answering questions.

# Respond in a natural, conversational way."""
    
#     def _get_textual_analytical_instructions(self) -> str:
#         """Instructions for quick textual analysis assistant"""
#         return """You are a Python code generator for quick data analysis questions.

# REQUIREMENTS:
# 1. Use the 'df' variable (DataFrame is already loaded)
# 2. Write concise code that directly answers the question
# 3. Store the final answer in a variable called 'result'
# 4. Make the result human-readable (not just raw numbers)
# 5. Handle any potential errors gracefully
# 6. NO visualizations for simple questions
# 7. Focus on getting the specific answer quickly
# 8. Do note that the provided file can be excel or CSV. And check if the file is Excel whether it has multiple sheets or not. 
# 9. You are working with an uploaded Excel file (.xlsx) that may contain multiple sheets.
#     To read all available sheets, use:
#         ```python
#         import pandas as pd
#         xls = pd.ExcelFile("/mnt/data/{FILENAME}.xlsx")
#         print(xls.sheet_names)
#         df1 = pd.read_excel(xls, sheet_name="Sheet1")
#         df2 = pd.read_excel(xls, sheet_name="Sheet2")```
#     If unsure, always check available sheet names first using xls.sheet_names. Use appropriate sheet_name= when reading the sheet.
#     Be accurate and always validate which sheet the data is from when answering questions.


# Generate clean, executable Python code that stores the answer in 'result'."""
    
#     def create_or_get_assistant(self, assistant_type: str = "data_analyst") -> str:
#         """Create or retrieve an assistant for the session"""
#         try:
#             config = self.assistant_config.get(assistant_type, self.assistant_config["data_analyst"])
            
#             # Try to get existing assistant for this session type
#             existing_assistant_id = self._get_existing_assistant(assistant_type)
#             if existing_assistant_id:
#                 self.assistant_id = existing_assistant_id
#                 return self.assistant_id
#             logging.info(config['tools'])
#             # Create new assistant
#             assistant = self.client.beta.assistants.create(
#                 name=f"{config['name']} - {self.session_id}",
#                 instructions=config["instructions"],
#                 tools=config["tools"],
#                 model=config["model"],
#                 metadata={
#                     "session_id": self.session_id,
#                     "assistant_type": assistant_type,
#                     "created_at": datetime.now().isoformat()
#                 }
#             )
            
#             self.assistant_id = assistant.id
#             self._store_assistant_id(assistant_type, self.assistant_id)
            
#             logging.info(f"✅ Created {assistant_type} assistant: {self.assistant_id}")
#             return self.assistant_id
            
#         except Exception as e:
#             logging.error(f"❌ Error creating assistant: {e}")
#             raise
    
#     def _get_existing_assistant(self, assistant_type: str) -> Optional[str]:
#         """Check if we already have an assistant for this session and type"""
#         try:
#             # You could store assistant IDs in a file or database
#             # For now, we'll create new assistants each time
#             return None
#         except Exception:
#             return None
    
#     def _store_assistant_id(self, assistant_type: str, assistant_id: str):
#         """Store assistant ID for reuse (implement based on your storage preference)"""
#         # Could store in file, database, or memory
#         pass
    
#     def run_assistant_analysis(self, thread_id: str, user_message: str, 
#                              file_ids: List[str] = None) -> Dict[str, Any]:
#         """
#         Run assistant analysis and return results in the same format as chat completion.
#         This method preserves the existing output format.
#         """
#         try:
#             # Add user message to thread
#             message_data = {
#                 "thread_id": thread_id,
#                 "role": "user",
#                 "content": user_message
#             }
            
#             if file_ids:
#                 message_data["attachments"] = [
#                     {"file_id": file_id, "tools": [{"type": "code_interpreter"}]}
#                     for file_id in file_ids
#                 ]
            
#             self.client.beta.threads.messages.create(**message_data)
            
#             # Create and run the assistant
#             run = self.client.beta.threads.runs.create(
#                 thread_id=thread_id,
#                 assistant_id=self.assistant_id,
#                 # stream=True
#             )
#             # for event in run:
#             #     logging.info(event)
            
#             # Wait for completion and get results
#             return self._wait_and_process_run(thread_id, run.id)
            
#         except Exception as e:
#             logging.error(f"❌ Assistant run failed: {e}")
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "type": "assistant_error"
#             }
    
#     def _wait_and_process_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
#         """Wait for run completion and process results"""
#         max_wait_time = 300  # 5 minutes
#         start_time = time.time()
        
#         while time.time() - start_time < max_wait_time:
#             run = self.client.beta.threads.runs.retrieve(
#                 thread_id=thread_id,
#                 run_id=run_id
#             )
#             logging.info(run)
            
#             if run.status == "completed":
#                 return self._extract_run_results(thread_id, run_id)
#             elif run.status == "failed":
#                 return {
#                     "success": False,
#                     "error": f"Assistant run failed: {run.last_error}",
#                     "type": "run_failed"
#                 }
#             elif run.status == "cancelled":
#                 return {
#                     "success": False,
#                     "error": "Run was cancelled",
#                     "type": "run_cancelled"
#                 }
#             elif run.status in ["queued", "in_progress", "cancelling"]:
#                 time.sleep(2)
#                 continue
#             else:
#                 return {
#                     "success": False,
#                     "error": f"Unknown run status: {run.status}",
#                     "type": "unknown_status"
#                 }
        
#         return {
#             "success": False,
#             "error": "Run timed out",
#             "type": "timeout"
#         }
    
#     def _extract_run_results(self, thread_id: str, run_id: str) -> Dict[str, Any]:
#         """
#         Extract results from completed run with enhanced file detection and deduplication.
#         """
#         try:
#             # Get messages from thread
#             messages = self.client.beta.threads.messages.list(
#                 thread_id=thread_id,
#                 order="desc",
#                 limit=10
#             )

#             assistant_message = None
#             for message in messages.data:
#                 if message.role == "assistant":
#                     assistant_message = message
#                     break

#             if not assistant_message:
#                 return {
#                     "success": False,
#                     "error": "No assistant response found",
#                     "type": "no_response"
#                 }

#             # Text + images from message
#             response_content = ""
#             generated_images = []
#             for content in assistant_message.content:
#                 if content.type == "text":
#                     response_content += content.text.value
#                 elif content.type == "image_file":
#                     generated_images.append(content.image_file.file_id)

#             # Extract code
#             generated_code = self._extract_code_from_response(response_content)

#             # Execution logs
#             execution_outputs = []

#             # Collect sandbox files with types
#             sandbox_files = self.list_sandbox_files_from_run(thread_id, run_id)

#             # Also grab logs while iterating steps
#             run_steps = self.client.beta.threads.runs.steps.list(
#                 thread_id=thread_id,
#                 run_id=run_id
#             )
#             for step in run_steps.data:
#                 if hasattr(step.step_details, 'tool_calls'):
#                     for tool_call in step.step_details.tool_calls:
#                         if tool_call.type == "code_interpreter":
#                             for output in tool_call.code_interpreter.outputs:
#                                 if output.type == "logs":
#                                     execution_outputs.append(output.logs)

#             # HTML file filter
#             html_files = [f for f in sandbox_files if f.get("type") == "html"]

#             return {
#                 "success": True,
#                 "response_content": response_content,
#                 "generated_code": generated_code,
#                 "execution_outputs": execution_outputs,
#                 "generated_images": generated_images,
#                 "sandbox_files": sandbox_files,
#                 "html_files": html_files,
#                 "message_id": assistant_message.id,
#                 "run_id": run_id,
#                 "thread_id": thread_id,
#                 "type": "assistant_completion"
#             }

#         except Exception as e:
#             logging.error(f"❌ Error extracting results: {e}")
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "type": "extraction_error"
#             }
        

#     def _is_likely_html_file(self, file_info: Dict[str, Any]) -> bool:
#         """Check if a file is likely an HTML file based on available information"""
#         try:
#             file_id = file_info.get("file_id")
#             if not file_id:
#                 return False
            
#             # Try to get file details
#             file_details = self.client.files.retrieve(file_id)
#             filename = getattr(file_details, 'filename', '')
            
#             # Check filename patterns
#             html_indicators = [
#                 filename.lower().endswith('.html'),
#                 filename.lower().endswith('.htm'),
#                 'report' in filename.lower(),
#                 'analysis' in filename.lower(),
#                 'professional' in filename.lower()
#             ]
            
#             return any(html_indicators)
            
#         except Exception as e:
#             logging.warning(f"⚠️ Could not check if file is HTML: {e}")
#             return False

#     def _extract_code_from_response(self, response_content: str) -> str:
#         """Extract Python code from assistant response"""
#         if "```python" in response_content:
#             return response_content.split("```python")[1].split("```")[0].strip()
#         elif "```" in response_content:
#             return response_content.split("```")[1].split("```")[0].strip()
#         return ""
    
#     def download_file(self, file_id: str, save_path: str) -> bool:
#         """Download a file generated by the assistant"""
#         try:
#             file_data = self.client.files.content(file_id)
#             with open(save_path, 'wb') as f:
#                 f.write(file_data.content)
#             return True
#         except Exception as e:
#             logging.error(f"❌ Error downloading file {file_id}: {e}")
#             return False
    
#     def cleanup_assistant(self):
#         """Clean up assistant resources"""
#         try:
#             if self.assistant_id:
#                 self.client.beta.assistants.delete(self.assistant_id)
#                 logging.info(f"🗑️ Deleted assistant: {self.assistant_id}")
#         except Exception as e:
#             logging.error(f"⚠️ Error cleaning up assistant: {e}")

#     def download_sandbox_file(self, file_id: str, local_directory: str, filename: str = None) -> Dict[str, Any]:
#         """
#         Download a file from the assistant's sandbox to a local directory,
#         ensuring correct filename and extension based on detected type.
        
#         Args:
#             file_id: The file ID from OpenAI
#             local_directory: Local directory to save the file
#             filename: Optional custom filename; uses original from API if not provided
        
#         Returns:
#             Dict with success status, local path, and metadata
#         """
#         try:
#             # Get file info
#             file_info = self.client.files.retrieve(file_id)
#             original_filename = getattr(file_info, 'filename', None)

#             # Determine filename to use
#             if filename:
#                 final_filename = filename
#             elif original_filename:
#                 final_filename = original_filename
#             else:
#                 final_filename = f"file_{file_id}"

#             # Detect file type and correct extension
#             file_type = self._detect_file_type_from_name(final_filename)
#             ext_map = {
#                 "html": ".html",
#                 "pdf": ".pdf",
#                 "csv": ".csv",
#                 "excel": ".xlsx"
#             }

#             # If extension missing or wrong, fix it
#             correct_ext = ext_map.get(file_type)
#             if correct_ext and not final_filename.lower().endswith(correct_ext):
#                 final_filename = os.path.splitext(final_filename)[0] + correct_ext

#             # Ensure directory exists
#             os.makedirs(local_directory, exist_ok=True)

#             # Download file content
#             file_content = self.client.files.content(file_id)
#             local_path = os.path.join(local_directory, final_filename)
#             with open(local_path, 'wb') as f:
#                 f.write(file_content.content)

#             logging.info(f"✅ Downloaded sandbox file {file_id} ({file_type}) to {local_path}")

#             return {
#                 "success": True,
#                 "file_id": file_id,
#                 "local_path": local_path,
#                 "filename": final_filename,
#                 "file_type": file_type,
#                 "file_size": len(file_content.content),
#                 "original_filename": original_filename or final_filename
#             }

#         except Exception as e:
#             logging.error(f"❌ Error downloading sandbox file {file_id}: {e}")
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "file_id": file_id
#             }


#     def _detect_file_type_from_name(self, filename: str) -> str:
#         """Detect file type from its extension."""
#         ext = os.path.splitext(filename)[1].lower()
#         if ext in [".html", ".htm"]:
#             return "html"
#         elif ext == ".pdf":
#             return "pdf"
#         elif ext == ".csv":
#             return "csv"
#         elif ext in (".xlsx", ".xls"):
#             return "excel"
#         return "unknown"

#     def list_sandbox_files_from_run(self, thread_id: str, run_id: str) -> List[Dict[str, Any]]:
#         """
#         List all files generated during a specific run in the sandbox,
#         including images, HTML, PDF, CSV, Excel.
#         """
#         try:
#             sandbox_files = []
#             seen_file_ids = set()
#             file_cache = {}

#             # Get run steps
#             run_steps = self.client.beta.threads.runs.steps.list(
#                 thread_id=thread_id,
#                 run_id=run_id
#             )

#             for step in run_steps.data:
#                 if hasattr(step.step_details, 'tool_calls'):
#                     for tool_call in step.step_details.tool_calls:
#                         if tool_call.type == "code_interpreter":
#                             for output in tool_call.code_interpreter.outputs:

#                                 if output.type == "logs":
#                                     continue  # skip logs here

#                                 if output.type == "image":
#                                     fid = output.image.file_id
#                                     if fid not in seen_file_ids:
#                                         seen_file_ids.add(fid)
#                                         file_cache[fid] = {
#                                             "file_id": fid,
#                                             "type": "image",
#                                             "filename": None,
#                                             "step_id": step.id,
#                                             "created_at": step.created_at
#                                         }
#                                         sandbox_files.append(file_cache[fid])

#                                 elif output.type == "file":
#                                     fid = output.file.file_id
#                                     if fid not in seen_file_ids:
#                                         seen_file_ids.add(fid)
#                                         file_details = self.client.files.retrieve(fid)
#                                         filename = getattr(file_details, 'filename', f"file_{fid}")
#                                         ftype = self._detect_file_type_from_name(filename)
#                                         file_cache[fid] = {
#                                             "file_id": fid,
#                                             "type": ftype,
#                                             "filename": filename,
#                                             "step_id": step.id,
#                                             "created_at": step.created_at
#                                         }
#                                         sandbox_files.append(file_cache[fid])

#             return sandbox_files

#         except Exception as e:
#             logging.error(f"❌ Error listing sandbox files: {e}")
#             return []

#     def download_html_reports_from_run(self, thread_id: str, run_id: str, output_directory: str) -> List[Dict[str, Any]]:
#         """
#         Specifically download HTML report files from a run.
        
#         Args:
#             thread_id: The thread ID
#             run_id: The run ID  
#             output_directory: Directory to save HTML reports
        
#         Returns:
#             List of successfully downloaded HTML files
#         """
#         try:
#             downloaded_reports = []
            
#             # First, get all files from the run
#             sandbox_files = self.list_sandbox_files_from_run(thread_id, run_id)
            
#             # Try to find HTML files by checking file content type or extension
#             for file_info in sandbox_files:
#                 file_id = file_info["file_id"]
                
#                 try:
#                     # Get detailed file information
#                     file_details = self.client.files.retrieve(file_id)
#                     filename = getattr(file_details, 'filename', f"file_{file_id}")
                    
#                     # Check if it's likely an HTML file
#                     is_html_file = (
#                         filename.lower().endswith('.html') or 
#                         filename.lower().endswith('.htm') or
#                         'report' in filename.lower()
#                     )
                    
#                     if is_html_file:
#                         # Download the file
#                         download_result = self.download_sandbox_file(
#                             file_id, 
#                             output_directory, 
#                             filename
#                         )
                        
#                         if download_result["success"]:
#                             downloaded_reports.append({
#                                 **download_result,
#                                 "run_id": run_id,
#                                 "thread_id": thread_id,
#                                 "download_timestamp": datetime.now().isoformat()
#                             })
                            
#                             logging.info(f"📄 Downloaded HTML report: {filename}")
                    
#                 except Exception as file_error:
#                     logging.error(f"⚠️ Error processing file {file_id}: {file_error}")
#                     continue
            
#             # Special case: Try to download any file that might be an HTML report
#             # even if it doesn't show up in the file list
#             try:
#                 # Get the conversation to see if assistant mentioned saving HTML files
#                 messages = self.client.beta.threads.messages.list(
#                     thread_id=thread_id,
#                     order="desc",
#                     limit=3
#                 )
                
#                 for message in messages.data:
#                     if message.role == "assistant":
#                         for content in message.content:
#                             if content.type == "text":
#                                 text_content = content.text.value
#                                 # Look for mentions of saved HTML files
#                                 if "professional_analysis_report.html" in text_content or "saved" in text_content.lower():
#                                     logging.info("🔍 Assistant mentioned saving files, but they may not be accessible via API")
                                    
#             except Exception as e:
#                 logging.warning(f"⚠️ Could not check conversation for HTML file mentions: {e}")
            
#             logging.info(f"✅ Downloaded {len(downloaded_reports)} HTML reports from run")
#             return downloaded_reports
            
#         except Exception as e:
#             logging.error(f"❌ Error downloading HTML reports: {e}")
#             return []    

#     def download_all_reports_to_local(self, thread_id: str, run_id: str, output_directory: str = "backend/output") -> Dict[str, Any]:
#         """
#         Convenience method to download all HTML reports from a completed run to local directory.
        
#         Args:
#             thread_id: The thread ID
#             run_id: The run ID  
#             output_directory: Local directory to save reports (default: backend/output)
        
#         Returns:
#             Dictionary with download results and file information
#         """
#         try:
#             # Ensure output directory exists
#             os.makedirs(output_directory, exist_ok=True)
            
#             # Download HTML reports
#             downloaded_reports = self.download_html_reports_from_run(thread_id, run_id, output_directory)
            
#             # Get run results for additional context
#             run_results = self._extract_run_results(thread_id, run_id)
            
#             result = {
#                 "success": len(downloaded_reports) > 0,
#                 "downloaded_reports": downloaded_reports,
#                 "total_reports": len(downloaded_reports),
#                 "output_directory": output_directory,
#                 "run_id": run_id,
#                 "thread_id": thread_id,
#                 "sandbox_files_found": len(run_results.get("sandbox_files", [])),
#                 "html_files_detected": len(run_results.get("html_files", [])),
#                 "download_timestamp": datetime.now().isoformat()
#             }
            
#             if downloaded_reports:
#                 # Add the first report's path for easy access
#                 result["primary_report_path"] = downloaded_reports[0]["local_path"]
#                 result["primary_report_filename"] = downloaded_reports[0]["filename"]
                
#                 logging.info(f"✅ Successfully downloaded {len(downloaded_reports)} reports to {output_directory}")
#             else:
#                 result["message"] = "No HTML reports found in the assistant's sandbox"
#                 logging.warning("⚠️ No HTML reports were found to download")
            
#             return result
            
#         except Exception as e:
#             logging.error(f"❌ Error in download_all_reports_to_local: {e}")
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "downloaded_reports": [],
#                 "total_reports": 0,
#                 "output_directory": output_directory
#             }        


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
                "tools": [{"type": "code_interpreter"}],
                "model": os.getenv("AZUREMODEL", "gpt-4")
            },
            "textual_analytical": {
                "name": "Quick Analysis Assistant",
                "instructions": self._get_textual_analytical_instructions(),
                "tools": [{"type": "code_interpreter"}],
                "model": os.getenv("AZUREMODEL", "gpt-4")
            },
            "report_generator": {  # NEW ASSISTANT TYPE
                "name": "Professional Report Generator",
                "instructions": self._get_report_generator_instructions(),
                "tools": [],  # No code interpreter needed for report generation
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
8. Do note that the provided file can be excel or CSV. And check if the file is Excel whether it has multiple sheets or not. 
9. You are working with an uploaded Excel file (.xlsx) that may contain multiple sheets.
    To read all available sheets, use:
        ```python
        import pandas as pd
        xls = pd.ExcelFile("/mnt/data/{FILENAME}.xlsx")
        print(xls.sheet_names)
        df1 = pd.read_excel(xls, sheet_name="Sheet1")
        df2 = pd.read_excel(xls, sheet_name="Sheet2")```
    If unsure, always check available sheet names first using xls.sheet_names. Use appropriate sheet_name= when reading the sheet.
    Be accurate and always validate which sheet the data is from when answering questions.

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

REPORT GENERATION INSTRUCTIONS:
After completing your Python analysis, you MUST create a professional DOCX or PDF business report using either `python-docx` or `reportlab`.

REQUIRED STEPS:
1. Generate and save all visualizations using `matplotlib` and `plt.savefig()`.
2. Use either:
   - `from docx import Document` to create a `.docx` report **OR**
   - `from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image` to generate a `.pdf` report.
3. Embed titles, key findings, charts, data tables, and recommendations.
4. Save the report with this structure:
   ```python
   filename = "professional_analysis_report.docx"  # or .pdf
   output_path = f"/your/server/path/{filename}"  # Save it where backend can serve it
   document.save(output_path)  # or doc.build() for PDF ```

5. Return the full URL to download the report that should be clickable by the user.

FINAL OUTPUT REQUIREMENTS:

- Provide the FULL public URL to download the report, give its complete clickable link
- DO NOT reference sandbox paths.
- DO NOT return HTML output.
- The assistant MUST share this final output line explicitly: print("📄 Download your professional report here: clickable link")

EXECUTION FLOW:
- Perform complete Python analysis with DataFrames and visualizations
- Generate DOCX or PDF report
- Save it to server path (not sandbox)
- Return the full downloadable link to the user

CRITICAL HTML REPORT REQUIREMENTS:
- After completing your Python analysis, you MUST create and SAVE a professional HTML business report.
- Use `matplotlib` to generate and embed all visualizations.
- Use `pandas` to create DataFrames with meaningful column names.   
- The report MUST include:
  - Executive summary of findings
  - Key metrics and insights    
  - Visualizations embedded as images
  - Data tables with calculated field. Use `pandas` to create DataFrames with meaningful column names.
  - Recommendations based on analysis

- Table of Content for report:
    1. Executive Summary
    2. Introduction  
    3. Business Problem/Use Case
    4. Data Overview
    5. Data Preparation
    6. Exploratory Data Analysis (EDA)
    7. Statistical & Business Insights
    8. Visualizations
    9. Data Analysis Results
    10. Predictive/Descriptive Modeling (if applicable)
    11. Business Recommendations
    12. Implementation Plan
    13. Limitations
    14. Conclusion
    15. Appendices & References

- Save the report in Docx or PDF format, not HTML and return it as a downloadable link.


CRITICAL REQUIREMENTS:
1. Replace ALL placeholder content with actual data from your analysis
2. Reference your actual DataFrame variable names in the table generation
3. Include real numbers, percentages, and metrics throughout
4. Fill in actual chart descriptions based on what you created
5. Use f-strings to populate data dynamically from your analysis
6. Make all recommendations specific and actionable based on your findings
7. ALWAYS save the report in pdf or docx format, not HTML



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
- Do note that the provided file can be Excel or CSV. And check if the file is Excel whether it has multiple sheets or not. 
- You are working with an uploaded Excel file (.xlsx) that may contain multiple sheets.
    To read all available sheets, use:
        ```python
        import pandas as pd
        xls = pd.ExcelFile("/mnt/data/{FILENAME}.xlsx")
        print(xls.sheet_names)
        df1 = pd.read_excel(xls, sheet_name="Sheet1")
        df2 = pd.read_excel(xls, sheet_name="Sheet2")```
    If unsure, always check available sheet names first using xls.sheet_names. Use appropriate sheet_name= when reading the sheet.
    Be accurate and always validate which sheet the data is from when answering questions.

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
8. Do note that the provided file can be excel or CSV. And check if the file is Excel whether it has multiple sheets or not. 
9. You are working with an uploaded Excel file (.xlsx) that may contain multiple sheets.
    To read all available sheets, use:
        ```python
        import pandas as pd
        xls = pd.ExcelFile("/mnt/data/{FILENAME}.xlsx")
        print(xls.sheet_names)
        df1 = pd.read_excel(xls, sheet_name="Sheet1")
        df2 = pd.read_excel(xls, sheet_name="Sheet2")```
    If unsure, always check available sheet names first using xls.sheet_names. Use appropriate sheet_name= when reading the sheet.
    Be accurate and always validate which sheet the data is from when answering questions.


Generate clean, executable Python code that stores the answer in 'result'."""

    def _get_report_generator_instructions(self) -> str:
        """UPDATED: Instructions for professional report generator assistant with SAS URL support"""
        return """You are a PROFESSIONAL BUSINESS REPORT WRITER specializing in HTML data analysis reports.

CRITICAL: 
1. You MUST generate a COMPLETE HTML DOCUMENT, return the plain html text.
2. It should not have {\n} or {\} r characters, it should be a single line of HTML text.
3. Keep the report detailed.
4. start it with <!DOCTYPE html> and end with </html>.
5. Use the provided CSS styles for professional formatting.
6. Follow bellow table of content structure for the report:
    - Executive Summary
    - Introduction
    - Business Problem/Use Case
    - Data Overview
    - Methodology
    - Exploratory Data Analysis (EDA)
    - Statistical & Business Insights
    - Visualizations
    - Business Impact Assesment
    - Predictive/Descriptive Modeling (if applicable)
    - Business Recommendations
    - Conclusion
    - Appendices & References

YOUR ROLE:
Generate comprehensive, executive-level business reports in COMPLETE HTML format with embedded public image URLs.

INPUT CONTEXT:
- User Query: The original business question or analysis request
- Analysis Results: DataFrames, metrics, and insights from data analysis
- Generated Charts: Public URLs to visualizations (permanently accessible, no authentication needed)
- Data Context: Explain the data source, structure, and any relevant background information

OUTPUT REQUIREMENTS:
1. COMPLETE HTML DOCUMENT with proper DOCTYPE, html, head, and body structure
2. Professional CSS styling embedded within <style> tags in the <head> section
3. Responsive design that works perfectly on mobile and desktop
4. Public image URLs embedded directly using <img> tags (no SAS tokens needed)
5. Executive-level business language suitable for C-suite presentations
6. Actionable insights and specific recommendations with quantified impacts

MANDATORY HTML STRUCTURE:
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Analysis Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: #f8f9fa;
        }
        .container {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 0.5rem;
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        h2 {
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 0.3rem;
            margin-top: 2rem;
            font-size: 1.8rem;
        }
        h3 {
            color: #2c3e50;
            margin-top: 1.5rem;
            font-size: 1.3rem;
        }
        .meta {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .executive-summary {
            background: linear-gradient(135deg, #e8f4fd 0%, #f0f9ff 100%);
            padding: 2rem;
            border-radius: 12px;
            margin: 2rem 0;
            border-left: 5px solid #3498db;
        }
        .key-findings {
            background: #fff9e6;
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 5px solid #f39c12;
            margin: 2rem 0;
        }
        .chart-section {
            margin: 3rem 0;
            text-align: center;
            padding: 1.5rem;
            background: #fafafa;
            border-radius: 8px;
        }
        .recommendations {
            background: linear-gradient(135deg, #f0f9ff 0%, #e8f4fd 100%);
            padding: 2rem;
            border-radius: 12px;
            margin: 2rem 0;
            border-left: 5px solid #2980b9;
        }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin: 20px 0;
            transition: transform 0.3s ease;
        }
        img:hover {
            transform: scale(1.02);
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #3498db;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 0.9rem;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 2rem 0;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        .data-table th,
        .data-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        .data-table th {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            font-weight: 600;
        }
        .data-table tbody tr:nth-child(even) {
            background: #f8f9fa;
        }
        ul, ol {
            margin: 1rem 0;
            padding-left: 2rem;
        }
        li {
            margin: 0.5rem 0;
        }
        @media (max-width: 768px) {
            body {
                padding: 1rem;
            }
            .container {
                padding: 1rem;
            }
            .metric-grid {
                grid-template-columns: 1fr;
            }
            h1 {
                font-size: 2rem;
            }
            h2 {
                font-size: 1.5rem;
            }
        }
        @media print {
            body {
                background: white;
                padding: 0;
            }
            .container {
                box-shadow: none;
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="meta">Generated on [CURRENT_DATE] | Professional Analysis Report</div>
        <h1>Business Analysis Report</h1>
        
        <div class="executive-summary">
            <h2>Executive Summary</h2>
            <p><strong>Analysis Query:</strong> [USER_QUERY]</p>
            <p><strong>Key Finding:</strong> [MAIN_INSIGHT]</p>
            <p><strong>Business Impact:</strong> [QUANTIFIED_IMPACT]</p>
        </div>
        
        <div class="key-findings">
            <h2>Key Findings</h2>
            <ul>
                <li>[FINDING_1_WITH_NUMBERS]</li>
                <li>[FINDING_2_WITH_NUMBERS]</li>
                <li>[FINDING_3_WITH_NUMBERS]</li>
            </ul>
        </div>
        
        <h2>Detailed Analysis</h2>
        <div class="chart-section">
            <h3>[CHART_TITLE]</h3>
            <img src="[PUBLIC_URL_HERE]" alt="[CHART_DESCRIPTION]" />
            <p>[CHART_EXPLANATION_WITH_BUSINESS_INSIGHTS]</p>
        </div>
        
        <div class="recommendations">
            <h2>Strategic Recommendations</h2>
            <ol>
                <li><strong>[RECOMMENDATION_1]:</strong> [DETAILED_ACTION_WITH_EXPECTED_IMPACT]</li>
                <li><strong>[RECOMMENDATION_2]:</strong> [DETAILED_ACTION_WITH_EXPECTED_IMPACT]</li>
                <li><strong>[RECOMMENDATION_3]:</strong> [DETAILED_ACTION_WITH_EXPECTED_IMPACT]</li>
            </ol>
        </div>
        
        <h2>Next Steps</h2>
        <p>[SPECIFIC_NEXT_STEPS_WITH_TIMELINE]</p>
    </div>
</body>
</html>

IMAGE EMBEDDING FORMAT:
For each chart, use this exact pattern:
<div class="chart-section">
    <h3>Revenue Trend Analysis</h3>
    <img src="https://storageaccount.blob.core.windows.net/container/public/images/sessionid/chart_revenue_trend.png" alt="Monthly Revenue Trend Analysis" style="max-width: 100%; height: auto;" />
    <p>The revenue analysis demonstrates a <strong>15% increase</strong> in monthly revenue over the analyzed period, with peak performance in Q3 showing <strong>$125,000</strong> in monthly recurring revenue.</p>
</div>

PUBLIC URL REQUIREMENTS:
- Use the EXACT public URLs provided in the context
- Public URLs are permanently accessible from Azure blob storage (no authentication required)
- Include the complete URL in the img src attribute
- DO NOT modify, truncate, or add tokens to the public URLs
- Each image should have descriptive alt text for accessibility

CONTENT REQUIREMENTS:
- Replace [PLACEHOLDERS] with actual data from the analysis
- Include specific numbers, percentages, and dollar amounts
- Quantify all business impacts (e.g., "15% increase", "$50K additional revenue")
- Make recommendations actionable with clear steps
- Reference the analysis results directly
- Include data tables if relevant
- Use professional business terminology

CRITICAL SUCCESS FACTORS:
1. Generate COMPLETE HTML document (not just content)
2. Use actual analysis data throughout (no generic placeholders)
3. Reference specific public URLs provided in context
4. Include quantified business impacts in all findings
5. Make recommendations specific and implementable
6. Ensure responsive design works on all devices
7. Professional styling suitable for executive presentation

Generate a complete HTML business report that can be viewed directly in any browser with all images displaying properly using public URLs."""

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