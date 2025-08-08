import logging
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from openai import AzureOpenAI
import json
import traceback
from typing import Dict, Any, List, Tuple
import warnings
import re
from datetime import datetime, timedelta
from pathlib import Path
import base64
from io import BytesIO
import shutil
import pickle
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings, generate_blob_sas, BlobSasPermissions
warnings.filterwarnings('ignore')
 
class ConversationHistory:
    """Manages conversation history for each session."""
    
    def __init__(self, session_id: str, output_dir: Path):
        self.session_id = session_id
        self.output_dir = output_dir
        self.history_file = output_dir / f"conversation_history_{session_id}.json"
        self.history = []
        self.load_history()
    
    def load_history(self):
        """Load conversation history from file if it exists."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                print(f"📜 Loaded {len(self.history)} previous conversations")
        except Exception as e:
            print(f"⚠️ Could not load conversation history: {e}")
            self.history = []
    
    def save_history(self):
        """Save conversation history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Could not save conversation history: {e}")
    
    def add_conversation(self, user_query: str, response: Dict[str, Any]):
        """Add a new conversation to history."""
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "response_type": response.get("type", "unknown"),
            "success": response.get("success", False),
            "error": response.get("error", None),
            "generated_images": response.get("generated_images", []),
            "dataframes_count": len(response.get("dataframes", {})),
            "execution_output": response.get("execution_result", {}).get("output", "")
        }
        
        # Store only essential information to avoid large files
        if response.get("type") == "comprehensive_report":
            conversation["report_generated"] = True
            conversation["report_length"] = len(response.get("comprehensive_report", ""))
        
        self.history.append(conversation)
        self.save_history()
    
    def get_context_for_ai(self, last_n: int = 5) -> str:
        """Get recent conversation context for AI."""
        if not self.history:
            return ""
        
        recent_history = self.history[-last_n:]
        context = "\n### RECENT CONVERSATION CONTEXT:\n"
        
        for i, conv in enumerate(recent_history, 1):
            context += f"\n{i}. Previous Query: {conv['user_query']}\n"
            context += f"   Response Type: {conv['response_type']}\n"
            context += f"   Success: {conv['success']}\n"
            
            if conv.get('generated_images'):
                context += f"   Generated Images: {len(conv['generated_images'])}\n"
            
            if conv.get('dataframes_count', 0) > 0:
                context += f"   Generated DataFrames: {conv['dataframes_count']}\n"
            
            if conv.get('error'):
                context += f"   Error: {conv['error'][:100]}...\n"
        
        context += "\nUse this context to provide more relevant and coherent responses.\n"
        return context
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary."""
        if not self.history:
            return {"total_queries": 0, "successful_queries": 0, "failed_queries": 0}
        
        total = len(self.history)
        successful = sum(1 for h in self.history if h.get('success', False))
        failed = total - successful
        
        query_types = {}
        for h in self.history:
            response_type = h.get('response_type', 'unknown')
            query_types[response_type] = query_types.get(response_type, 0) + 1
        
        return {
            "total_queries": total,
            "successful_queries": successful,
            "failed_queries": failed,
            "query_types": query_types,
            "session_duration": self._calculate_session_duration()
        }
    
    def _calculate_session_duration(self) -> str:
        """Calculate session duration."""
        if len(self.history) < 2:
            return "N/A"
        
        start_time = datetime.fromisoformat(self.history[0]['timestamp'])
        end_time = datetime.fromisoformat(self.history[-1]['timestamp'])
        duration = end_time - start_time
        
        return str(duration).split('.')[0]  # Remove microseconds


class QuadraticCSVAnalyzer:
    """
    Enhanced Quadratic-inspired CSV analyzer that returns DataFrame results by default,
    with comprehensive report generation only when specifically requested.
    Focus on actionable data that can be updated back to the original file.
    """
   
    def __init__(self):
        """Initialize the analyzer with Azure OpenAI client and result management."""
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZUREAPI"),
            api_version=os.getenv("AZUREVERSION"),
            azure_endpoint=os.getenv("AZUREENDPOINT")
        )
        self.MODEL = "gpt-4o-mini"
        self.df = None
        self.csv_info = ""
        self.original_file_path = None
       
        # Session management
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Azure Blob Storage client
        self.blob_service_client = BlobServiceClient(
            account_url=os.getenv("AZURE_STORAGE_ACCOUNT_URL"),
            credential=os.getenv("AZURE_STORAGE_KEY")
        )
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "pmc")
        
        # Create blob-based directory structure
        self.analysis_folder_name = f"analysis_{self.current_session_id}"
        self.images_folder_name = f"{self.analysis_folder_name}/images"
        self.reports_folder_name = f"{self.analysis_folder_name}/reports"
        self.data_folder_name = f"{self.analysis_folder_name}/data_updates"
        
        # Local directories for temporary storage
        self.output_dir = Path(f"temp_analysis_output_{self.current_session_id}")
        self.images_dir = self.output_dir / "images"
        self.reports_dir = self.output_dir / "reports"
        self.data_dir = self.output_dir / "data_updates"
        
        # Track generated images with blob URLs
        self.generated_images = []
        self.blob_image_urls = {}
       
        # Result tracking
        self.analysis_results = {}
        self.data_updates = {}
        
        # Create local directories and initialize blob structure
        self._setup_directories()
        self._initialize_blob_structure()
       
    def _setup_directories(self):
        """Create necessary local directories for temporary storage."""
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        print(f"📁 Local temp directory created: {self.output_dir}")
    
    def _initialize_blob_structure(self):
        """Initialize the folder structure in the blob container."""
        try:
            # Create placeholder files to establish folder structure in blob storage
            placeholder_content = "# Analysis session structure"
            
            # Create analysis folder structure
            folder_paths = [
                f"{self.analysis_folder_name}/session_info.txt",
                f"{self.images_folder_name}/placeholder.txt",
                f"{self.reports_folder_name}/placeholder.txt", 
                f"{self.data_folder_name}/placeholder.txt"
            ]
            
            for blob_path in folder_paths:
                try:
                    blob_client = self.blob_service_client.get_blob_client(
                        container=self.container_name,
                        blob=blob_path
                    )
                    blob_client.upload_blob(
                        placeholder_content.encode('utf-8'),
                        overwrite=True
                    )
                except Exception as e:
                    print(f"⚠️ Could not create blob structure for {blob_path}: {e}")
            
            print(f"🗂️ Initialized blob folder structure: {self.container_name}/{self.analysis_folder_name}")
            
        except Exception as e:
            print(f"⚠️ Could not initialize blob structure: {e}")
    
    def _upload_image_to_blob(self, image_path: str) -> str:
        logging.basicConfig(level=logging.DEBUG)

        try:
            if not os.path.isfile(image_path):
                logging.error(f"❌ Image file not found: {image_path}")
                return ""

            image_filename = Path(image_path).name
            blob_name = f"{self.images_folder_name}/{image_filename}"

            account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL").rstrip('/')
            account_name = account_url.split("//")[1].split(".")[0]
            account_key = os.getenv("AZURE_STORAGE_KEY")
            container_name = self.container_name

            if not account_key or not container_name:
                logging.error("❌ Missing Azure credentials.")
                return ""

            # Re-initialize client
            self.blob_service_client = BlobServiceClient(account_url=account_url, credential=account_key)

            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)

            with open(image_path, "rb") as data:
                blob_client.upload_blob(
                    data,
                    overwrite=True,
                    content_settings=ContentSettings(content_type='image/png')
                )

            logging.info(f"📤 Uploaded image to blob: {container_name}/{blob_name}")

            # 🔐 Generate SAS token
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=2)
            )

            # ✅ Build full SAS URL
            sas_url = f"{account_url}/{container_name}/{blob_name}"
            logging.debug(f"🔗 SAS URL: {sas_url}")

            # Store SAS URL
            self.blob_image_urls[image_filename] = sas_url
            return sas_url

        except Exception as e:
            logging.exception(f"⚠️ Exception during upload: {str(e)}")
            return ""
    
    def _upload_file_to_blob(self, local_file_path: str, blob_subfolder: str) -> str:
        """
        Upload any file to Azure Blob Storage under a specified subfolder
        within the analysis folder. Returns the public blob URL.
        """
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

        try:
            logging.info(f"🧪 Uploading file: {local_file_path}")

            if not os.path.isfile(local_file_path):
                logging.error(f"❌ File not found: {local_file_path}")
                return ""

            file_name = Path(local_file_path).name

            # Validate required instance variables
            if not self.analysis_folder_name or not self.container_name:
                logging.error("❌ Missing required configuration in class instance.")
                return ""

            # Build the blob path
            blob_name = f"{self.analysis_folder_name}/{blob_subfolder}/{file_name}".strip('/')
            logging.debug(f"📁 Target blob path: {blob_name}")

            # Ensure blob_service_client is initialized
            if not self.blob_service_client:
                logging.error("❌ BlobServiceClient is not initialized.")
                return ""

            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            logging.debug("✅ Blob client created successfully.")

            # Open and upload file
            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(
                    data,
                    overwrite=True,
                    content_settings=ContentSettings(content_type="application/octet-stream")
                )
            logging.info(f"📤 Uploaded file to blob: {self.container_name}/{blob_name}")

            # Construct public URL
            public_url = f"{self.blob_service_client.url.rstrip('/')}/{self.container_name}/{blob_name}"
            logging.debug(f"🌐 Public URL: {public_url}")

            return public_url

        except Exception as e:
            logging.exception(f"⚠️ Exception occurred during file upload: {str(e)}")
            return ""
       
    def load_csv(self, file_path: str) -> bool:
        """Load CSV or Excel file and analyze its structure, supporting multiple Excel sheets."""
        try:
            import pandas as pd
            import os

            self.original_file_path = file_path
            file_ext = os.path.splitext(file_path)[-1].lower()

            if file_ext == ".csv":
                self.df = pd.read_csv(file_path, encoding="utf-8")
                self.df = self._prepare_dataframe(self.df)
                self.df_map = {"Sheet1": self.df}

            elif file_ext in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
                sheet_map = pd.read_excel(file_path, sheet_name=None, engine="openpyxl")
                self.df_map = {name: self._prepare_dataframe(df) for name, df in sheet_map.items()}
                logging.info(f"📊 Loaded {len(self.df_map)} sheets from Excel file")
                # You can assign default to first sheet {shett name: [df]}
                self.df = next(iter(self.df_map.values()))

            elif file_ext == ".xls":
                sheet_map = pd.read_excel(file_path, sheet_name=None, engine="xlrd")
                self.df_map = {name: self._prepare_dataframe(df) for name, df in sheet_map.items()}
                self.df = next(iter(self.df_map.values()))

            elif file_ext == ".ods":
                sheet_map = pd.read_excel(file_path, sheet_name=None, engine="odf")
                self.df_map = {name: self._prepare_dataframe(df) for name, df in sheet_map.items()}
                self.df = next(iter(self.df_map.values()))

            elif file_ext == ".xlsb":
                import pyxlsb
                sheet_map = pd.read_excel(file_path, sheet_name=None, engine="pyxlsb")
                self.df_map = {name: self._prepare_dataframe(df) for name, df in sheet_map.items()}
                self.df = next(iter(self.df_map.values()))

            else:
                raise ValueError(f"Unsupported file extension: {file_ext}")

            self.csv_info = self._generate_csv_info()
            self.original_df = self.df.copy()
            self._generate_basic_trends()

            print(f"✅ File loaded successfully!")
            print(f"📊 Shape: {self.df.shape}")
            print(f"🔍 Sheets: {list(self.df_map.keys())}")
            print(f"📈 Data types: {dict(self.df.dtypes)}")

            return True

        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return False


    def _prepare_dataframe(self, df):
        """Convert columns and data to string, and fill NaNs."""
        df.columns = df.columns.astype(str)
        df.index = df.index.astype(str)
        return df.applymap(lambda x: "" if pd.isna(x) else str(x))


        
    def _generate_basic_trends(self):
        """Generate basic trend metrics without generating reports."""
        try:
            trend_data = self.analyze_trends()
            self.analysis_results['basic_trends'] = trend_data
            print("✅ Basic trend analysis completed and stored")
        except Exception as e:
            print(f"⚠️ Basic trend analysis failed: {str(e)}")
 
    def _is_report_request(self, query: str) -> bool:
        """Detect if user is specifically requesting a report."""
        report_keywords = [
            'report', 'summary report', 'generate report', 'create report',
            'comprehensive report', 'strategic report', 'executive summary',
            'write report', 'full report', 'detailed report', 'analysis report'
        ]
       
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in report_keywords)
 
    def _extract_data_request(self, query: str) -> Dict[str, str]:
        """Extract what type of data modification/addition is being requested."""
        query_lower = query.lower()
       
        request_type = "analysis"  # default
       
        if any(word in query_lower for word in ['add', 'create', 'calculate', 'compute']):
            request_type = "add_columns"
        elif any(word in query_lower for word in ['update', 'modify', 'change', 'adjust']):
            request_type = "update_data"
        elif any(word in query_lower for word in ['forecast', 'predict', 'project']):
            request_type = "forecast_data"
        elif any(word in query_lower for word in ['rank', 'score', 'rate', 'classify']):
            request_type = "add_metrics"
        elif any(word in query_lower for word in ['clean', 'fix', 'correct']):
            request_type = "clean_data"
       
        return {
            "type": request_type,
            "query": query,
            "focus": "data_output"
        }
 
    def analyze_trends(self) -> Dict[str, Any]:
        """Comprehensive trend analysis for both overall data and category-wise breakdowns."""
        if self.df is None:
            return {"error": "No data loaded"}
       
        trend_results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "dataset_info": {
                "shape": self.df.shape,
                "columns": list(self.df.columns)
            },
            "overall_trends": {},
            "category_trends": {},
            "time_series_trends": {},
            "correlation_analysis": {},
            "summary_insights": []
        }
       
        try:
            # 1. Overall Numeric Trends
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col in self.df.columns:
                    series = self.df[col].dropna()
                    if len(series) > 1:
                        trend_results["overall_trends"][col] = {
                            "mean": float(series.mean()),
                            "median": float(series.median()),
                            "std": float(series.std()),
                            "trend_direction": self._calculate_trend_direction(series),
                            "volatility": float(series.std() / series.mean()) if series.mean() != 0 else 0,
                            "growth_rate": self._calculate_growth_rate(series),
                            "outliers_count": len(self._detect_outliers(series))
                        }
           
            # 2. Category-wise Trends
            categorical_cols = self.df.select_dtypes(include=['object']).columns
            for cat_col in categorical_cols:
                if cat_col in self.df.columns:
                    category_analysis = {}
                   
                    for numeric_col in numeric_cols:
                        if numeric_col in self.df.columns:
                            grouped = self.df.groupby(cat_col)[numeric_col].agg(['mean', 'count', 'std']).fillna(0)
                            category_analysis[numeric_col] = {
                                "by_category": grouped.to_dict(),
                                "top_performing": grouped['mean'].idxmax() if not grouped.empty else None,
                                "most_volatile": grouped['std'].idxmax() if not grouped.empty else None
                            }
                   
                    trend_results["category_trends"][cat_col] = category_analysis
           
            # 3. Time Series Analysis (if date columns exist)
            date_columns = [col for col in self.df.columns
                           if 'date' in col.lower() or 'time' in col.lower() or 'year' in col.lower()]
           
            for date_col in date_columns:
                if date_col in self.df.columns:
                    try:
                        df_temp = self.df.copy()
                        df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
                        df_temp = df_temp.dropna(subset=[date_col]).sort_values(date_col)
                       
                        if len(df_temp) > 1:
                            time_trends = {}
                            for num_col in numeric_cols:
                                if num_col in df_temp.columns:
                                    time_series = df_temp.set_index(date_col)[num_col].dropna()
                                    if len(time_series) > 1:
                                        time_trends[num_col] = {
                                            "start_date": str(time_series.index.min()),
                                            "end_date": str(time_series.index.max()),
                                            "period_days": (time_series.index.max() - time_series.index.min()).days,
                                            "seasonal_pattern": self._detect_seasonality(time_series),
                                            "trend_strength": self._calculate_trend_strength(time_series.values)
                                        }
                           
                            trend_results["time_series_trends"][date_col] = time_trends
                    except Exception as e:
                        print(f"⚠️ Time series analysis failed for {date_col}: {str(e)}")
           
            # 4. Correlation Analysis
            if len(numeric_cols) > 1:
                corr_matrix = self.df[numeric_cols].corr()
                strong_correlations = []
               
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:  # Strong correlation threshold
                            strong_correlations.append({
                                "variables": [col1, col2],
                                "correlation": float(corr_val),
                                "strength": "strong" if abs(corr_val) > 0.8 else "moderate"
                            })
               
                trend_results["correlation_analysis"] = {
                    "strong_correlations": strong_correlations,
                    "correlation_matrix": corr_matrix.to_dict()
                }
           
            # 5. Generate Summary Insights
            insights = []
            insights.append(f"Dataset contains {self.df.shape[0]:,} records with {self.df.shape[1]} variables")
           
            if trend_results["overall_trends"]:
                growing_vars = [var for var, data in trend_results["overall_trends"].items()
                              if data.get("growth_rate", 0) > 0]
                if growing_vars:
                    insights.append(f"Growing trends observed in: {', '.join(growing_vars[:3])}")
           
            if trend_results["category_trends"]:
                insights.append(f"Category analysis completed for {len(trend_results['category_trends'])} categorical variables")
           
            strong_corrs = trend_results.get("correlation_analysis", {}).get("strong_correlations", [])
            if strong_corrs:
                insights.append(f"Found {len(strong_corrs)} strong correlations between variables")
           
            trend_results["summary_insights"] = insights
           
        except Exception as e:
            trend_results["error"] = str(e)
            trend_results["traceback"] = traceback.format_exc()
       
        return trend_results
   
    def _calculate_trend_direction(self, series: pd.Series) -> str:
        """Calculate overall trend direction of a numeric series."""
        if len(series) < 2:
            return "insufficient_data"
       
        x = np.arange(len(series))
        slope = np.polyfit(x, series.values, 1)[0]
       
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"
   
    def _calculate_growth_rate(self, series: pd.Series) -> float:
        """Calculate compound annual growth rate."""
        if len(series) < 2:
            return 0.0
       
        start_val = series.iloc[0]
        end_val = series.iloc[-1]
       
        if start_val <= 0:
            return 0.0
       
        periods = len(series) - 1
        growth_rate = (end_val / start_val) ** (1/periods) - 1
        return float(growth_rate)
   
    def _detect_outliers(self, series: pd.Series) -> List[float]:
        """Detect outliers using IQR method."""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return series[(series < lower_bound) | (series > upper_bound)].tolist()
   
    def _detect_seasonality(self, time_series: pd.Series) -> Dict[str, Any]:
        """Detect seasonal patterns in time series data."""
        try:
            if len(time_series) < 12:
                return {"detected": False, "reason": "insufficient_data"}
           
            autocorr_12 = time_series.autocorr(lag=12) if len(time_series) >= 12 else 0
            autocorr_4 = time_series.autocorr(lag=4) if len(time_series) >= 4 else 0
           
            seasonal_strength = max(abs(autocorr_12), abs(autocorr_4))
           
            return {
                "detected": seasonal_strength > 0.3,
                "strength": float(seasonal_strength),
                "monthly_pattern": float(autocorr_12) if len(time_series) >= 12 else None,
                "quarterly_pattern": float(autocorr_4) if len(time_series) >= 4 else None
            }
        except:
            return {"detected": False, "reason": "calculation_error"}
   
    def _calculate_trend_strength(self, values: np.array) -> float:
        """Calculate trend strength using linear regression R-squared."""
        if len(values) < 2:
            return 0.0
       
        from scipy import stats
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        return float(r_value ** 2)
 
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
        """Create system prompt focused on DataFrame results and data updates, with Python basics and error protections."""
        return f"""
