import os
import json
import uuid
import re
import traceback
import base64
import pandas as pd
import matplotlib.pyplot as plt
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup OpenAI client
openai_client = AzureOpenAI(
    api_key=os.getenv("AZUREAPI"),
    api_version=os.getenv("AZUREVERSION"),
    azure_endpoint=os.getenv("AZUREENDPOINT")
)

MODEL = "gpt-4o-mini"
os.makedirs("charts/test3", exist_ok=True)

# Utility Functions
def print_step(title, content=""):
    print(f"\n\U0001f9e0 {title}\n{'-' * len(title)}")
    if content:
        print(content)

def spreadsheet_json_to_dataframe(sheet_data):
    columns = {}
    max_row = 0
    for cell_ref, cell in sheet_data.items():
        col_letter = ''.join(filter(str.isalpha, cell_ref))
        row_number = int(''.join(filter(str.isdigit, cell_ref)))
        col_index = ord(col_letter.upper()) - ord('A')
        max_row = max(max_row, row_number)
        if row_number == 1:
            columns[col_index] = cell['value']

    num_cols = max(columns.keys()) + 1
    col_names = [columns.get(i, f"Col{i+1}") for i in range(num_cols)]

    all_rows = []
    for row in range(2, max_row + 1):
        row_data = []
        for col in range(num_cols):
            cell_ref = f"{chr(65 + col)}{row}"
            cell = sheet_data.get(cell_ref, {})
            row_data.append(cell.get("value", None))
        all_rows.append(row_data)

    return pd.DataFrame(all_rows, columns=col_names)

def extract_code_block(markdown):
    match = re.search(r"```(?:python)?\n(.*?)```", markdown, re.DOTALL)
    return match.group(1).strip() if match else ""

def embed_chart_base64(chart_filename):
    with open(chart_filename, "rb") as img_file:
        b64 = base64.b64encode(img_file.read()).decode('utf-8')
    return f"<img src='data:image/png;base64,{b64}' style='max-width:100%;'>"

# Load spreadsheet.json
print_step("Step 1: Loading spreadsheet")
with open('spreadsheet.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

user_query = payload['query']
sheet_data = payload['spreadsheet']['data']['data']
df = spreadsheet_json_to_dataframe(sheet_data)
print(df.head())

# Generate analysis plan
print_step("Step 2: Asking AI for multi-step plan with code")
full_prompt = f"""
You are a world-class AI data analyst with expertise in interpreting business data.

User Query: "{user_query}"

Here is a sample of the spreadsheet (first 10 rows):

{df.head(10).to_string(index=False)}

Please perform the following:
1. Rephrase the user query with full explanation (at least 150 words).
2. Perform a data audit: missing values, formatting issues, inconsistencies, invalid entries. Describe if cleaning is needed. If yes, write code.
3. Define logical steps needed to analyze the query.
4. For each step:
   - Step number and title
   - 100-word explanation
   - Python code block for that step
5. Ensure at least one step creates a chart using matplotlib or seaborn.
6. After all steps, write a final insight section.
7. Return the full analysis in Markdown format with all code blocks clearly formatted using triple backticks.
8. IMPORTANT: Use the existing variable `df` for the dataset. Do NOT reload from CSV or any file. Use `df` throughout the steps.
"""

response = openai_client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": full_prompt}],
    temperature=0.3
)

markdown_report = response.choices[0].message.content.strip()

# Execute AI-generated code blocks
print_step("Step 3: Executing steps from AI plan")
code_blocks = re.findall(r"```(?:python)?\n(.*?)```", markdown_report, re.DOTALL)
exec_env = {'df': df, 'pd': pd, 'np': __import__('numpy'), 'plt': plt}
chart_filename = None
successful_steps = []

for i, code in enumerate(code_blocks):
    print_step(f"Executing Step {i + 1}", code)
    try:
        if 'plt.show' in code or 'plt.savefig' in code:
            code = code.replace('plt.show()', '')  # remove interactive show
            chart_filename = f"charts/test3/{uuid.uuid4().hex}.png"
            print("\U0001f4f8 Saving chart:", chart_filename)
            code += f"\nplt.savefig('{chart_filename}', bbox_inches='tight')\nplt.close()"

        exec(code, exec_env)
        successful_steps.append(i + 1)
        print(f"✅ Variables after Step {i+1}: {list(exec_env.keys())}")

    except Exception as e:
        traceback_str = traceback.format_exc()
        print(f"❌ Error in Step {i + 1}: {e}\n{traceback_str}")
        print("🔁 Requesting alternate approach from AI")

        retry_prompt = f"""
A multi-step analysis plan failed on Step {i + 1}.

User Query: {user_query}

Data Sample:
{df.head(10).to_string(index=False)}

Original Step {i + 1} Code:
```python
{code}
```

Error:
{traceback_str}

Previously successful steps: {successful_steps}

Please revise the above step to avoid the error. Return ONLY the corrected Python code.
"""
        retry_response = openai_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": retry_prompt}],
            temperature=0.3
        )
        retry_code = extract_code_block(retry_response.choices[0].message.content)

        try:
            exec(retry_code, exec_env)
            successful_steps.append(i + 1)
            print(f"✅ Step {i + 1} recovered successfully after retry")
        except Exception as e2:
            print(f"❌ Retry of Step {i + 1} also failed: {e2}")
            print("🚫 Halting further execution.")
            break

# Generate final HTML report
html_report = f"""
<html><head><title>AI Analysis Report</title></head><body>
<h1>AI-Generated Analysis Report</h1>
<pre>{markdown_report}</pre>
"""
if chart_filename:
    html_report += "<h2>Generated Chart</h2>" + embed_chart_base64(chart_filename)

html_report += "</body></html>"
report_path = "charts/detailed_report.html"

with open(report_path, "w", encoding="utf-8") as f:
    f.write(html_report)

with open("charts/report.md", "w", encoding="utf-8") as f:
    f.write(markdown_report)

print_step("✅ Final Report Saved", report_path)
