import os
import time
from openai import AzureOpenAI
from dotenv import load_dotenv
import glob
from pathlib import Path

# Load environment variables
load_dotenv()

class AzureOpenAICodeAnalyzer:
    """
    Code analyzer using Azure OpenAI Assistants API with Code Interpreter
    Supports Python files, bug detection, and solution recommendations
    """
    
    # Supported file formats
    SUPPORTED_FORMATS = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.cs': 'C#',
        '.go': 'Go',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.rs': 'Rust',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.css': 'CSS',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.xml': 'XML',
        '.md': 'Markdown',
        '.txt': 'Text',
        '.log': 'Log file',
        '.env': 'Environment file'
    }
    
    def __init__(self):
        """Initialize the Azure OpenAI client"""
        self.client = self._setup_azure_client()
        self.assistant_id = None
        self.thread_id = None
        self.uploaded_files = []
        self.backend_structure = {}
        
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
    
    def scan_backend_folder(self, folder_path: str, max_files: int = 50) -> dict:
        """Scan backend folder and categorize files"""
        backend_structure = {
            'total_files': 0,
            'by_type': {},
            'files': [],
            'directories': []
        }
        
        if not os.path.exists(folder_path):
            print(f"❌ Folder not found: {folder_path}")
            return backend_structure
        
        print(f"🔍 Scanning backend folder: {folder_path}")
        
        # Get all files recursively
        for root, dirs, files in os.walk(folder_path):
            # Skip common build/cache directories
            dirs[:] = [d for d in dirs if d not in [
                '__pycache__', '.git', 'node_modules', '.venv', 'venv', 
                'build', 'dist', '.pytest_cache', '.mypy_cache'
            ]]
            
            backend_structure['directories'].extend([
                os.path.relpath(os.path.join(root, d), folder_path) for d in dirs
            ])
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, folder_path)
                
                if self._validate_file(file_path):
                    file_type = self._detect_file_format(file_path)
                    
                    if file_type not in backend_structure['by_type']:
                        backend_structure['by_type'][file_type] = []
                    
                    backend_structure['by_type'][file_type].append(rel_path)
                    backend_structure['files'].append({
                        'path': file_path,
                        'relative_path': rel_path,
                        'type': file_type,
                        'size': os.path.getsize(file_path)
                    })
                    
                    backend_structure['total_files'] += 1
                    
                    if backend_structure['total_files'] >= max_files:
                        print(f"⚠️ Reached maximum file limit ({max_files}). Stopping scan.")
                        break
            
            if backend_structure['total_files'] >= max_files:
                break
        
        self.backend_structure = backend_structure
        return backend_structure
    
    def display_backend_structure(self):
        """Display the scanned backend structure"""
        if not self.backend_structure:
            print("❌ No backend structure found. Run scan_backend_folder first.")
            return
        
        print("\n" + "="*60)
        print("📁 BACKEND FOLDER STRUCTURE")
        print("="*60)
        print(f"📊 Total files: {self.backend_structure['total_files']}")
        
        print("\n📋 Files by type:")
        for file_type, files in self.backend_structure['by_type'].items():
            print(f"  {file_type}: {len(files)} files")
            for file_path in files[:5]:  # Show first 5 files
                print(f"    - {file_path}")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more")
        
        print(f"\n📂 Total directories: {len(self.backend_structure['directories'])}")
    
    def create_assistant(self, name: str = "Backend Code Analyst") -> str:
        """Create an assistant with code analysis capabilities"""
        try:
            deployment_name = os.getenv("AZUREMODEL")
            if not deployment_name:
                raise ValueError("AZUREMODEL environment variable must be set to your deployment name")
            
            print(f"Creating code analysis assistant with deployment: {deployment_name}")
            
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions="""You are a senior software engineer and code analyst assistant specializing in backend development and debugging.

Your expertise includes:
- Python, JavaScript, TypeScript, Java, C++, C#, Go, PHP, Ruby, Rust
- Backend frameworks (Django, Flask, FastAPI, Express, Spring, etc.)
- Database technologies and SQL
- API development and debugging
- Code quality assessment and best practices
- Security vulnerability detection
- Performance optimization
- Architecture analysis

When analyzing code:

1. **Code Structure Analysis:**
   - Examine file organization and architecture
   - Identify design patterns and code structure
   - Assess code maintainability and readability

2. **Bug Detection & Analysis:**
   - Identify syntax errors, logic errors, and runtime issues
   - Detect potential security vulnerabilities
   - Find performance bottlenecks
   - Spot code smells and anti-patterns

3. **Solution Recommendations:**
   - Provide specific, actionable bug fixes
   - Suggest code improvements and refactoring
   - Recommend best practices implementation
   - Offer alternative approaches when applicable

4. **Code Quality Assessment:**
   - Check for proper error handling
   - Validate input sanitization and security measures
   - Assess testing coverage and quality
   - Review documentation and comments

5. **Dependency Analysis:**
   - Identify outdated or vulnerable dependencies
   - Suggest better alternatives when needed
   - Check for unused imports/dependencies

For visualizations:
- Create code complexity charts
- Generate dependency graphs when possible
- Show bug distribution across files
- Create improvement priority matrices

Always provide:
- Clear explanations of identified issues
- Step-by-step solutions
- Code examples for fixes
- Prevention strategies for future issues
- Executive summaries for non-technical stakeholders""",
                tools=[{"type": "code_interpreter"}],
                model=deployment_name
            )
            
            self.assistant_id = assistant.id
            print(f"✅ Code analysis assistant created! ID: {self.assistant_id}")
            return self.assistant_id
            
        except Exception as e:
            print(f"❌ Error creating assistant: {e}")
            print("\n🔧 Troubleshooting:")
            print("1. Check that AZUREMODEL is your deployment name")
            print("2. Verify deployment exists in Azure AI Foundry portal")
            print("3. Ensure API version is 2024-08-01-preview or newer")
            print("4. Confirm your region supports Assistants API")
            raise
    
    def upload_backend_files(self, folder_path: str, file_types: list = None, max_files: int = None) -> list:
        """Upload multiple backend files to Azure OpenAI"""
        if file_types is None:
            file_types = ['Python', 'JavaScript', 'TypeScript']  # Default types
        
        uploaded_files = []
        
        if not self.backend_structure:
            self.scan_backend_folder(folder_path, max_files=1000)  # Scan more files
        
        print(f"\n📤 Uploading ALL backend files in batches of 10...")
        
        # Filter files by type and size
        files_to_upload = []
        for file_info in self.backend_structure['files']:
            if (file_info['type'] in file_types and 
                file_info['size'] < 10 * 1024 * 1024 and  # Max 10MB per file
                file_info['size'] > 0):  # Skip empty files
                files_to_upload.append(file_info)
        
        # Sort by importance (Python files first, main files before tests, then by size)
        files_to_upload.sort(key=lambda x: (
            0 if x['type'] == 'Python' else 1,
            1 if 'test' in x['relative_path'].lower() else 0,  # Main files before tests
            1 if '__pycache__' in x['relative_path'] else 0,  # Skip cache files
            -x['size']  # Larger files first
        ))
        
        total_files = len(files_to_upload)
        print(f"📊 Found {total_files} files to upload")
        
        if total_files == 0:
            print("❌ No files found matching the criteria")
            return []
        
        # Upload all files (we'll batch them when attaching to thread)
        for i, file_info in enumerate(files_to_upload, 1):
            try:
                print(f"📁 Uploading ({i}/{total_files}) {file_info['type']} file: {file_info['relative_path']}")
                
                with open(file_info['path'], "rb") as file:
                    uploaded_file = self.client.files.create(
                        file=file,
                        purpose="assistants"
                    )
                
                uploaded_files.append({
                    'file_id': uploaded_file.id,
                    'path': file_info['relative_path'],
                    'type': file_info['type']
                })
                
                # Progress indicator
                if i % 10 == 0:
                    print(f"✅ Progress: {i}/{total_files} files uploaded")
                
            except Exception as e:
                print(f"❌ Error uploading {file_info['relative_path']}: {e}")
        
        self.uploaded_files = uploaded_files
        print(f"\n✅ Successfully uploaded ALL {len(uploaded_files)} files!")
        print(f"📋 Files will be attached to thread in batches of 10")
        return uploaded_files
    
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
    
    def add_files_to_thread(self, initial_message: str = None) -> None:
        """Add ALL uploaded files to the thread in batches of 10"""
        try:
            if not self.uploaded_files:
                print("❌ No files uploaded to add to thread")
                return
            
            # Azure OpenAI has a limit of 10 attachments per message
            max_attachments_per_message = 10
            total_files = len(self.uploaded_files)
            
            print(f"\n📎 Attaching {total_files} files to thread in batches of {max_attachments_per_message}...")
            
            if not initial_message:
                file_list = "\n".join([f"- {f['path']} ({f['type']})" for f in self.uploaded_files])
                initial_message = f"""I'm uploading my complete backend codebase for comprehensive analysis. 

TOTAL FILES: {total_files}

Files being analyzed:
{file_list}

Please provide:
1. Overall code structure and architecture analysis
2. Comprehensive bug detection across all files
3. Security vulnerability assessment
4. Code quality evaluation for the entire codebase
5. Cross-file dependency and integration analysis
6. Performance optimization recommendations
7. Improvement suggestions with priorities

Focus especially on finding bugs, security issues, and providing actionable solutions across the entire codebase."""
            
            # Split files into batches of 10
            file_batches = []
            for i in range(0, len(self.uploaded_files), max_attachments_per_message):
                batch = self.uploaded_files[i:i + max_attachments_per_message]
                file_batches.append(batch)
            
            print(f"📊 Created {len(file_batches)} batches of files")
            
            # Send first batch with detailed initial message
            first_batch = file_batches[0]
            attachments = [{
                "file_id": file_info['file_id'],
                "tools": [{"type": "code_interpreter"}]
            } for file_info in first_batch]
            
            self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=initial_message,
                attachments=attachments
            )
            
            print(f"✅ Batch 1/{len(file_batches)}: {len(first_batch)} files attached!")
            
            # Send additional batches
            for batch_num, batch in enumerate(file_batches[1:], 2):
                batch_files = [f"- {f['path']} ({f['type']})" for f in batch]
                batch_message = f"""Additional files for analysis (Batch {batch_num}/{len(file_batches)}):

{chr(10).join(batch_files)}

Please continue analyzing these files as part of the complete codebase review."""
                
                attachments = [{
                    "file_id": file_info['file_id'],
                    "tools": [{"type": "code_interpreter"}]
                } for file_info in batch]
                
                self.client.beta.threads.messages.create(
                    thread_id=self.thread_id,
                    role="user",
                    content=batch_message,
                    attachments=attachments
                )
                
                print(f"✅ Batch {batch_num}/{len(file_batches)}: {len(batch)} additional files attached!")
                time.sleep(1)  # Small delay between requests to avoid rate limits
            
            print(f"\n🎉 SUCCESS: All {total_files} files attached to thread in {len(file_batches)} batches!")
            print("🤖 The assistant now has access to your complete codebase for analysis.")
            
        except Exception as e:
            print(f"❌ Error adding files to thread: {e}")
            raise
    
    def ask_question(self, question: str) -> str:
        """Ask a question about the code"""
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
            print("🤔 Analyzing code...")
            while run.status in ['queued', 'in_progress', 'cancelling']:
                time.sleep(2)
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
                return f"❌ Analysis failed with status: {run.status}"
                
        except Exception as e:
            return f"❌ Error processing question: {e}"
    
    def download_generated_files(self) -> list:
        """Download all assistant-generated files (reports, fixes, etc.)"""
        try:
            downloaded_files = []
            current_time = int(time.time())

            # List all available files
            all_files = self.client.files.list()
            print(f"🔍 Checking {len(all_files.data)} total files...")

            for file_obj in all_files.data:
                # Only consider files created within the last 30 minutes
                if current_time - file_obj.created_at > 1800:
                    continue

                # Skip our uploaded files
                if any(f['file_id'] == file_obj.id for f in self.uploaded_files):
                    continue

                try:
                    file_data = self.client.files.content(file_obj.id)
                    content = file_data.content
                    
                    # Determine file extension
                    try:
                        content_str = content.decode('utf-8', errors='ignore')
                        if 'import ' in content_str or 'def ' in content_str:
                            ext = '.py'
                        elif content_str.strip().startswith('{') or content_str.strip().startswith('['):
                            ext = '.json'
                        elif content_str.strip().startswith('<!DOCTYPE html>') or '<html' in content_str:
                            ext = '.html'
                        else:
                            ext = '.txt'
                    except Exception:
                        ext = '.bin'

                    filename = file_obj.filename or f"analysis_result_{file_obj.id}{ext}"
                    filepath = f"downloads/{filename}"

                    # Ensure downloads directory exists
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)

                    with open(filepath, "wb") as f:
                        f.write(content)

                    downloaded_files.append(filepath)
                    print(f"📥 Downloaded: {filepath}")

                except Exception as e:
                    print(f"⚠️ Skipping file {file_obj.id} due to error: {e}")

            if not downloaded_files:
                print("📭 No new analysis files found.")

            return downloaded_files

        except Exception as e:
            print(f"❌ Error during file download: {e}")
            return []

    def cleanup(self):
        """Clean up Azure resources"""
        try:
            # Delete uploaded files
            for file_info in self.uploaded_files:
                try:
                    self.client.files.delete(file_info['file_id'])
                    print(f"🗑️ Deleted file: {file_info['path']}")
                except Exception as e:
                    print(f"❌ Error deleting file {file_info['path']}: {e}")
            
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
        
        return False
    
    return True