You are a Python code generator that MUST create COMPLETE, EXECUTABLE data analysis solutions.

MANDATORY REQUIREMENTS:
1. Generate COMPLETE Python code that runs from start to finish - NO PARTIAL CODE
2. ALWAYS include data exploration, analysis, modeling, AND visualization
3. NEVER stop at data exploration - always complete the full analysis
4. ALWAYS create charts/visualizations using matplotlib for EVERY analysis
5. Return results as DataFrames with meaningful column names
6. Use the 'df' variable (DataFrame is already loaded - NEVER use pd.read_csv())

VISUALIZATION REQUIREMENTS (MANDATORY):
- ALWAYS create at least one chart for every analysis
- Use Bar charts for comparisons, categories, rankings
- Use Line charts for trends, time series, forecasting
- Use Pie charts for revenue/profit breakdowns by category/SKU
- Save all plots using plt.savefig() and plt.show()
- Include proper titles, labels, and legends

SUCCESS CRITERIA FOR EVERY RESPONSE:
✓ Code runs completely without errors
✓ Creates actionable DataFrame results
✓ Generates meaningful visualizations
✓ Returns complete analysis (not just exploration)
✓ Includes proper data insights

CORE PHILOSOPHY:
- Focus on returning ACTIONABLE DATA as DataFrames
- Create new columns, calculated fields, or enhanced datasets
- Always show what data would be ADDED or UPDATED in the original file
- Generate visualizations only when they add value to the data analysis
 
