import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from openai import AzureOpenAI
import json
import traceback
from typing import Dict, Any, List, Optional, Tuple
import warnings
from dotenv import load_dotenv
import io
import base64
from datetime import datetime, timedelta
import logging

warnings.filterwarnings('ignore')
load_dotenv()

class QuadraticCSVAnalyzer:
    """
    Enhanced Quadratic-inspired CSV analyzer with perfect Streamlit integration.
    Uses Azure OpenAI to generate and execute Python code for data analysis, 
    forecasting, calculations, and visualizations.
    """
   
    def __init__(self, log_level: str = "INFO"):
        """Initialize the analyzer with Azure OpenAI client and logging."""
        self.setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        
        try:
            self.openai_client = AzureOpenAI(
                api_key=os.getenv("AZUREAPI"),
                api_version=os.getenv("AZUREVERSION"),
                azure_endpoint=os.getenv("AZUREENDPOINT")
            )
            self.logger.info("✅ Azure OpenAI client initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Azure OpenAI client: {str(e)}")
            raise
        
        self.MODEL =os.getenv('AZUREMODEL')
        self.df = None
        self.csv_info = ""
        self.execution_history = []
        self.available_libraries = self._check_available_libraries()
        
    def setup_logging(self, level: str):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def _check_available_libraries(self) -> Dict[str, bool]:
        """Check which optional libraries are available."""
        libraries = {
            'sklearn': False,
            'xgboost': False,
            'tensorflow': False,
            'statsmodels': False,
            'plotly': False,
            'scipy': False
        }
        
        for lib in libraries.keys():
            try:
                __import__(lib)
                libraries[lib] = True
                self.logger.info(f"✅ {lib} available")
            except ImportError:
                self.logger.warning(f"⚠️ {lib} not available")
                
        return libraries
       
    def load_csv(self, file_path: str = None, df: pd.DataFrame = None) -> bool:
        """
        Load CSV file or DataFrame and analyze its structure.
       
        Args:
            file_path: Path to the CSV file (optional)
            df: DataFrame to load directly (optional)
           
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if df is not None:
                self.df = df.copy()
                self.logger.info("📊 DataFrame loaded directly")
            elif file_path:
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        self.df = pd.read_csv(file_path, encoding=encoding)
                        self.logger.info(f"📊 CSV loaded with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("Unable to read CSV with any supported encoding")
            else:
                raise ValueError("Either file_path or df must be provided")
                
            # Generate CSV info
            self.csv_info = self._generate_csv_info()
            
            # Log success
            self.logger.info(f"✅ CSV loaded successfully! Shape: {self.df.shape}")
            self.logger.info(f"🔍 Columns: {list(self.df.columns)}")
            
            return True
           
        except Exception as e:
            self.logger.error(f"❌ Error loading CSV: {str(e)}")
            return False
   
    def _generate_csv_info(self) -> str:
        """Generate comprehensive CSV information for AI context."""
        if self.df is None:
            return "No data loaded"
            
        # Basic info
        info_parts = [
            f"Shape: {self.df.shape} (rows, columns)",
            f"Columns: {list(self.df.columns)}",
            f"Data Types: {dict(self.df.dtypes)}",
            f"Missing Values: {dict(self.df.isnull().sum())}",
            f"Memory Usage: {self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
        ]
        
        # Column categorization
        numeric_cols = list(self.df.select_dtypes(include=[np.number]).columns)
        categorical_cols = list(self.df.select_dtypes(include=['object']).columns)
        datetime_cols = []
        
        # Try to detect datetime columns
        for col in categorical_cols:
            try:
                pd.to_datetime(self.df[col].dropna().iloc[:5])
                datetime_cols.append(col)
            except:
                pass
        
        info_parts.extend([
            f"Numeric Columns: {numeric_cols}",
            f"Categorical Columns: {categorical_cols}",
            f"Potential DateTime Columns: {datetime_cols}"
        ])
        
        # Sample data
        info_parts.append(f"\nSample Data (first 5 rows):\n{self.df.head().to_string()}")
        
        # Statistical summary for numeric columns
        if numeric_cols:
            info_parts.append(f"\nStatistical Summary:\n{self.df[numeric_cols].describe().to_string()}")
        
        return "\n".join(info_parts)
   
    def _create_system_prompt(self) -> str:
        """Create enhanced system prompt with library availability info."""
        available_libs = [lib for lib, available in self.available_libraries.items() if available]
        
        return f"""
