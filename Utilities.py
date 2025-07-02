import pandas as pd
from pathlib import Path
from openai import AzureOpenAI
from dotenv import load_dotenv
from dateutil.parser import parser as _parse_date
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_numeric_dtype
)
import os
from step import (
    upload_dataset,
    preview_dataset,
    extract_datetime_columns,
    auto_clean_data,
    detect_frequency_from_columns,
    long_with_id
    ) 
from Data_transform import (
    grouping_data
)
import json

load_dotenv()


openai_client = AzureOpenAI(
    api_key= os.getenv("AZUREAPI"),
    api_version= os.getenv("AZUREVERSION"),
    azure_endpoint= os.getenv("AZUREENDPOINT")
)

MODEL = "gpt-4o-mini"

def check_total_col(df):
    
    total_col = 'Total'
    
    df= df.copy()
    if total_col not in df.columns:
        df[total_col] = 'Total'
    
    return df

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

def allow_manual_column_override(column, role, llm_schema):
    
    # normalize string inputs
    if (
        column is None 
        or role is None
        or (isinstance(column, str) and column.strip().lower() == "none")
        or (isinstance(role,   str) and role.strip().lower()   == "none")
    ):
        return llm_schema

    
    if column not in llm_schema['column'].values:
        raise KeyError(f"No column name exists as {column}")
    if role not in llm_schema['role'].values:
        raise KeyError(f"No role could be found with {role}")
    
    df = llm_schema.copy()
    
    mask = df['column'] == column
    df.loc[mask, 'role'] = role
    df.loc[mask, 'reason'] =(
        "User-overridden role: required by the user for forecasting."
    )
    
    return df  
        

def Standardize_Headers(data):
    
    ###dict of all the columns 
    
    synonym_map = {"total_products": ["quantity", "qty", "units", "total", "no of products", "number of products", "count"],
    "location": ["warehouse", "region", "based at", "area", "zone", "territory", "store location", "distribution center", "branch", "facility", "delivery location", "shipping point", "geo location", "market", "sales region", "sales area", "country", "state", "province", "district", "city", "locality", "place", "hub", "center", "business unit location", "plant location", "retail outlet", "channel location", "fulfillment center", "inventory location", "site", "geography"],
    "category": ["type", "product type", "product category", "item group", "group", "class", "variable name"],
    "sku" : ["product code", "item code", "sku id", "stock keeping unit", "code", "product id", "sku number"],
    "description": ["product name", "item name", "name", "product description", "details", "desc"],
    "date": ["order date", "invoice date", "transaction date", "created at", "date of sale", "sale date"],
    "value": ["amount", "total price", "price", "sale value", "cost", "revenue", "value (INR)"]}
    
    
    # invert to variant -> canonical
    variant_to_key = {
        variant.lower() : key
        for key, variants in synonym_map.items()
        for variant in variants
    }
    
    ##build a rename dict 
    rename_dict = {}
    
    for col in data.columns:
        lookup = col.strip().lower()
        if lookup in variant_to_key:
            rename_dict[col] = variant_to_key[lookup]
        else:
            continue
        
    return data.rename(columns = rename_dict)
             

# if __name__ == "__main__":
    
    file_path = input("Enter the file you want to upload:")
    
    file_name = Path(file_path).stem
    
    data = upload_dataset(file_path)
    
    data_n = check_total_col(data)
    
    print(f"Dataset:{preview_dataset(data_n).drop(columns=['Total'])}")
    date_cols = extract_datetime_columns(data_n)
    # print(date_cols)
    if not date_cols:
        print("[ERROR] No datetime-like columns found.")
        
       
    df_long = long_with_id(data_n, date_cols)
    print(df_long)
        
    df_clean = auto_clean_data(df_long)
    
    print(df_clean.columns)

    
    prompt, prompt_sum = generate_column_detection_prompt(df_clean)
    
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
    
    column_name = df_role['column'].to_list()
    # print(column_name)

    print(df_role)
    
    
    summary = llm_generate_schema_explanation(df_role, prompt_sum)
    
    print({"summary for schema": summary})
    
    
    column = input(f"Select the column whose role you wanna change from {column_name}:")    
    # column_name = input("Enter the column name you want to override:")
    role = input("Enter the role you want to override:")
    df_manual = allow_manual_column_override(column, role, df_role)
    
    print(f"Manual Change role: \n{df_manual}")
    
    freq = detect_frequency_from_columns(df_clean['Date'])
    
    print(f"frequency of the Date column is: {freq}")
    
    df_standard = Standardize_Headers(df_clean)
    print(f"Standardize columns data: \n {df_standard}")
    # df_standard.to_excel("Data/New_file_formated.xlsx", index=False)
    
    col = df_standard.select_dtypes(include=['object']).columns
    column = input(f"Enter the column of your choice to group for {col}:")
    
    df_group = grouping_data(df_standard, column , freq )
    
    print(df_group)
    # df_group.to_excel(f"Data\\Groupby_{column}_{file_name}.xlsx", index=False)
    
    
    
    
    
    
    
    
    
    

