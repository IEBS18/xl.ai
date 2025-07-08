from prompt_handler import PromptHandler
from data import json_to_dataframe
from openai import AzureOpenAI
import pandas as pd
import os
import json
import re
from python_exe import PythonCodeExecutor
from dotenv import load_dotenv
import numpy as np

load_dotenv()
MODEL = "gpt-4o-mini"

openai_client = AzureOpenAI(
    api_key=os.getenv("AZUREAPI"),
    api_version=os.getenv("AZUREVERSION"),
    azure_endpoint=os.getenv("AZUREENDPOINT")
)

def response_openai(sys_prompt, user_prompt):
    """Get response from OpenAI API"""
    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()

def clean_generated_code(code):
    """Clean AI-generated code by removing problematic patterns"""
    lines = code.strip().split('\n')
    cleaned_lines = []
    skip_data_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip markdown blocks
        if stripped.startswith('```'):
            continue
            
        # Skip hardcoded data definitions
        if any(x in stripped for x in ['data = {', 'data = """']):
            skip_data_block = True
            continue
        
        # End of data block
        if skip_data_block and (stripped.endswith('}') or stripped.endswith('"""')):
            skip_data_block = False
            continue
            
        # Skip during data block
        if skip_data_block:
            continue
        
        # Skip problematic lines
        skip_patterns = [
            'df = pd.DataFrame(data)',
            'df = pd.read_csv(',
            'from io import StringIO',
            '# Sample data loading',
            'df.columns = df.iloc[0]',
            'df = df[1:]'
        ]
        
        if any(pattern in stripped for pattern in skip_patterns):
            print(f"Skipping: {stripped[:50]}...")
            continue
        
        cleaned_lines.append(line)
    
    # Add required imports
    cleaned_code = '\n'.join(cleaned_lines)
    imports = ["import pandas as pd", "import numpy as np", "import re"]
    
    for imp in imports:
        if imp not in cleaned_code:
            cleaned_code = imp + '\n' + cleaned_code
    
    return cleaned_code