CRITICAL REQUIREMENTS:
1. Use 'df' variable which contains the loaded DataFrame - NEVER use pd.read_csv()
2. ALWAYS return results as DataFrames that can be merged/joined with original data
3. Create meaningful column names for new calculated fields
4. Show before/after data previews
5. Focus on data enrichment rather than just analysis
 
DATA OUTPUT PRIORITIES:
1. New calculated columns (trends, scores, rankings, categories)
2. Forecasted values with future dates
3. Cleaned/standardized versions of existing data
4. Category classifications and performance metrics
5. Statistical measures and derived insights
 
Data Context:
{self.csv_info}
 
EXAMPLE OUTPUT PATTERNS:
- Adding trend indicators: df['trend_direction'], df['growth_rate']
- Creating rankings: df['performance_rank'], df['category_score']
- Forecasting: future_predictions_df with new dates and predicted values
- Classifications: df['risk_category'], df['performance_tier']
- Metrics: df['volatility_score'], df['seasonal_index']
 
VISUALIZATION GUIDELINES:
- Generate visualizations only when they help understand the data modifications
- Always save plots using plt.savefig() when created
- Keep visualizations focused on showing the new data insights
 
DATA CLEANING RULES:
- Always clean string data before converting to numeric
- Handle missing values appropriately
- Ensure data types are correct for calculations
- Validate results before returning
 
EXECUTION FOCUS:
Return DataFrames that enhance the original dataset with new insights, predictions, or calculated fields.
Show exactly what data would be added to the original file.
You MUST complete the entire analysis with visualizations in one code block.
Focus on creating NEW DATA that enhances the original dataset.

----------------- PYTHON BASICS DOCUMENTATION (FOR REFERENCE) -----------------

# Common Python Structures:
my_list = [1, 2, 3]
my_dict = {{'key': 'value'}}
for item in my_list:
    print(item)

if x > 0:
    print("Positive")
elif x < 0:
    print("Negative")
else:
    print("Zero")

def my_func(x):
    return x * 2

# DataFrame Basics:
df.head()
df.info()
df.describe()
df['column_name']
df[['col1', 'col2']]
df[df['col'] > 10]
df.groupby('category').mean()
df['new'] = df['old'] * 0.1

# Plotting with matplotlib:
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(df['date'], df['value'])  # or plt.bar(), plt.pie()
plt.title("Trend Over Time")
plt.xlabel("Date")
plt.ylabel("Value")
plt.legend(["Series A"])
plt.savefig("trend_plot.png")
plt.show()

# Handling Missing Values:
df.dropna()
df.fillna(0)
df['col'].isna().sum()

# Type Conversion:
df['col'] = df['col'].astype(float)
df['date'] = pd.to_datetime(df['date'])

# Statistical Methods:
df['col'].mean()
df['col'].median()
df['col'].std()
df.corr()

# Forecasting Example with Prophet:
from prophet import Prophet

df_prophet = df.rename(columns={{'date': 'ds', 'value': 'y'}})
model = Prophet()
model.fit(df_prophet)
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

---------------- SYNTAX SAFETY CHECKLIST (MANDATORY FOR EVERY CODE) ----------------

✓ NO unexpected indent or over-indented lines
✓ All brackets ((), [], {{}}) and quotes ('' or "") are closed properly
✓ ALL import statements at the top
✓ No use of undefined variables or functions (e.g., using plt without import)
✓ Function definitions and loops are correctly indented (4 spaces)
✓ Each line is syntactically complete (e.g., no unclosed `if`, `for`, or `def`)
✓ Save and display all plots with both `plt.savefig()` AND `plt.show()`

