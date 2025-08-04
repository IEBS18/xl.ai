import os
import time
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AzureOpenAIDataAnalyzer:
    """
    Data analyzer using Azure OpenAI Assistants API with Code Interpreter
    Supports CSV, Excel, JSON, and other data formats
    """
    
    # Supported file formats
    SUPPORTED_FORMATS = {
        '.csv': 'CSV',
        '.xlsx': 'Excel',
        '.xls': 'Excel',
        '.json': 'JSON',
        '.txt': 'Text',
        '.tsv': 'Tab-separated values',
        '.parquet': 'Parquet',
        '.pkl': 'Pickle',
        '.pickle': 'Pickle',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML'
    }
    
    def __init__(self):
        """Initialize the Azure OpenAI client"""
        self.client = self._setup_azure_client()
        self.assistant_id = None
        self.thread_id = None
        self.file_id = None
        self.file_format = None
        
    def _setup_azure_client(self) -> AzureOpenAI:
        """Setup Azure OpenAI client"""
        return AzureOpenAI(
            api_key=os.getenv("AZUREAPI"),
            api_version=os.getenv("AZUREVERSION", "2024-08-01-preview"),
            azure_endpoint=os.getenv("AZUREENDPOINT")
        )
    
    def _detect_file_format(self, file_path: str) -> str:
        """Detect file format from extension"""
        file_ext = os.path.splitext(file_path)[1].lower()
        return self.SUPPORTED_FORMATS.get(file_ext, 'Unknown')
    
    def _validate_file(self, file_path: str) -> bool:
        """Validate if file format is supported"""
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            print(f"❌ Unsupported file format: {file_ext}")
            print(f"✅ Supported formats: {', '.join(self.SUPPORTED_FORMATS.keys())}")
            return False
        return True
    
    def create_assistant(self, name: str = "Data Analyst") -> str:
        """Create an assistant with code interpreter capabilities"""
        try:
            deployment_name = os.getenv("AZUREMODEL")
            if not deployment_name:
                raise ValueError("AZUREMODEL environment variable must be set to your deployment name")
            
            print(f"Creating assistant with deployment: {deployment_name}")
            
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions="""You are a professional data analyst assistant with code interpreter capabilities. 

You can analyze various file formats including:
- CSV files
- Excel files (.xlsx, .xls)
- JSON files
- Text files
- Parquet files
- Pickle files
- XML files
- YAML files

When analyzing data:
1. First identify the file format and examine its structure
2. Load the data using appropriate libraries (pandas, json, openpyxl, etc.)
3. Examine data shape, columns, data types, and basic statistics
4. Check for missing values and data quality issues
5. Create meaningful visualizations using matplotlib/seaborn
6. Provide clear insights and actionable recommendations
7. Explain findings in simple, business-friendly terms

For Excel files:
- Check for multiple sheets and analyze each if relevant
- Handle merged cells and formatting appropriately

For JSON files:
- Parse nested structures and flatten if needed for analysis
- Handle arrays and objects appropriately

For visualizations:
- Use clear, descriptive titles and labels
- Choose appropriate chart types for the data
- Use professional styling with seaborn
- Create publication-ready plots
- Always use plt.show() to display plots

Always provide executive summaries and key takeaways.""",
                tools=[{"type": "code_interpreter"}],
                model=deployment_name
            )
            
            self.assistant_id = assistant.id
            print(f"✅ Assistant created! ID: {self.assistant_id}")
            return self.assistant_id
            
        except Exception as e:
            print(f"❌ Error creating assistant: {e}")
            print("\n🔧 Troubleshooting:")
            print("1. Check that AZUREMODEL is your deployment name")
            print("2. Verify deployment exists in Azure AI Foundry portal")
            print("3. Ensure API version is 2024-08-01-preview or newer")
            print("4. Confirm your region supports Assistants API")
            raise
    
    def upload_data_file(self, file_path: str) -> str:
        """Upload data file to Azure OpenAI"""
        try:
            # Validate file format
            if not self._validate_file(file_path):
                raise ValueError("Unsupported file format")
            
            self.file_format = self._detect_file_format(file_path)
            file_name = os.path.basename(file_path)
            
            print(f"📁 Uploading {self.file_format} file: {file_name}")
            
            with open(file_path, "rb") as file:
                uploaded_file = self.client.files.create(
                    file=file,
                    purpose="assistants"
                )
            
            self.file_id = uploaded_file.id
            print(f"✅ {self.file_format} file uploaded! ID: {self.file_id}")
            return self.file_id
            
        except Exception as e:
            print(f"❌ Error uploading file: {e}")
            raise
    
    def create_thread(self) -> str:
        """Create a conversation thread"""
        try:
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id
            print(f"✅ Thread created! ID: {self.thread_id}")
            return self.thread_id
            
        except Exception as e:
            print(f"❌ Error creating thread: {e}")
            raise
    
    def add_file_to_thread(self, message: str) -> None:
        """Add the uploaded file to the thread"""
        try:
            # Customize message based on file format
            format_specific_message = f"{message}\n\nThis is a {self.file_format} file. Please use appropriate methods to load and analyze the data."
            
            self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=format_specific_message,
                attachments=[{
                    "file_id": self.file_id,
                    "tools": [{"type": "code_interpreter"}]
                }]
            )
            print(f"✅ {self.file_format} file attached to thread!")
            
        except Exception as e:
            print(f"❌ Error adding file to thread: {e}")
            raise
    
    def ask_question(self, question: str) -> str:
        """Ask a question about the data"""
        try:
            # Add user message
            self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=question
            )
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            print("🤔 Processing...")
            while run.status in ['queued', 'in_progress', 'cancelling']:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
            
            if run.status == 'completed':
                # Get the response
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread_id
                )
                
                # Get the latest assistant message
                for message in messages.data:
                    if message.role == "assistant":
                        response_text = ""
                        for content in message.content:
                            if content.type == "text":
                                response_text += content.text.value + "\n"
                        return response_text.strip()
            else:
                return f"❌ Run failed with status: {run.status}"
                
        except Exception as e:
            return f"❌ Error processing question: {e}"
    
    def download_generated_files(self) -> list:
        """Download any files generated by the assistant (plots, reports, etc.)"""
        try:
            # Get the latest run
            runs = self.client.beta.threads.runs.list(thread_id=self.thread_id)
            if not runs.data:
                return []
            
            latest_run = runs.data[0]
            
            # Get run steps to find generated files
            run_steps = self.client.beta.threads.runs.steps.list(
                thread_id=self.thread_id,
                run_id=latest_run.id
            )
            
            downloaded_files = []
            
            for step in run_steps.data:
                if hasattr(step.step_details, 'tool_calls'):
                    for tool_call in step.step_details.tool_calls:
                        if (tool_call.type == "code_interpreter" and 
                            hasattr(tool_call.code_interpreter, 'outputs')):
                            
                            for output in tool_call.code_interpreter.outputs:
                                if output.type == "image":
                                    # Download images (plots/charts)
                                    file_data = self.client.files.content(output.image.file_id)
                                    file_name = f"plot_{output.image.file_id}.png"
                                    
                                    with open(file_name, "wb") as f:
                                        f.write(file_data.content)
                                    
                                    downloaded_files.append(file_name)
                                    print(f"📊 Downloaded image: {file_name}")
                                    
                                elif output.type == "logs":
                                    # Check if logs contain file references
                                    if hasattr(output, 'logs') and 'sandbox:/mnt/data/' in output.logs:
                                        print("📄 Found file reference in logs - trying to download...")
            
            # Also check for files in the thread messages
            messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
            
            for message in messages.data:
                if message.role == "assistant":
                    for content in message.content:
                        if content.type == "text" and hasattr(content.text, 'annotations'):
                            for annotation in content.text.annotations:
                                if hasattr(annotation, 'file_path'):
                                    try:
                                        # Try to download the file
                                        file_id = annotation.file_path.file_id
                                        file_data = self.client.files.content(file_id)
                                        
                                        # Determine file extension based on content
                                        content_str = file_data.content.decode('utf-8', errors='ignore')
                                        if content_str.strip().startswith('<!DOCTYPE html>') or '<html>' in content_str:
                                            file_name = f"report_{file_id}.html"
                                        elif content_str.strip().startswith('{') or content_str.strip().startswith('['):
                                            file_name = f"data_{file_id}.json"
                                        else:
                                            file_name = f"report_{file_id}.txt"
                                        
                                        with open(file_name, "wb") as f:
                                            f.write(file_data.content)
                                        
                                        downloaded_files.append(file_name)
                                        print(f"📄 Downloaded file: {file_name}")
                                        
                                    except Exception as file_error:
                                        print(f"⚠️ Could not download file {annotation.file_path.file_id}: {file_error}")
            
            # If no files found through normal methods, try to get all files from the run
            if not downloaded_files:
                try:
                    # List all files created during this conversation
                    all_files = self.client.files.list()
                    print(f"🔍 Checking {len(all_files.data)} total files...")
                    
                    # Look for recently created files (created in last hour)
                    current_time = int(time.time())
                    recent_files = [f for f in all_files.data if current_time - f.created_at < 3600]
                    
                    for file_obj in recent_files[:5]:  # Limit to 5 most recent files
                        try:
                            file_data = self.client.files.content(file_obj.id)
                            
                            # Determine file type
                            if file_obj.filename:
                                file_name = f"downloaded_{file_obj.filename}"
                            else:
                                file_name = f"file_{file_obj.id}.txt"
                            
                            with open(file_name, "wb") as f:
                                f.write(file_data.content)
                            
                            downloaded_files.append(file_name)
                            print(f"📁 Downloaded recent file: {file_name}")
                            
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"⚠️ Could not list files: {e}")
            
            return downloaded_files
            
        except Exception as e:
            print(f"❌ Error downloading files: {e}")
            return []
    
    def cleanup(self):
        """Clean up Azure resources"""
        try:
            if self.file_id:
                self.client.files.delete(self.file_id)
                print("🗑️ File deleted")
            
            if self.assistant_id:
                self.client.beta.assistants.delete(self.assistant_id)
                print("🗑️ Assistant deleted")
                
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

