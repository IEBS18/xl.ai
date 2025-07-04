import os
import json
import re
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from openai import AzureOpenAI
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

# Azure OpenAI client
openai_client = AzureOpenAI(
    api_key=os.getenv("AZUREAPI"),
    api_version=os.getenv("AZUREVERSION"),
    azure_endpoint=os.getenv("AZUREENDPOINT")
)

MODEL = "gpt-4o-mini"


def generate_forecast_chart_from_gpt(forecast_data):
    """Creates a forecast chart from GPT response."""
    if not forecast_data:
        return None

    labels = []
    values = []

    for entry in forecast_data:
        label = entry.get("label")
        value = entry.get("value")
        if label and isinstance(value, (int, float)):
            labels.append(label)
            values.append(value)

    if not labels or not values:
        return None

    chart_id = f"ForecastChart_{uuid.uuid4().hex[:6]}"
    image_path = f"static/{chart_id}.png"

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values, color="orange")
    plt.xlabel("Forecast Target")
    plt.ylabel("Predicted Value")
    plt.title("GPT-Assisted Forecast")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(image_path)
    plt.close()

    return {
        "id": chart_id,
        "label": "GPT-Assisted Forecast",
        "imageUrl": f"/static/{chart_id}.png"
    }


def generate_product_sales_chart(sheet_data, sheet_name="Sheet1"):
    """Generates a real chart for Product vs Sales."""
    products = []
    sales = []

    for cell, val in sheet_data.items():
        if cell.startswith("B") and isinstance(val.get("value"), str):
            row = re.findall(r"\d+", cell)[0]
            sales_cell = f"F{row}"
            if sales_cell in sheet_data:
                product = val["value"]
                sale = sheet_data[sales_cell]["value"]
                if isinstance(sale, (int, float)):
                    products.append(product)
                    sales.append(sale)

    if not products or not sales:
        return None

    chart_id = f"Chart_{uuid.uuid4().hex[:6]}"
    image_path = f"static/{chart_id}.png"

    plt.figure(figsize=(10, 5))
    plt.bar(products, sales, color='skyblue')
    plt.xlabel("Product")
    plt.ylabel("Total Sales ($)")
    plt.title("Product vs Total Sales")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(image_path)
    plt.close()

    return {
        "id": chart_id,
        "label": "Product vs Total Sales",
        "imageUrl": f"/static/{chart_id}.png"
    }