"""

   
    def _capture_matplotlib_plots(self) -> List[str]:
        logging.info("capture started")
        """Capture any matplotlib plots that were created during code execution and upload to blob storage."""
        captured_images = []
       
        fig_nums = plt.get_fignums()
       
        for i, fig_num in enumerate(fig_nums):
            try:
                fig = plt.figure(fig_num)
                logging.info("hello")
               
                timestamp = datetime.now().strftime("%H%M%S")
                image_filename = f"plot_{timestamp}_{i+1}.png"
                image_path = self.images_dir / image_filename
               
                fig.savefig(image_path, dpi=300, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
                
                # Upload to blob storage and get public URL
                public_url = self._upload_image_to_blob(str(image_path))
                if public_url:
                    captured_images.append(public_url)
                    self.generated_images.append(public_url)
                    logging.info(f"📸 Saved and uploaded plot: {image_filename}")
                else:
                    # Fallback to local path if upload fails
                    captured_images.append(str(image_path))
                    self.generated_images.append(image_filename)
                    print(f"📸 Saved plot locally: {image_filename}")
               
            except Exception as e:
                print(f"⚠️ Failed to save plot {i+1}: {str(e)}")
       
        return captured_images
 
    def save_data_updates(self, result_df: pd.DataFrame, update_name: str) -> str:
        """Save DataFrame results that can be used to update the original file."""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{update_name}_{timestamp}.csv"
            local_file_path = self.data_dir / filename
           
            # Save locally first
            result_df.to_csv(local_file_path, index=False)
            
            # Upload to blob storage
            blob_url = self._upload_file_to_blob(str(local_file_path), "data_updates")
           
            print(f"💾 Data update saved: {filename}")
            print(f"📊 Shape: {result_df.shape}")
            print(f"🔍 New columns: {list(result_df.columns)}")
            if blob_url:
                print(f"☁️ Uploaded to blob: {blob_url}")
           
            return blob_url if blob_url else str(local_file_path)
           
        except Exception as e:
            print(f"❌ Failed to save data update: {str(e)}")
            return ""
 
    def show_data_preview(self, original_df: pd.DataFrame, updated_df: pd.DataFrame):
        """Show a preview of what data would be added/updated."""
        print("\n" + "="*60)
        print("📊 DATA UPDATE PREVIEW")
        print("="*60)
       
        print(f"\n📈 ORIGINAL DATA (Shape: {original_df.shape}):")
        print(original_df.head(3).to_string())
       
        print(f"\n✨ UPDATED DATA (Shape: {updated_df.shape}):")
        print(updated_df.head(3).to_string())
       
        # Show new columns
        new_cols = set(updated_df.columns) - set(original_df.columns)
        if new_cols:
            print(f"\n🆕 NEW COLUMNS ADDED: {list(new_cols)}")
       
        # Show modified columns (if applicable)
        common_cols = set(original_df.columns) & set(updated_df.columns)
        modified_cols = []
        for col in common_cols:
            if not original_df[col].equals(updated_df[col]):
                modified_cols.append(col)
       
        if modified_cols:
            print(f"📝 MODIFIED COLUMNS: {modified_cols}")
       
        print("="*60)

    def _convert_dataframes_to_html_tables(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """Convert DataFrames to styled HTML tables for report inclusion."""
        html_tables = {}
        
        for df_name, df in dataframes.items():
            if df is None or df.empty:
                continue
                
            try:
                # Limit table size for readability (show first 20 rows, all columns)
                display_df = df.head(20) if len(df) > 20 else df
                
                # Generate HTML table with enhanced styling
                html_table = display_df.to_html(
                    table_id=f"table_{df_name}",
                    classes="data-table",
                    escape=False,
                    index=False,
                    float_format=lambda x: f"{x:,.2f}" if pd.notnull(x) else ""
                )
                
                # Add table metadata
                table_info = f"""
                <div class="table-container">
                    <div class="table-header">
                        <h3 class="table-title">{df_name.replace('_', ' ').title()}</h3>
                        <div class="table-meta">
                            <span class="table-info">📊 {len(df):,} rows × {len(df.columns)} columns</span>
                            {f'<span class="table-note">📝 Showing first 20 rows</span>' if len(df) > 20 else ''}
                        </div>
                    </div>
                    {html_table}
                </div>
                """
                
                html_tables[df_name] = table_info
                
            except Exception as e:
                print(f"⚠️ Failed to convert {df_name} to HTML table: {str(e)}")
                html_tables[df_name] = f"<p class='error'>❌ Error rendering table: {str(e)}</p>"
        
        return html_tables

    def _prepare_dataframes_section(self, dataframes: Dict[str, pd.DataFrame]) -> str:
        """Prepare the DataFrames section for the report."""
        if not dataframes:
            return ""
        
        html_tables = self._convert_dataframes_to_html_tables(dataframes)
        
        section_content = """
        <section id="data-results" class="report-section">
            <h2 class="section-title">📊 Generated Data Results</h2>
            <div class="section-intro">
                <p>The following tables present the key data outputs generated from the analysis. These DataFrames contain actionable insights and can be used to update the original dataset with enhanced information.</p>
            </div>
        """
        
        for df_name, html_table in html_tables.items():
            section_content += html_table
        
        # Add download links section
        section_content += """
            <div class="download-section">
                <h4>📥 Data Export Options</h4>
                <p>All generated DataFrames are available for download and can be merged with your original dataset. Check the data updates folder in blob storage for CSV exports of these results.</p>
            </div>
        </section>
        """
        
        return section_content
 
    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        """
        Analyze user query and return DataFrame results by default.
        Only generate comprehensive reports when specifically requested.
        """
        if self.df is None:
            return {"error": "No CSV file loaded. Please load a CSV first."}
       
        try:
            print(f"🤖 Analyzing query: {user_query}")
           
            # Reset generated images for this query
            self.generated_images = []
           
            # Check if this is a report request
            is_report_request = self._is_report_request(user_query)
           
            # Extract data request type
            data_request = self._extract_data_request(user_query)
           
            # Detect if this is a forecasting query
            forecasting_keywords = ['forecast', 'predict', 'future', 'next', 'ahead', 'months', 'years', 'projection']
            is_forecasting = any(keyword in user_query.lower() for keyword in forecasting_keywords)
       
            if is_report_request:
                # Generate comprehensive report
                return self._generate_comprehensive_report(user_query, is_forecasting)
            else:
                # Focus on DataFrame results
                return self._generate_dataframe_analysis(user_query, data_request, is_forecasting)
               
        except Exception as e:
            return {
                "error": f"Error analyzing query: {str(e)}",
                "traceback": traceback.format_exc(),
                "type": "error"
            }
 
    def _generate_dataframe_analysis(self, user_query: str, data_request: Dict, is_forecasting: bool) -> Dict[str, Any]:
        """Generate analysis focused on returning actionable DataFrame results."""
       
        # Enhanced prompt for DataFrame-focused analysis
        base_requirements = f"""
Generate Python code to: {user_query}
 
PRIMARY GOAL: Return actionable DataFrame results that can enhance the original dataset.
 
CRITICAL REQUIREMENTS:
- Use 'df' variable which contains the loaded DataFrame
- NEVER use pd.read_csv() or file paths
- Focus on creating NEW DATA that adds value to the original dataset
- Return results as DataFrames with meaningful column names
- Show before/after data previews
 
DATA OUTPUT FOCUS:
- Create calculated columns, derived metrics, or classifications
- Generate forecasted data with future dates if requested
- Add trend indicators, performance scores, or category rankings
- Provide data that can be merged back to the original file
 
RESULT STRUCTURE:
1. Examine original data structure
2. Perform calculations/analysis
3. Create enhanced DataFrame with new columns
4. Show preview of original vs enhanced data
5. Save results that can update the original file
 
REQUEST TYPE: {data_request['type']}
"""
 
        if is_forecasting:
            enhanced_prompt = base_requirements + f"""
FORECASTING-SPECIFIC REQUIREMENTS:
- Create a separate DataFrame with future predictions
- Include future dates beyond the last date in dataset
- Provide confidence intervals or prediction ranges
- Return forecasted_data_df with columns: [Date, Predicted_Value, Confidence_Lower, Confidence_Upper]
- Show both historical trend analysis and future predictions
 
FORECASTING OUTPUT:
- Original data with trend indicators added
- Separate forecast DataFrame for future periods
- Combined visualization showing historical + predicted


===============================================
FORECASTING FUNDAMENTALS & CRITICAL DEFINITIONS
===============================================
 
FORECASTING DEFINITION:
Forecasting = Predicting FUTURE values that extend BEYOND the existing dataset's time range.
- Historical data: Used for training models
- Future predictions: Generated for periods AFTER the last date in the dataset
- NEVER predict on known historical values when asked to "forecast"
 
TIME SERIES FORECASTING MODELS & THEIR LOGIC:
 
1. LINEAR REGRESSION FORECASTING:
```
Pseudo-code:
1. Create time index (0, 1, 2, ..., n-1) for historical data
2. Fit: y = ax + b where x = time_index
3. For future predictions:
   - future_time_indices = [n, n+1, n+2, ..., n+forecast_periods-1]
   - future_values = model.predict(future_time_indices)
4. Convert future_time_indices back to actual future dates
```
 
2. MOVING AVERAGE FORECASTING:
```
Pseudo-code:
1. Simple Moving Average: forecast = mean(last_N_values)
2. Weighted Moving Average: forecast = sum(weights * last_N_values)
3. Exponential Moving Average:
   - alpha = smoothing_factor (0.1 to 0.3)
   - forecast = alpha * last_value + (1-alpha) * previous_forecast
```
 
3. AUTOREGRESSIVE (AR) MODELS:
```
Pseudo-code:
1. AR(p): y_t = c + φ₁*y_{{t-1}} + φ₂*y_{{t-2}} + ... + φ_p*y_{{t-p}} + ε_t
2. For forecasting:
   - Use last p values to predict next value
   - Recursively use predictions to forecast multiple periods ahead
3. Implementation: Use statsmodels.tsa.ar_model.AutoReg
```
 
4. ARIMA FORECASTING:
```
Pseudo-code:
1. ARIMA(p,d,q): Combines AR(p) + Integration(d) + MA(q)
2. Auto-detect parameters using auto_arima or AIC/BIC
3. For forecasting:
   - model.fit(historical_data)
   - forecast = model.forecast(steps=forecast_periods)
4. Implementation: Use statsmodels.tsa.arima.ARIMA
```
 
5. XGBOOST TIME SERIES FORECASTING:
```
Pseudo-code:
1. Create lagged features: [y_{{t-1}}, y_{{t-2}}, ..., y_{{t-window_size}}]
2. Feature matrix X: Each row = [lag1, lag2, ..., lag_window]
3. Target y: y_t (current value to predict)
4. Train: XGBRegressor.fit(X, y)
5. For multi-step forecasting:
   a. Predict next value using last window
   b. Add prediction to window, remove oldest value
   c. Repeat for each future period
```
 
6. LSTM NEURAL NETWORK FORECASTING:
```
Pseudo-code:
1. Reshape data: (samples, window_size, features)
2. Architecture: Input -> LSTM(50-100 units) -> Dense(1)
3. Training: Minimize MSE between predicted and actual
4. For forecasting:
   a. Use last window_size values as input
   b. Predict next value
   c. Update window with prediction
   d. Repeat for multiple periods
```
 
===============================================
MANDATORY FORECASTING IMPLEMENTATION RULES
===============================================
 
STEP 1: DATA PREPARATION
```python
# Always start with data exploration
print("=== DATA EXPLORATION ===")
print(f"DataFrame shape: {{df.shape}}")
print(f"Columns: {{df.columns.tolist()}}")
print(df.info())
print(df.head())
 
# Identify time and target columns
date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower() or 'year' in col.lower()]
numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
print(f"Potential date columns: {{date_columns}}")
print(f"Numeric columns: {{numeric_columns}}")
```
 