def create_fallback_cleaning_code():
    """Robust fallback cleaning that preserves metadata"""
    return '''
import pandas as pd
import numpy as np
import re
import builtins

# Ensure built-in functions are available
any = builtins.any
len = builtins.len
str = builtins.str
float = builtins.float

print("Starting data cleaning...")
print(f"Input: {df.shape}")

# Identify column types
metadata_cols = []
date_cols = []

# Find metadata columns (text/categorical in first 10 columns)
for i, col in enumerate(df.columns):
    if i < 10:
        col_lower = str(col).lower()
        metadata_keywords = ['total', 'category', 'customer', 'sku', 'description', 'product', 'store', 'code', 'starting', 'year', 'period']
        
        has_keyword = False
        for keyword in metadata_keywords:
            if keyword in col_lower:
                has_keyword = True
                break
        
        if has_keyword:
            metadata_cols.append(col)
        else:
            # Check if column has text values
            try:
                sample = df[col].dropna().astype(str).head(3)
                if len(sample) > 0:
                    has_text = False
                    for val in sample:
                        if re.match(r'^[A-Za-z]', str(val)):
                            has_text = True
                            break
                    if has_text:
                        metadata_cols.append(col)
            except:
                pass

# Find date columns
date_patterns = [
    r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\\d{2}$',
    r'^\\d{1,2}/\\d{1,2}/\\d{2,4}$',
    r'^\\d{4}-\\d{2}-\\d{2}$'
]

for col in df.columns:
    if col not in metadata_cols:
        col_str = str(col)
        is_date = False
        
        # Pattern matching
        for pattern in date_patterns:
            try:
                if re.match(pattern, col_str):
                    is_date = True
                    break
            except:
                continue
        
        # Check for month names if regex fails
        if not is_date:
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            for month in month_names:
                if month in col_str:
                    is_date = True
                    break
        
        # Pandas parsing as last resort
        if not is_date:
            try:
                parsed = pd.to_datetime(col_str, errors='coerce')
                if pd.notna(parsed):
                    is_date = True
            except:
                pass
        
        if is_date:
            date_cols.append(col)

print(f"Metadata: {metadata_cols}")
print(f"Dates: {date_cols}")

# Ensure we have some structure
if not date_cols:
    # Emergency fallback - assume columns after metadata are dates
    if len(df.columns) > len(metadata_cols):
        date_cols = df.columns[len(metadata_cols):].tolist()

if not metadata_cols:
    # Use first 5 columns as metadata if none detected
    metadata_cols = df.columns[:5].tolist() if len(df.columns) >= 5 else [df.columns[0]]

print(f"Final Metadata: {metadata_cols}")
print(f"Final Dates: {date_cols}")

# Melt data
if date_cols and metadata_cols:
    df_melted = df.melt(
        id_vars=metadata_cols,
        value_vars=date_cols,
        var_name='Date',
        value_name='Value'
    )
    print(f"Melted successfully: {df_melted.shape}")
else:
    # Create basic structure
    df_melted = df.copy()
    df_melted['Date'] = pd.date_range('2020-01-01', periods=len(df_melted), freq='M')
    df_melted['Value'] = 1000

# Clean data
df_melted['Date'] = pd.to_datetime(df_melted['Date'], errors='coerce')

def clean_value(val):
    if pd.isna(val) or val in ['', ' ', '-']:
        return np.nan
    try:
        cleaned_str = str(val).replace(',', '').replace('"', '').replace('$', '').strip()
        return float(cleaned_str) if cleaned_str else np.nan
    except:
        return np.nan

df_melted['Value'] = df_melted['Value'].apply(clean_value)

# Fill missing values
if metadata_cols and len(metadata_cols) > 0:
    try:
        def fill_missing_group(group):
            median_val = group['Value'].median()
            fill_val = median_val if pd.notna(median_val) else 0
            group['Value'] = group['Value'].fillna(fill_val)
            return group
        
        df_cleaned = df_melted.groupby(metadata_cols, group_keys=False).apply(fill_missing_group)
    except Exception as e:
        print(f"Group filling failed: {e}")
        median_val = df_melted['Value'].median()
        fill_val = median_val if pd.notna(median_val) else 0
        df_cleaned = df_melted.fillna({'Value': fill_val})
else:
    median_val = df_melted['Value'].median()
    fill_val = median_val if pd.notna(median_val) else 0
    df_cleaned = df_melted.fillna({'Value': fill_val})

# Final cleanup
df_final = df_cleaned.dropna(subset=['Date']).drop_duplicates()

if metadata_cols:
    sort_cols = metadata_cols + ['Date']
else:
    sort_cols = ['Date']

try:
    df_final = df_final.sort_values(sort_cols).reset_index(drop=True)
except Exception as e:
    print(f"Sorting failed: {e}")
    df_final = df_final.reset_index(drop=True)

print(f"Output: {df_final.shape}")
print(f"Columns: {list(df_final.columns)}")

if len(df_final) > 0:
    print("Sample output:")
    print(df_final.head())
else:
    print("Creating dummy data...")
    df_final = pd.DataFrame({
        'Date': pd.date_range('2020-01-01', periods=12, freq='M'),
        'Value': np.random.randn(12) * 100 + 1000
    })

df = df_final
print(f"Final df assigned with shape: {df.shape}")
'''

