import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from openai import AzureOpenAI
import json
import traceback
from typing import Dict, Any, List
import warnings
import base64
import io
import time
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr
import sys
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go

# Load environment variables
load_dotenv()

# Suppress warnings
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="AI-Powered CSV Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class StreamlitReportBuilder:
    """Builds comprehensive reports for Streamlit with real-time updates."""
    
    def __init__(self):
        self.report_sections = []
        self.start_time = datetime.now()
        self.charts_generated = []
        self.code_blocks = []
        self.data_summary = ""
        self.analysis_results = []
        
    def add_section(self, title: str, content: str, section_type: str = "info"):
        """Add a section to the report."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        section = {
            "timestamp": timestamp,
            "title": title,
            "content": content,
            "type": section_type
        }
        self.report_sections.append(section)
        
    def add_analysis_result(self, query: str, code: str, output: str, success: bool):
        """Add analysis result to the report."""
        result = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "query": query,
            "code": code,
            "output": output,
            "success": success
        }
        self.analysis_results.append(result)
        
    def stream_section_to_streamlit(self, container, title: str, content: str = "", section_type: str = "info"):
        """Stream a section to Streamlit container."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        with container:
            if section_type == "header":
                st.markdown(f"## {title}")
                st.caption(f"Generated at {timestamp}")
            elif section_type == "code":
                st.markdown(f"### 📝 Generated Code - {title}")
                st.caption(f"{timestamp}")
                st.code(content, language="python")
            elif section_type == "output":
                st.markdown(f"### 📊 Execution Output - {title}")
                st.caption(f"{timestamp}")
                st.text(content)
            elif section_type == "error":
                st.markdown(f"### ❌ Error - {title}")
                st.caption(f"{timestamp}")
                st.error(content)
            else:
                st.markdown(f"### {title}")
                st.caption(f"{timestamp}")
                st.markdown(content)
                
        # Also add to report sections
        self.add_section(title, content, section_type)

    def set_data_summary(self, df: pd.DataFrame):
        """Set data summary for report generation."""
        self.data_summary = f"""
**Dataset Overview:**
- Shape: {df.shape[0]:,} rows × {df.shape[1]} columns
- Columns: {', '.join(df.columns.tolist())}
- Data Types: {dict(df.dtypes)}
- Missing Values: {dict(df.isnull().sum())}
- Numeric Columns: {list(df.select_dtypes(include=[np.number]).columns)}
- Categorical Columns: {list(df.select_dtypes(include=['object']).columns)}

**Statistical Summary:**
{df.describe().to_string()}

**Sample Data:**
{df.head().to_string()}
"""

    def generate_report_prompt(self, df: pd.DataFrame, report_type: str = "comprehensive") -> str:
        """Generate prompt for AI report generation."""
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Prepare data section
        data_section = f"""
### DATA
{self.data_summary}

**Analysis Results Performed:**
"""
        for i, result in enumerate(self.analysis_results, 1):
            data_section += f"""
{i}. **Query:** {result['query']}
   **Success:** {'✅ Yes' if result['success'] else '❌ No'}
   **Output:** {result['output'][:500]}{'...' if len(result['output']) > 500 else ''}
"""

        if report_type == "comprehensive":
            prompt = f"""You are a senior strategy consultant at a top-tier global firm.  
Draft a comprehensive **Data Analysis Report** that follows leading consulting and industry-analysis conventions.  
Use only the information contained in the ### DATA section and clearly state any additional assumptions.

### REPORT SPECIFICATIONS
1. **Cover Page**  
   - Title: "Data Analysis Report - {current_date}"  
   - Prepared for: Data Analytics Team  
   - Prepared by: AI Analytics Consultant, {current_date}

2. **Executive Summary** (≤2 pages)  
   - Three-bullet headline ("What", "So What", "Now What")  
   - Snapshot table of key findings and metrics  
   - Top three strategic recommendations  

3. **Table of Contents**  

4. **Background & Objectives**  
   - Dataset description, scope, and analysis goals  
   - Key stakeholders and business questions addressed  

5. **Data Sources & Methodology**  
   - Dataset characteristics and quality assessment  
   - Analysis approaches used  
   - Validation steps and limitations  

6. **Key Findings & Analysis**  
   - Statistical insights and patterns discovered  
   - Visual representations of key trends  
   - Comparative analysis across different dimensions  

7. **Deep Dive Analysis**  
   - Detailed examination of significant patterns  
   - Correlation and relationship analysis  
   - Outlier and anomaly identification  

8. **Strategic Implications**  
   - Business impact of findings  
   - Opportunities and challenges identified  
   - Performance benchmarks and KPIs  

9. **Recommendations & Next Steps**  
   - Prioritized actions by impact/feasibility (H/M/L)  
   - Implementation roadmap and timeline  
   - Resource requirements  

10. **Risks & Considerations**  
    - Data quality and methodology limitations  
    - External factors that may impact findings  
    - Mitigation strategies  

11. **Appendices**  
    - Detailed statistical tables  
    - Technical methodology details  
    - Glossary of terms  

### STYLE & TONE
- Professional consulting voice, concise, data-driven  
- Use numerals with correct formatting (e.g., 3.2%, $5.4M, 1,234)  
- Bullet lists for clarity; multi-sentence paragraphs for complex concepts  
- Reference data insights inline (e.g., "Analysis shows 24.5% increase [Finding-1]")  
- No external citations; rely solely on ### DATA  

### OUTPUT FORMAT
Return ONLY the finished report in Markdown, properly structured with headings (##, ###) as specified above.

{data_section}
"""
        else:  # Quick summary report
            prompt = f"""Generate a concise data analysis summary report based on the data and analysis results provided.

Focus on:
1. Key findings from the data
2. Main insights discovered
3. Actionable recommendations
4. Next steps

Use professional consulting language and structure with clear headings.

{data_section}
"""
        
        return prompt

    def generate_final_report(self, openai_client, df: pd.DataFrame, model: str = "gpt-o3-mini") -> str:
        """Generate comprehensive final report using AI."""
        try:
            # Update data summary
            self.set_data_summary(df)
            
            # Generate report prompt
            report_prompt = self.generate_report_prompt(df, "comprehensive")
            
            # Get AI-generated report
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a senior data analytics consultant. Generate comprehensive, professional reports based on data analysis results."
                    },
                    {
                        "role": "user", 
                        "content": report_prompt
                    }
                ],
                temperature=0.3,
            )
            
            ai_report = response.choices[0].message.content
            
            # Add session metadata
            metadata_section = f"""
---
**Report Metadata**
- Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Session Duration: {datetime.now() - self.start_time}
- Total Analyses: {len(self.analysis_results)}
- Successful Analyses: {sum(1 for r in self.analysis_results if r['success'])}
- Dataset Shape: {df.shape[0]:,} rows × {df.shape[1]} columns
---
"""
            
            return ai_report + metadata_section
            
        except Exception as e:
            # Fallback to basic report
            return self.generate_basic_report(df, str(e))
    
    def generate_basic_report(self, df: pd.DataFrame, error_msg: str = "") -> str:
        """Generate basic report as fallback."""
        report = f"""# Data Analysis Report
        
## Executive Summary
This report provides an analysis of the uploaded dataset containing {df.shape[0]:,} rows and {df.shape[1]} columns.

## Dataset Overview
{self.data_summary}

## Analysis Session Summary
- **Session Start:** {self.start_time.strftime("%Y-%m-%d %H:%M:%S")}
- **Duration:** {datetime.now() - self.start_time}
- **Total Queries:** {len(self.analysis_results)}
- **Successful Analyses:** {sum(1 for r in self.analysis_results if r['success'])}

## Analysis Results
"""
        
        for i, result in enumerate(self.analysis_results, 1):
            status = "✅ Success" if result['success'] else "❌ Failed"
            report += f"""
### {i}. {result['query']}
**Status:** {status}  
**Time:** {result['timestamp']}  
**Output:** {result['output'][:300]}{'...' if len(result['output']) > 300 else ''}

"""

        if error_msg:
            report += f"""
## Note
Report generation encountered an issue: {error_msg}
This is a basic fallback report.
"""

        report += f"""
## Recommendations
1. Review the analysis results above for key insights
2. Consider additional analysis based on patterns found
3. Validate findings with domain expertise
4. Plan next steps based on discovered trends

---
*Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        return report

class StreamlitOutputCapture:
    """Captures output for Streamlit display."""
    
    def __init__(self):
        self.captured_output = []
        
    def write(self, text):
        """Capture output."""
        if text.strip():
            self.captured_output.append(text)
            
    def flush(self):
        pass
    
    def get_output(self):
        """Return all captured output as a single string."""
        return ''.join(self.captured_output)

class StreamlitCSVAnalyzer:
    """
    Streamlit-based CSV analyzer with AI-powered analysis.
    """
    
    def __init__(self):
        """Initialize the analyzer."""
        self.MODEL = "gpt-o3-mini"
        self.df = None
        self.csv_info = ""
        self.report_builder = StreamlitReportBuilder()
        self.chart_counter = 0
        
        # Initialize Azure OpenAI client
        try:
            self.openai_client = AzureOpenAI(
                api_key=os.getenv("AZUREAPI"),
                api_version=os.getenv("AZUREVERSION"),
                azure_endpoint=os.getenv("AZUREENDPOINT")
            )
        except Exception as e:
            st.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
            self.openai_client = None
            
    def load_data_from_upload(self, uploaded_file) -> bool:
        """Load data from uploaded file."""
        try:
            if uploaded_file.name.endswith('.csv'):
                self.df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                self.df = pd.read_excel(uploaded_file)
            else:
                st.error("Unsupported file format. Please upload CSV or Excel files.")
                return False
                
            self.csv_info = self._generate_csv_info()
            # Update report builder with data summary
            self.report_builder.set_data_summary(self.df)
            return True
            
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            return False
    
    def _generate_csv_info(self) -> str:
        """Generate comprehensive CSV information for AI context."""
        info = f"""
