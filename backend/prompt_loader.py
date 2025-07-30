"""
Prompt Management System for CSV Analyzer
Handles loading and managing prompts from text files
"""

import os
from pathlib import Path
from typing import Dict, Any

class PromptLoader:
    """Centralized prompt loader for the CSV analyzer system."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(exist_ok=True)
        self._prompts_cache = {}
        
    def load_prompt(self, prompt_name: str, **kwargs) -> str:
        """Load a prompt from file and format with provided kwargs."""
        if prompt_name not in self._prompts_cache:
            prompt_file = self.prompts_dir / f"{prompt_name}.txt"
            if not prompt_file.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self._prompts_cache[prompt_name] = f.read()
        
        prompt_template = self._prompts_cache[prompt_name]
        
        # Format the prompt with provided kwargs
        try:
            return prompt_template.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"Missing required parameter for prompt '{prompt_name}': {e}")
    
    def create_default_prompts(self):
        """Create default prompt files if they don't exist."""
        default_prompts = {
            "system_base": self._get_system_base_prompt(),
            "dataframe_analysis_base": self._get_dataframe_analysis_base_prompt(),
            "forecasting_requirements": self._get_forecasting_requirements_prompt(),
            "analysis_requirements": self._get_analysis_requirements_prompt(),
            "error_context_prompt": self._get_error_context_prompt(),
            "forecasting_error_fixes": self._get_forecasting_error_fixes_prompt(),
            "analysis_error_fixes": self._get_analysis_error_fixes_prompt(),
            "mandatory_error_handling": self._get_mandatory_error_handling_prompt(),
            "report_system_prompt": self._get_report_system_prompt(),
            "report_generation_prompt": self._get_report_generation_prompt(),
            "xgboost_template": self._get_xgboost_template_prompt()
        }
        
        for prompt_name, content in default_prompts.items():
            prompt_file = self.prompts_dir / f"{prompt_name}.txt"
            if not prompt_file.exists():
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Created prompt file: {prompt_file}")
    
    def _get_system_base_prompt(self) -> str:
        return """You are a Python code generator that MUST create COMPLETE, EXECUTABLE data analysis solutions.

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
 
CSV Data Context:
{csv_info}
 
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
Focus on creating NEW DATA that enhances the original dataset."""

    def _get_dataframe_analysis_base_prompt(self) -> str:
        return """Generate Python code to: {user_query}
 
PRIMARY GOAL: Return actionable DataFrame results that can enhance the original dataset.
 
CRITICAL REQUIREMENTS:
- Use 'df' variable which contains the loaded DataFrame
- NEVER use pd.read_csv() or file paths
- Focus on creating NEW DATA that adds value to the original dataset
- Return results as DataFrames with meaningful column names
- Show before/after data previews
- Always give charts using matplotlib for visualization using Bar-Charts, Line Graphs, Pie Chart. 
- Use Line charts for forecastings and Trend analysis.
- Use PieChart for Revenue per Product or Category or SKU 
- Use Bar Chart for other types of viualisation
 
DATA OUTPUT FOCUS:
- Create calculated columns, derived metrics, or classifications
- Generate forecasted data with future dates if requested
- Add trend indicators, performance scores, or category rankings
- Provide data that can be merged back to the original file
- Provide the charts for the visualisations for tasks such as trend, revenue, forecast, predictions, analyzation, best products, performance.
 
RESULT STRUCTURE:
1. Examine original data structure
2. Perform calculations/analysis
3. Create enhanced DataFrame with new columns
4. Show preview of original vs enhanced data
5. Save results that can update the original file
6. Return the chart
 
REQUEST TYPE: {request_type}"""

    def _get_forecasting_requirements_prompt(self) -> str:
        return """FORECASTING-SPECIFIC REQUIREMENTS:
- Create a separate DataFrame with future predictions
- Target variable are to be choose betweeen revenue, sales, units sold, quantity and similar data. 
- Never drop the Date column. 
- Always first run the xgBoost algorithm{{given below in example}}for forecasting or prediction then go with the user suggested model if any
- Include future dates beyond the last date in dataset
- Provide confidence intervals or prediction ranges
- Return forecasted_data_df with columns: [Date, Predicted_Value, Confidence_Lower, Confidence_Upper]
- Show both historical trend analysis and future predictions

FORECASTING OUTPUT:
- Original data with trend indicators added
- Separate forecast DataFrame for future periods
- Combined visualization showing historical + predicted
- Viuslaisation must be in Line or Bar charts for forecating and predictions

- Use below code as template for xgboost algorithm: 

{xgboost_template}

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

 
2. AUTOREGRESSIVE (AR) MODELS:
```
Pseudo-code:
1. AR(p): y_t = c + φ₁*y_{{t-1}} + φ₂*y_{{t-2}} + ... + φ_p*y_{{t-p}} + ε_t
2. For forecasting:
   - Use last p values to predict next value
   - Recursively use predictions to forecast multiple periods ahead
3. Implementation: Use statsmodels.tsa.ar_model.AutoReg
```
 
3. ARIMA FORECASTING:
```
Pseudo-code:
1. ARIMA(p,d,q): Combines AR(p) + Integration(d) + MA(q)
2. Auto-detect parameters using auto_arima or AIC/BIC
3. For forecasting:
   - model.fit(historical_data)
   - forecast = model.forecast(steps=forecast_periods)
4. Implementation: Use statsmodels.tsa.arima.ARIMA
```
 
4. XGBOOST TIME SERIES FORECASTING:
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
 
5. LSTM NEURAL NETWORK FORECASTING:
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
        df[target_col] = df[target_col].astype(str).str.replace(',', '').str.replace('$', '').str.strip()
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
 
Remember: Forecasting means predicting the FUTURE, not explaining the past!"""

    def _get_analysis_requirements_prompt(self) -> str:
        return """ANALYSIS-SPECIFIC REQUIREMENTS:
- Add calculated fields to enhance business insights
- Create performance metrics, rankings, or categorizations  
- Generate trend indicators and growth rates
- Provide statistical measures as new columns
- Focus on actionable business intelligence

ANALYSIS OUTPUT:
- Enhanced DataFrame with new calculated columns
- Summary statistics as additional rows/columns
- Category-wise metrics and comparisons
- Data quality indicators and flags"""

    def _get_error_context_prompt(self) -> str:
        return """PREVIOUS ATTEMPT FAILED - PLEASE FIX THE ISSUES:

ORIGINAL REQUEST: {user_query}
REQUEST TYPE: {request_type}

FAILED CODE:
```python
{failed_code}
```

ERROR MESSAGE:
{error_message}

CRITICAL FIXES NEEDED:
1. Analyze the error message above and fix the root cause
2. Ensure all required libraries are properly imported
3. Handle missing columns gracefully with proper error checking
4. Use proper data type conversions and null handling
5. Validate data structure before processing

COMMON ERROR PATTERNS TO AVOID:
- KeyError: Check if columns exist before accessing them
- ValueError: Validate data types and handle conversion errors
- IndexError: Check DataFrame length before indexing
- AttributeError: Verify DataFrame methods and attributes exist
- TypeError: Ensure proper data type matching

FALLBACK STRATEGIES:
- Use try-except blocks for risky operations
- Provide alternative column names if primary ones don't exist
- Use .get() method for dictionary-like access
- Add data validation steps before processing
- Include fallback methods if primary analysis fails

MANDATORY ERROR HANDLING TEMPLATE:
```python
try:
    # Your main analysis code here
    pass
except KeyError as e:
    print(f"⚠️ Column not found: {{e}}. Available columns: {{df.columns.tolist()}}")
    # Provide alternative approach
except ValueError as e:
    print(f"⚠️ Data conversion error: {{e}}")
    # Handle data type issues
except Exception as e:
    print(f"⚠️ Unexpected error: {{e}}")
    # Provide minimal fallback result
```

ENHANCED REQUIREMENTS:"""

    def _get_forecasting_error_fixes_prompt(self) -> str:
        return """FORECASTING-SPECIFIC ERROR FIXES:
- Ensure date columns are properly identified and converted
- Handle missing or invalid date formats
- Keep in mind that never to drop Date, Datetime columns
- Validate that target columns contain numeric data
- Provide fallback if advanced models fail (use simple moving average)
- Generate future dates correctly beyond the dataset range

FORECASTING FALLBACK HIERARCHY:
1. Primary: Advanced models (ARIMA, SARIMA,EMA, FBProphet etc.)
2. Secondary: Linear regression with time trend
3. Tertiary: Moving averages (simple, exponential)
4. Fallback: Last known value with trend adjustment

FORECASTING ERROR HANDLING:
```python
# Always include this forecasting fallback
try:
    # Advanced forecasting code
    pass
except Exception as e:
    print(f"⚠️ Advanced forecasting failed: {{e}}")
    print("🔄 Falling back to simple moving average...")
    
    # Simple fallback forecasting
    window_size = min(12, len(df) // 4)
    last_values = df[target_col].tail(window_size)
    simple_forecast = last_values.mean()
    
    # Create simple forecast DataFrame
    forecast_df = pd.DataFrame({{
        'Date': future_dates,
        'Predicted_Value': [simple_forecast] * len(future_dates),
        'Confidence_Lower': [simple_forecast * 0.9] * len(future_dates),
        'Confidence_Upper': [simple_forecast * 1.1] * len(future_dates)
    }})
```"""

    def _get_analysis_error_fixes_prompt(self) -> str:
        return """ANALYSIS-SPECIFIC ERROR FIXES:
- Validate column existence before calculations
- Handle mixed data types in columns
- Provide alternative metrics if primary ones fail
- Use robust statistical methods that handle outliers
- Include data quality checks

ANALYSIS FALLBACK HIERARCHY:
1. Primary: Advanced calculated metrics
2. Secondary: Basic statistical measures, Use simpler algortihms as SARIMA and ARIMA
3. Tertiary: Simple aggregations
4. Fallback: Data structure summary

ANALYSIS ERROR HANDLING:
```python
# Always include this analysis fallback
try:
    # Advanced analysis code
    pass
except Exception as e:
    print(f"⚠️ Advanced analysis failed: {{e}}")
    print("🔄 Falling back to basic analysis...")
    
    # Simple fallback analysis
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) > 0:
        # Create basic summary
        summary_df = df[numeric_cols].describe()
        print("📊 Basic statistical summary:")
        print(summary_df)
    else:
        print("⚠️ No numeric columns found for analysis")
```"""

    def _get_mandatory_error_handling_prompt(self) -> str:
        return """MANDATORY DATA EXPLORATION (Always include this first):
```python
print("=== DEBUGGING DATA STRUCTURE ===")
print(f"DataFrame shape: {{df.shape}}")
print(f"Column names: {{df.columns.tolist()}}")
print(f"Data types: {{df.dtypes}}")
print(f"Missing values: {{df.isnull().sum()}}")
print(f"Sample data:")
print(df.head())

# Check for object columns that might be numeric
object_cols = df.select_dtypes(include=['object']).columns
for col in object_cols:
    print(f"Column '{{col}}' sample values: {{df[col].dropna().head().tolist()}}")
```

FINAL REQUIREMENTS:
- Always start with data exploration
- Use robust error handling throughout
- Provide meaningful fallback options
- Test column existence before use
- Return results even if primary analysis fails
- Include clear error messages and solutions
- If no code works then generate the code for SARIMA/ARIMA code"""

    def _get_report_system_prompt(self) -> str:
        return """You are a senior strategy consultant at a top-tier global consulting firm (McKinsey, BCG, Bain level).
You specialize in creating comprehensive forecast reports that follow leading consulting and industry-analysis conventions.

CRITICAL REQUIREMENTS:
- Generate COMPLETE HTML documents with embedded CSS
- Use ONLY the provided image URLs (NO local file paths)
- All images are available as public URLs from blob storage
- Insert <img src="url"> tags directly in appropriate sections
- Reference figures properly in text (e.g., "Figure 1 shows...")

AVAILABLE RESOURCES:
- Data Context: Comprehensive dataset analysis provided
- Market Topic: {market_topic}
- Available Images: {image_count} charts available as public URLs
- All styling must be embedded CSS (no external dependencies)

Your reports are:
- Data-driven and analytically rigorous
- Structured following consulting best practices
- Written in professional consulting voice
- Concise yet comprehensive
- Actionable with clear strategic implications
- Include high-quality visualizations with proper URL integration
- Fully self-contained HTML documents ready for viewing

Generate reports that would meet the standards of top-tier strategy consulting firms with complete image integration using only the provided URLs."""

    def _get_report_generation_prompt(self) -> str:
        return """You are a senior strategy consultant at a top-tier global firm. Draft a comprehensive **Strategic Analysis Report** in HTML format with embedded CSS styling. Use only the information contained in the ### DATA section and clearly state any additional assumptions.

### DATA SECTION
{data_context}

### AVAILABLE IMAGES
{available_images_info}

### REPORT SPECIFICATIONS

Create a complete HTML document with the following structure:

1. **HTML Document Structure**
- DOCTYPE html5 with proper meta tags
- Embedded CSS for professional styling
- Responsive design for various screen sizes

2. **Report Sections** (in order):
- Cover Page with title: "{market_topic} Strategic Outlook {current_year}-{end_year}"
- Executive Summary (≤2 pages equivalent)
- Table of Contents with clickable navigation
- Background & Objectives
- Data Sources & Methodology
- Market & Trend Analysis (reference charts if available)
- Analysis Results (reference main insights from charts)
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
- Hover effects and subtle animations for interactivity

4. **Image Integration Instructions**
- {num_images} chart(s) are provided as public URLs, embed them in report as <img src="url" /> method wherever needed.
- Create sections for charts with proper figure numbering
- Reference the figures in your text (e.g., "as shown in Figure 1")
- Include figure captions describing what each chart shows
- Use the actual public URLs provided for the images

### HTML STRUCTURE TEMPLATE

```html
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
        
        /* Add more CSS as needed */
    </style>
</head>
<body>
    <div class="container">
        <!-- Report content with actual chart URLs -->
    </div>
</body>
</html>
```

### ANALYSIS PARAMETERS
- Primary Focus: {market_topic}
- Target Variable: {target_variable}
- Analysis Horizon: {forecast_periods} periods
- Available Charts: {num_images}

### OUTPUT FORMAT
Return ONLY the complete HTML document with embedded CSS and actual image URLs. The file should be ready to save as .html and open in any browser.

Maximum content length: 5000 words equivalent for comprehensive coverage while maintaining executive readability."""

    def _get_xgboost_template_prompt(self) -> str:
        return """import pandas as pd
import numpy as np
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error, mean_absolute_error

print("=== STEP 1: DATA PREPARATION ===")
# Convert date and prepare data
df['Date'] = pd.to_datetime(df['Date'])

# Aggregate by date to create time series
daily_data = df.groupby('Date').agg({{
    'Revenue': 'sum',
    'Units Sold': 'sum',
    'Profit': 'sum'
}}).reset_index()

# Choose target variable (Revenue is primary choice)
target_col = 'Revenue'
print(f"Target variable: {{target_col}}")
print(f"Date range: {{daily_data['Date'].min()}} to {{daily_data['Date'].max()}}")
print(f"Data points: {{len(daily_data)}}")

print("=== STEP 2: FEATURE ENGINEERING ===")
def create_features(data, target_column, n_lags=7):
    features_df = data.copy()
    
    # Time-based features
    features_df['year'] = features_df['Date'].dt.year
    features_df['month'] = features_df['Date'].dt.month
    features_df['day'] = features_df['Date'].dt.day
    features_df['dayofweek'] = features_df['Date'].dt.dayofweek
    features_df['quarter'] = features_df['Date'].dt.quarter
    features_df['is_weekend'] = features_df['dayofweek'].isin([5, 6]).astype(int)
    
    # Lag features (previous values)
    for lag in range(1, n_lags + 1):
        features_df[f'{{target_column}}_lag_{{lag}}'] = features_df[target_column].shift(lag)
    
    # Rolling window features (moving averages)
    for window in [3, 7, 14, 30]:
        features_df[f'{{target_column}}_rolling_{{window}}'] = features_df[target_column].rolling(window).mean()
        features_df[f'{{target_column}}_rolling_std_{{window}}'] = features_df[target_column].rolling(window).std()
    
    # Growth rate features
    features_df[f'{{target_column}}_growth_1d'] = features_df[target_column].pct_change(1)
    features_df[f'{{target_column}}_growth_7d'] = features_df[target_column].pct_change(7)
    
    return features_df

# Create features
featured_data = create_features(daily_data, target_col, n_lags=14)
# Remove rows with NaN (due to lag features)
featured_data = featured_data.dropna().reset_index(drop=True)
print(f"Features created. Final shape: {{featured_data.shape}}")

print("=== STEP 3: MODEL TRAINING ===")
# Prepare feature columns
feature_columns = [col for col in featured_data.columns if col not in ['Date', target_col]]
X = featured_data[feature_columns]
y = featured_data[target_col]

# Split data (use last 20% for validation)
split_idx = int(len(featured_data) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

print(f"Training set: {{len(X_train)}} samples")
print(f"Test set: {{len(X_test)}} samples")

# Train XGBoost model with robust parameters
model = XGBRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# Evaluate model performance
train_pred = model.predict(X_train)
test_pred = model.predict(X_test)

train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
train_mae = mean_absolute_error(y_train, train_pred)
test_mae = mean_absolute_error(y_test, test_pred)

print(f"Model Performance:")
print(f"Train RMSE: {{train_rmse:.2f}}, MAE: {{train_mae:.2f}}")
print(f"Test RMSE: {{test_rmse:.2f}}, MAE: {{test_mae:.2f}}")

print("=== STEP 4: GENERATE 12-MONTH FORECAST ===")
# Generate future dates (365 days = 12 months)
last_date = featured_data['Date'].max()
future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=365, freq='D')
print(f"Forecasting from {{future_dates[0]}} to {{future_dates[-1]}}")

# Multi-step forecasting
forecast_predictions = []
forecast_lower = []
forecast_upper = []

# Get recent data for context
recent_data = featured_data.tail(30).copy()
all_predictions = list(featured_data[target_col].tail(14))

for i, future_date in enumerate(future_dates):
    # Create time-based features
    future_features = {{
        'year': future_date.year,
        'month': future_date.month,
        'day': future_date.day,
        'dayofweek': future_date.dayofweek,
        'quarter': future_date.quarter,
        'is_weekend': int(future_date.dayofweek in [5, 6])
    }}
    
    # Get recent values (combine historical + previous predictions)
    recent_values = all_predictions[-30:]  # Last 30 values
    
    # Create lag features
    for lag in range(1, 15):
        if lag <= len(recent_values):
            future_features[f'{{target_col}}_lag_{{lag}}'] = recent_values[-lag]
        else:
            future_features[f'{{target_col}}_lag_{{lag}}'] = recent_values[-1]
    
    # Create rolling features
    for window in [3, 7, 14, 30]:
        if len(recent_values) >= window:
            future_features[f'{{target_col}}_rolling_{{window}}'] = np.mean(recent_values[-window:])
            future_features[f'{{target_col}}_rolling_std_{{window}}'] = np.std(recent_values[-window:])
        else:
            future_features[f'{{target_col}}_rolling_{{window}}'] = np.mean(recent_values)
            future_features[f'{{target_col}}_rolling_std_{{window}}'] = np.std(recent_values)
    
    # Create growth features
    if len(recent_values) >= 2:
        future_features[f'{{target_col}}_growth_1d'] = (recent_values[-1] - recent_values[-2]) / recent_values[-2]
    else:
        future_features[f'{{target_col}}_growth_1d'] = 0
        
    if len(recent_values) >= 8:
        future_features[f'{{target_col}}_growth_7d'] = (recent_values[-1] - recent_values[-8]) / recent_values[-8]
    else:
        future_features[f'{{target_col}}_growth_7d'] = 0
    
    # Create feature vector (ensure same order as training)
    feature_vector = pd.DataFrame([future_features])
    feature_vector = feature_vector.reindex(columns=feature_columns, fill_value=0)
    
    # Make prediction
    prediction = model.predict(feature_vector)[0]
    
    # Add some uncertainty bounds (±15% based on test error)
    error_margin = test_rmse * 1.5
    lower_bound = max(0, prediction - error_margin)
    upper_bound = prediction + error_margin
    
    # Store predictions
    forecast_predictions.append(prediction)
    forecast_lower.append(lower_bound)
    forecast_upper.append(upper_bound)
    all_predictions.append(prediction)

print(f"Generated {{len(forecast_predictions)}} daily forecasts")

print("=== STEP 5: CREATE FORECASTED DATA ===")
# Create detailed forecasted_data DataFrame
forecasted_data = pd.DataFrame({{
'Date': future_dates,
'Predicted_Value': forecast_predictions,
'Confidence_Lower': forecast_lower,
'Confidence_Upper': forecast_upper,
'Model_Used': 'XGBoost',
'Target_Variable': target_col,
'Forecast_Day': range(1, len(future_dates) + 1)
}})

# Add monthly aggregation for easier interpretation
forecasted_data['Year_Month'] = forecasted_data['Date'].dt.to_period('M')
monthly_forecast = forecasted_data.groupby('Year_Month').agg({{
    'Predicted_Value': 'sum',
    'Confidence_Lower': 'sum',
    'Confidence_Upper': 'sum'
}}).reset_index()

print("FORECAST SUMMARY:")
print(f"Daily average forecast: {{forecasted_data['Predicted_Value'].mean():.2f}}")
print(f"Monthly forecast range: {{monthly_forecast['Predicted_Value'].min():.2f}} - {{monthly_forecast['Predicted_Value'].max():.2f}}")
print(f"Total 12-month forecast: {{forecasted_data['Predicted_Value'].sum():.2f}}")

print("=== STEP 6: MANDATORY VISUALIZATIONS ===")

# Create comprehensive visualization
fig, axes = plt.subplots(2, 2, figsize=(20, 12))

# 1. Historical vs Forecast (Daily)
ax1 = axes[0, 0]
# Plot last 90 days of historical data
recent_historical = daily_data.tail(90)
ax1.plot(recent_historical['Date'], recent_historical[target_col], 
         label='Historical (Last 90 days)', color='blue', linewidth=2)
ax1.plot(forecasted_data['Date'], forecasted_data['Predicted_Value'], 
         label='XGBoost Forecast (12 months)', color='red', linewidth=2, linestyle='--')
ax1.fill_between(forecasted_data['Date'], 
                forecasted_data['Confidence_Lower'], 
                forecasted_data['Confidence_Upper'], 
                alpha=0.2, color='red', label='Confidence Interval')
ax1.set_title('Daily Forecast: Historical vs Predicted', fontsize=14, fontweight='bold')
ax1.set_xlabel('Date')
ax1.set_ylabel(target_col)
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.tick_params(axis='x', rotation=45)

# 2. Monthly Aggregated Forecast
ax2 = axes[0, 1]
monthly_historical = daily_data.groupby(daily_data['Date'].dt.to_period('M'))[target_col].sum().tail(12)
ax2.bar(range(len(monthly_historical)), monthly_historical.values, 
        label='Historical (Last 12 months)', color='skyblue', alpha=0.7)
ax2.bar(range(len(monthly_historical), len(monthly_historical) + len(monthly_forecast)), 
        monthly_forecast['Predicted_Value'], 
        label='Forecasted (Next 12 months)', color='orange', alpha=0.7)
ax2.set_title('Monthly Forecast Comparison', fontsize=14, fontweight='bold')
ax2.set_xlabel('Month')
ax2.set_ylabel(f'Monthly {{target_col}}')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. Feature Importance
ax3 = axes[1, 0]
feature_importance = model.feature_importances_
top_features = sorted(zip(feature_columns, feature_importance), key=lambda x: x[1], reverse=True)[:10]
features, importances = zip(*top_features)
ax3.barh(range(len(features)), importances, color='green', alpha=0.7)
ax3.set_yticks(range(len(features)))
ax3.set_yticklabels(features)
ax3.set_title('Top 10 Feature Importance (XGBoost)', fontsize=14, fontweight='bold')
ax3.set_xlabel('Importance Score')
ax3.grid(True, alpha=0.3)

# 4. Forecast Distribution
ax4 = axes[1, 1]
ax4.hist(forecasted_data['Predicted_Value'], bins=30, color='purple', alpha=0.7, edgecolor='black')
ax4.axvline(forecasted_data['Predicted_Value'].mean(), color='red', linestyle='--', linewidth=2, 
        label=f'Mean: {{forecasted_data["Predicted_Value"].mean():.2f}}')
ax4.set_title('Distribution of Daily Forecasted Values', fontsize=14, fontweight='bold')
ax4.set_xlabel(f'Predicted {{target_col}}')
ax4.set_ylabel('Frequency')
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()"""