def setup_environment():
    """Check environment variables"""
    required_vars = ["AZUREAPI", "AZUREENDPOINT", "AZUREMODEL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        
        print("\n📝 Create a .env file with:")
        print("AZUREAPI=your-azure-openai-api-key")
        print("AZUREENDPOINT=https://your-resource.openai.azure.com/")
        print("AZUREVERSION=2024-08-01-preview")
        print("AZUREMODEL=your-deployment-name")
        
        print("\n" + "="*60)
        print("🚨 CRITICAL: AZUREMODEL MUST BE YOUR DEPLOYMENT NAME")
        print("="*60)
        print("❌ DON'T use: AZUREMODEL=gpt-4o")
        print("✅ DO use: AZUREMODEL=my-gpt4-deployment")
        print("\n📍 Find your deployment name in:")
        print("   Azure AI Foundry → Deployments → Model deployments")
        print("   Look for the 'Deployment name' column")
        print("="*60)
        
        print("\n⚠️ Requirements:")
        print("- Assistants API enabled (preview)")
        print("- Code Interpreter tool enabled")
        print("- GPT-4 or GPT-4o deployment in supported region")
        print("- API version 2024-08-01-preview or newer")
        return False
    
    # Validate deployment name format
    model_value = os.getenv("AZUREMODEL")
    if model_value in ["gpt-4", "gpt-4o", "gpt-35-turbo", "gpt-3.5-turbo"]:
        print("⚠️  WARNING: AZUREMODEL looks like a model name, not deployment name")
        print(f"   Current value: {model_value}")
        print("   This might cause 'Unsupported data type' error")
        print("   Please use your actual deployment name from Azure portal")
    
    return True

def main():
    """Main function"""
    print("🤖 Azure OpenAI Data Analyzer")
    print("📊 Supports CSV, Excel, JSON, and more!")
    print("=" * 50)
    
    if not setup_environment():
        return
    
    # Show supported formats
    analyzer = AzureOpenAIDataAnalyzer()
    print(f"📁 Supported formats: {', '.join(analyzer.SUPPORTED_FORMATS.keys())}")
    
    # Get data file
    file_path = input("\n📁 Enter data file path: ").strip()
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    analyzer_instance = None
    
    try:
        # Initialize
        analyzer_instance = AzureOpenAIDataAnalyzer()
        analyzer_instance.create_assistant()
        analyzer_instance.upload_data_file(file_path)
        analyzer_instance.create_thread()
        analyzer_instance.add_file_to_thread(f"Analyze this {analyzer_instance.file_format} file and provide a comprehensive summary.")
        
        # Initial analysis
        print("\n" + "="*50)
        print("📊 INITIAL DATA ANALYSIS")
        print("="*50)
        
        initial_prompt = f"Please analyze this {analyzer_instance.file_format} file and provide:\n1. Data structure overview\n2. Basic statistics\n3. Data quality assessment\n4. Key insights\n5. Recommendations for further analysis"
        
        response = analyzer_instance.ask_question(initial_prompt)
        print(response)
        
        # Interactive loop
        print("\n" + "="*50)
        print("💬 ASK QUESTIONS ABOUT YOUR DATA")
        print("Commands: 'examples', 'download', 'quit'")
        print("="*50)
        
        examples = [
            "What are the basic statistics?",
            "Are there any missing values?",
            "Create a histogram of numeric columns",
            "Generate a correlation heatmap",
            "Show distribution of categorical variables",
            "Identify outliers in the data",
            "What patterns and trends do you see?",
            "Create a comprehensive dashboard",
            "Generate an executive summary report",
            "What insights would be valuable for business decisions?"
        ]
        
        # Add format-specific examples
        if analyzer_instance.file_format == "Excel":
            examples.extend([
                "Analyze all sheets in the Excel file",
                "Compare data across different sheets",
                "Check for formatting issues in Excel"
            ])
        elif analyzer_instance.file_format == "JSON":
            examples.extend([
                "Parse nested JSON structures",
                "Flatten the JSON data for analysis",
                "Identify the data hierarchy"
            ])
        
        while True:
            question = input("\n💭 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            elif question.lower() == 'examples':
                print("\n📋 Example questions:")
                for i, ex in enumerate(examples, 1):
                    print(f"{i}. {ex}")
            elif question.lower() == 'download':
                files = analyzer_instance.download_generated_files()
                if files:
                    print(f"📥 Downloaded: {', '.join(files)}")
                else:
                    print("📭 No files to download")
            elif question:
                response = analyzer_instance.ask_question(question)
                print(f"\n🤖 {response}")
                
                # Auto-download plots and reports
                files = analyzer_instance.download_generated_files()
                if files:
                    print(f"\n📊 New files: {', '.join(files)}")
            else:
                print("❓ Please enter a question or command")
        
        print("\n👋 Goodbye!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Cleanup
        if analyzer_instance:
            cleanup = input("\n🗑️ Clean up Azure resources? (y/n): ").lower()
            if cleanup == 'y':
                analyzer_instance.cleanup()

if __name__ == "__main__":
    main()