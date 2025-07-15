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
warnings.filterwarnings('ignore')
 
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
        self.MODEL = "gpt-o3-mini"
        self.df = None
        self.csv_info = ""
        self.original_file_path = None
       
        # Session management
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"analysis_output_{self.current_session_id}")
        self.images_dir = self.output_dir / "images"
        self.reports_dir = self.output_dir / "reports"
        self.data_dir = self.output_dir / "data_updates"
        self.generated_images = []
       
        # Result tracking
        self.analysis_results = {}
        self.data_updates = {}
       
        # Create output directories
        self._setup_directories()
       
    def _setup_directories(self):
        """Create necessary directories for output files."""
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        print(f"📁 Output directory created: {self.output_dir}")
       
    def load_csv(self, file_path: str) -> bool:
        """Load CSV file and analyze its structure."""
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
           
            # Store original data for comparison
            self.original_df = self.df.copy()
           
            # Automatically generate basic trend metrics (stored, not reported)
            self._generate_basic_trends()
            return True
           
        except Exception as e:
            print(f"❌ Error loading CSV: {str(e)}")
            return False
   
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
        """Create system prompt focused on DataFrame results and data updates."""
        return f"""
You are an advanced AI assistant specialized in data analysis that returns actionable DataFrame results.
Your primary goal is to generate Python code that creates DataFrames with new data that can be written back to the original file.
 
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
 
CSV Data Context:
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
"""
   
    def _capture_matplotlib_plots(self) -> List[str]:
        """Capture any matplotlib plots that were created during code execution."""
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
               
                captured_images.append(str(image_path))
                self.generated_images.append(image_filename)
               
                print(f"📸 Saved plot: {image_filename}")
               
            except Exception as e:
                print(f"⚠️ Failed to save plot {i+1}: {str(e)}")
       
        return captured_images
 
    def save_data_updates(self, result_df: pd.DataFrame, update_name: str) -> str:
        """Save DataFrame results that can be used to update the original file."""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{update_name}_{timestamp}.csv"
            file_path = self.data_dir / filename
           
            result_df.to_csv(file_path, index=False)
           
            print(f"💾 Data update saved: {filename}")
            print(f"📊 Shape: {result_df.shape}")
            print(f"🔍 New columns: {list(result_df.columns)}")
           
            return str(file_path)
           
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
                print(f"   • Data saved to: {self.data_dir}")
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
           
            report = self.generate_forecast_report(
                forecast_results=analysis_result,
                client_name="Executive Leadership Team",
                market_topic=market_topic,
                forecast_periods=forecast_periods,
                target_variable=target_variable
            )
           
            analysis_result.update({
                "type": "comprehensive_report",
                "comprehensive_report": report,
                "report_generated": True,
                "market_topic": market_topic,
                "target_variable": target_variable,
                "forecast_periods": forecast_periods
            })
           
            print("✅ Comprehensive strategic report generated successfully!")
           
        except Exception as report_error:
            print(f"⚠️ Report generation failed: {str(report_error)}")
            analysis_result.update({
                "report_error": str(report_error),
                "report_generated": False,
                "type": "report_error"
            })
       
        return analysis_result
 
    def _extract_market_topic(self, query: str) -> str:
        """Extract market topic from user query."""
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
 
    def generate_forecast_report(self,
                                forecast_results: Dict[str, Any] = None,
                                client_name: str = "Executive Leadership Team",
                                market_topic: str = "Business Intelligence Analysis",
                                forecast_periods: int = 12,
                                target_variable: str = None) -> str:
        """Generate comprehensive strategy report with image integration."""
        if self.df is None:
            return "Error: No data loaded. Please load a CSV file first."
       
        try:
            data_context = self._prepare_report_data_context(forecast_results, target_variable)
            report_prompt = self._create_report_prompt(
                data_context, client_name, market_topic, forecast_periods, target_variable
            )
           
            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self._create_report_system_prompt()},
                    {"role": "user", "content": report_prompt}
                ],
            )
           
            report_content = response.choices[0].message.content
           
            report_filename = f"strategic_report_{market_topic.replace(' ', '_').lower()}_{self.current_session_id}.md"
            report_path = self.reports_dir / report_filename
           
            try:
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                print(f"📄 Report saved: {report_path}")
            except Exception as e:
                print(f"⚠️ Could not save report file: {e}")
           
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
 
    def _create_report_system_prompt(self) -> str:
        """Create system prompt for report generation."""
        return """
You are a senior strategy consultant at a top-tier global consulting firm (McKinsey, BCG, Bain level).
You specialize in creating comprehensive forecast reports that follow leading consulting and industry-analysis conventions.
 
Your reports are:
- Data-driven and analytically rigorous
- Structured following consulting best practices
- Written in professional consulting voice
- Concise yet comprehensive
- Actionable with clear strategic implications
- Include high-quality visualizations with proper references
 
Generate reports that would meet the standards of top-tier strategy consulting firms with proper image integration.
"""
 
    def _create_report_prompt(self, data_context: str, client_name: str, market_topic: str,
                             forecast_periods: int, target_variable: str = None) -> str:
        """Create comprehensive report prompt with image integration."""
        current_year = pd.Timestamp.now().year
        end_year = current_year + (forecast_periods // 12) + 1
       
        image_references = ""
        if self.generated_images:
            image_references = "\n**Available Visualizations:**\n"
            for i, img in enumerate(self.generated_images, 1):
                image_references += f"- Figure {i}: ![Chart {i}](images/{img})\n"
       
        prompt = f"""
You are a senior strategy consultant at a top-tier global firm. Draft a comprehensive **Strategic Analysis Report** that follows leading consulting and industry-analysis conventions.
 
{data_context}
 
{image_references}
 
### REPORT SPECIFICATIONS
 
Generate a professional strategic analysis report covering:
1. Executive Summary with key findings
2. Data Analysis and Methodology  
3. Market & Trend Analysis with visualizations
4. Category-wise Performance Analysis
5. Overall Trend Assessment
6. Strategic Implications and Recommendations
7. Implementation Roadmap
8. Risk Assessment
 
### ANALYSIS PARAMETERS
- Primary Focus: {market_topic}
- Target Variable: {target_variable or 'Key business metrics'}
- Analysis Horizon: {forecast_periods} periods
 
### OUTPUT FORMAT
Return ONLY the finished report in Markdown format with proper image integration.
Maximum length: 4000 words for comprehensive coverage while maintaining executive readability.
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
 
    def interactive_session(self):
        """Start an interactive session focused on DataFrame results."""
        print("🚀 Welcome to Enhanced Quadratic-Inspired CSV AI Analyzer!")
        print("📊 Focus: DataFrame Results & Data Updates")
        print("=" * 70)
        print(f"📁 Output Directory: {self.output_dir}")
       
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
                    print("👋 Thanks for using Enhanced CSV Analyzer!")
                    print(f"📁 All outputs saved in: {self.output_dir}")
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
                        print(f"📄 Saved to: {self.reports_dir}")
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
                                print("   • Data saved for potential file update")
                                print("   • Use generated DataFrames to enhance your original data")
                       
                        if result.get('generated_images'):
                            print(f"📸 Generated {len(result['generated_images'])} visualizations")
               
                print("=" * 70)
               
            except KeyboardInterrupt:
                print(f"\n👋 Thanks for using Enhanced CSV Analyzer!")
                print(f"📁 All outputs saved in: {self.output_dir}")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
 
def main():
    """Main function to run the enhanced analyzer."""
    required_vars = ["AZUREAPI", "AZUREVERSION", "AZUREENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set the following:")
        print("- AZUREAPI: Your Azure OpenAI API key")
        print("- AZUREVERSION: API version (e.g., '2024-02-01')")
        print("- AZUREENDPOINT: Your Azure OpenAI endpoint")
        return
   
    analyzer = QuadraticCSVAnalyzer()
    analyzer.interactive_session()
 
if __name__ == "__main__":
    main()
 