CSV Dataset Information:
- Shape: {self.df.shape} (rows, columns)
- Columns: {list(self.df.columns)}
- Data Types: {dict(self.df.dtypes)}
- Missing Values: {dict(self.df.isnull().sum())}
- Numeric Columns: {list(self.df.select_dtypes(include=[np.number]).columns)}
- Categorical Columns: {list(self.df.select_dtypes(include=['object']).columns)}

Sample Data (first 5 rows):
{self.df.head().to_string()}

Statistical Summary:
{self.df.describe().to_string()}
"""
        return info
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for AI analysis."""
        return f"""
You are an AI assistant for data analysis. Generate ONLY executable Python code without any explanations or text.

CSV Data Context:
{self.csv_info}

CRITICAL RULES:
1. RETURN ONLY PYTHON CODE - NO explanations, descriptions, or text before/after code
2. ALWAYS use the variable 'df' to reference the loaded DataFrame - NEVER use pd.read_csv()
3. The DataFrame 'df' is already loaded and available
4. Include all necessary imports at the top
5. For matplotlib plots: create figure, plot, use plt.tight_layout(), assign to 'fig' variable
6. For plotly plots: create figure and assign to 'fig' variable
7. Handle missing data appropriately with proper error checking
8. Add brief comments only within the code using # 
9. NEVER include file loading code - data is already in 'df'
10. Always examine data structure first with df.info() or df.head() if needed

MANDATORY CODE STRUCTURE:
```python
# Import required libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# ... other imports as needed

# Examine data (if needed)
print("Data shape:", df.shape)
print("Columns:", df.columns.tolist())

# Your analysis code here
# ...

# For visualizations, create figure
fig, ax = plt.subplots(figsize=(10, 6))
# ... plotting code ...
plt.tight_layout()

# OR for plotly:
# import plotly.express as px
# fig = px.scatter(df, x='column1', y='column2')
```

RESPONSE REQUIREMENTS:
- Return ONLY the Python code block
- NO explanatory text before or after
- NO markdown formatting around the code
- Start directly with imports or code
- End with the last line of executable code
- Code must be complete and runnable as-is
"""

    def extract_python_code(self, response: str) -> str:
        """Extract Python code from AI response, handling various formats."""
        import re
        
        # Try to find code blocks with ```python
        python_blocks = re.findall(r'```python\s*\n(.*?)\n```', response, re.DOTALL)
        if python_blocks:
            return python_blocks[0].strip()
        
        # Try to find any code blocks with ```
        code_blocks = re.findall(r'```\s*\n(.*?)\n```', response, re.DOTALL)
        if code_blocks:
            # Filter out non-Python code blocks
            for block in code_blocks:
                block = block.strip()
                # Check if it looks like Python code
                if any(keyword in block for keyword in ['import ', 'df.', 'plt.', 'pd.', 'np.', 'print(', 'fig']):
                    return block
        
        # Try to find inline code with ```
        inline_code = re.findall(r'```(.*?)```', response, re.DOTALL)
        if inline_code:
            for code in inline_code:
                code = code.strip()
                if any(keyword in code for keyword in ['import ', 'df.', 'plt.', 'pd.', 'np.', 'print(', 'fig']):
                    return code
        
        # If no code blocks found, try to extract code from the response
        lines = response.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            # Skip explanatory text
            if any(phrase in line.lower() for phrase in [
                'here is', 'below is', 'example', 'code:', 'python code',
                'let me', 'i will', 'this code', 'the following'
            ]) and not line.strip().startswith(('#', 'import', 'df.', 'plt.', 'pd.', 'np.')):
                continue
            
            # Start collecting code when we see Python-like statements
            if any(keyword in line for keyword in ['import ', 'df.', 'plt.', 'pd.', 'np.', 'print(', 'fig']):
                in_code = True
            
            if in_code:
                # Stop if we hit explanatory text again
                if any(phrase in line.lower() for phrase in [
                    'this will', 'this code will', 'explanation:', 'note:', 'output:'
                ]) and not line.strip().startswith('#'):
                    break
                code_lines.append(line)
        
        if code_lines:
            return '\n'.join(code_lines).strip()
        
        # Last resort - return the whole response if it looks like code
        if any(keyword in response for keyword in ['import ', 'df.', 'plt.', 'pd.', 'np.']):
            return response.strip()
        
        return ""

    def stream_openai_response(self, messages: List[Dict], container) -> str:
        """Stream OpenAI response to Streamlit."""
        if not self.openai_client:
            st.error("OpenAI client not initialized. Please check your environment variables.")
            return ""
            
        try:
            with container:
                st.markdown("### 🤖 Generating AI Code...")
                code_placeholder = st.empty()
                response_placeholder = st.empty()
                
                response = self.openai_client.chat.completions.create(
                    model=self.MODEL,
                    messages=messages,
                    stream=True
                )
                
                full_response = ""
                
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        
                        # Show the raw response in an expander
                        with response_placeholder:
                            with st.expander("🔍 View Full AI Response", expanded=False):
                                st.text(full_response)
                        
                        # Extract and display code
                        extracted_code = self.extract_python_code(full_response)
                        if extracted_code:
                            code_placeholder.code(extracted_code, language="python")
                
                # Extract final code
                final_code = self.extract_python_code(full_response)
                
                if not final_code:
                    st.warning("⚠️ Could not extract valid Python code from the response. Please try rephrasing your query.")
                    with st.expander("🔍 Full Response for Debugging"):
                        st.text(full_response)
                    return ""
                    
                return final_code
                
        except Exception as e:
            st.error(f"Error in OpenAI streaming: {str(e)}")
            return ""

    def validate_python_code(self, code: str) -> tuple[bool, str]:
        """Validate if the code is syntactically correct Python."""
        try:
            compile(code, '<string>', 'exec')
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax Error: {str(e)}"
        except Exception as e:
            return False, f"Validation Error: {str(e)}"

    def execute_code_in_streamlit(self, code: str, container, query: str = "") -> Dict[str, Any]:
        """Execute generated Python code and display results in Streamlit."""
        
        # Validate code first
        is_valid, error_msg = self.validate_python_code(code)
        if not is_valid:
            with container:
                st.error(f"❌ Invalid Python code: {error_msg}")
                st.code(code, language="python")
                with st.expander("🔧 Debugging Tips"):
                    st.markdown("""
                    **Common Issues:**
                    - AI returned explanatory text mixed with code
                    - Missing imports or incomplete code blocks
                    - Syntax errors in generated code
                    
                    **Try:**
                    - Rephrase your query to be more specific
                    - Ask for "Python code only" in your request
                    - Use simpler, more direct language
                    """)
            
            # Add to report builder
            self.report_builder.add_analysis_result(query, code, error_msg, False)
            
            return {
                "success": False,
                "error": error_msg,
                "message": "Code validation failed"
            }
        
        try:
            # Setup execution environment
            exec_globals = {
                'df': self.df,
                'pd': pd,
                'np': np,
                'plt': plt,
                'sns': sns,
                'json': json,
                'os': os,
                'warnings': warnings,
                'time': time,
                'px': px,
                'go': go
            }
            
            # Import additional libraries
            try:
                from sklearn.linear_model import LinearRegression
                from sklearn.model_selection import train_test_split
                from sklearn.metrics import mean_squared_error, r2_score
                from sklearn.preprocessing import StandardScaler, MinMaxScaler
                from scipy import stats
                from datetime import datetime, timedelta
                exec_globals.update({
                    'LinearRegression': LinearRegression,
                    'train_test_split': train_test_split,
                    'mean_squared_error': mean_squared_error,
                    'r2_score': r2_score,
                    'StandardScaler': StandardScaler,
                    'MinMaxScaler': MinMaxScaler,
                    'stats': stats,
                    'datetime': datetime,
                    'timedelta': timedelta
                })
            except ImportError as e:
                st.warning(f"Some advanced libraries not available: {e}")
            
            # Capture output
            output_capture = StreamlitOutputCapture()
            original_stdout = sys.stdout
            sys.stdout = output_capture
            
            exec_locals = {}
            exec(code, exec_globals, exec_locals)
            
            # Restore stdout
            sys.stdout = original_stdout
            
            # Get captured output
            captured_output = output_capture.get_output()
            
            with container:
                st.markdown("### 📊 Execution Results")
                
                # Display text output if any
                if captured_output.strip():
                    st.markdown("#### Text Output:")
                    st.text(captured_output)
                
                # Look for matplotlib figures
                if 'fig' in exec_locals and exec_locals['fig'] is not None:
                    st.markdown("#### Generated Chart:")
                    st.pyplot(exec_locals['fig'])
                elif plt.get_fignums():  # Check if there are any matplotlib figures
                    st.markdown("#### Generated Chart:")
                    st.pyplot(plt.gcf())
                    plt.clf()  # Clear the figure
                
                # Look for plotly figures
                plotly_figs = [v for k, v in exec_locals.items() if hasattr(v, 'show') and hasattr(v, 'data')]
                if plotly_figs:
                    st.markdown("#### Interactive Chart:")
                    for fig in plotly_figs:
                        st.plotly_chart(fig, use_container_width=True)
                
                # Display any dataframes created
                dataframes = {k: v for k, v in exec_locals.items() if isinstance(v, pd.DataFrame) and k != 'df'}
                if dataframes:
                    st.markdown("#### Generated DataFrames:")
                    for name, df_result in dataframes.items():
                        st.markdown(f"**{name}:**")
                        st.dataframe(df_result, use_container_width=True)
                
                # Display other notable variables
                other_vars = {k: v for k, v in exec_locals.items() 
                             if not k.startswith('_') and k not in ['fig'] and not isinstance(v, pd.DataFrame)}
                if other_vars:
                    st.markdown("#### Other Results:")
                    for name, value in other_vars.items():
                        if isinstance(value, (int, float, str, list, dict)) and len(str(value)) < 1000:
                            st.write(f"**{name}:** {value}")
            
            # Add to report builder
            self.report_builder.add_analysis_result(query, code, captured_output, True)
            
            return {
                "success": True,
                "output": captured_output,
                "variables": exec_locals,
                "message": "Code executed successfully!"
            }
            
        except Exception as e:
            sys.stdout = original_stdout
            error_msg = f"Execution failed: {str(e)}"
            traceback_msg = traceback.format_exc()
            
            with container:
                st.error(error_msg)
                with st.expander("Error Details"):
                    st.code(traceback_msg)
                with st.expander("🔧 Debugging Help"):
                    st.markdown("""
                    **Possible Solutions:**
                    1. **Check your data**: Make sure the columns referenced in the query exist
                    2. **Simplify the request**: Try asking for a simpler analysis first
                    3. **Check data types**: Some operations require specific data types
                    4. **Handle missing values**: Your data might have NaN values that need cleaning
                    
                    **Example queries that usually work:**
                    - "Show df.info() and df.describe()"
                    - "Create a simple bar chart of the first column"
                    - "Display basic statistics"
                    """)
            
            # Add to report builder
            self.report_builder.add_analysis_result(query, code, error_msg, False)
            
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback_msg,
                "message": error_msg
            }