STEP 2: TIME SERIES PREPARATION
```python
# Clean and prepare time series
def prepare_time_series(df, date_col, target_col):
    # Convert date column
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
   
    # Clean target column
    if df[target_col].dtype == 'object':
        df[target_col] = df[target_col].astype(str).str.replace(',', '').str.replace(', '').str.strip()
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
   
    # Remove missing values
    df = df.dropna(subset=[date_col, target_col])
   
    # Sort by date
    df = df.sort_values(date_col).reset_index(drop=True)
   
    return df
```
 
STEP 3: FUTURE DATE GENERATION
```python
def generate_future_dates(last_date, periods, frequency):
    \"\"\"Generate future dates beyond the dataset\"\"\"
    if frequency == 'D':
        return pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods, freq='D')
    elif frequency == 'W':
        return pd.date_range(start=last_date + pd.Timedelta(weeks=1), periods=periods, freq='W')
    elif frequency == 'M':
        return pd.date_range(start=last_date + pd.DateOffset(months=1), periods=periods, freq='M')
    elif frequency == 'Y':
        return pd.date_range(start=last_date + pd.DateOffset(years=1), periods=periods, freq='Y')
   
# Usage example:
last_historical_date = df[date_col].max()
future_dates = generate_future_dates(last_historical_date, forecast_periods, frequency)
print(f"Historical data ends: {{last_historical_date}}")
    print(f"Forecasting from: {{future_dates[0]}} to {{future_dates[-1]}}")
```
 
CRITICAL EXECUTION REQUIREMENTS
===============================================
 
1. ALWAYS use the variable 'df' to reference the loaded DataFrame - NEVER use pd.read_csv()
2. ALWAYS start with data exploration: df.info(), df.head(), column analysis
3. ALWAYS generate future dates that come AFTER the last date in the dataset
4. ALWAYS implement multiple forecasting models for comparison
5. ALWAYS use recursive/iterative prediction for multi-step ahead forecasting
6. ALWAYS create visualizations showing clear separation between historical and forecasted data
7. ALWAYS provide forecast summary statistics and comparison tables
8. ALWAYS include proper error handling with fallback models
9. ALWAYS validate that forecasted dates are in the future, not historical
 
DATA CLEANING RULES:
- Always clean string data before converting to numeric: .astype(str).str.replace(',', '').str.strip()
- Handle empty strings and spaces: replace with np.nan or 0
- Use pd.to_numeric(errors='coerce') for safe conversion
- Check for object dtype columns that should be numeric
- Remove or skip completely empty columns (like 'Unnamed' columns)
 
FORECASTING VALIDATION CHECKLIST:
✓ Historical data used for training only
✓ Future dates generated beyond dataset range  
✓ Multiple models implemented and compared
✓ Recursive forecasting for multi-step predictions
✓ Proper data cleaning and preprocessing
✓ Clear visualization with historical vs forecasted data
✓ Summary statistics and model comparison
✓ Error handling with fallback options
 
Remember: Forecasting means predicting the FUTURE, not explaining the past!
"""
        else:
            enhanced_prompt = base_requirements + f"""
ANALYSIS-SPECIFIC REQUIREMENTS:
- Add calculated fields to enhance business insights
- Create performance metrics, rankings, or categorizations  
- Generate trend indicators and growth rates
- Provide statistical measures as new columns
- Focus on actionable business intelligence
 