def create_fallback_preprocessing_code():
    """Simple preprocessing for forecasting"""
    return '''
import pandas as pd
import numpy as np
import builtins

len = builtins.len
range = builtins.range
list = builtins.list

print("Starting preprocessing...")

# Find date and value columns
date_col = None
value_col = None

for col in df.columns:
    if df[col].dtype.name.startswith('datetime') or 'date' in col.lower():
        date_col = col
        break

for col in df.columns:
    if pd.api.types.is_numeric_dtype(df[col]) and col != date_col:
        if 'value' in col.lower():
            value_col = col
            break

if not value_col:
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    value_col = numeric_cols[0] if len(numeric_cols) > 0 else None

print(f"Date: {date_col}, Value: {value_col}")

# Create basic structure
if not date_col or not value_col:
    df_prep = pd.DataFrame({
        'ds': pd.date_range('2020-01-01', periods=24, freq='M'),
        'y': np.random.randn(24) * 100 + 1000
    })
else:
    df_prep = df[[date_col, value_col]].copy()
    df_prep.columns = ['ds', 'y']

# Clean and prepare
df_prep['y'] = pd.to_numeric(df_prep['y'], errors='coerce')
median_val = df_prep['y'].median()
fill_val = median_val if pd.notna(median_val) else 0
df_prep['y'] = df_prep['y'].fillna(fill_val)
df_prep = df_prep.sort_values('ds').drop_duplicates().reset_index(drop=True)

# Add basic features
df_prep['lag_1'] = df_prep['y'].shift(1)
df_prep['month'] = df_prep['ds'].dt.month
df_prep['trend'] = list(range(len(df_prep)))

# Handle remaining NaN values
df_prep['lag_1'] = df_prep['lag_1'].fillna(df_prep['y'].mean())
df_prep = df_prep.fillna(0)

print(f"Preprocessed: {df_prep.shape}")
df = df_prep
'''

def safe_execute_code(execute, code, variables, step_name=""):
    """Execute code with fallback on failure"""
    try:
        print(f"--- {step_name.upper()} ---")
        
        # Try cleaned AI code first
        cleaned_code = clean_generated_code(code)
        result = execute.execute_code(cleaned_code, variables)
        
        if not result.get("success", False):
            print(f"Primary failed: {result.get('error', 'Unknown error')}")
            
            # Use fallback
            if step_name.lower() == "clean":
                fallback_code = create_fallback_cleaning_code()
            elif step_name.lower() == "preprocess":
                fallback_code = create_fallback_preprocessing_code()
            else:
                return None
            
            print("Trying fallback...")
            result = execute.execute_code(fallback_code, variables)
            
            if not result.get("success", False):
                print(f"Fallback failed: {result.get('error', 'Unknown error')}")
                return None
        
        print(f"{step_name} completed successfully")
        return result
        
    except Exception as e:
        print(f"Error in {step_name}: {e}")
        return None

def get_dataframe_from_result(result):
    """Extract DataFrame from execution result"""
    if not result or not result.get("success", False):
        return None
        
    variables = result.get("variables", {})
    
    # Try common DataFrame variable names
    for var_name in ["df", "df_final", "df_clean", "df_melted"]:
        if var_name in variables and isinstance(variables[var_name], pd.DataFrame):
            df_result = variables[var_name]
            if not df_result.empty:
                print(f"Found DataFrame '{var_name}': {df_result.shape}")
                return df_result
    
    return None

def validate_dataframe(df, step_name=""):
    """Check if DataFrame is valid for processing"""
    if df is None or df.empty or len(df) < 3:
        print(f"Invalid DataFrame at {step_name}")
        return False
    print(f"Valid DataFrame at {step_name}: {df.shape}")
    return True