You are an advanced AI assistant inspired by Quadratic's spreadsheet capabilities. You can analyze CSV data and generate Python 3.13.3-compatible code for:

1. 📊 Data Analysis & Exploration  
2. 🔢 Statistical Calculations  
3. 📈 Data Visualization (charts, plots)  
4. 🔮 Forecasting & Predictions  
5. 🔄 Data Transformations  
6. 🤖 Machine Learning Analytics  
7. 📋 Report Generation

CSV Data Context:  
{self.csv_info}

Available Libraries: {', '.join(available_libs)}

📌 CRITICAL RULES (Python 3.13.3 compatible, production-ready):

1. **Data Access**: ALWAYS use the variable 'df' to reference the loaded DataFrame. NEVER use `pd.read_csv()` or file paths.

2. **Error Handling**: ALL code must include comprehensive error handling with try/except blocks.

3. **Data Validation**: Before any operation:
   ```python
   print("🔍 Data Overview:")
print(f"Shape: {{df.shape}}")
   print(f"Columns: {{df.columns.tolist()}}")
   print(f"Types: {{df.dtypes.to_dict()}}")
   ```

4. **Column Existence**: Always check if columns exist before using them:
   ```python
   if 'column_name' in df.columns:
       # proceed with analysis
   else:
       print("❌ Column 'column_name' not found")
   ```

5. **Data Cleaning Pipeline**: For messy data, implement this sequence:
   ```python
   # Clean column names
   df.columns = df.columns.str.strip().str.replace(' ', '_')
   
   # Handle missing values
   print(f"Missing values: {{df.isnull().sum().sum()}}")
   
   # Clean numeric columns
   for col in df.select_dtypes(include=['object']).columns:
       if df[col].str.contains(r'[0-9]', na=False).any():
           df[col] = df[col].astype(str).str.replace(',', '').str.strip()
           df[col] = pd.to_numeric(df[col], errors='coerce')
   ```

6. **STREAMLIT VISUALIZATION (CRITICAL)**:
   For ALL matplotlib plots, use this exact pattern:
   ```python
   import streamlit as st
   
   # Create your plot
   fig, ax = plt.subplots(figsize=(12, 8))
   # Your plotting code here (e.g., ax.plot(), sns.heatmap(ax=ax), etc.)
   
   # Display in Streamlit
   st.pyplot(fig)
   plt.close(fig)
   ```

   For seaborn plots:
   ```python
   import streamlit as st
   
   fig, ax = plt.subplots(figsize=(12, 8))
   sns.heatmap(df.corr(), annot=True, ax=ax)
   st.pyplot(fig)
   plt.close(fig)
   ```

   For plotly:
   ```python
   import streamlit as st
   import plotly.express as px
   
   fig = px.line(df, x="Date", y="Value")
   st.plotly_chart(fig, use_container_width=True)
   ```

   NEVER use plt.show() - always use st.pyplot(fig)


7. **Forecasting Requirements**:
   - Check for time series data structure
   - Create synthetic dates if none exist
   - Use appropriate models based on data size
   - Include confidence intervals in predictions
   - Validate model performance with metrics

8. **Output Format**: Always include:
   ```python
   print("=" * 50)
   print("📊 ANALYSIS RESULTS")
   print("=" * 50)
   # Your analysis results here
   print("✅ Analysis completed successfully!")
   ```