ANALYSIS OUTPUT:
- Enhanced DataFrame with new calculated columns
- Summary statistics as additional rows/columns
- Category-wise metrics and comparisons
- Data quality indicators and flags
"""
       
        # Generate and execute the analysis code
        response = self.openai_client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user",   "content": enhanced_prompt}
            ],
            # temperature=0.1,
        )
       
        generated_code = response.choices[0].message.content
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0].strip()
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0].strip()
       
        print("📝 Generated code:")
        print(generated_code)
        print("-" * 50)
       
        result = self._execute_code(generated_code)
       
        # Process results to extract DataFrames
        dataframes_found = {}
        if result.get("success") and result.get("variables"):
            for var_name, var_value in result["variables"].items():
                if isinstance(var_value, pd.DataFrame):
                    dataframes_found[var_name] = var_value
                    print(f"📊 Found DataFrame: {var_name} (Shape: {var_value.shape})")
       
        # Prepare the result
        analysis_result = {
            "query": user_query,
            "type": "dataframe_analysis",
            "request_type": data_request['type'],
            "generated_code": generated_code,
            "execution_result": result,
            "success": result.get("success", False),
            "is_forecasting": is_forecasting,
            "generated_images": self.generated_images.copy(),
            "blob_image_urls": self.blob_image_urls.copy(),
            "dataframes": dataframes_found,
            "data_update_available": len(dataframes_found) > 0
        }
       
        # Show data updates if successful
        if result.get("success") and dataframes_found:
            print(f"\n✅ Analysis completed successfully!")
            print(f"📊 Generated {len(dataframes_found)} result DataFrames")
           
            # Save the main result DataFrame
            main_df_name = list(dataframes_found.keys())[0]
            main_df = dataframes_found[main_df_name]
           
            if len(main_df) > 0:
                # Show preview
                self.show_data_preview(self.original_df, main_df)
               
                # Save for potential file update
                update_name = data_request['type'].replace('_', '-')
                saved_path = self.save_data_updates(main_df, update_name)
                analysis_result["saved_data_path"] = saved_path
               
                print(f"\n💡 NEXT STEPS:")
                print(f"   • Review the data updates above")
                print(f"   • Data saved to: {self.container_name}/{self.data_folder_name}")
                print(f"   • Use this data to update your original file")
                if is_forecasting:
                    print(f"   • Forecast data can be appended to extend your dataset")
       
        return analysis_result
 
    def _generate_comprehensive_report(self, user_query: str, is_forecasting: bool) -> Dict[str, Any]:
        """Generate comprehensive report when specifically requested."""
        print("\n📋 Generating comprehensive strategic report...")
       
        try:
            # First run the analysis to get data
            data_request = self._extract_data_request(user_query)
            analysis_result = self._generate_dataframe_analysis(user_query, data_request, is_forecasting)
           
            if not analysis_result.get("success"):
                return {
                    "error": "Cannot generate report - analysis failed",
                    "type": "report_error"
                }
           
            # Generate the report
            market_topic = self._extract_market_topic(user_query)
            target_variable = self._extract_target_variable(user_query)
            forecast_periods = self._extract_forecast_periods(user_query) if is_forecasting else 6
           
            # Prepare data context for report
            data_context = self._prepare_report_data_context(analysis_result, target_variable)
            
            # Use blob image URLs for report generation
            image_urls = analysis_result.get("blob_image_urls", {})
            
            # Get generated DataFrames for table inclusion
            dataframes = analysis_result.get("dataframes", {})
           
            report = self.generate_forecast_report(
                data_context=data_context,
                forecast_results=analysis_result,
                client_name="Executive Leadership Team",
                market_topic=market_topic,
                forecast_periods=forecast_periods,
                target_variable=target_variable,
                image_urls=image_urls,
                dataframes=dataframes  # Pass DataFrames to report generation
            )
           
            # Save report to blob storage
            if report:
                report_filename = f"strategic_report_{market_topic.replace(' ', '_').lower()}_{self.current_session_id}.html"
                local_report_path = self.reports_dir / report_filename
                
                # Save locally first
                with open(local_report_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                # Upload to blob storage
                report_blob_url = self._upload_file_to_blob(str(local_report_path), "reports")
           
            analysis_result.update({
                "type": "comprehensive_report",
                "comprehensive_report": report,
                "report_generated": True,
                "report_blob_url": report_blob_url if 'report_blob_url' in locals() else None,
                "market_topic": market_topic,
                "target_variable": target_variable,
                "forecast_periods": forecast_periods
            })
           
            print("✅ Comprehensive strategic report generated successfully!")
            if 'report_blob_url' in locals() and report_blob_url:
                print(f"☁️ Report uploaded to blob: {report_blob_url}")
           
        except Exception as report_error:
            print(f"⚠️ Report generation failed: {str(report_error)}")
            analysis_result.update({
                "report_error": str(report_error),
                "report_generated": False,
                "type": "report_error"
            })
       
        return analysis_result
 
    def _extract_market_topic(self, query: str) -> str:
        """Extract market topic from user query using AI-powered analysis."""
        import re
        
        query_lower = query.lower()
        
        # First, try to extract a specific topic from the query using pattern matching
        topic_title = self._generate_dynamic_report_title(query)
        
        if topic_title and topic_title != "Business Intelligence Analysis":
            return topic_title
        
        # Fallback to keyword matching if AI generation fails
        topic_keywords = {
            'sales': 'Sales Performance Analysis',
            'revenue': 'Revenue Growth Analysis', 
            'profit': 'Profitability Analysis',
            'market': 'Market Analysis',
            'customer': 'Customer Analytics',
            'product': 'Product Performance Analysis',
            'financial': 'Financial Analysis',
            'growth': 'Growth Analysis',
            'trend': 'Trend Analysis',
            'demand': 'Demand Forecasting',
            'supply': 'Supply Chain Analysis'
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in query_lower:
                return topic
        
        return "Business Intelligence Analysis"

    def _generate_dynamic_report_title(self, query: str) -> str:
        """Generate dynamic report title based on user query using AI."""
        try:
            # Create a prompt to generate a professional report title
            title_prompt = f"""
            Based on the following user query, generate a professional strategic report title that would be appropriate for an executive-level business report.
            
            User Query: "{query}"
            
            Requirements:
            - Keep it concise (3-7 words)
            - Make it professional and executive-friendly
            - Focus on the main business objective or analysis type
            - Avoid generic terms like "Business Intelligence" unless specifically relevant
            - Examples of good titles: "Q4 Sales Performance Analysis", "Customer Retention Strategy Review", "Market Expansion Feasibility Study"
            
            Return ONLY the title, no additional text or explanations.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert business analyst who creates professional report titles."},
                    {"role": "user", "content": title_prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            generated_title = response.choices[0].message.content.strip()
            
            # Clean up the title (remove quotes, ensure proper capitalization)
            generated_title = generated_title.strip('"\'')
            
            # Validate the title isn't too long or generic
            if len(generated_title.split()) <= 8 and "analysis" in generated_title.lower() or "report" in generated_title.lower() or any(word in generated_title.lower() for word in ["strategy", "performance", "forecast", "review", "study"]):
                return generated_title
            else:
                return self._extract_title_from_query_patterns(query)
                
        except Exception as e:
            print(f"AI title generation failed: {e}")
            return self._extract_title_from_query_patterns(query)

    def _extract_title_from_query_patterns(self, query: str) -> str:
        """Extract title using pattern matching as fallback."""
        query_lower = query.lower()
        
        # Pattern-based title extraction
        patterns = [
            # Forecast patterns
            (r'forecast.*?(\w+(?:\s+\w+)*)', r'\1 Forecasting Analysis'),
            # Analysis patterns  
            (r'analyz[e|ing].*?(\w+(?:\s+\w+)*)', r'\1 Strategic Analysis'),
            # Report patterns
            (r'report.*?on.*?(\w+(?:\s+\w+)*)', r'\1 Performance Report'),
            # Predict patterns
            (r'predict.*?(\w+(?:\s+\w+)*)', r'\1 Predictive Analysis'),
            # Compare patterns
            (r'compar[e|ing].*?(\w+(?:\s+\w+)*)', r'\1 Comparative Analysis'),
            # Trend patterns
            (r'trend.*?(\w+(?:\s+\w+)*)', r'\1 Trend Analysis'),
        ]
        
        for pattern, replacement in patterns:
            match = re.search(pattern, query_lower)
            if match:
                subject = match.group(1).title()
                title = replacement.replace(r'\1', subject)
                return title
        
        # If no patterns match, try to extract key business terms
        business_terms = []
        key_words = ['sales', 'revenue', 'profit', 'market', 'customer', 'product', 
                    'financial', 'growth', 'performance', 'strategy', 'forecast',
                    'demand', 'supply', 'pricing', 'competition', 'efficiency']
        
        words = query_lower.split()
        for word in words:
            if word in key_words:
                business_terms.append(word.title())
        
        if business_terms:
            if len(business_terms) == 1:
                return f"{business_terms[0]} Strategic Analysis"
            else:
                return f"{' & '.join(business_terms[:2])} Analysis"
        
        return "Business Intelligence Analysis"

 
    def _extract_target_variable(self, query: str) -> str:
        """Extract target variable from user query."""
        query_lower = query.lower()
       
        if 'sales' in query_lower:
            return 'sales'
        elif 'revenue' in query_lower:
            return 'revenue'
        elif 'profit' in query_lower:
            return 'profit'
        elif 'price' in query_lower:
            return 'price'
        elif 'volume' in query_lower:
            return 'volume'
        elif 'cost' in query_lower:
            return 'cost'
        else:
            if self.df is not None:
                numeric_cols = self.df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    return numeric_cols[0]
       
        return None
 
    def _extract_forecast_periods(self, query: str) -> int:
        """Extract forecast periods from user query."""
        patterns = [
            r'(\d+)\s*months?',
            r'(\d+)\s*years?',
            r'(\d+)\s*quarters?',
            r'(\d+)\s*periods?',
            r'next\s+(\d+)',
        ]
       
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return int(match.group(1))
       
        return 12
 
    def generate_forecast_report(self, data_context,
                            forecast_results: Dict[str, Any] = None,
                            client_name: str = "Executive Leadership Team",
                            market_topic: str = "Business Intelligence Analysis",
                            forecast_periods: int = 12,
                            target_variable: str = None,
                            image_urls: Dict[str, str] = None,
                            dataframes: Dict[str, pd.DataFrame] = None) -> str:
        """Generate comprehensive strategy report with proper image integration and DataFrame tables."""
        if self.df is None:
            return "Error: No data loaded. Please load a CSV file first."

        try:
            # Use the passed data_context instead of regenerating
            if not data_context:
                data_context = self._prepare_report_data_context(forecast_results, target_variable)
            
            # Prepare DataFrames section
            dataframes_section = ""
            if dataframes:
                dataframes_section = self._prepare_dataframes_section(dataframes)
            
            report_prompt = self._create_report_prompt(
                data_context, client_name, market_topic, forecast_periods, target_variable, image_urls, dataframes_section
            )
            
            # Prepare messages in the correct format for Vision API
            messages = [
                {
                    "role": "system", 
                    "content": [
                        {
                            "type": "text",
                            "text": self._create_report_system_prompt(data_context, market_topic, image_urls, dataframes)
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": report_prompt
                        }
                    ]
                }
            ]
            
            # Add images to the user message if available
            if image_urls and len(image_urls) > 0:
                for key, image_url in image_urls.items():
                    messages[1]["content"].append({
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    })
                messages[1]["content"].append({
                        "type": "text",
                        "text": f"Embed the above images in report wherever needed as <img src={list(image_urls.values())}>"
                    })
            # Use vision-capable model
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use Vision model
                messages=messages,
                # max_tokens=4000,  # Adjust as needed
                # temperature=0.1
            )
        
            report_content = response.choices[0].message.content
        
            return report_content
        
        except Exception as e:
            return f"Error generating report: {str(e)}\n{traceback.format_exc()}"
   
    def _prepare_report_data_context(self, forecast_results: Dict[str, Any], target_variable: str = None) -> str:
        """Prepare data context for report generation."""
        data_summary = self._extract_data_summary()
       
        context = f"""
### DATA SECTION
 
**Dataset Overview:**
- Total Records: {data_summary['total_records']:,}
- Columns: {len(data_summary['columns'])}
- Numeric Variables: {data_summary['numeric_columns']}
- Categorical Variables: {data_summary['categorical_columns']}
"""
       
        if data_summary['date_range']:
            context += f"""
- Time Period: {data_summary['date_range']['start'].strftime('%Y-%m-%d')} to {data_summary['date_range']['end'].strftime('%Y-%m-%d')}
- Date Column: {data_summary['date_range']['column']}
"""
       
        context += f"""
**Sample Data (First 5 Rows):**
{self.df.head().to_string()}
 
**Statistical Summary:**
{self.df.describe().to_string()}
"""
       
        if self.generated_images:
            context += f"""
**Generated Visualizations:**
"""
            for img in self.generated_images:
                context += f"- {img}\n"
       
        if forecast_results and forecast_results.get('success'):
            context += f"""
**Analysis Results:**
- Query: {forecast_results.get('query', 'N/A')}
- Execution Status: {'Success' if forecast_results.get('success') else 'Failed'}
- Analysis Type: {'Forecasting' if forecast_results.get('is_forecasting') else 'General Analysis'}
"""
           
            if forecast_results.get('execution_result', {}).get('variables'):
                context += f"- Generated Variables: {list(forecast_results['execution_result']['variables'].keys())}\n"
       
        return context
    
    def _create_report_system_prompt(self, data_context: str, market_topic: str, image_urls: Dict[str, str] = None, dataframes: Dict[str, pd.DataFrame] = None) -> str:
        """Create system prompt for report generation with image context and DataFrame tables."""
        image_count = len(image_urls) if image_urls else 0
        dataframe_count = len(dataframes) if dataframes else 0
    
        return f"""
You are a senior strategy consultant at a top-tier global consulting firm (McKinsey, BCG, Bain level).
You specialize in creating comprehensive forecast reports that follow leading consulting and industry-analysis conventions.

CRITICAL REQUIREMENTS:
- Generate COMPLETE HTML documents with embedded CSS
- Use ONLY the provided image URLs (NO local file paths)
- All images are available as public URLs from blob storage
- Insert <img src="url"> tags directly in appropriate sections
- Reference figures properly in text (e.g., "Figure 1 shows...")
- Include generated DataFrames as styled HTML tables in the report
- Integrate data tables seamlessly with analysis narrative
-remove ```html``` tags 

AVAILABLE RESOURCES:
- Data Context: Comprehensive dataset analysis provided
- Market Topic: {market_topic}
- Available Images: {image_count} charts available as public URLs
- Available DataFrames: {dataframe_count} data tables to include
- All styling must be embedded CSS (no external dependencies)

DATAFRAME INTEGRATION REQUIREMENTS:
- Include all generated DataFrames as properly styled HTML tables
- Reference tables in the narrative (e.g., "Table 1 presents...")
- Provide context and interpretation for each data table
- Use responsive table design for mobile compatibility
- Highlight key insights from the tabular data

Your reports are:
- Data-driven and analytically rigorous using {dataframes}
- Structured following consulting best practices
- Written in professional consulting voice
- Concise yet comprehensive
- Actionable with clear strategic implications using the images from the url {image_urls}
- Include high-quality visualizations with proper URL integration
- Feature integrated data tables with insights
- Fully self-contained HTML documents ready for viewing

Generate reports that would meet the standards of top-tier strategy consulting firms with complete image and data table integration using only the provided URLs and DataFrame content.
"""

    def _create_report_prompt(self, data_context: str, client_name: str, market_topic: str,
                     forecast_periods: int, target_variable: str = None, image_urls: Dict[str, str] = None, 
                     dataframes_section: str = None) -> str:
        """Create comprehensive report prompt with dynamic title."""
        current_year = pd.Timestamp.now().year
        end_year = current_year + (forecast_periods // 12) + 1
        
        # Generate dynamic subtitle based on time horizon
        if forecast_periods <= 6:
            time_horizon = "Short-term Outlook"
        elif forecast_periods <= 12:
            time_horizon = "Annual Strategic Outlook" 
        elif forecast_periods <= 24:
            time_horizon = "Medium-term Strategic Outlook"
        else:
            time_horizon = "Long-term Strategic Outlook"
        
        # Create the full report title
        full_report_title = f"{market_topic}: {time_horizon} {current_year}-{end_year}"
        
        # Count available images and dataframes for reference in prompt
        num_images = len(image_urls) if image_urls else 0
        has_dataframes = bool(dataframes_section and dataframes_section.strip())
        
        prompt = f"""
    You are a senior strategy consultant at a top-tier global firm. Draft a comprehensive **Strategic Analysis Report** in HTML format with embedded CSS styling. Use only the information contained in the ### DATA section and clearly state any additional assumptions.

    ### DATA SECTION
    {data_context}

    ### AVAILABLE RESOURCES
    **Available Visualizations:** {num_images} chart(s) provided as public URLs
    **Available Data Tables:** {"Generated DataFrames ready for inclusion" if has_dataframes else "No data tables available"}

    ### DATAFRAMES SECTION TO INCLUDE
    {dataframes_section if dataframes_section else "<!-- No DataFrames section available -->"}

    ### REPORT SPECIFICATIONS

    Create a complete HTML document with the following structure:

    1. **HTML Document Structure**
    - DOCTYPE html5 with proper meta tags
    - Embedded CSS for professional styling
    - Responsive design for various screen sizes

    2. **Report Sections** (in order):
    - Cover Page with title: "{full_report_title}"
    - Executive Summary (≤2 pages equivalent)
    - Table of Contents with clickable navigation
    - Background & Objectives
    - Data Sources & Methodology
    - Market & Trend Analysis (reference charts if available)
    - Generated Data Results (include the DataFrames section provided above)
    - Analysis Results (reference main insights from charts and tables)
    - Strategic Implications
    - Recommendations & Implementation Roadmap
    - Risks & Mitigations
    - Appendices

    3. **CSS Styling Requirements**
    - Modern light theme with white, light grey, and subtle gradient color scheme
    - Card-based design for key metrics and KPIs
    - Typography: Clean sans-serif fonts (Inter, Roboto, or fallback to Arial)
    - Subtle gradient backgrounds and soft shadows for depth
    - Page layout: Max-width 1200px, centered with light background
    - Print-friendly styles (@media print) with high contrast
    - Chart integration areas with clean light borders
    - Responsive card layouts for metrics and data displays
    - Enhanced table styling for DataFrames with:
      * Alternating row colors
      * Hover effects on rows
      * Sticky headers for long tables
      * Responsive horizontal scrolling
      * Clear borders and proper spacing
    - Hover effects and subtle animations for interactivity

    4. **Image Integration Instructions**
    - {num_images} chart(s) are provided as public URLs, embed them in report as <img src="url" /> method wherever needed.
    - Analyse the image the well in respect to the user query
    - Create sections for charts with proper figure numbering
    - Reference the figures in your text (e.g., "as shown in Figure 1")
    - Include figure captions describing what each chart shows
    - Use the actual public URLs provided for the images

    5. **DataFrame Table Integration Instructions**
    - Include the complete DataFrames section provided above in the "Generated Data Results" section
    - Reference tables in the narrative text (e.g., "Table 1 demonstrates...")
    - Provide interpretation and context for each data table
    - Highlight key findings from the tabular data
    - Explain how the generated data enhances the original dataset
    
    ### ENHANCED CSS FOR TABLES
    Include these additional CSS styles for the data tables:

    ```css
    .table-container {{
        margin: 30px 0;
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        overflow: hidden;
        border: 1px solid #e9ecef;
    }}
    
    .table-header {{
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 20px;
        border-bottom: 2px solid #dee2e6;
    }}
    
    .table-title {{
        margin: 0 0 8px 0;
        color: #2d3748;
        font-size: 1.4em;
        font-weight: 600;
    }}
    
    .table-meta {{
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
    }}
    
    .table-info, .table-note {{
        font-size: 0.9em;
        color: #6c757d;
        padding: 4px 8px;
        background: rgba(255, 255, 255, 0.7);
        border-radius: 4px;
    }}
    
    .data-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9em;
        margin: 0;
    }}
    
    .data-table th {{
        background: linear-gradient(135deg, #495057 0%, #6c757d 100%);
        color: white;
        padding: 12px 8px;
        text-align: left;
        font-weight: 600;
        font-size: 0.85em;
        letter-spacing: 0.5px;
        position: sticky;
        top: 0;
        z-index: 10;
    }}
    
    .data-table td {{
        padding: 10px 8px;
        border-bottom: 1px solid #e9ecef;
        vertical-align: top;
    }}
    
    .data-table tbody tr:nth-child(even) {{
        background-color: #f8f9fa;
    }}
    
    .data-table tbody tr:hover {{
        background-color: #e3f2fd;
        transition: background-color 0.2s ease;
    }}
    
    .data-table tbody tr:nth-child(even):hover {{
        background-color: #e3f2fd;
    }}
    
    @media (max-width: 768px) {{
        .table-container {{
            margin: 20px -10px;
            border-radius: 0;
        }}
        
        .data-table {{
            font-size: 0.8em;
        }}
        
        .data-table th, .data-table td {{
            padding: 8px 4px;
        }}
    }}
    ```

    ### HTML STRUCTURE TEMPLATE
    Return the HTML as just HTML like below no added extra text below or above the structure. The report should be generated in such a way it is minimum 7-8 pages and includes the DataFrames section.

    
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{market_topic} Strategic Outlook {current_year}-{end_year}</title>
        <style>
            /* Modern light theme CSS goes here */
            body {{
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                color: #2d3748;
                font-family: 'Inter', 'Roboto', Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                padding: 40px;
            }}
            
            .chart-container {{
                background: #ffffff;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
                border: 1px solid #e9ecef;
            }}
            
            .chart-image {{
                width: 100%;
                height: auto;
                max-width: 800px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }}
            
            /* Include the enhanced table CSS from above */
            
            /* Add more CSS as needed */
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Report content with actual chart URLs and DataFrame tables -->
            <!-- MUST include the DataFrames section in "Generated Data Results" section -->
        </div>
    </body>
    </html>
    

    ### ANALYSIS PARAMETERS
    - Primary Focus: {market_topic}
    - Target Variable: {target_variable or 'Key business metrics'}
    - Analysis Horizon: {forecast_periods} periods
    - Available Charts: {num_images}
    - Available Data Tables: {"Yes" if has_dataframes else "No"}

    ### CRITICAL INTEGRATION REQUIREMENTS
    1. **MUST include the entire DataFrames section** provided above in the "Generated Data Results" section
    2. **Reference the data tables** in your analysis narrative
    3. **Interpret the DataFrame results** and explain their business significance
    4. **Connect table insights** with chart visualizations where applicable
    5. **Provide actionable recommendations** based on the tabular data

    ### OUTPUT FORMAT
    Return ONLY the complete HTML document with embedded CSS, actual image URLs, and integrated DataFrame tables. The file should be ready to save as .html and open in any browser.

    Minimum content length: 20000 words equivalent for comprehensive coverage while maintaining executive readability and full DataFrame integration.
    """
        
        return prompt
  
    def _extract_data_summary(self) -> Dict[str, Any]:
        """Extract key summary information from the loaded dataset."""
        summary = {
            "total_records": len(self.df),
            "date_range": None,
            "columns": list(self.df.columns),
            "numeric_columns": list(self.df.select_dtypes(include=[np.number]).columns),
            "categorical_columns": list(self.df.select_dtypes(include=['object']).columns),
            "missing_data": dict(self.df.isnull().sum()),
            "data_types": dict(self.df.dtypes.astype(str))
        }
       
        date_columns = [col for col in self.df.columns
                       if 'date' in col.lower() or 'time' in col.lower() or 'year' in col.lower()]
       
        if date_columns:
            try:
                date_col = date_columns[0]
                date_series = pd.to_datetime(self.df[date_col], errors='coerce')
                valid_dates = date_series.dropna()
                if len(valid_dates) > 0:
                    summary["date_range"] = {
                        "start": valid_dates.min(),
                        "end": valid_dates.max(),
                        "column": date_col
                    }
            except:
                pass
       
        return summary
 
    def _execute_code(self, code: str) -> Dict[str, Any]:
        """Execute generated Python code with enhanced libraries and automatic image capture."""
        try:
            from scipy import stats
           
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
                're': re,
                'stats': stats,
                'datetime': datetime,
                'timedelta': timedelta,
                'Path': Path,
                'images_dir': str(self.images_dir)
            }
           
            # Add sklearn libraries
            try:
                from sklearn.linear_model import LinearRegression
                from sklearn.model_selection import train_test_split
                from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
                from sklearn.preprocessing import StandardScaler, MinMaxScaler, PolynomialFeatures
               
                exec_globals.update({
                    'LinearRegression': LinearRegression,
                    'train_test_split': train_test_split,
                    'mean_squared_error': mean_squared_error,
                    'r2_score': r2_score,
                    'mean_absolute_error': mean_absolute_error,
                    'StandardScaler': StandardScaler,
                    'MinMaxScaler': MinMaxScaler,
                    'PolynomialFeatures': PolynomialFeatures
                })
            except ImportError as e:
                print(f"⚠️ Some sklearn libraries not available: {e}")
           
            # Add statsmodels for time series
            try:
                import statsmodels.api as sm
                from statsmodels.tsa.arima.model import ARIMA
                from statsmodels.tsa.seasonal import seasonal_decompose
                from statsmodels.tsa.holtwinters import ExponentialSmoothing
               
                exec_globals.update({
                    'sm': sm,
                    'ARIMA': ARIMA,
                    'seasonal_decompose': seasonal_decompose,
                    'ExponentialSmoothing': ExponentialSmoothing
                })
            except ImportError:
                print("⚠️ Statsmodels not available. Install with: pip install statsmodels")
           
            # Add XGBoost
            try:
                import xgboost as xgb
                from xgboost import XGBRegressor
                exec_globals.update({'xgb': xgb, 'XGBRegressor': XGBRegressor})
            except ImportError:
                print("⚠️ XGBoost not available. Install with: pip install xgboost")
           
            plt.style.use('default')
            plt.ioff()
           
            exec_locals = {}
            exec(code, exec_globals, exec_locals)
           
            captured_images = self._capture_matplotlib_plots()
            plt.close('all')
           
            result_vars = {k: v for k, v in exec_locals.items() if not k.startswith('_')}
           
            return {
                "success": True,
                "output": "Code executed successfully!",
                "variables": result_vars,
                "captured_images": captured_images,
                "message": f"✅ Execution completed successfully! Captured {len(captured_images)} images."
            }
           
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "message": f"❌ Execution failed: {str(e)}"
            }
 
    def update_original_file(self, result_df: pd.DataFrame, update_type: str = "merge") -> bool:
        """Update the original file with new data."""
        if not self.original_file_path:
            print("❌ No original file path available")
            return False
       
        try:
            if update_type == "merge":
                # Merge new columns with original data
                updated_df = self.original_df.copy()
                for col in result_df.columns:
                    if col not in updated_df.columns:
                        updated_df[col] = result_df[col]
            elif update_type == "append":
                # Append new rows
                updated_df = pd.concat([self.original_df, result_df], ignore_index=True)
            else:
                # Replace entirely
                updated_df = result_df
           
            # Save updated file
            backup_path = f"{self.original_file_path}.backup_{self.current_session_id}"
            shutil.copy2(self.original_file_path, backup_path)
           
            if self.original_file_path.endswith('.csv'):
                updated_df.to_csv(self.original_file_path, index=False)
            else:
                updated_df.to_excel(self.original_file_path, index=False)
           
            print(f"✅ Original file updated successfully!")
            print(f"💾 Backup saved: {backup_path}")
            print(f"📊 New shape: {updated_df.shape}")
           
            return True
           
        except Exception as e:
            print(f"❌ Failed to update original file: {str(e)}")
            return False
 
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary including blob storage info."""
        return {
            "session_id": self.current_session_id,
            "container_name": self.container_name,
            "analysis_folder": self.analysis_folder_name,
            "blob_structure": {
                "images": self.images_folder_name,
                "reports": self.reports_folder_name,
                "data_updates": self.data_folder_name
            },
            "generated_images_count": len(self.generated_images),
            "blob_image_urls": self.blob_image_urls,
            "local_temp_dir": str(self.output_dir)
        }
 
    def cleanup_session(self):
        """Clean up local temporary files while keeping blob storage intact."""
        try:
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
                print(f"🧹 Cleaned up local temp directory: {self.output_dir}")
            
            print(f"☁️ Blob storage preserved at: {self.container_name}/{self.analysis_folder_name}")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
 
    def interactive_session(self):
        """Start an interactive session focused on DataFrame results with blob storage integration."""
        print("🚀 Welcome to Enhanced Quadratic-Inspired CSV AI Analyzer!")
        print("📊 Focus: DataFrame Results & Data Updates")
        print("☁️ Storage: Azure Blob Storage Integration")
        print("📋 Reports: Now include DataFrames as HTML tables")
        print("=" * 70)
        print(f"📁 Container: {self.container_name}")
        print(f"🗂️ Analysis Folder: {self.analysis_folder_name}")
        print(f"📂 Local Temp: {self.output_dir}")
       
        while True:
            csv_path = input("\n📁 Enter CSV file path: ").strip()
            if csv_path.lower() == 'quit':
                return
            if self.load_csv(csv_path):
                break
            else:
                print("Please try again or type 'quit' to exit.")
       
        print("\n🎯 Ask questions to get actionable DataFrame results!")
        print("📊 Default behavior: Returns data that can update your original file")
        print("📋 For comprehensive reports: Include 'report' in your query")
        print("📝 Reports now include generated DataFrames as styled HTML tables")
        print("☁️ All images automatically uploaded to blob storage")
        print("\nExamples:")
        print("- Add trend indicators to the data")
        print("- Calculate performance scores for each category")
        print("- Forecast next 12 months of sales")
        print("- Create risk categories based on volatility")
        print("- Generate report on sales performance (for full report with tables)")
        print("- Add seasonal indicators to the dataset")
        print("\nType 'quit' to exit\n")
       
        while True:
            try:
                query = input("🔍 Your query: ").strip()
               
                if query.lower() == 'quit':
                    session_summary = self.get_session_summary()
                    print("👋 Thanks for using Enhanced CSV Analyzer!")
                    print(f"📁 Session: {session_summary['session_id']}")
                    print(f"☁️ Blob Storage: {session_summary['container_name']}/{session_summary['analysis_folder']}")
                    print(f"📸 Images Generated: {session_summary['generated_images_count']}")
                    
                    cleanup_choice = input("\n🧹 Clean up local temp files? (y/n): ").strip().lower()
                    if cleanup_choice == 'y':
                        self.cleanup_session()
                    break
                   
                if not query:
                    continue
                   
                result = self.analyze_query(query)
               
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                elif result.get("type") == "comprehensive_report":
                    # Handle report generation
                    print("📋 Comprehensive report generated!")
                    report = result.get('comprehensive_report', '')
                    if report:
                        print(f"📊 Report length: {len(report):,} characters")
                        print(f"📝 Includes {len(result.get('dataframes', {}))} data tables")
                        print(f"☁️ Saved to blob storage")
                        if result.get('report_blob_url'):
                            print(f"🔗 Report URL: {result['report_blob_url']}")
                elif result.get("type") == "dataframe_analysis":
                    # Handle DataFrame results (default behavior)
                    print(f"📊 {result['execution_result']['message']}")
                   
                    if result['execution_result']['success']:
                        if result.get('dataframes'):
                            print(f"✅ Generated {len(result['dataframes'])} result DataFrames")
                           
                            # Show what data can be updated
                            if result.get('data_update_available'):
                                print("\n💡 DATA UPDATE OPTIONS:")
                                print("   • Review the data preview above")
                                print(f"   • Data saved to: {self.container_name}/{self.data_folder_name}")
                                print("   • Use generated DataFrames to enhance your original data")
                                print("   • For reports with tables: Add 'report' to your next query")
                       
                        if result.get('generated_images'):
                            print(f"📸 Generated {len(result['generated_images'])} visualizations")
                            print(f"☁️ Images uploaded to: {self.container_name}/{self.images_folder_name}")
               
                print("=" * 70)
               
            except KeyboardInterrupt:
                session_summary = self.get_session_summary()
                print(f"\n👋 Thanks for using Enhanced CSV Analyzer!")
                print(f"📁 Session: {session_summary['session_id']}")
                print(f"☁️ Blob Storage: {session_summary['container_name']}/{session_summary['analysis_folder']}")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
 
def main():
    """Main function to run the enhanced analyzer."""
    required_vars = ["AZUREAPI", "AZUREVERSION", "AZUREENDPOINT", "AZURE_STORAGE_ACCOUNT_URL", "AZURE_STORAGE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set the following:")
        print("- AZUREAPI: Your Azure OpenAI API key")
        print("- AZUREVERSION: API version (e.g., '2024-02-01')")
        print("- AZUREENDPOINT: Your Azure OpenAI endpoint")
        print("- AZURE_STORAGE_ACCOUNT_URL: Your Azure Storage account URL")
        print("- AZURE_STORAGE_KEY: Your Azure Storage account key")
        print("- AZURE_STORAGE_CONTAINER_NAME: Your blob container name (optional, defaults to 'pmc')")
        return
   
    analyzer = QuadraticCSVAnalyzer()
    analyzer.interactive_session()
 
if __name__ == "__main__":
    main()