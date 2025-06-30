import pandas as pd
from openai import AzureOpenAI
from dotenv import load_dotenv
from dateutil.parser import parser as _parse_date
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_numeric_dtype,
)
import os
from step import (
    upload_dataset,
    preview_dataset,
    extract_datetime_columns,
    validate_time_series,
    auto_clean_data,
    detect_frequency_from_columns,
    long_with_id
    ) 
import json

load_dotenv()


openai_client = AzureOpenAI(
    api_key= os.getenv("AZUREAPI"),
    api_version= os.getenv("AZUREVERSION"),
    azure_endpoint= os.getenv("AZUREENDPOINT")
)

MODEL = "gpt-4o-mini"

def generate_column_detection_prompt(data):
    sample = data.head(5).to_dict(orient = 'records')
    prompt_detection = f"""
You are a data analyst AI. Your task is to identify the role of each column in a time series forecasting context.

Here are the first few rows of the data:
{sample}

For each column, provide the following:
- Column Name
- Role (One of: 'date', 'target', 'feature', 'ignore')
- Reason for classification

Note: don't mention like detection:```json``` for later to convert in dataframe.
keep the role consistent, multiple columns can be in feature but there will be one date and one target column

Return your answer as a JSON list like:
[
  {{
    "column": "Date",
    "role": "date",
    "reason": "Contains datetime values in a consistent format."
  }},
  ...
]
"""
    prompt_summary = f"""
    You are a data analyst AI. Your task is to identify all the columns and create a summary of 
    schema in a time series forecasting context.

INSTRUCTION:
1. look into all the columns in the schema 
2. Summarizes detected schema for user
3. it should be in a paragraph as an Explaination 
4. don't add any special character or line breaks like '**', '\n', '\b'
    
    """

    return prompt_detection, prompt_summary

def llm_column_role_detector(prompt):
    response = openai_client.chat.completions.create(
        model= MODEL,
        messages=[{"role": "system", "content": prompt},
        {
            'role': "user", "content": "Detect all columns, their roles(target, feature, ignore) and reason to detect all the column roles."
        }],
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

def llm_generate_schema_explanation(data, prompt):
    
    schema = data.to_dict(orient = 'records')
    schema_str = json.dumps(schema)
    
    response = openai_client.chat.completions.create(
        model= MODEL,
        messages=[{"role": "system", "content": prompt},
        {
            'role': "user", "content": schema_str
        }],
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

def allow_manual_column_override(column_name, role, llm_schema):
    pass
    
        

if __name__ == "__main__":
    
    file_path = input("Enter the file you want to upload:")
    
    data = upload_dataset(file_path)
    
    print({"Dataset":preview_dataset(data)})
    
    date_cols = extract_datetime_columns(data)
    # print(date_cols)
    if not date_cols:
        print("[ERROR] No datetime-like columns found.")
       
    df_long = long_with_id(data, date_cols)
    print(df_long)

    
    prompt, prompt_sum = generate_column_detection_prompt(df_long)
    
    role_detect = llm_column_role_detector(prompt)
    
    clean = role_detect.strip()
    if clean.startswith("```"):
        clean = clean.strip("` \n")
    if clean.startswith("json"):
        clean = clean[len("json"):].strip()
    

    # 2) Load into a Python object
    try:
        role_list = json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse LLM output as JSON: {e}\n\nOutput was:\n{clean}")

    # 3) Build your DataFrame
    df_role = pd.DataFrame(role_list)

    print(df_role)
    
    
    summary = llm_generate_schema_explanation(df_role, prompt_sum)
    
    print({"summary for schema": summary})
    
    column_name = input("Enter the column name you want to override:")
    role = input("Enter the role you want to override:")
    
    allow_manual_column_override(column_name, role, df_role)
    
    
    
    
    
    
    
    
    
    
    

