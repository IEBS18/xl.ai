from flask import Flask, request, jsonify, send_from_directory, stream_with_context, Response
from flask_cors import CORS
from openai import AzureOpenAI
import json
import os
from datetime import datetime
import pandas as pd
import io
import re
import openpyxl
from dotenv import load_dotenv

from test import get_cell_value_from_query

app = Flask(__name__)
CORS(app)

load_dotenv()


openai_client = AzureOpenAI(
    api_key= os.getenv("AZUREAPI"),
    api_version= os.getenv("AZUREVERSION"),
    azure_endpoint= os.getenv("AZUREENDPOINT")
)

MODEL = "gpt-4o-mini"
# Global storage for spreadsheet data (in production, use a database)
spreadsheet_data = {}
chat_history = []

def generate_sample_data(prompt):
    """Generate sample data based on the prompt using Azure OpenAI"""
    system_prompt = """You are a data generator that creates realistic spreadsheet data based on user prompts. 
    Always respond with ONLY a JSON object containing:
    1. "data": a 2D array where the first row contains headers
    2. "description": a brief description of the data created
    
    Make the data realistic and include at least 10-20 rows of data.
    
    Example format:
    {
        "data": [
            ["Date", "Product", "Sales", "Region"],
            ["2025-01-01", "Product A", 1500, "North"],
            ["2025-01-02", "Product B", 2000, "South"]
        ],
        "description": "Sales data with dates, products, sales amounts, and regions"
    }"""
    
    try:
        response = openai_client.chat.completions.create(
            model=MODEL,  # Replace with your deployment name
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        print(response)
        
        content = response.choices[0].message.content.strip()
        # Extract JSON from the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"error": "Could not parse response"}
    except Exception as e:
        return {"error": str(e)}

def analyze_data_with_ai(data, prompt):
    """Analyze existing data with AI and return insights or modifications"""
    system_prompt = """You are a data analyst that can analyze spreadsheet data and provide insights or modifications.
    The user will provide spreadsheet data and a prompt. You should:
    1. Analyze the data if asked for insights
    2. Modify the data if asked for changes
    3. Always respond in JSON format with "response", "data" (if modified), and "analysis" fields
    
    Current data structure will be provided as a 2D array where first row is headers."""
    
    try:
        data_str = json.dumps(data)
        user_message = f"Current spreadsheet data: {data_str}\n\nUser request: {prompt}"
        
        response = openai_client.chat.completions.create(
            model=MODEL,  # Replace with your deployment name
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )

        print(response)
        
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"response": content, "analysis": "Analysis completed"}
    except Exception as e:
        return {"error": str(e)}

def stream_ai_response(messages):
    """Stream AI response for real-time chat."""
    try:
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            stream=True
        )
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return

    for chunk in response:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        content = delta.content  # ✅ Access attribute directly

        if content:
            yield f"data: {json.dumps({'content': content})}\n\n"

    yield f"data: {json.dumps({'done': True})}\n\n"

