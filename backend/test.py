import os
import json
import re
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from openai import AzureOpenAI
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
You are a backend AI assistant analyzing spreadsheet JSON and answering business queries.

Spreadsheet structure:
- Each key is a cell (e.g., "A1", "B2").
- Each value has `type` and `value`.
- Column B contains product names.
- Column F contains total sales.
- Column I (if present) contains date or time info.

Instructions:
1. If the user asks for trends or forecasts, analyze existing data to generate future predictions.
2. Return JSON like this:
```json
{{
  "updates": [
    {{
      "cell": "Sheet1!F9",
      "value": 3000,
      "label": "Wireless Keyboard Sales"
    }}
  ],
  "forecast": [
    {{
      "label": "Smartphone (Q4)",
      "value": 62000
    }},
    {{
      "label": "Smart Watch (Q4)",
      "value": 54000
    }}
  ]
}}
Only include `forecast` if the query involves future prediction.

Spreadsheet preview:
{preview_data}

User query:
"{user_query}"
"""

    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful spreadsheet assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

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
