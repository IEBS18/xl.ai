import os
import json
import requests
import pandas as pd
import time
import platform
import subprocess
from openai import AzureOpenAI
from typing import Dict, Any, List, Optional
import traceback
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

class APIAnalysisAssistant:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZUREAPI"),
            api_version=os.getenv("AZUREVERSION"),
            azure_endpoint=os.getenv("AZUREENDPOINT")
        )
        self.assistant = None
        self.thread = None
        self.setup_assistant()
    
    def setup_assistant(self):
        """Create and configure the assistant"""
        try:
            model_name = os.getenv("AZURE_MODEL_NAME", "gpt-4o")
            print(f"🔧 Using model: {model_name}")
            
            self.assistant = self.client.beta.assistants.create(
                name="API Analysis Expert",
                instructions="""You are an expert API analysis assistant. Your role is to:

1. **API Analysis**: When given an API URL, analyze its structure, response format, and limitations
2. **Field Discovery**: Identify all available fields in API responses and present them to users  
3. **Data Extraction**: Help users select specific fields and extract data accordingly
4. **Code Generation**: Write Python code to fetch, process, and export API data
5. **Local File Export**: Export data in user's preferred format (Excel, CSV, JSON - default JSON) TO THEIR LOCAL SYSTEM

**CRITICAL: Always save files to the user's local Downloads folder, NOT to any sandbox or temporary location.**

**Workflow:**
- When user provides an API URL, immediately analyze it using the analyze_api function
- Show the response structure and available fields
- Ask user which specific fields they want
- Generate and execute code to extract those fields
- Export to their local system using export_data function
- Verify the file was created using verify_file_exists function
- Provide the full local path where they can find their file

**File Handling:**
- ALWAYS use the export_data function to save files locally
- NEVER create files in sandbox environments
- Always verify file creation with verify_file_exists
- Provide clear local file paths to users
- Files should be saved to Downloads folder or Desktop

Be helpful, clear, and always ensure files are saved to the user's actual local system.""",
                model=model_name,
                tools=[
                    {"type": "code_interpreter"},
                    {
                        "type": "function",
                        "function": {
                            "name": "analyze_api",
                            "description": "Analyze an API endpoint to understand its structure and limitations",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "api_url": {
                                        "type": "string",
                                        "description": "The API endpoint URL to analyze"
                                    },
                                    "headers": {
                                        "type": "object",
                                        "description": "Optional headers for the API request"
                                    }
                                },
                                "required": ["api_url"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "export_data",
                            "description": "Export processed data to specified format",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "data": {
                                        "type": "string",
                                        "description": "JSON string of data to export"
                                    },
                                    "filename": {
                                        "type": "string",
                                        "description": "Base filename for export"
                                    },
                                    "format_type": {
                                        "type": "string",
                                        "enum": ["json", "csv", "excel"],
                                        "description": "Export format"
                                    }
                                },
                                "required": ["data", "filename", "format_type"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "open_download_folder",
                            "description": "Open the downloads folder to show the user where their file was saved",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "folder_path": {
                                        "type": "string",
                                        "description": "Path to the folder to open"
                                    }
                                },
                                "required": ["folder_path"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "verify_file_exists",
                            "description": "Verify that a file was successfully created on the user's system",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "file_path": {
                                        "type": "string",
                                        "description": "Full path to the file to verify"
                                    }
                                },
                                "required": ["file_path"]
                            }
                        }
                    }
                ]
            )
            
            self.thread = self.client.beta.threads.create()
            
            print(f"✅ Assistant created with ID: {self.assistant.id}")
            print(f"✅ Thread created with ID: {self.thread.id}")
            
        except Exception as e:
            print(f"❌ Error setting up assistant: {str(e)}")
            raise
    
    def analyze_api_function(self, api_url: str, headers: Optional[Dict] = None) -> str:
        """Function to analyze API - called by assistant"""
        try:
            headers = headers or {}
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    structure = self._analyze_json_structure(data)
                    
                    result = {
                        "success": True,
                        "status_code": response.status_code,
                        "data_type": type(data).__name__,
                        "total_items": len(data) if isinstance(data, list) else 1,
                        "available_fields": structure,
                        "sample_data": data[:2] if isinstance(data, list) else data,
                        "response_headers": dict(response.headers)
                    }
                    
                except json.JSONDecodeError:
                    result = {
                        "success": True,
                        "status_code": response.status_code,
                        "data_type": "text",
                        "content_preview": response.text[:500],
                        "response_headers": dict(response.headers)
                    }
            else:
                result = {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"API returned status code {response.status_code}",
                    "response_preview": response.text[:200]
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
    
    def export_data_function(self, data: str, filename: str, format_type: str) -> str:
        """Function to export data - called by assistant"""
        try:
            parsed_data = json.loads(data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            possible_dirs = [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Desktop"),
                os.getcwd(),
                os.path.expanduser("~")
            ]
            
            downloads_dir = None
            for directory in possible_dirs:
                if os.path.exists(directory) and os.access(directory, os.W_OK):
                    downloads_dir = directory
                    break
            
            if not downloads_dir:
                downloads_dir = os.path.expanduser("~/Downloads")
                os.makedirs(downloads_dir, exist_ok=True)
            
            if format_type.lower() == "excel":
                if isinstance(parsed_data, list):
                    df = pd.DataFrame(parsed_data)
                elif isinstance(parsed_data, dict):
                    df = pd.DataFrame([parsed_data])
                else:
                    df = pd.DataFrame({"data": [parsed_data]})
                
                filename_with_ext = f"{filename}_{timestamp}.xlsx"
                full_path = os.path.join(downloads_dir, filename_with_ext)
                df.to_excel(full_path, index=False)
                
            elif format_type.lower() == "csv":
                if isinstance(parsed_data, list):
                    df = pd.DataFrame(parsed_data)
                elif isinstance(parsed_data, dict):
                    df = pd.DataFrame([parsed_data])
                else:
                    df = pd.DataFrame({"data": [parsed_data]})
                
                filename_with_ext = f"{filename}_{timestamp}.csv"
                full_path = os.path.join(downloads_dir, filename_with_ext)
                df.to_csv(full_path, index=False)
                
            else:
                filename_with_ext = f"{filename}_{timestamp}.json"
                full_path = os.path.join(downloads_dir, filename_with_ext)
                with open(full_path, 'w') as f:
                    json.dump(parsed_data, f, indent=2, default=str)
            
            return json.dumps({
                "success": True,
                "filename": filename_with_ext,
                "full_path": full_path,
                "format": format_type,
                "record_count": len(parsed_data) if isinstance(parsed_data, list) else 1,
                "download_location": downloads_dir,
                "file_size_mb": round(os.path.getsize(full_path) / (1024 * 1024), 2),
                "message": f"File successfully saved to your local system at: {full_path}"
            })
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
    
    def _analyze_json_structure(self, data: Any, prefix: str = "") -> List[str]:
        """Recursively analyze JSON structure"""
        fields = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{prefix}.{key}" if prefix else key
                fields.append(f"{current_path} ({type(value).__name__})")
                
                if isinstance(value, (dict, list)) and len(str(value)) < 1000:
                    fields.extend(self._analyze_json_structure(value, current_path))
        
        elif isinstance(data, list) and data:
            first_item = data[0]
            fields.extend(self._analyze_json_structure(first_item, f"{prefix}[0]"))
            
        return fields
    
    def open_download_folder_function(self, folder_path: str) -> str:
        """Open the downloads folder in file explorer"""
        try:
            system = platform.system()
            
            if system == "Windows":
                os.startfile(folder_path)
            elif system == "Darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])
            
            return json.dumps({
                "success": True,
                "message": f"Opened folder: {folder_path}"
            })
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Could not open folder: {str(e)}"
            })
    
    def verify_file_exists_function(self, file_path: str) -> str:
        """Verify that a file exists on the local system"""
        try:
            if os.path.exists(file_path):
                file_stats = os.stat(file_path)
                return json.dumps({
                    "success": True,
                    "exists": True,
                    "file_path": file_path,
                    "file_size_bytes": file_stats.st_size,
                    "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                    "created_time": datetime.fromtimestamp(file_stats.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                    "message": f"✅ File confirmed to exist at: {file_path}"
                })
            else:
                return json.dumps({
                    "success": False,
                    "exists": False,
                    "file_path": file_path,
                    "message": f"❌ File not found at: {file_path}"
                })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"❌ Error checking file: {str(e)}"
            })
    
    def handle_function_calls(self, tool_calls):
        """Handle function calls from the assistant"""
        tool_outputs = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name == "analyze_api":
                result = self.analyze_api_function(
                    function_args.get("api_url"),
                    function_args.get("headers")
                )
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": result
                })
            
            elif function_name == "export_data":
                result = self.export_data_function(
                    function_args.get("data"),
                    function_args.get("filename"),
                    function_args.get("format_type")
                )
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": result
                })
            
            elif function_name == "open_download_folder":
                result = self.open_download_folder_function(
                    function_args.get("folder_path")
                )
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": result
                })
            
            elif function_name == "verify_file_exists":
                result = self.verify_file_exists_function(
                    function_args.get("file_path")
                )
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": result
                })
        
        return tool_outputs
    
    def chat(self, message: str) -> str:
        """Send message to assistant and get response"""
        try:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=message
            )
            
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id
            )
            
            while True:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=run.id
                )
                
                if run_status.status == "completed":
                    break
                elif run_status.status == "requires_action":
                    tool_outputs = self.handle_function_calls(run_status.required_action.submit_tool_outputs.tool_calls)
                    
                    self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                elif run_status.status in ["failed", "cancelled", "expired"]:
                    error_details = run_status.last_error if hasattr(run_status, 'last_error') and run_status.last_error else "Unknown error"
                    return f"❌ Run failed with status: {run_status.status}. Error: {error_details}"
                else:
                    time.sleep(1)
            
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread.id,
                order="desc",
                limit=1
            )
            
            return messages.data[0].content[0].text.value
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.assistant:
                self.client.beta.assistants.delete(self.assistant.id)
                print(f"🗑️  Assistant {self.assistant.id} deleted")
        except Exception as e:
            print(f"⚠️  Error cleaning up: {str(e)}")

