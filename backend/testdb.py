import os
import json
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import AzureOpenAI

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

AZURE_ENDPOINT = os.getenv("AZUREENDPOINT")
AZURE_VERSION = os.getenv("AZUREVERSION")
AZURE_MODEL = os.getenv("AZUREMODEL")
AZURE_API_KEY = os.getenv("AZUREAPIKEY")

# -------------------------------
# Azure OpenAI Client
# -------------------------------
client = AzureOpenAI(
    api_key= os.getenv("AZUREAPI"),
    api_version= os.getenv("AZUREVERSION"),
    azure_endpoint= os.getenv("AZUREENDPOINT")
)

# -------------------------------
# Database Schema Loader
# -------------------------------
def get_db_schema():
    """Fetch table and column info from PostgreSQL."""
    conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema='public'
        ORDER BY table_name, ordinal_position;
    """)
    rows = cur.fetchall()
    conn.close()

    schema = {}
    for table, column, dtype in rows:
        schema.setdefault(table, []).append(f"{column} ({dtype})")
    return schema

# -------------------------------
# Database Query Function
# -------------------------------
def query_database(sql_query: str):
    """Run SQL and return rows as list of dicts."""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        dbname=DB_NAME
    )
    df = pd.read_sql(sql_query, conn)
    conn.close()
    return df.to_dict(orient="records")

# -------------------------------
# Visualization Function
# -------------------------------
def create_visualization(data, chart_type, x, y):
    """Generate a chart and return image path."""
    try:
        print(f"Creating visualization with data type: {type(data)}")
        print(f"Data: {data}")
        
        os.makedirs("charts", exist_ok=True)
        df = pd.DataFrame(data)
        
        print(f"DataFrame shape: {df.shape}")
        print(f"DataFrame columns: {list(df.columns)}")
        
        if df.empty:
            return {"error": "No data to visualize"}
        
        if x not in df.columns or y not in df.columns:
            return {"error": f"Columns {x} or {y} not found in data. Available columns: {list(df.columns)}"}
        
        plt.figure(figsize=(12, 8))

        if chart_type == "bar":
            plt.bar(df[x], df[y])
            plt.xticks(rotation=45, ha='right')
        elif chart_type == "line":
            plt.plot(df[x], df[y], marker='o')
            plt.xticks(rotation=45, ha='right')
        elif chart_type == "pie":
            plt.pie(df[y], labels=df[x], autopct='%1.1f%%')

        plt.title(f"{y} by {x}")
        if chart_type != "pie":
            plt.xlabel(x)
            plt.ylabel(y)
        
        plt.tight_layout()
        path = f"charts/{chart_type}_{x}_{y}.png"
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Chart saved to: {path}")
        return {"image_path": path}
        
    except Exception as e:
        print(f"Error in create_visualization: {e}")
        return {"error": str(e)}

# -------------------------------
# Assistant Creation
# -------------------------------
def create_assistant(schema):
    """Create assistant with schema context for SQL awareness."""
    system_prompt = (
        "You are a data analyst assistant. "
        "Use the database schema below to write accurate SQL queries. "
        "Always use existing table and column names exactly as shown.\n\n"
        "IMPORTANT WORKFLOW:\n"
        "1. When asked for visualizations, FIRST query the database to get the data\n"
        "2. THEN use the create_visualization function with the actual data from step 1\n"
        "3. The create_visualization function requires the 'data' parameter with actual query results\n\n"
        f"Database Schema:\n{json.dumps(schema, indent=2)}"
    )

    assistant = client.beta.assistants.create(
        name="DB Analyst Assistant",
        model=AZURE_MODEL,
        instructions=system_prompt,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "query_database",
                    "description": "Run SQL queries on the PostgreSQL database and return results as JSON.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql_query": {"type": "string"}
                        },
                        "required": ["sql_query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_and_visualize",
                    "description": "Query the database and create a visualization in one step. Use this for creating charts.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql_query": {"type": "string", "description": "SQL query to get data"},
                            "chart_type": {"type": "string", "enum": ["bar", "line", "pie"]},
                            "x": {"type": "string", "description": "Column name for x-axis"},
                            "y": {"type": "string", "description": "Column name for y-axis"}
                        },
                        "required": ["sql_query", "chart_type", "x", "y"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_visualization",
                    "description": "Generate a chart (bar, line, pie) from existing data and return image path.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data": {"type": "array", "items": {"type": "object"}},
                            "chart_type": {"type": "string", "enum": ["bar", "line", "pie"]},
                            "x": {"type": "string"},
                            "y": {"type": "string"}
                        },
                        "required": ["data", "chart_type", "x", "y"]
                    }
                }
            }
        ]
    )
    return assistant

# -------------------------------
# Helper function for query and visualization
# -------------------------------
def query_and_visualize(sql_query, chart_type, x, y):
    """Query database and create visualization in one step."""
    try:
        # First get the data
        data = query_database(sql_query)
        print(f"Retrieved {len(data)} rows from database")
        
        if not data:
            return {"error": "No data returned from query"}
        
        # Then create visualization
        result = create_visualization(data, chart_type, x, y)
        return result
    except Exception as e:
        return {"error": f"Error in query_and_visualize: {str(e)}"}

# -------------------------------
# Tool Handler - FIXED
# -------------------------------
def handle_tool_call(tool_call):
    # Fixed: Use attribute access instead of dictionary access
    func_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    
    print(f"Function called: {func_name}")
    print(f"Arguments: {args}")

    if func_name == "query_database":
        return query_database(args["sql_query"])

    if func_name == "create_visualization":
        # Add validation to ensure all required parameters are present
        required_params = ["data", "chart_type", "x", "y"]
        for param in required_params:
            if param not in args:
                raise ValueError(f"Missing required parameter: {param}")
        
        return create_visualization(args["data"], args["chart_type"], args["x"], args["y"])
    
    if func_name == "query_and_visualize":
        required_params = ["sql_query", "chart_type", "x", "y"]
        for param in required_params:
            if param not in args:
                raise ValueError(f"Missing required parameter: {param}")
        
        return query_and_visualize(args["sql_query"], args["chart_type"], args["x"], args["y"])
    
    return {"error": f"Unknown function: {func_name}"}

# -------------------------------
# Main Conversation Flow
# -------------------------------
def main():
    print("Fetching database schema...")
    schema = get_db_schema()
    print("Loaded schema:")
    print(json.dumps(schema, indent=2))

    assistant = create_assistant(schema)
    thread = client.beta.threads.create()

    user_question = input("\nAsk your question: ")

    # Add user message
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_question
    )

    # Start assistant run
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # Process steps
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

        if run_status.status == "completed":
            break
        elif run_status.status == "requires_action":
            tool_outputs = []
            for tc in run_status.required_action.submit_tool_outputs.tool_calls:
                try:
                    output = handle_tool_call(tc)
                    tool_outputs.append({
                        "tool_call_id": tc.id,
                        "output": json.dumps(output)
                    })
                except Exception as e:
                    print(f"Error handling tool call: {e}")
                    print(f"Tool call ID: {tc.id}")
                    print(f"Function name: {tc.function.name}")
                    print(f"Arguments: {tc.function.arguments}")
                    tool_outputs.append({
                        "tool_call_id": tc.id,
                        "output": json.dumps({"error": str(e)})
                    })

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
        elif run_status.status == "failed":
            print(f"Run failed: {run_status.last_error}")
            break
        else:
            continue

    # Display assistant response
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for msg in messages.data:
        if msg.role == "assistant":
            print("\nAssistant:", msg.content[0].text.value)

if __name__ == "__main__":
    main()