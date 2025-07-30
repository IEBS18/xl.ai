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
from prompt_loader import PromptLoader

warnings.filterwarnings('ignore')
 
class ConversationHistory:
    def __init__(self, session_id: str, output_dir: Path):
        self.session_id = session_id
        self.output_dir = output_dir
        self.history_file = output_dir / f"conversation_history_{session_id}.json"
        self.history = []
        self.load_history()
    
    def load_history(self):
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                print(f"📜 Loaded {len(self.history)} previous conversations")
        except Exception as e:
            print(f"⚠️ Could not load conversation history: {e}")
            self.history = []
    
    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Could not save conversation history: {e}")
    
    def add_conversation(self, user_query: str, response: Dict[str, Any]):
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
        
        if response.get("type") == "comprehensive_report":
            conversation["report_generated"] = True
            conversation["report_length"] = len(response.get("comprehensive_report", ""))
        
        self.history.append(conversation)
        self.save_history()
    
    def get_context_for_ai(self, last_n: int = 5) -> str:
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
        if len(self.history) < 2:
            return "N/A"
        
        start_time = datetime.fromisoformat(self.history[0]['timestamp'])
        end_time = datetime.fromisoformat(self.history[-1]['timestamp'])
        duration = end_time - start_time
        
        return str(duration).split('.')[0]