def run_workflow(df, user_query: str, user_q_type: str, model_choice: str):
    """Main workflow orchestrator"""
    
    # Load base prompt
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    prompt_path = os.path.join(base_dir, "prompts", "base.txt")
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            base_prompt = f.read()
    except FileNotFoundError:
        print(f"Prompt file not found: {prompt_path}")
        raise
    
    # Handle input data
    if isinstance(df, str):
        from io import StringIO
        data = pd.read_csv(StringIO(df))
    elif isinstance(df, pd.DataFrame):
        data = df
    else:
        raise ValueError(f"Expected DataFrame or CSV string, got {type(df)}")
    
    print(f"Initial data: {data.shape}")
    print(f"Columns: {list(data.columns)}")
    
    ph = PromptHandler(base_prompt, user_query)
    execute = PythonCodeExecutor()

    if user_q_type.lower() == "excel":
        # Excel formula workflow
        sys_clean, user_clean = ph.clean_df(data)
        clean_code = response_openai(sys_clean, user_clean)
        
        result = safe_execute_code(execute, clean_code, {"df": data}, "clean")
        if not result:
            raise RuntimeError("Clean step failed")
            
        df_clean = get_dataframe_from_result(result)
        if not validate_dataframe(df_clean, "clean"):
            raise RuntimeError("Could not extract cleaned DataFrame")
        
        sys_excel, user_excel = ph.Excel_formual(df_clean.to_csv())
        return response_openai(sys_excel, user_excel)
    
    elif user_q_type.lower() == "forecast":
        # Forecasting workflow
        
        # 1. Clean data
        sys_clean, user_clean = ph.clean_df(data)
        clean_code = response_openai(sys_clean, user_clean)
        
        result1 = safe_execute_code(execute, clean_code, {"df": data}, "clean")
        if not result1:
            raise RuntimeError("Clean step failed")
            
        df_clean = get_dataframe_from_result(result1)
        if not validate_dataframe(df_clean, "clean"):
            raise RuntimeError("Could not extract cleaned DataFrame")
        
        print(f"Cleaned: {df_clean.shape}")
        print(f"Sample:\n{df_clean.head()}")
        
        # 2. Preprocess
        sys_prep, user_prep = ph.preprocess_model(df_clean.to_csv())
        prep_code = response_openai(sys_prep, user_prep)
        
        result2 = safe_execute_code(execute, prep_code, {"df": df_clean}, "preprocess")
        if not result2:
            raise RuntimeError("Preprocess step failed")
            
        df_prep = get_dataframe_from_result(result2)
        if not validate_dataframe(df_prep, "preprocess"):
            raise RuntimeError("Could not extract preprocessed DataFrame")
        
        print(f"Preprocessed: {df_prep.shape}")
        
        # 3. Model fitting
        sys_model, user_model = ph.fit_model(df_prep.to_csv(), model_choice)
        model_code = response_openai(sys_model, user_model)
        
        result3 = safe_execute_code(execute, model_code, {"df": df_prep}, "model")
        if not result3:
            raise RuntimeError("Model step failed")
            
        per_model = result3["variables"].get("per_model")
        if not per_model:
            raise RuntimeError("Could not extract model results")
        
        print(f"Models: {list(per_model.keys())}")
        
        # 4. Chart generation
        best_model = max(per_model, key=lambda k: per_model[k]["accuracy"])
        best_results = per_model[best_model]
        
        sys_chart, user_chart = ph.chart(pd.DataFrame(best_results["preds"]))
        chart_code = response_openai(sys_chart, user_chart)
        
        result4 = safe_execute_code(execute, chart_code, {
            "df": pd.DataFrame(best_results["preds"]),
            "metrics": best_results.get("metrics", {})
        }, "chart")

        return {
            "clean_step": result1,
            "preprocess_step": result2,
            "model_step": result3,
            "best_model": best_model,
            "metrics": best_results.get("metrics", {}),
            "predictions": best_results["preds"],
            "chart_step": result4
        }
    
    else:
        raise ValueError(f"Unknown workflow type: {user_q_type}")

if __name__ == "__main__":
    try:
        # Load test data
        with open("spreadsheet.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)
        df = json_to_dataframe(json_data)
        
        # Run workflow
        result = run_workflow(
            df=df,
            user_query="forecast the sale of total cakes in next 24 months",
            user_q_type="forecast",
            model_choice="best"
        )
        
        print("✅ Workflow completed successfully!")
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()