def main():
    """Main function"""
    print("🐛 Azure OpenAI Backend Code Analyzer")
    print("🔍 Find bugs, get solutions, improve your code!")
    print("=" * 60)
    
    if not setup_environment():
        return
    
    # Get backend folder
    backend_folder = input("\n📁 Enter backend folder path: ").strip()
    if not os.path.exists(backend_folder):
        print(f"❌ Folder not found: {backend_folder}")
        return
    
    analyzer_instance = None
    
    try:
        # Initialize
        analyzer_instance = AzureOpenAICodeAnalyzer()
        
        # Scan and display backend structure
        analyzer_instance.scan_backend_folder(backend_folder)
        analyzer_instance.display_backend_structure()
        
        # Ask which file types to analyze
        available_types = list(analyzer_instance.backend_structure['by_type'].keys())
        print(f"\n📋 Available file types: {', '.join(available_types)}")
        print("✨ NEW: Will upload ALL files and attach them in batches of 10!")
        
        file_types_input = input("Enter file types to analyze (comma-separated, or 'all'): ").strip()
        if file_types_input.lower() == 'all':
            selected_types = available_types
        else:
            selected_types = [t.strip() for t in file_types_input.split(',') if t.strip() in available_types]
        
        if not selected_types:
            selected_types = ['Python']  # Default
            print("No valid types selected, defaulting to Python files")
        
        print(f"✅ Selected types: {', '.join(selected_types)}")
        
        # Upload files and create assistant
        analyzer_instance.create_assistant()
        analyzer_instance.upload_backend_files(backend_folder, selected_types)
        analyzer_instance.create_thread()
        analyzer_instance.add_files_to_thread()
        
        # Initial analysis
        print("\n" + "="*60)
        print("🔍 INITIAL CODE ANALYSIS")
        print("="*60)
        
        response = analyzer_instance.ask_question(
            "Perform a comprehensive analysis focusing on bug detection and provide actionable solutions."
        )
        print(response)
        
        # Interactive loop
        print("\n" + "="*60)
        print("💬 ASK QUESTIONS ABOUT YOUR CODE")
        print("Commands: 'examples', 'download', 'quit'")
        print("="*60)
        
        code_examples = [
            "What bugs can you find in my code?",
            "Are there any security vulnerabilities?",
            "How can I improve performance?",
            "What code smells do you detect?",
            "Review my error handling",
            "Check for potential race conditions",
            "Analyze my database queries for issues",
            "What design patterns could I implement?",
            "Find unused imports and variables",
            "Review my API endpoints for issues",
            "Check for SQL injection vulnerabilities",
            "Analyze memory usage patterns",
            "What testing improvements do you suggest?",
            "Review my authentication implementation",
            "Find hardcoded values that should be configurable"
        ]
        
        while True:
            question = input("\n💭 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            elif question.lower() == 'examples':
                print("\n📋 Example questions:")
                for i, ex in enumerate(code_examples, 1):
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
                
                # Auto-download analysis results
                files = analyzer_instance.download_generated_files()
                if files:
                    print(f"\n📊 New files: {', '.join(files)}")
            else:
                print("❓ Please enter a question or command")
        
        print("\n👋 Analysis complete!")
        
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