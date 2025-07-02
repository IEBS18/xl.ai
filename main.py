from step import (
    upload_dataset,
    preview_dataset,
    extract_datetime_columns,
    auto_clean_data,
    detect_frequency_from_columns,
    long_with_id
    ) 
from Utilities import(
    check_total_col,
    generate_column_detection_prompt,
    llm_column_role_detector,
    llm_generate_schema_explanation,
    allow_manual_column_override,
    Standardize_Headers
    
)
from Data_transform import (
    grouping_data
)
from Prophet import ProphetTimeSeriesModel
import pandas as pd 
from pathlib import Path
import json

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

# manage the data 
category = df_group.select_dtypes(include='object').columns
# print(category.nunique())
if category.nunique() == 0:
    unique_values = {'Total': ['Total']}
else:
    unique_values = {col: df_group[col].unique().tolist() for col in category}
    # print(unique_values)

for col, vals in unique_values.items():
    for val in vals:
        subset = df_group[df_group[col] == val].copy()
        subset = subset[['Date','Value']].dropna()
        # print(subset)
        model = ProphetTimeSeriesModel(data=subset, freq='ME')

        model.preprocess_data()

        model.train_model()

        metrices = model.evaluate_model()
        print(f"Metrics for {val}:\n", metrices)

        future = model.predict_future(3)
        print(f"Forecast for {val}:\n", future, "\n")
        


 




# model.plot_forecast()
# model.plot_components()