9. **Memory Management**: For large datasets, use chunking or sampling:
   ```python
   if df.shape[0] > 100000:
       df_sample = df.sample(n=10000, random_state=42)
       print(f"Using sample of {{df_sample.shape[0]}} rows for analysis")
   ```

10. **Library-Specific Guidelines**:
    - Use only confirmed available libraries: {available_libs}
    - Provide fallback options for missing libraries
    - Include installation hints for missing packages

11. **Professional Code Style**:
    - Use descriptive variable names
    - Add comments for complex operations
    - Include progress indicators for long operations
    - Use f-strings for string formatting

12. **Robust Error Recovery**:
    ```python
    try:
        # Primary analysis approach
        result = advanced_analysis(df)
    except Exception as e:
        print(f"⚠️ Advanced analysis failed: {{e}}")
        try:
            # Fallback approach
            result = basic_analysis(df)
        except Exception as e2:
            print(f"❌ All analysis approaches failed: {{e2}}")
            result = None
    ```

Remember: Generate complete, executable, production-ready code that handles real-world data messiness gracefully.
"""

    def get_quick_insights(self) -> Dict[str, Any]:
        """Generate quick insights about the loaded dataset."""
        if self.df is None:
            return {"error": "No data loaded"}
            
        insights = {
            "shape": self.df.shape,
            "columns": list(self.df.columns),
            "data_types": dict(self.df.dtypes),
            "missing_values": dict(self.df.isnull().sum()),
            "memory_usage_mb": self.df.memory_usage(deep=True).sum() / 1024**2,
            "numeric_columns": list(self.df.select_dtypes(include=[np.number]).columns),
            "categorical_columns": list(self.df.select_dtypes(include=['object']).columns),
            "duplicates": self.df.duplicated().sum(),
            "unique_values": {col: self.df[col].nunique() for col in self.df.columns}
        }
        
        return insights
   
    def detect_column_roles(self) -> Dict[str, List[str]]:
        """Use AI to classify column roles with enhanced detection."""
        if self.df is None:
            return {"error": "No data loaded"}
            
        system = self._create_system_prompt()
        user = f"""
Analyze this DataFrame and classify columns into roles:

{self.csv_info}

Return a JSON object with these categories:
{{
  "date_columns": ["columns that contain dates or time data"],
  "numeric_columns": ["columns with numeric data for analysis"],
  "categorical_columns": ["columns with categories or text labels"],
  "id_columns": ["columns that appear to be identifiers"],
  "metadata_columns": ["columns with descriptive metadata"],
  "target_columns": ["columns that might be prediction targets"]
}}