def main():
    assistant = None
    
    try:
        print("🚀 Initializing API Analysis Assistant...")
        assistant = APIAnalysisAssistant()
        
        print("\n🤖 API Analysis Assistant Ready!")
        print("Ask me to analyze any API and I'll help you extract data in your preferred format.")
        print("📁 Files will be automatically saved to your Downloads folder!")
        print("\nExamples:")
        print("  • 'Analyze this API: https://api.example.com/data and export to Excel'")
        print("  • 'I want data from https://api.github.com/users in CSV format'")
        print("  • 'Check this API structure: https://jsonplaceholder.typicode.com/posts'")
        print("  • 'Export the title and body fields to Excel from that posts API'\n")
        
        while True:
            try:
                user_input = input("👤 You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("\n🤖 Assistant: Processing your request...\n")
                
                response = assistant.chat(user_input)
                print(f"🤖 Assistant: {response}")
                
                if "full_path" in response and "✅" in response:
                    print("\n📁 File saved successfully!")
                    print("💡 You can find your file in your Downloads folder or the current directory.")
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ An error occurred: {str(e)}\n")
    
    finally:
        if assistant:
            assistant.cleanup()

if __name__ == "__main__":
    required_vars = ["AZUREAPI", "AZUREVERSION", "AZUREENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these environment variables:")
        for var in missing_vars:
            print(f"  export {var}='your-value-here'")
        print("  export AZURE_MODEL_NAME='your-deployment-name'  # Optional, defaults to 'gpt-4'")
        print("\nThen run the script again.")
    else:
        print("🔍 Environment variables found:")
        print(f"  API Endpoint: {os.getenv('AZUREENDPOINT')}")
        print(f"  API Version: {os.getenv('AZUREVERSION')}")
        print(f"  Model Name: {os.getenv('AZURE_MODEL_NAME', 'gpt-4')}")
        print()
        main()