class QuadraticCSVAnalyzer:
    def __init__(self):
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZUREAPI"),
            api_version=os.getenv("AZUREVERSION"),
            azure_endpoint=os.getenv("AZUREENDPOINT")
        )
        self.MODEL = "gpt-4o-mini"
        self.df = None
        self.csv_info = ""
        self.original_file_path = None
       
        self.prompt_loader = PromptLoader()
        self.prompt_loader.create_default_prompts()
        
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.blob_service_client = BlobServiceClient(
            account_url=os.getenv("AZURE_STORAGE_ACCOUNT_URL"),
            credential=os.getenv("AZURE_STORAGE_KEY")
        )
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "pmc")
        
        self.analysis_folder_name = f"analysis_{self.current_session_id}"
        self.images_folder_name = f"{self.analysis_folder_name}/images"
        self.reports_folder_name = f"{self.analysis_folder_name}/reports"
        self.data_folder_name = f"{self.analysis_folder_name}/data_updates"
        
        self.output_dir = Path(f"temp_analysis_output_{self.current_session_id}")
        self.images_dir = self.output_dir / "images"
        self.reports_dir = self.output_dir / "reports"
        self.data_dir = self.output_dir / "data_updates"
        
        self.generated_images = []
        self.blob_image_urls = {}
        self.analysis_results = {}
        self.data_updates = {}
        
        self._setup_directories()
        self._initialize_blob_structure()
       
    def _setup_directories(self):
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        print(f"📁 Local temp directory created: {self.output_dir}")
    
    def _initialize_blob_structure(self):
        try:
            placeholder_content = "# Analysis session structure"
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
        try:
            if not os.path.isfile(image_path):
                return ""

            image_filename = Path(image_path).name
            blob_name = f"{self.images_folder_name}/{image_filename}"

            account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL").rstrip('/')
            account_name = account_url.split("//")[1].split(".")[0]
            account_key = os.getenv("AZURE_STORAGE_KEY")
            container_name = self.container_name

            if not account_key or not container_name:
                return ""

            self.blob_service_client = BlobServiceClient(account_url=account_url, credential=account_key)
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)

            with open(image_path, "rb") as data:
                blob_client.upload_blob(
                    data,
                    overwrite=True,
                    content_settings=ContentSettings(content_type='image/png')
                )

            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=2)
            )

            sas_url = f"{account_url}/{container_name}/{blob_name}?{sas_token}"
            self.blob_image_urls[image_filename] = sas_url
            return sas_url

        except Exception as e:
            return ""
    
    def _upload_file_to_blob(self, local_file_path: str, blob_subfolder: str) -> str:
        try:
            if not os.path.isfile(local_file_path):
                return ""

            file_name = Path(local_file_path).name

            if not self.analysis_folder_name or not self.container_name:
                return ""

            blob_name = f"{self.analysis_folder_name}/{blob_subfolder}/{file_name}".strip('/')

            if not self.blob_service_client:
                return ""

            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(
                    data,
                    overwrite=True,
                    content_settings=ContentSettings(content_type="application/octet-stream")
                )

            public_url = f"{self.blob_service_client.url.rstrip('/')}/{self.container_name}/{blob_name}"
            return public_url

        except Exception as e:
            return ""
       
    def load_csv(self, file_path: str) -> bool:
        try:
            self.original_file_path = file_path
            try:
                self.df = pd.read_csv(file_path, encoding='utf-8')
                self.csv_info = self._generate_csv_info()
            except:
                self.df = pd.read_excel(file_path, engine='openpyxl')
                self.csv_info = self._generate_csv_info()
            print(f"✅ CSV loaded successfully!")
            print(f"📊 Shape: {self.df.shape}")
            print(f"🔍 Columns: {list(self.df.columns)}")
            print(f"📈 Data types: {dict(self.df.dtypes)}")
           
            self.original_df = self.df.copy()
            self._generate_basic_trends()
            return True
           
        except Exception as e:
            print(f"❌ Error loading CSV: {str(e)}")
            return False
   
    def _generate_basic_trends(self):
        try:
            trend_data = self.analyze_trends()
            self.analysis_results['basic_trends'] = trend_data
            print("✅ Basic trend analysis completed and stored")
        except Exception as e:
            print(f"⚠️ Basic trend analysis failed: {str(e)}")
 
    def _is_report_request(self, query: str) -> bool:
        report_keywords = [
            'report', 'summary report', 'generate report', 'create report',
            'comprehensive report', 'strategic report', 'executive summary',
            'write report', 'full report', 'detailed report', 'analysis report'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in report_keywords)
 
    def _extract_data_request(self, query: str) -> Dict[str, str]:
        query_lower = query.lower()
        request_type = "analysis"
       
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
        if self.df is None:
            return {"error": "No data loaded"}
       
        trend_results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "dataset_info": {"shape": self.df.shape, "columns": list(self.df.columns)},
            "overall_trends": {},
            "category_trends": {},
            "time_series_trends": {},
            "correlation_analysis": {},
            "summary_insights": []
        }
       
        try:
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
           
            if len(numeric_cols) > 1:
                corr_matrix = self.df[numeric_cols].corr()
                strong_correlations = []
               
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:
                            strong_correlations.append({
                                "variables": [col1, col2],
                                "correlation": float(corr_val),
                                "strength": "strong" if abs(corr_val) > 0.8 else "moderate"
                            })
               
                trend_results["correlation_analysis"] = {
                    "strong_correlations": strong_correlations,
                    "correlation_matrix": corr_matrix.to_dict()
                }
           
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
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return series[(series < lower_bound) | (series > upper_bound)].tolist()
   
    def _detect_seasonality(self, time_series: pd.Series) -> Dict[str, Any]:
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
        if len(values) < 2:
            return 0.0
        from scipy import stats
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        return float(r_value ** 2)
 
    def _generate_csv_info(self) -> str:
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
        return self.prompt_loader.load_prompt("system_base", csv_info=self.csv_info)
   
    def _capture_matplotlib_plots(self) -> List[str]:
        captured_images = []
        fig_nums = plt.get_fignums()
       
        for i, fig_num in enumerate(fig_nums):
            try:
                fig = plt.figure(fig_num)
                timestamp = datetime.now().strftime("%H%M%S")
                image_filename = f"plot_{timestamp}_{i+1}.png"
                image_path = self.images_dir / image_filename
               
                fig.savefig(image_path, dpi=300, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
                
                public_url = self._upload_image_to_blob(str(image_path))
                if public_url:
                    captured_images.append(public_url)
                    self.generated_images.append(public_url)
                else:
                    captured_images.append(str(image_path))
                    self.generated_images.append(image_filename)
               
            except Exception as e:
                print(f"⚠️ Failed to save plot {i+1}: {str(e)}")
        return captured_images
 
    def save_data_updates(self, result_df: pd.DataFrame, update_name: str) -> str:
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{update_name}_{timestamp}.csv"
            local_file_path = self.data_dir / filename
           
            result_df.to_csv(local_file_path, index=False)
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
        print("\n" + "="*60)
        print("📊 DATA UPDATE PREVIEW")
        print("="*60)
       
        print(f"\n📈 ORIGINAL DATA (Shape: {original_df.shape}):")
        print(original_df.head(3).to_string())
       
        print(f"\n✨ UPDATED DATA (Shape: {updated_df.shape}):")
        print(updated_df.head(3).to_string())
       
        new_cols = set(updated_df.columns) - set(original_df.columns)
        if new_cols:
            print(f"\n🆕 NEW COLUMNS ADDED: {list(new_cols)}")
       
        common_cols = set(original_df.columns) & set(updated_df.columns)
        modified_cols = []
        for col in common_cols:
            if not original_df[col].equals(updated_df[col]):
                modified_cols.append(col)
       
        if modified_cols:
            print(f"📝 MODIFIED COLUMNS: {modified_cols}")
       
        print("="*60)
 
    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        if self.df is None:
            return {"error": "No CSV file loaded. Please load a CSV first."}
       
        try:
            print(f"🤖 Analyzing query: {user_query}")
            self.generated_images = []
            
            is_report_request = self._is_report_request(user_query)
            data_request = self._extract_data_request(user_query)
            
            forecasting_keywords = ['forecast', 'predict', 'future', 'next', 'ahead', 'months', 'years', 'projection']
            is_forecasting = any(keyword in user_query.lower() for keyword in forecasting_keywords)
       
            if is_report_request:
                return self._generate_comprehensive_report(user_query, is_forecasting)
            else:
                return self._generate_dataframe_analysis(user_query, data_request, is_forecasting)
               
        except Exception as e:
            return {
                "error": f"Error analyzing query: {str(e)}",
                "traceback": traceback.format_exc(),
                "type": "error"
            }
 
    def _generate_dataframe_analysis(self, user_query: str, data_request: Dict, is_forecasting: bool) -> Dict[str, Any]:
        base_requirements = self.prompt_loader.load_prompt(
            "dataframe_analysis_base", 
            user_query=user_query,
            request_type=data_request['type']
        )
 
        if is_forecasting:
            xgboost_template = self.prompt_loader.load_prompt("xgboost_template")
            enhanced_prompt = base_requirements + "\n\n" + self.prompt_loader.load_prompt(
                "forecasting_requirements",
                xgboost_template=xgboost_template
            )
        else:
            enhanced_prompt = base_requirements + "\n\n" + self.prompt_loader.load_prompt("analysis_requirements")
       
        response = self.openai_client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user",   "content": enhanced_prompt}
            ],
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
       
        dataframes_found = {}
        if result.get("success") and result.get("variables"):
            for var_name, var_value in result["variables"].items():
                if isinstance(var_value, pd.DataFrame):
                    dataframes_found[var_name] = var_value
                    print(f"📊 Found DataFrame: {var_name} (Shape: {var_value.shape})")
       
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
       
        if result.get("success") and dataframes_found:
            print(f"\n✅ Analysis completed successfully!")
            print(f"📊 Generated {len(dataframes_found)} result DataFrames")
           
            main_df_name = list(dataframes_found.keys())[0]
            main_df = dataframes_found[main_df_name]
           
            if len(main_df) > 0:
                self.show_data_preview(self.original_df, main_df)
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
        print("\n📋 Generating comprehensive strategic report...")
       
        try:
            data_request = self._extract_data_request(user_query)
            analysis_result = self._generate_dataframe_analysis(user_query, data_request, is_forecasting)
           
            if not analysis_result.get("success"):
                return {"error": "Cannot generate report - analysis failed", "type": "report_error"}
           
            market_topic = self._extract_market_topic(user_query)
            target_variable = self._extract_target_variable(user_query)
            forecast_periods = self._extract_forecast_periods(user_query) if is_forecasting else 6
           
            data_context = self._prepare_report_data_context(analysis_result, target_variable)
            image_urls = analysis_result.get("blob_image_urls", {})
           
            report = self.generate_forecast_report(
                data_context=data_context,
                forecast_results=analysis_result,
                client_name="Executive Leadership Team",
                market_topic=market_topic,
                forecast_periods=forecast_periods,
                target_variable=target_variable,
                image_urls=image_urls
            )
           
            if report:
                report_filename = f"strategic_report_{market_topic.replace(' ', '_').lower()}_{self.current_session_id}.html"
                local_report_path = self.reports_dir / report_filename
                
                with open(local_report_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                
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
        query_lower = query.lower()
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
 
    def _extract_target_variable(self, query: str) -> str:
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
        patterns = [
            r'(\d+)\s*months?', r'(\d+)\s*years?', r'(\d+)\s*quarters?',
            r'(\d+)\s*periods?', r'next\s+(\d+)',
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
                            image_urls: Dict[str, str] = None) -> str:
        if self.df is None:
            return "Error: No data loaded. Please load a CSV file first."

        try:
            if not data_context:
                data_context = self._prepare_report_data_context(forecast_results, target_variable)
            
            current_year = pd.Timestamp.now().year
            end_year = current_year + (forecast_periods // 12) + 1
            num_images = len(image_urls) if image_urls else 0
            
            available_images_info = f"**Available Visualizations:** {num_images} chart(s) provided as public URLs" if num_images > 0 else "**No visualizations available for this report**"
            
            report_prompt = self.prompt_loader.load_prompt(
                "report_generation_prompt",
                data_context=data_context,
                available_images_info=available_images_info,
                market_topic=market_topic,
                current_year=current_year,
                end_year=end_year,
                num_images=num_images,
                target_variable=target_variable or 'Key business metrics',
                forecast_periods=forecast_periods
            )
            
            messages = [
                {
                    "role": "system", 
                    "content": [
                        {
                            "type": "text",
                            "text": self.prompt_loader.load_prompt(
                                "report_system_prompt",
                                market_topic=market_topic,
                                image_count=num_images
                            )
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": report_prompt}]
                }
            ]
            
            if image_urls and len(image_urls) > 0:
                for key, image_url in image_urls.items():
                    messages[1]["content"].append({
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    })
                messages[1]["content"].append({
                        "type": "text",
                        "text": f"Embed the above images in report wherever needed as <img src={list(image_urls.values())}>"
                    })
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
            )
        
            report_content = response.choices[0].message.content
            return report_content
        
        except Exception as e:
            return f"Error generating report: {str(e)}\n{traceback.format_exc()}"
   
    def _prepare_report_data_context(self, forecast_results: Dict[str, Any], target_variable: str = None) -> str:
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
  
    def _extract_data_summary(self) -> Dict[str, Any]:
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
        if not self.original_file_path:
            print("❌ No original file path available")
            return False
       
        try:
            if update_type == "merge":
                updated_df = self.original_df.copy()
                for col in result_df.columns:
                    if col not in updated_df.columns:
                        updated_df[col] = result_df[col]
            elif update_type == "append":
                updated_df = pd.concat([self.original_df, result_df], ignore_index=True)
            else:
                updated_df = result_df
           
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
        try:
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
                print(f"🧹 Cleaned up local temp directory: {self.output_dir}")
            print(f"☁️ Blob storage preserved at: {self.container_name}/{self.analysis_folder_name}")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
 
    def interactive_session(self):
        print("🚀 Welcome to Enhanced Quadratic-Inspired CSV AI Analyzer!")
        print("📊 Focus: DataFrame Results & Data Updates")
        print("☁️ Storage: Azure Blob Storage Integration")
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
        print("☁️ All images automatically uploaded to blob storage")
        print("\nExamples:")
        print("- Add trend indicators to the data")
        print("- Calculate performance scores for each category")
        print("- Forecast next 12 months of sales")
        print("- Create risk categories based on volatility")
        print("- Generate report on sales performance (for full report)")
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
                    print("📋 Comprehensive report generated!")
                    report = result.get('comprehensive_report', '')
                    if report:
                        print(f"📊 Report length: {len(report):,} characters")
                        print(f"☁️ Saved to blob storage")
                        if result.get('report_blob_url'):
                            print(f"🔗 Report URL: {result['report_blob_url']}")
                elif result.get("type") == "dataframe_analysis":
                    print(f"📊 {result['execution_result']['message']}")
                   
                    if result['execution_result']['success']:
                        if result.get('dataframes'):
                            print(f"✅ Generated {len(result['dataframes'])} result DataFrames")
                           
                            if result.get('data_update_available'):
                                print("\n💡 DATA UPDATE OPTIONS:")
                                print("   • Review the data preview above")
                                print(f"   • Data saved to: {self.container_name}/{self.data_folder_name}")
                                print("   • Use generated DataFrames to enhance your original data")
                       
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