@app.route('/api/chat', methods=['POST'])
def chat():
    global spreadsheet_data, chat_history
    
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({"error": "No messages provided"}), 400
        
        latest_message = messages[-1]['content']
        
        # Check if this is a request to create new spreadsheet data
        create_keywords = ['create', 'generate', 'make', 'build', 'new spreadsheet', 'new data']
        is_create_request = any(keyword in latest_message.lower() for keyword in create_keywords)
        
        if is_create_request and not spreadsheet_data:
            # Generate new spreadsheet data
            result = generate_sample_data(latest_message)
            if 'error' not in result:
                spreadsheet_data = result['data']
                chat_history.append({
                    "role": "user",
                    "content": latest_message,
                    "timestamp": datetime.now().isoformat()
                })
                
                response_content = f"I've created a spreadsheet with {result['description']}. The data includes {len(result['data'])-1} rows with columns: {', '.join(result['data'][0])}."
                
                chat_history.append({
                    "role": "assistant", 
                    "content": response_content,
                    "timestamp": datetime.now().isoformat(),
                    "data_created": True
                })
                
                return jsonify({
                    "message": response_content,
                    "data": spreadsheet_data,
                    "success": True
                })
            else:
                return jsonify({"error": result['error']}), 500
        
        elif spreadsheet_data:
            # Analyze or modify existing data
            result = analyze_data_with_ai(spreadsheet_data, latest_message)
            if 'error' not in result:
                chat_history.append({
                    "role": "user",
                    "content": latest_message,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Update data if modified
                if 'data' in result:
                    spreadsheet_data = result['data']
                
                chat_history.append({
                    "role": "assistant",
                    "content": result['response'],
                    "timestamp": datetime.now().isoformat(),
                    "analysis": result.get('analysis', '')
                })
                
                return jsonify({
                    "message": result['response'],
                    "data": spreadsheet_data,
                    "analysis": result.get('analysis', ''),
                    "success": True
                })
            else:
                return jsonify({"error": result['error']}), 500
        
        else:
            # General chat without spreadsheet data
            system_message = {
                "role": "system", 
                "content": "You are a helpful assistant that specializes in spreadsheet data analysis and creation. Help users with their data needs."
            }
            
            all_messages = [system_message] + messages
            
            def generate():
                yield "data: " + json.dumps({"type": "start"}) + "\n\n"
                
                for chunk in stream_ai_response(all_messages):
                    yield chunk
            
            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                }
            )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Streaming endpoint for real-time chat"""
    global spreadsheet_data, chat_history  # Declare globals for outer scope if needed
    
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({"error": "No messages provided"}), 400
        
        latest_message = messages[-1]['content']
        
        def generate():
            global spreadsheet_data, chat_history  # Fix: declare inside generator to avoid UnboundLocalError

            yield "data: " + json.dumps({"type": "start"}) + "\n\n"
            
            # Check if this is a request to create new spreadsheet data
            create_keywords = ['create', 'generate', 'make', 'build', 'new spreadsheet', 'new data']
            is_create_request = any(keyword in latest_message.lower() for keyword in create_keywords)
            
            if is_create_request and not spreadsheet_data:
                yield "data: " + json.dumps({"content": "Creating spreadsheet data based on your request...", "type": "thinking"}) + "\n\n"
                
                result = generate_sample_data(latest_message)
                if 'error' not in result:
                    spreadsheet_data = result['data']
                    response_content = f"I've created a spreadsheet with {result['description']}. The data includes {len(result['data'])-1} rows with columns: {', '.join(result['data'][0])}."
                    
                    yield "data: " + json.dumps({"content": response_content, "type": "message"}) + "\n\n"
                    yield "data: " + json.dumps({"data": spreadsheet_data, "type": "data"}) + "\n\n"
                else:
                    yield "data: " + json.dumps({"content": f"Error: {result['error']}", "type": "error"}) + "\n\n"
            
            elif spreadsheet_data:
                yield "data: " + json.dumps({"content": "Analyzing your spreadsheet data...", "type": "thinking"}) + "\n\n"
                
                result = analyze_data_with_ai(spreadsheet_data, latest_message)
                if 'error' not in result:
                    if 'data' in result:
                        spreadsheet_data = result['data']
                        yield "data: " + json.dumps({"data": spreadsheet_data, "type": "data"}) + "\n\n"
                    
                    yield "data: " + json.dumps({"content": result['response'], "type": "message"}) + "\n\n"
                    
                    if 'analysis' in result:
                        yield "data: " + json.dumps({"content": result['analysis'], "type": "analysis"}) + "\n\n"
                else:
                    yield "data: " + json.dumps({"content": f"Error: {result['error']}", "type": "error"}) + "\n\n"
            
            else:
                # General chat (no data yet)
                system_message = {
                    "role": "system", 
                    "content": "You are a helpful assistant that specializes in spreadsheet data analysis and creation."
                }
                
                all_messages = [system_message] + messages

                # print(all_messages)
                
                for chunk in stream_ai_response(all_messages):
                    print(chunk)
                    yield chunk
            
            yield "data: " + json.dumps({"type": "end"}) + "\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
            }
        )
    
    except Exception as e:
        return Response(
            f"data: {json.dumps({'error': str(e)})}\n\n",
            mimetype='text/event-stream'
        )

@app.route('/api/spreadsheet/data', methods=['GET'])
def get_spreadsheet_data():
    """Get current spreadsheet data"""
    return jsonify({
        "data": spreadsheet_data,
        "success": True
    })

@app.route('/api/spreadsheet/data', methods=['POST'])
def update_spreadsheet_data():
    """Update spreadsheet data"""
    global spreadsheet_data
    
    try:
        data = request.get_json()
        new_data = data.get('data', [])
        
        if new_data:
            spreadsheet_data = new_data
            return jsonify({"success": True, "message": "Spreadsheet data updated"})
        else:
            return jsonify({"error": "No data provided"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """Export spreadsheet data as CSV"""
    if not spreadsheet_data:
        return jsonify({"error": "No data to export"}), 400
    
    try:
        df = pd.DataFrame(spreadsheet_data[1:], columns=spreadsheet_data[0])
        csv_data = df.to_csv(index=False)
        
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=spreadsheet_data.csv'}
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat history"""
    return jsonify({
        "history": chat_history,
        "success": True
    })

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """Clear chat history and spreadsheet data"""
    global chat_history, spreadsheet_data
    
    chat_history = []
    spreadsheet_data = {}
    
    return jsonify({
        "success": True,
        "message": "Chat history and spreadsheet data cleared"
    })