def main():
    """Main Streamlit app function."""
    st.title("🚀 AI-Powered CSV/Excel Analyzer")
    st.markdown("Upload your data, edit it, and get AI-powered insights with real-time code generation!")
    
    # Check environment variables
    required_vars = ["AZUREAPI", "AZUREVERSION", "AZUREENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        st.error(f"Missing environment variables: {missing_vars}")
        st.info("Please set the following environment variables:")
        st.code("""
AZUREAPI=your_azure_openai_api_key
AZUREVERSION=2024-02-01
AZUREENDPOINT=your_azure_openai_endpoint
        """)
        st.stop()
    
    # Initialize analyzer
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = StreamlitCSVAnalyzer()
    
    analyzer = st.session_state.analyzer
    
    # Sidebar for file upload and data info
    with st.sidebar:
        st.header("📁 Data Upload")
        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=['csv', 'xlsx', 'xls'],
            help="Upload your CSV or Excel file to get started"
        )
        
        if uploaded_file is not None:
            if st.button("Load Data") or 'data_loaded' not in st.session_state:
                with st.spinner("Loading data..."):
                    if analyzer.load_data_from_upload(uploaded_file):
                        st.session_state.data_loaded = True
                        st.session_state.df_original = analyzer.df.copy()
                        st.success(f"✅ Loaded {uploaded_file.name}")
                        st.info(f"Shape: {analyzer.df.shape}")
                        
        if 'data_loaded' in st.session_state and st.session_state.data_loaded:
            st.header("📊 Data Overview")
            st.write(f"**Rows:** {analyzer.df.shape[0]:,}")
            st.write(f"**Columns:** {analyzer.df.shape[1]}")
            st.write("**Column Types:**")
            for col, dtype in analyzer.df.dtypes.items():
                st.write(f"• {col}: {dtype}")
    
    # Main content area
    if 'data_loaded' in st.session_state and st.session_state.data_loaded:
        # Create tabs for different sections
        tab1, tab2, tab3 = st.tabs(["📝 Data Editor", "🤖 AI Analysis", "📋 Reports"])
        
        with tab1:
            st.header("Edit Your Data")
            st.info("You can edit cells directly. Changes will be reflected in the analysis.")
            
            # Editable dataframe
            edited_df = st.data_editor(
                analyzer.df,
                use_container_width=True,
                num_rows="dynamic",
                height=400
            )
            
            # Update the analyzer's dataframe if changes were made
            if not edited_df.equals(analyzer.df):
                analyzer.df = edited_df
                analyzer.csv_info = analyzer._generate_csv_info()
                analyzer.report_builder.set_data_summary(analyzer.df)
                st.success("Data updated! Changes will be reflected in AI analysis.")
            
            # Display basic statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Statistical Summary")
                st.dataframe(analyzer.df.describe(), use_container_width=True)
            
            with col2:
                st.subheader("🔍 Missing Values")
                missing_data = analyzer.df.isnull().sum()
                missing_df = pd.DataFrame({
                    'Column': missing_data.index,
                    'Missing Count': missing_data.values,
                    'Missing %': (missing_data.values / len(analyzer.df) * 100).round(2)
                })
                st.dataframe(missing_df, use_container_width=True)
        
        with tab2:
            st.header("AI-Powered Analysis")
            
            # Example queries
            with st.expander("💡 Example Queries"):
                st.markdown("""
                - **Basic Analysis:** "Show me a summary of the data"
                - **Visualizations:** "Create a correlation heatmap", "Plot top 10 values by category"
                - **Forecasting:** "Predict future sales for the next 6 months"
                - **Statistical Analysis:** "Find outliers in the dataset", "Perform regression analysis"
                - **Data Exploration:** "Show distribution of numeric columns"
                - **Advanced:** "Create an interactive dashboard", "Cluster analysis with visualization"
                """)
            
            # Query input
            user_query = st.text_area(
                "🔍 Enter your analysis query:",
                placeholder="e.g., Create a bar chart showing the top 10 categories by sales...",
                height=100
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                analyze_button = st.button("🚀 Analyze", type="primary")
            
            if analyze_button and user_query.strip():
                # Create containers for streaming content
                code_container = st.container()
                results_container = st.container()
                
                with st.spinner("Generating AI analysis..."):
                    # Detect if this is a forecasting query
                    forecasting_keywords = ['forecast', 'predict', 'future', 'next', 'ahead', 'months', 'years', 'projection']
                    is_forecasting = any(keyword in user_query.lower() for keyword in forecasting_keywords)
                    
                    if is_forecasting:
                        enhanced_prompt = f"""
Generate ONLY executable Python code (no explanations) to: {user_query}

FORECASTING REQUIREMENTS:
- Use 'df' variable (already loaded DataFrame)
- Examine data structure first
- Identify time/date and target columns
- Train on ALL historical data
- Generate future dates BEYOND dataset
- Create clear visualizations
- Assign matplotlib figure to 'fig' variable

RESPONSE: Return only Python code, starting with imports.
"""
                    else:
                        enhanced_prompt = f"""
Generate ONLY executable Python code (no explanations) to: {user_query}

REQUIREMENTS:
- Use 'df' variable (already loaded DataFrame)
- Include necessary imports
- Create appropriate visualizations
- Assign matplotlib figure to 'fig' variable for plots
- Handle errors gracefully

RESPONSE: Return only Python code, starting with imports.
"""

                    messages = [
                        {"role": "system", "content": analyzer._create_system_prompt()},
                        {"role": "user", "content": enhanced_prompt}
                    ]
                    
                    # Generate and stream code
                    generated_code = analyzer.stream_openai_response(messages, code_container)
                    
                    if generated_code:
                        # Execute the code
                        st.markdown("---")
                        execution_result = analyzer.execute_code_in_streamlit(
                            generated_code, results_container, user_query
                        )
                        
                        if execution_result["success"]:
                            st.success("✅ Analysis completed successfully!")
                        else:
                            st.error("❌ Analysis failed.")
                            
                            # Offer retry with more specific prompt
                            if st.button("🔄 Try Again with Simplified Request"):
                                simplified_prompt = f"""
Generate simple Python code only (no text) for: {user_query}

Use df variable. Keep it basic. Start with:
import pandas as pd
import matplotlib.pyplot as plt

End with:
fig, ax = plt.subplots()
# simple plot
plt.tight_layout()
"""
                                retry_messages = [
                                    {"role": "system", "content": "Generate only executable Python code. No explanations."},
                                    {"role": "user", "content": simplified_prompt}
                                ]
                                
                                retry_container = st.container()
                                retry_code = analyzer.stream_openai_response(retry_messages, retry_container)
                                
                                if retry_code:
                                    st.markdown("---")
                                    retry_result = analyzer.execute_code_in_streamlit(
                                        retry_code, retry_container, f"{user_query} (Simplified)"
                                    )
                                    if retry_result["success"]:
                                        st.success("✅ Retry successful!")
                    else:
                        st.error("Failed to generate code. Please try a different query.")
        
        with tab3:
            st.header("📋 Analysis Reports")
            
            if analyzer.report_builder.analysis_results:
                # Report generation options
                col1, col2 = st.columns(2)
                
                with col1:
                    report_type = st.selectbox(
                        "Report Type",
                        ["Comprehensive Report", "Quick Summary"],
                        help="Choose the type of report to generate"
                    )
                
                with col2:
                    if st.button("📊 Generate AI Report", type="primary"):
                        if analyzer.openai_client:
                            with st.spinner("Generating comprehensive report..."):
                                try:
                                    if report_type == "Comprehensive Report":
                                        ai_report = analyzer.report_builder.generate_final_report(
                                            analyzer.openai_client, analyzer.df, analyzer.MODEL
                                        )
                                    else:
                                        # Quick summary
                                        prompt = analyzer.report_builder.generate_report_prompt(analyzer.df, "quick")
                                        response = analyzer.openai_client.chat.completions.create(
                                            model=analyzer.MODEL,
                                            messages=[
                                                {"role": "system", "content": "Generate a concise data analysis summary."},
                                                {"role": "user", "content": prompt}
                                            ],
                                            temperature=0.3
                                        )
                                        ai_report = response.choices[0].message.content
                                    
                                    # Display the report
                                    st.markdown("### 📄 Generated Report")
                                    st.markdown(ai_report)
                                    
                                    # Download button
                                    st.download_button(
                                        label="📥 Download Report",
                                        data=ai_report,
                                        file_name=f"ai_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                        mime="text/markdown"
                                    )
                                    
                                except Exception as e:
                                    st.error(f"Error generating AI report: {str(e)}")
                                    # Fallback to basic report
                                    basic_report = analyzer.report_builder.generate_basic_report(analyzer.df, str(e))
                                    st.markdown("### 📄 Basic Report (Fallback)")
                                    st.markdown(basic_report)
                                    
                                    st.download_button(
                                        label="📥 Download Basic Report",
                                        data=basic_report,
                                        file_name=f"basic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                        mime="text/markdown"
                                    )
                        else:
                            st.error("OpenAI client not available. Cannot generate AI report.")
                
                # Session summary
                st.subheader("Session Summary")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Analyses", len(analyzer.report_builder.analysis_results))
                
                with col2:
                    successful = sum(1 for r in analyzer.report_builder.analysis_results if r['success'])
                    st.metric("Successful", successful)
                
                with col3:
                    duration = datetime.now() - analyzer.report_builder.start_time
                    st.metric("Session Duration", str(duration).split('.')[0])
                
                # Analysis history
                st.subheader("Analysis History")
                for i, result in enumerate(analyzer.report_builder.analysis_results):
                    status_icon = "✅" if result['success'] else "❌"
                    with st.expander(f"{status_icon} {result['timestamp']} - {result['query'][:60]}..."):
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.markdown("**Query:**")
                            st.write(result['query'])
                            st.markdown("**Status:**")
                            st.write("Success" if result['success'] else "Failed")
                        
                        with col2:
                            st.markdown("**Generated Code:**")
                            st.code(result['code'], language="python")
                        
                        st.markdown("**Output:**")
                        if result['success']:
                            st.text(result['output'])
                        else:
                            st.error(result['output'])
                
            else:
                st.info("No analysis performed yet. Go to the AI Analysis tab to start!")
                st.markdown("""
                ### How to Generate Reports:
                1. **Perform Analysis:** Use the AI Analysis tab to run queries on your data
                2. **Build History:** Each successful analysis adds to your session history
                3. **Generate Report:** Come back here to create comprehensive reports
                4. **Download:** Get your reports in Markdown format for sharing
                """)
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to AI-Powered CSV Analyzer! 🎉
        
        ### Features:
        - 📊 **Interactive Data Editing**: Upload and edit your CSV/Excel files directly
        - 🤖 **AI Code Generation**: Get Python code generated in real-time
        - 📈 **Instant Visualizations**: See charts and graphs generated automatically  
        - 🔮 **Advanced Analytics**: Forecasting, clustering, statistical analysis
        - 📋 **Comprehensive Reports**: Download detailed analysis reports with AI insights
        
        ### How to Get Started:
        1. **Upload your file** using the sidebar
        2. **Edit your data** if needed in the Data Editor tab
        3. **Ask questions** in natural language in the AI Analysis tab
        4. **Generate professional reports** in the Reports tab
        
        ### Example Queries:
        - "Show me the correlation between all numeric columns"
        - "Create a forecast for the next 6 months of sales data"
        - "Find and visualize outliers in the dataset"
        - "Generate an interactive dashboard with key metrics"
        
        👈 **Start by uploading a file in the sidebar!**
        """)

if __name__ == "__main__":
    main()