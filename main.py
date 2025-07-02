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
from XGB import XGBoostTimeSeries
from ema import ExponentialSmoothingTimeSeries
import pandas as pd 
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json

# Upload & preview
file_path = input("Enter the file you want to upload:")
file_name = Path(file_path).stem
data = upload_dataset(file_path)
data_n = check_total_col(data)
print(f"Dataset:{preview_dataset(data_n).drop(columns=['Total'])}")

# Date column check
date_cols = extract_datetime_columns(data_n)
# print(date_cols)
if not date_cols:
    print("[ERROR] No datetime-like columns found.")
    
# Convert to long format    
df_long = long_with_id(data_n, date_cols)
print(df_long)
    
# Clean data    
df_clean = auto_clean_data(df_long)
print(df_clean.columns)

# Detect roles via LLM
prompt, prompt_sum = generate_column_detection_prompt(df_clean)
role_detect = llm_column_role_detector(prompt)

clean = role_detect.strip()
if clean.startswith("```"):
    clean = clean.strip("` \n")
if clean.startswith("json"):
    clean = clean[len("json"):].strip()


try:
    role_list = json.loads(clean)
except json.JSONDecodeError as e:
    raise ValueError(f"Could not parse LLM output as JSON: {e}\n\nOutput was:\n{clean}")

df_role = pd.DataFrame(role_list)
column_name = df_role['column'].to_list()
# print(column_name)
print(df_role)

summary = llm_generate_schema_explanation(df_role, prompt_sum)
print({"summary for schema": summary})

# Manual override
user_input = input("Choose to override column's role yes/no:")

if user_input == 'yes':
    column = input(f"Select the column whose role you wanna change from {column_name}:")    
    # column_name = input("Enter the column name you want to override:")
    role = input("Enter the role you want to override:")
    df_manual = allow_manual_column_override(column, role, df_role)
    print(f"Manual Change role: \n{df_manual}")
else: pass

# Detect frequency
freq = detect_frequency_from_columns(df_clean['Date'])
print(f"frequency of the Date column is: {freq}")

#Standardize Columns
df_standard = Standardize_Headers(df_clean)
print(f"Standardize columns data: \n {df_standard}")
# df_standard.to_excel("Data/New_file_formated.xlsx", index=False)

#Group By
col = df_standard.select_dtypes(include=['object']).columns
column = input(f"Enter the column of your choice to group for {col}:")
df_grp = grouping_data(df_standard, column , freq )
df_group = df_grp.set_index('Date')
print(df_group)
# df_group.to_excel(f"Data\\Groupby_{column}_{file_name}.xlsx", index=False)

# manage the data 
category = df_group.select_dtypes(include='object').columns
# print(category.nunique())
if len(category) == 0:
    sum_df = (
        df_group
        .groupby('Date', as_index=True)['Value']
        .sum()
        .sort_index()
    )
    subsets = [('Total', sum_df)]
else:
    # unique_values = {col: df_group[col].unique().tolist() for col in category}
    # print(unique_values)
    grp_cat = category[0]
    # print(grp_cat)
    subsets = [
        (val, 
         df_group[df_group[grp_cat] == val][['Date','Value']].dropna().copy()
        )
        for val in df_group[grp_cat].unique()
    ]


# Parallel model function
def run_all_models(subset, val):
    # subset = subset[['Date', 'Value']].dropna()
    # subset = subset.copy()

    model1 = ProphetTimeSeriesModel(data=subset, freq='ME')
    model1.preprocess_data()
    model1.train_model()
    metrics1 = model1.evaluate_model()
    forecast1 = model1.predict_future(3)

    model2 = XGBoostTimeSeries(subset)
    model2.preprocess_data()
    model2.train_model()
    metrics2 = model2.evaluate_model()
    end_date = subset.index[-1] + pd.DateOffset(months=12)
    forecast2 = model2.predict_future(end_date)

    model3 = ExponentialSmoothingTimeSeries(
        data=subset,
        seasonal_periods=12,
        trend='add',
        seasonal='add',
        damped_trend=True
    )
    model3.preprocess_data()
    model3.train_model()
    metrics3 = model3.evaluate_model()
    forecast3 = model3.predict_future(steps=12)

    return val, metrics1, forecast1, metrics2, forecast2, metrics3, forecast3

# Run models in parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = []
    # for col, vals in unique_values.items():
    #     for val in vals:
    #         subset = df_group[df_group[col] == val].copy()
    for label, subset in subsets:
        futures.append(executor.submit(run_all_models, subset, label))

    for future in futures:
        val, m1, f1, m2, f2, m3, f3 = future.result()
        print(f"\n[Results for: {val}]\n")
        print("Prophet Model Metrics:", m1)
        print("Prophet Forecast:\n", f1)
        print("XGBoost Metrics:", m2)
        print("XGBoost Forecast:\n", f2)
        print("ETS Model Metrics:", m3)
        print("ETS Forecast:\n", f3)

 
# for col, vals in unique_values.items():
#     for val in vals:
#         subset = df_group[df_group[col] == val].copy()
#         subset = subset[['Date','Value']].dropna()
#         # print(subset)
#         model1 = ProphetTimeSeriesModel(data=subset, freq='ME')
#         model1.preprocess_data()
#         model1.train_model()
#         model2 = XGBoostTimeSeries (subset)
#         model2.preprocess_data()
#         model2.train_model()
#         model3 = ExponentialSmoothingTimeSeries (data=subset, seasonal_periods=12, trend='add', seasonal='add', damped_trend=True)
#         model3.preprocess_data()
#         model3.train_model()

        

#         metrices1 = model1.evaluate_model()
#         print(f"Metrics for {val}:\n", metrices1)
#         metrices2 = model2.evaluate_model()
#         print(f"Metrics for {val}:\n", metrices2)
#         metrices3 = model3.evaluate_model()
#         print(f"Metrics for {val}:\n", metrices3)
        

#         future1 = model1.predict_future(3)
#         print(f"Forecast for {val}:\n", future1, "\n")
#         end_date =subset.index[-1] + pd.DateOffset(months=12)
#         future2 = model2.predict_future(end_date)
#         print(f"Forecast for {val}:\n", future2, "\n")
#         future3 = model3.predict_future(steps=12)
#         print(f"Forecast for {val}:\n", future3, "\n")



# # model.plot_forecast()
# # model.plot_components()