def get_cell_value_from_query(spreadsheet_json: dict, user_query: str, sheet_name: str = "Sheet1") -> dict:
    """Main handler: calls OpenAI, parses updates, generates charts if needed."""
    sheet_data = spreadsheet_json.get("data", {}).get("data", {})
    preview_data = json.dumps({k: sheet_data[k] for k in list(sheet_data)[:300]}, indent=2)

    prompt = f"""

# 📊 Spreadsheet & Forecasting AI Agent Prompt



You are a backend AI assistant that powers intelligent spreadsheet automation, business analytics, and time series forecasting.



---



## 🔧 INPUTS



You are given:

1. A **spreadsheet preview** in JSON format:

   - Each key is a cell address (e.g., "A1", "B2")

   - Each value is a dictionary with:

     - `type`: ("text", "number")

     - `value`: e.g., `"Wireless Mouse"` or `32000`



   By convention:

   - Column B → **product names**

   - Column F → **sales or revenue**

   - Column I (if present) → **date/time**



2. A **natural language query**, such as:

   - “What are total sales for keyboards?”

   - “Compare laptop and tablet sales”

   - “Forecast sales for Q4 next year”



---



## 🧠 TASKS



1. Understand the user’s query.

2. If the query involves totals, summaries, or comparisons → extract relevant cell values.

3. If the query involves future prediction, seasonality, or trend analysis → perform forecasting.

4. Return a structured JSON object like:



```json

{{

  "updates": [

    {{

      "cell": "Sheet1!F9",

      "value": 32000,

      "label": "Wireless Keyboard Sales"

    }}

  ],

  "forecast": [

    {{

      "label": "Wireless Keyboard (Q4)",

      "value": 39000,

      "model_used": "XGBoost"

    }}

  ]

}}

```



---



## 📌 OUTPUT RULES



- If the query is **non-forecasting**, populate only `updates`.

- If the query **requires forecasting**, populate both `updates` and `forecast`.

- Include `model_used` with the **best-performing model** (lowest RMSE).

- If no relevant data, return:



```json

{{

  "updates": [],

  "forecast": []

}}

```



- Output must be valid JSON. Do not include natural language explanations.



---



## 🛠 HELPER FUNCTIONS



### 🧹 Clean Time Series Data



```python

def clean_forecasting_data(df, date_col='ds', value_col='y'):

    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    df = df.dropna(subset=[date_col, value_col])

    df = df.drop_duplicates(subset=[date_col]).sort_values(by=date_col)

    df = df.set_index(date_col).asfreq('D')

    df[value_col] = df[value_col].interpolate(method='linear')

    df[value_col] = pd.to_numeric(df[value_col], errors='coerce')

    return df.reset_index().rename(columns={{'index': 'ds'}})

```



---



### 🧠 Feature Engineering



```python

def add_date_features(df):

    df['dayofweek'] = df['ds'].dt.dayofweek

    df['dayofmonth'] = df['ds'].dt.day

    df['month'] = df['ds'].dt.month

    df['quarter'] = df['ds'].dt.quarter

    df['year'] = df['ds'].dt.year

    df['weekofyear'] = df['ds'].dt.isocalendar().week

    return df

```



---



## 🔮 Forecasting Models



### ✅ Exponential Moving Average (EMA)



```python

df['ema'] = df['y'].ewm(span=10, adjust=False).mean()

```



---



### ✅ Prophet Forecast



```python

from prophet import Prophet

model = Prophet()

model.fit(df[['ds', 'y']])

future = model.make_future_dataframe(periods=30)

forecast = model.predict(future)

```



---



### ✅ ARIMA Forecast



```python

import statsmodels.api as sm

arima_model = sm.tsa.ARIMA(df.set_index('ds')['y'], order=(2,1,2))

model_fit = arima_model.fit()

forecast = model_fit.forecast(steps=30)

```



---



### ✅ XGBoost Forecast



```python

import xgboost as xgb

from sklearn.model_selection import train_test_split

from sklearn.metrics import mean_squared_error



df = add_date_features(df)

X = df[['dayofweek', 'dayofmonth', 'month', 'quarter', 'year', 'weekofyear']]

y = df['y']

X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False)



model = xgb.XGBRegressor()

model.fit(X_train, y_train)

y_pred = model.predict(X_test)

rmse = mean_squared_error(y_test, y_pred, squared=False)

```



---



### ✅ Linear Regression Forecast



```python

from sklearn.linear_model import LinearRegression

lr = LinearRegression()

lr.fit(X_train, y_train)

y_pred = lr.predict(X_test)

rmse = mean_squared_error(y_test, y_pred, squared=False)

```



---



## ✅ MODEL SELECTION RULE



Use RMSE to compare XGBoost, Prophet, ARIMA, Linear Regression, and EMA.  

Return the forecast from the model with **lowest RMSE** and specify `model_used` in the output.



---



## 🔍 INPUT CONTEXT



**Spreadsheet preview:**

`{preview_data}`



**User query:**

`"{user_query}"`

"""

    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful spreadsheet assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    print(response)

    content = response.choices[0].message.content
    print("\n--- AI Raw Output ---\n", content)

    try:
        # Extract valid JSON block from GPT output
        match = re.search(r"```json(.*?)```", content, re.DOTALL)
        if match:
            json_text = match.group(1).strip()
        else:
            json_start = content.find("{")
            json_text = content[json_start:]

        parsed = json.loads(json_text)

        # Forecast logic (GPT-assisted)
        forecast_requested = any(x in user_query.lower() for x in ["forecast", "predict", "future trend"])
        if forecast_requested and "forecast" in parsed:
            forecast_chart = generate_forecast_chart_from_gpt(parsed["forecast"])
            if forecast_chart:
                parsed["chart"] = forecast_chart

        # If not forecast, fallback to regular product sales chart
        elif "chart" in parsed or any(x in user_query.lower() for x in ["chart", "compare", "vs", "visual"]):
            chart_data = generate_product_sales_chart(sheet_data, sheet_name)
            if chart_data:
                parsed["chart"] = chart_data

        return parsed

    except Exception as e:
        print("Failed to parse response:", e)
        return {
            "updates": [],
            "chart": None,
            "error": "Failed to parse AI response"
        }



# Example usage
if __name__ == "__main__":
    with open("sample.json", encoding="utf-8") as f:
        spreadsheet = json.load(f)

    query = "Total sales of wireless keyboard with a chart"
    result = get_cell_value_from_query(spreadsheet, query)
    print(json.dumps(result, indent=2))
