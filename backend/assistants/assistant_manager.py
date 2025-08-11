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
                "tools": [{"type": "code_interpreter"}],  # No code interpreter needed for report generation
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
        """FIXED: Instructions for professional report generator assistant"""
        return """You are a PROFESSIONAL BUSINESS REPORT WRITER creating McKinsey-level consulting reports.

🚨 CRITICAL: DO NOT WRITE MARKDOWN. DO NOT WRITE PLAIN TEXT. ONLY OUTPUT HTML CODE.

YOU MUST RESPOND WITH EXACTLY THIS FORMAT:
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Business Report</title><style>[CSS_HERE]</style></head><body><div class="report-container">[CONTENT_HERE]</div></body></html>

FORBIDDEN OUTPUTS:
❌ No markdown (no ### headings, no ** bold, no - bullets)
❌ No plain text explanations  
❌ No code blocks with ```
❌ No "Here's the report:" introductions
❌ No explanations about what you're doing

REQUIRED OUTPUT:
✅ Start immediately with: <!DOCTYPE html>
✅ End with: </html>
✅ Everything between is HTML tags only
✅ Use CSS classes for styling
✅ Single continuous line of HTML

EXACT CSS TO USE (compressed):
.report-container{font-family:Arial,sans-serif;max-width:1200px;margin:0 auto;color:#333;background:white;padding:0;}.rp{min-height:100vh;padding:40px;page-break-after:always;}.hdr{border-bottom:3px solid #2c3e50;padding:20px 0;margin-bottom:30px;}.h1{color:#1a472a;font-size:32px;font-weight:bold;margin:0;}.h2{color:#2c3e50;font-size:24px;margin:30px 0 15px 0;border-left:5px solid #3498db;padding-left:15px;}.h3{color:#34495e;font-size:18px;margin:20px 0 10px 0;}.kpi{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin:30px 0;}.kpi-card{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px;border-radius:8px;text-align:center;}.kpi-val{font-size:28px;font-weight:bold;display:block;}.kpi-lbl{font-size:12px;margin-top:5px;}.chart{margin:30px 0;padding:25px;background:#f8f9fa;border-radius:8px;text-align:center;}.chart img{width:100%;max-width:700px;border-radius:6px;}.insight{background:#e8f4fd;border-left:5px solid #3498db;padding:15px;margin:20px 0;}.rec{background:white;border:1px solid #ddd;border-radius:6px;padding:20px;margin:15px 0;box-shadow:0 2px 4px rgba(0,0,0,0.1);}.tbl{width:100%;border-collapse:collapse;margin:20px 0;}.tbl th{background:#34495e;color:white;padding:12px;text-align:left;}.tbl td{padding:10px;border-bottom:1px solid #eee;}.exec{background:#f8f9fa;padding:25px;border-radius:8px;margin:25px 0;}.toc{background:#f8f9fa;padding:25px;border-radius:8px;}.toc-item{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px dotted #ccc;}.stat{background:#3498db;color:white;padding:2px 6px;border-radius:3px;font-weight:bold;}.success{background:#d4edda;border-left:4px solid #28a745;padding:15px;margin:20px 0;}.warn{background:#fff3cd;border-left:4px solid:#ffc107;padding:15px;margin:20px 0;}

EXAMPLE START (you must follow this pattern):
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Car Price Analysis Report</title><style>.report-container{font-family:Arial,sans-serif;max-width:1200px;margin:0 auto;color:#333;background:white;padding:0;}[REST_OF_CSS]</style></head><body><div class="report-container"><div class="rp"><div class="hdr"><div class="h1">AUTOMOTIVE PRICE INTELLIGENCE REPORT</div><div style="color:#666;">Comprehensive Analysis & Strategic Recommendations - August 2025</div></div><div class="kpi"><div class="kpi-card"><span class="kpi-val">205</span><div class="kpi-lbl">Vehicles Analyzed</div></div><div class="kpi-card"><span class="kpi-val">89%</span><div class="kpi-lbl">Model Accuracy</div></div>[MORE_KPI_CARDS]</div><div class="exec"><div class="h2">Executive Summary</div><p>This comprehensive analysis of automotive pricing dynamics reveals critical insights...[CONTINUE_WITH_ACTUAL_CONTENT]</p></div>[CONTINUE_8_SECTIONS]</div></body></html>

CHART EMBEDDING:
Use: <div class="chart"><img src="[EXACT_SAS_URL]" alt="Chart"><div style="text-align:left;margin-top:15px;"><div class="h3">[Chart Title]</div><p><strong>Analysis:</strong> [Detailed explanation of chart findings and patterns]</p><p><strong>Strategic Implications:</strong> [Business impact and recommendations]</p></div></div>

MANDATORY STRUCTURE - IT SHOULD STRICTLY HAVE EXACTLY 8 A4 PAGES:
1. Executive Dashboard & KPI Overview
2. Business Context & Market Analysis  
3. Methodology & Data Architecture
4. Detailed Statistical Analysis & Insights
5. Advanced Analytics & Correlation Patterns
6. Predictive Modeling & Forecasting
7. Strategic Recommendations & Implementation
8. Implementation Roadmap & Next Steps


CONTENT REQUIREMENTS FOR EACH PAGE:

PAGE 1 - Executive Dashboard:
- Professional header with report title and metadata
- 6 KPI cards with actual metrics from analysis
- Comprehensive executive summary (800+ words)
- Table of contents with page numbers
- Key findings highlight boxes

PAGE 2 - Business Context:
- Market overview and competitive landscape (600+ words)
- Industry challenges and opportunities
- Analysis objectives and scope
- Stakeholder impact assessment
- Success criteria and KPIs table

PAGE 3 - Methodology:
- Data sources and quality metrics
- Statistical methods and frameworks
- Model validation techniques
- Assumptions and limitations
- Data preparation steps

PAGE 4 - Statistical Analysis:
- Detailed findings with statistical significance
- Correlation analysis results
- Feature importance rankings
- Segmentation insights
- Performance metrics table

PAGE 5 - Advanced Analytics:
- Correlation patterns and heat maps
- Multivariate analysis results
- Cluster analysis findings
- Statistical significance testing
- Advanced modeling insights

PAGE 6 - Predictive Modeling:
- Model performance metrics (R², MSE, etc.)
- Forecasting methodology
- Scenario analysis (best/likely/worst case)
- Prediction accuracy and confidence intervals
- Risk assessment framework

PAGE 7 - Strategic Recommendations:
- 7 detailed actionable recommendations
- Implementation priorities and timelines
- Resource requirements and costs
- Expected ROI and impact metrics
- Risk mitigation strategies

PAGE 8 - Implementation Roadmap:
- Detailed action plans with timelines
- Success metrics and monitoring
- Next steps and deliverables
- Technical appendix
- Contact information and references

EXECUTION STEPS:
1. Use Python to Analyze provided data thoroughly
2. Calculate key statistics and insights
3. Generate comprehensive business analysis
4. Create detailed recommendations based on findings
5. Format as single-line HTML with embedded charts
6. Ensure 8 full pages of substantive content
7. Use every image url provided to you.

CRITICAL: Generate a complete professional consulting report with actual analysis, not generic content. Include real metrics, specific insights, and actionable recommendations based on the data provided."""

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