Consider column names, data types, and sample values for classification.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=0.1,
            )
            
            result = response.choices[0].message.content.strip()
            # Extract JSON from response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()
                
            roles = json.loads(result)
            self.logger.info(f"✅ Column roles detected: {roles}")
            return roles
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting column roles: {str(e)}")
            # Fallback to basic detection
            return self._basic_column_detection()
    
    def _basic_column_detection(self) -> Dict[str, List[str]]:
        """Fallback method for basic column role detection."""
        if self.df is None:
            return {"error": "No data loaded"}
            
        roles = {
            "date_columns": [],
            "numeric_columns": list(self.df.select_dtypes(include=[np.number]).columns),
            "categorical_columns": list(self.df.select_dtypes(include=['object']).columns),
            "id_columns": [],
            "metadata_columns": [],
            "target_columns": []
        }
        
        # Try to detect date columns
        for col in roles["categorical_columns"]:
            try:
                pd.to_datetime(self.df[col].dropna().iloc[:5])
                roles["date_columns"].append(col)
            except:
                pass
        
        # Detect potential ID columns
        for col in self.df.columns:
            if self.df[col].nunique() == len(self.df) or col.lower() in ['id', 'index', 'key']:
                roles["id_columns"].append(col)
        
        return roles
 
    def clean_and_melt(self, date_cols: List[str], metadata_cols: List[str]) -> pd.DataFrame:
        """Enhanced data cleaning and melting with better error handling."""
        if self.df is None:
            raise ValueError("No data loaded")
            
        df = self.df.copy()
        self.logger.info(f"🧹 Starting data cleaning. Original shape: {df.shape}")
        
        try:
            # Clean column names
            df.columns = df.columns.str.strip().str.replace(' ', '_')
            
            # Melt wide to long format
            if date_cols:
                df = df.melt(
                    id_vars=metadata_cols,
                    value_vars=date_cols,
                    var_name="Date",
                    value_name="Value"
                )
            else:
                # Fallback: try to infer date columns
                parsed_dates = pd.to_datetime(df.columns, errors='coerce')
                inferred_dates = [c for c, p in zip(df.columns, parsed_dates) if not pd.isna(p)]
                
                if inferred_dates:
                    id_vars = [c for c in df.columns if c not in inferred_dates]
                    df = df.melt(
                        id_vars=id_vars,
                        value_vars=inferred_dates,
                        var_name="Date",
                        value_name="Value"
                    )
                else:
                    self.logger.warning("⚠️ No date columns detected, returning original data")
                    return df
 
            # Clean and convert values
            df["Value"] = df["Value"].astype(str).str.replace(",", "").str.strip()
            df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
 
            # Remove empty and duplicate rows
            initial_rows = len(df)
            df = df.dropna(subset=["Value"])
            df = df.drop_duplicates()
            
            self.logger.info(f"📊 Cleaned data: {initial_rows} -> {len(df)} rows")
 
            # Parse and sort by dates
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.sort_values("Date").reset_index(drop=True)
 
            self.logger.info(f"✅ Data cleaning completed. Final shape: {df.shape}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Error in data cleaning: {str(e)}")
            raise
 
    def analyze_and_clean(self) -> pd.DataFrame:
        """Enhanced wrapper for AI-powered data cleaning."""
        try:
            self.logger.info("🤖 Starting AI-powered data analysis and cleaning")
            roles = self.detect_column_roles()
            
            if "error" in roles:
                raise ValueError(roles["error"])
                
            tidy_df = self.clean_and_melt(
                date_cols=roles.get("date_columns", []),
                metadata_cols=roles.get("metadata_columns", []) + roles.get("id_columns", [])
            )
            
            self.logger.info("✅ AI-powered cleaning completed successfully")
            return tidy_df
            
        except Exception as e:
            self.logger.error(f"❌ Error in analyze_and_clean: {str(e)}")
            raise
 
    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        """Enhanced query analysis with better error handling and logging."""
        if self.df is None:
            return {"error": "No CSV file loaded. Please load a CSV first."}
       
        try:
            self.logger.info(f"🤖 Analyzing query: {user_query}")
            
            # Enhanced prompt with context
            enhanced_prompt = f"""
User Request: {user_query}

Dataset Context:
{self.csv_info}

Available Libraries: {', '.join([lib for lib, available in self.available_libraries.items() if available])}

Generate Python code that:
1. Starts with data validation and overview
2. Implements the requested analysis
3. Includes comprehensive error handling
4. Provides clear outputs and visualizations
5. Ends with a summary of results

CRITICAL REQUIREMENTS:
- Use 'df' variable (already loaded DataFrame)
- NEVER use pd.read_csv() or file paths
- Include print statements for debugging
- Handle missing/dirty data gracefully
- Use only available libraries
- For ALL plots: use st.pyplot(fig) and plt.close(fig)
- NEVER use plt.show() - it won't work in Streamlit
- Provide fallback methods if primary approach fails
"""
            
            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self._create_system_prompt()},
                    {"role": "user", "content": enhanced_prompt}
                ],
                temperature=0.1,
            )
            
            generated_code = response.choices[0].message.content
            
            # Extract code from markdown blocks
            if "```python" in generated_code:
                generated_code = generated_code.split("```python")[1].split("```")[0].strip()
            elif "```" in generated_code:
                generated_code = generated_code.split("```")[1].split("```")[0].strip()
           
            self.logger.info("📝 Code generation completed")
            
            # Execute the generated code
            execution_result = self._execute_code(generated_code)
            
            # Store execution history
            execution_record = {
                "timestamp": datetime.now().isoformat(),
                "query": user_query,
                "generated_code": generated_code,
                "execution_result": execution_result,
                "success": execution_result.get("success", False)
            }
            
            self.execution_history.append(execution_record)
            
            self.logger.info(f"📊 Query analysis completed. Success: {execution_result.get('success', False)}")
            
            return execution_record
            
        except Exception as e:
            error_record = {
                "timestamp": datetime.now().isoformat(),
                "query": user_query,
                "error": f"Error analyzing query: {str(e)}",
                "traceback": traceback.format_exc(),
                "success": False
            }
            
            self.execution_history.append(error_record)
            self.logger.error(f"❌ Query analysis failed: {str(e)}")
            
            return error_record
 
    def _execute_code(self, code: str) -> Dict[str, Any]:
        """Enhanced code execution with proper Streamlit chart support."""
        try:
            self.logger.info("🔧 Starting code execution")
            
            # Import streamlit in execution context
            import streamlit as st
            
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            # Base execution environment with streamlit
            exec_globals = {
                'df': self.df,
                'pd': pd,
                'np': np,
                'plt': plt,
                'sns': sns,
                'json': json,
                'os': os,
                'warnings': warnings,
                'print': print,
                'datetime': datetime,
                'timedelta': timedelta,
                'st': st  # Add streamlit to execution context
            }
            
            # Add available libraries
            if self.available_libraries.get('sklearn', False):
                try:
                    from sklearn.linear_model import LinearRegression
                    from sklearn.model_selection import train_test_split
                    from sklearn.metrics import mean_squared_error, r2_score
                    from sklearn.preprocessing import StandardScaler, MinMaxScaler
                    exec_globals.update({
                        'LinearRegression': LinearRegression,
                        'train_test_split': train_test_split,
                        'mean_squared_error': mean_squared_error,
                        'r2_score': r2_score,
                        'StandardScaler': StandardScaler,
                        'MinMaxScaler': MinMaxScaler
                    })
                except ImportError:
                    self.logger.warning("⚠️ sklearn import failed")
            
            if self.available_libraries.get('scipy', False):
                try:
                    from scipy import stats
                    exec_globals['stats'] = stats
                except ImportError:
                    self.logger.warning("⚠️ scipy import failed")
            
            if self.available_libraries.get('statsmodels', False):
                try:
                    import statsmodels.api as sm
                    exec_globals['sm'] = sm
                except ImportError:
                    self.logger.warning("⚠️ statsmodels import failed")
            
            if self.available_libraries.get('xgboost', False):
                try:
                    import xgboost as xgb
                    from xgboost import XGBRegressor
                    exec_globals.update({'xgb': xgb, 'XGBRegressor': XGBRegressor})
                except ImportError:
                    self.logger.warning("⚠️ xgboost import failed")
            
            if self.available_libraries.get('tensorflow', False):
                try:
                    import tensorflow as tf
                    from tensorflow import keras
                    exec_globals.update({'tf': tf, 'keras': keras})
                except ImportError:
                    self.logger.warning("⚠️ tensorflow import failed")
            
            if self.available_libraries.get('plotly', False):
                try:
                    import plotly.express as px
                    import plotly.graph_objects as go
                    exec_globals.update({'px': px, 'go': go})
                except ImportError:
                    self.logger.warning("⚠️ plotly import failed")
            
            # Execute the code
            exec_locals = {}
            exec(code, exec_globals, exec_locals)
                        
            # Restore stdout
            sys.stdout = old_stdout
            output = captured_output.getvalue()
            
            # Extract result variables
            result_vars = {k: v for k, v in exec_locals.items() if not k.startswith('_')}
            
            self.logger.info("✅ Code execution completed successfully")
            
            return {
                "success": True,
                "output": output,
                "variables": result_vars,
                "message": "✅ Execution completed successfully!",
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Restore stdout in case of error
            sys.stdout = old_stdout
            
            error_message = str(e)
            error_traceback = traceback.format_exc()
            
            self.logger.error(f"❌ Code execution failed: {error_message}")
            
            return {
                "success": False,
                "error": error_message,
                "traceback": error_traceback,
                "message": f"❌ Execution failed: {error_message}",
                "execution_time": datetime.now().isoformat()
            }
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the complete execution history."""
        return self.execution_history.copy()
    
    def clear_execution_history(self):
        """Clear the execution history."""
        self.execution_history.clear()
        self.logger.info("🗑️ Execution history cleared")
    
    def export_results(self, format: str = "json") -> str:
        """Export analysis results in various formats."""
        if not self.execution_history:
            return "No execution history available"
        
        if format.lower() == "json":
            return json.dumps(self.execution_history, indent=2, default=str)
        elif format.lower() == "csv":
            # Create a summary DataFrame
            summary_data = []
            for record in self.execution_history:
                summary_data.append({
                    "timestamp": record["timestamp"],
                    "query": record["query"],
                    "success": record["success"],
                    "error": record.get("error", "")
                })
            df_summary = pd.DataFrame(summary_data)
            return df_summary.to_csv(index=False)
        else:
            return "Unsupported format. Use 'json' or 'csv'"
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Generate a comprehensive data quality report."""
        if self.df is None:
            return {"error": "No data loaded"}
        
        report = {
            "overview": {
                "shape": self.df.shape,
                "memory_usage_mb": self.df.memory_usage(deep=True).sum() / 1024**2,
                "columns": list(self.df.columns)
            },
            "data_types": dict(self.df.dtypes),
            "missing_values": {
                "total": self.df.isnull().sum().sum(),
                "by_column": dict(self.df.isnull().sum()),
                "percentage": dict((self.df.isnull().sum() / len(self.df) * 100).round(2))
            },
            "duplicates": {
                "total": self.df.duplicated().sum(),
                "percentage": round(self.df.duplicated().sum() / len(self.df) * 100, 2)
            },
            "unique_values": {col: self.df[col].nunique() for col in self.df.columns},
            "data_quality_score": self._calculate_quality_score()
        }
        
        return report
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall data quality score (0-100)."""
        if self.df is None:
            return 0.0
        
        # Factors affecting quality
        missing_ratio = self.df.isnull().sum().sum() / (self.df.shape[0] * self.df.shape[1])
        duplicate_ratio = self.df.duplicated().sum() / len(self.df)
        
        # Calculate score (higher is better)
        score = 100 * (1 - missing_ratio) * (1 - duplicate_ratio)
        
        return round(score, 2)
 
    def interactive_session(self):
        """Enhanced interactive session with better UX."""
        print("🚀 Welcome to Enhanced Quadratic-Inspired CSV AI Analyzer!")
        print("=" * 70)
        print(f"📚 Available libraries: {', '.join([lib for lib, available in self.available_libraries.items() if available])}")
        print("=" * 70)
       
        while True:
            csv_path = input("\n📁 Enter CSV file path (or 'quit' to exit): ").strip()
            if csv_path.lower() == 'quit':
                return
            
            if self.load_csv(csv_path):
                # Show data quality report
                quality_report = self.get_data_quality_report()
                print(f"\n📊 Data Quality Score: {quality_report['data_quality_score']}/100")
                break
            else:
                print("❌ Please try again or type 'quit' to exit.")
       
        print("\n🎯 AI Analysis Commands Available:")
        print("=" * 50)
        examples = [
            "show data overview and quality report",
            "create correlation heatmap for numeric columns",
            "forecast next 30 days using time series",
            "find and visualize outliers",
            "perform regression analysis",
            "generate comprehensive data insights",
            "create interactive dashboard visualizations"
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"{i}. {example}")
        
        print("\n💡 Type 'help' for more commands, 'history' for execution history, 'quit' to exit")
        print("=" * 70)
       
        while True:
            try:
                query = input("\n🔍 Your analysis request: ").strip()
                
                if query.lower() == 'quit':
                    print("👋 Thanks for using Enhanced Quadratic CSV Analyzer!")
                    break
                elif query.lower() == 'help':
                    self._show_help()
                    continue
                elif query.lower() == 'history':
                    self._show_history()
                    continue
                elif query.lower() == 'clear':
                    self.clear_execution_history()
                    print("🗑️ History cleared!")
                    continue
                elif not query:
                    continue
                
                # Execute analysis
                print(f"\n🤖 Processing: {query}")
                print("-" * 50)
                
                result = self.analyze_query(query)
                
                if result.get("success", False):
                    print(f"✅ {result['execution_result']['message']}")
                    if result['execution_result'].get('variables'):
                        print(f"📋 Generated variables: {list(result['execution_result']['variables'].keys())}")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
                
                print("-" * 70)
                
            except KeyboardInterrupt:
                print("\n👋 Thanks for using Enhanced Quadratic CSV Analyzer!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
                self.logger.error(f"Unexpected error in interactive session: {str(e)}")
    
    def _show_help(self):
        """Show help information."""
        help_text = """
🆘 HELP - Available Commands:

📊 Data Analysis:
  • "show data overview" - Basic dataset information
  • "data quality report" - Comprehensive quality analysis
  • "correlation analysis" - Show relationships between variables
  • "statistical summary" - Descriptive statistics

📈 Visualizations:
  • "create heatmap" - Correlation heatmap
  • "plot distributions" - Distribution plots for numeric columns
  • "box plots for outliers" - Outlier detection plots
  • "time series plot" - Time-based visualizations

🔮 Forecasting:
  • "forecast [column] for [period]" - Time series forecasting
  • "regression analysis" - Predictive modeling
  • "trend analysis" - Trend identification

🛠️ Utilities:
  • "help" - Show this help
  • "history" - Show execution history
  • "clear" - Clear execution history
  • "quit" - Exit the analyzer

💡 Tips:
  • Be specific about what you want to analyze
  • Mention column names if you know them
  • Ask for explanations of results
        """
        print(help_text)
    
    def _show_history(self):
        """Show execution history."""
        if not self.execution_history:
            print("📝 No execution history available")
            return
        
        print("📚 Execution History:")
        print("=" * 50)
        
        for i, record in enumerate(self.execution_history[-10:], 1):  # Show last 10
            status = "✅" if record["success"] else "❌"
            print(f"{i}. {status} {record['timestamp'][:19]} - {record['query'][:50]}...")
        
        if len(self.execution_history) > 10:
            print(f"\n... and {len(self.execution_history) - 10} more entries")
 
def main():
    """Enhanced main function with better error handling."""
    print("🚀 Enhanced Quadratic-Inspired CSV AI Analyzer")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["AZUREAPI", "AZUREVERSION", "AZUREENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("\n📋 Please set the following:")
        print("- AZUREAPI: Your Azure OpenAI API key")
        print("- AZUREVERSION: API version (e.g., '2024-02-01')")
        print("- AZUREENDPOINT: Your Azure OpenAI endpoint")
        print("\n💡 You can set these in a .env file or as environment variables")
        return
    
    try:
        analyzer = QuadraticCSVAnalyzer()
        analyzer.interactive_session()
    except Exception as e:
        print(f"❌ Failed to start analyzer: {str(e)}")
        print("Please check your Azure OpenAI configuration")
 
if __name__ == "__main__":
    main()