def parse_excel_to_json(file_stream, filename):
    data = {}

    # Determine file type by extension
    if filename.lower().endswith(".csv"):
        # Read CSV
        df = pd.read_csv(file_stream).fillna("")
        data["Sheet1"] = convert_dataframe_to_sheet(df)
    elif filename.lower().endswith((".xls", ".xlsx")):
        # Read Excel using openpyxl
        xls = pd.ExcelFile(file_stream, engine="openpyxl")
        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name).fillna("")
            data[sheet_name] = convert_dataframe_to_sheet(df)
    else:
        raise ValueError("Unsupported file format")

    return data

def convert_dataframe_to_sheet(df):
    df = df.reset_index(drop=True)
    cell_map = {}

    rows = df.shape[0]
    cols = df.shape[1]

    # Add headers (row 1)
    for col_idx, col_name in enumerate(df.columns):
        col_letter = chr(65 + col_idx)
        cell_map[f"{col_letter}1"] = {"value": str(col_name), "type": "text"}

    # Add data starting from row 2
    for row_idx, row in df.iterrows():
        for col_idx, cell in enumerate(row):
            col_letter = chr(65 + col_idx)
            cell_ref = f"{col_letter}{row_idx + 2}"
            cell_type = "number" if isinstance(cell, (int, float)) else "text"
            cell_map[cell_ref] = {"value": cell, "type": cell_type}

    return {
        "data": cell_map,
        "rows": rows + 5,
        "cols": cols + 5,
        "charts": [],
    }

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"})

    file = request.files["file"]
    try:
        structured = parse_excel_to_json(file, file.filename)
        print(structured)
        return jsonify({"success": True, "data": structured})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    

@app.route("/get-cell-value", methods=["POST"])
def get_cell_value():
    try:
        req_data = request.get_json()
        spreadsheet_json = req_data.get("spreadsheet")
        user_query = req_data.get("query")
        sheet_name = req_data.get("sheetName", "Sheet1")

        if not spreadsheet_json or not user_query:
            return jsonify({"error": "Missing spreadsheet or query"}), 400

        result = get_cell_value_from_query(spreadsheet_json, user_query, sheet_name)
        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)