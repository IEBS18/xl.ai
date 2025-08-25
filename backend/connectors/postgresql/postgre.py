# from llama_index.core import SQLDatabase
# from llama_index.core.query_engine import NLSQLTableQueryEngine
# from llama_index.llms.azure_openai import AzureOpenAI  # USE AZURE-SPECIFIC CLASS!
# from llama_index.core import Settings
# from sqlalchemy import create_engine, text
# import urllib.parse
# import os
# from dotenv import load_dotenv

# load_dotenv()

# # ========================================
# # AZURE OPENAI CONFIGURATION
# # ========================================
# AZURE_API_KEY = os.getenv("AZURE_API")
# AZURE_BASE_URL = os.getenv("AZURE_BASE_URL")
# AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2024-08-01-preview")
# AZURE_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-mini")

# # Extract the clean endpoint and deployment name from your URL
# # Your URL: "https://hites-m730vlcq-swedencentral.openai.azure.com/openai/deployments/pharmaX/chat/completions?api-version=..."
# if "/openai/deployments/" in AZURE_BASE_URL:
#     # Extract base endpoint
#     azure_endpoint = AZURE_BASE_URL.split("/openai/deployments/")[0]
#     # Extract deployment name
#     deployment_name = AZURE_BASE_URL.split("/openai/deployments/")[1].split("/")[0]
# else:
#     # Fallback if URL format is different
#     azure_endpoint = AZURE_BASE_URL.rstrip("/")
#     deployment_name = "pharmaX"

# print("=" * 50)
# print("AZURE OPENAI CONFIGURATION")
# print("=" * 50)
# print(f"Endpoint: {azure_endpoint}")
# print(f"Deployment: {deployment_name}")
# print(f"Model: {AZURE_MODEL}")
# print(f"API Version: {AZURE_API_VERSION}")
# print(f"API Key: {'***' + AZURE_API_KEY[-4:] if AZURE_API_KEY else 'NOT SET'}")

# # ========================================
# # DATABASE CONFIGURATION
# # ========================================
# config = {
#     "username": os.getenv("DB_USER"),
#     "password": os.getenv("DB_PASSWORD"),
#     "host": os.getenv('DB_HOST'),
#     "port": 5432,
#     "database": os.getenv("DB_NAME")
# }

# # Check for missing configs
# missing_configs = []
# for key, value in config.items():
#     if not value and key != "port":
#         missing_configs.append(f"DB_{key.upper()}")

# if missing_configs:
#     print(f"\n❌ MISSING REQUIRED ENVIRONMENT VARIABLES: {', '.join(missing_configs)}")
#     exit(1)

# # Build connection string
# password_encoded = urllib.parse.quote_plus(config["password"])
# connection_string = (
#     f"postgresql://{config['username']}:{password_encoded}@"
#     f"{config['host']}:{config['port']}/{config['database']}?sslmode=require"
# )

# print("\n" + "=" * 50)
# print("DATABASE CONNECTION")
# print("=" * 50)

# try:
#     # Create engine and test connection
#     engine = create_engine(connection_string)
    
#     with engine.connect() as conn:
#         result = conn.execute(text("SELECT version()"))
#         print(f"✓ Connected to PostgreSQL!")
        
#         # List tables
#         result = conn.execute(text("""
#             SELECT table_name 
#             FROM information_schema.tables 
#             WHERE table_schema = 'public' 
#             ORDER BY table_name
#             LIMIT 10;
#         """))
#         tables = result.fetchall()
#         print(f"\nAvailable tables:")
#         for table in tables:
#             print(f"  - {table[0]}")
    
#     # ========================================
#     # INITIALIZE AZURE OPENAI WITH LLAMAINDEX
#     # ========================================
#     print("\n" + "=" * 50)
#     print("INITIALIZING AZURE OPENAI LLM")
#     print("=" * 50)
    
#     # CRITICAL: Use AzureOpenAI class, not OpenAI!
#     llm = AzureOpenAI(
#         deployment_name=deployment_name,
#         model=AZURE_MODEL,           
#         api_key=AZURE_API_KEY,
#         azure_endpoint=azure_endpoint,
#         api_version=AZURE_API_VERSION,
#         temperature=0,
#         max_tokens=1000
#     )
    
#     # Test the LLM connection
#     try:
#         print("Testing LLM connection...")
#         test_response = llm.complete("Say 'Hello, Azure OpenAI is working!'")
#         print(f"✓ LLM Test Response: {test_response.text.strip()}")
#     except Exception as e:
#         print(f"❌ LLM Test Failed: {e}")
        
#         # Fallback: Try with environment variables
#         print("\nTrying fallback method with environment variables...")
#         os.environ["AZURE_OPENAI_API_KEY"] = AZURE_API_KEY
#         os.environ["AZURE_OPENAI_ENDPOINT"] = azure_endpoint
#         os.environ["OPENAI_API_VERSION"] = AZURE_API_VERSION
        
#         llm = AzureOpenAI(
#             deployment_name=deployment_name,
#             model=AZURE_MODEL,
#             temperature=0,
#             max_tokens=1000
#         )
        
#         test_response = llm.complete("Say 'Hello, Azure OpenAI is working!'")
#         print(f"✓ Fallback successful! Response: {test_response.text.strip()}")
    
#     # ========================================
#     # SETUP EMBEDDINGS (OPTIONAL)
#     # ========================================
#     print("\n" + "=" * 50)
#     print("SETTING UP EMBEDDINGS")
#     print("=" * 50)
    
#     try:
#         # Option 1: Use Azure OpenAI embeddings if you have a deployment
#         from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
        
#         # Uncomment if you have an embeddings deployment
#         # embed_model = AzureOpenAIEmbedding(
#         #     deployment_name="your-embedding-deployment",
#         #     api_key=AZURE_API_KEY,
#         #     azure_endpoint=azure_endpoint,
#         #     api_version=AZURE_API_VERSION
#         # )
        
#         # Option 2: Use local embeddings (no API calls)
#         from llama_index.embeddings.huggingface import HuggingFaceEmbedding
#         embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
#         print("✓ Using HuggingFace local embeddings")
        
#     except ImportError:
#         print("⚠️ No embeddings model available, proceeding without embeddings")
#         embed_model = None
    
#     # ========================================
#     # CONFIGURE LLAMAINDEX SETTINGS
#     # ========================================
#     Settings.llm = llm
#     if embed_model:
#         Settings.embed_model = embed_model
    
#     # ========================================
#     # CREATE QUERY ENGINE
#     # ========================================
#     print("\n" + "=" * 50)
#     print("CREATING QUERY ENGINE")
#     print("=" * 50)
    
#     sql_database = SQLDatabase(engine)
    
#     query_engine = NLSQLTableQueryEngine(
#         sql_database=sql_database,
#         llm=llm,
#         verbose=True  # Show SQL queries being generated
#     )
    
#     # ========================================
#     # TEST QUERIES
#     # ========================================
#     print("\n" + "=" * 50)
#     print("TESTING QUERIES")
#     print("=" * 50)
    
#     # Use the first available table or default
#     table_name = tables[0][0] if tables else "users"
    
#     test_queries = [
#         f"How many rows are in the {table_name} table?",
#         f"What are the column names in the {table_name} table?",
#         # Add more test queries as needed
#     ]
    
#     for query in test_queries:
#         try:
#             print(f"\nQuery: {query}")
#             response = query_engine.query(query)
#             print(f"Response: {response}")
#         except Exception as e:
#             print(f"Error: {e}")
    
#     print("\n" + "=" * 50)
#     print("✓ SETUP COMPLETE!")
#     print("=" * 50)
    
# except Exception as e:
#     print(f"\n❌ ERROR: {e}")
#     import traceback
#     traceback.print_exc()
    
#     # Additional debugging
#     print("\n" + "=" * 50)
#     print("DEBUGGING INFORMATION")
#     print("=" * 50)
#     print(f"Python version: {os.sys.version}")
    
#     # Check installed packages
#     try:
#         import llama_index
#         print(f"LlamaIndex version: {llama_index.__version__}")
#     except:
#         print("LlamaIndex not properly installed")
    
#     try:
#         import openai
#         print(f"OpenAI version: {openai.__version__}")
#     except:
#         print("OpenAI package not installed")



from flask import Flask, request, jsonify
from flask_cors import CORS
from llama_index.core import SQLDatabase, Settings
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from sqlalchemy import create_engine, text, inspect
from cryptography.fernet import Fernet
import urllib.parse
import os
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
import threading
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

# Generate or load encryption key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

# Store active connections in memory (use Redis in production)
active_connections = {}
connection_lock = threading.Lock()

# Azure OpenAI Configuration
def get_azure_config():
    """Extract Azure OpenAI configuration from environment variables"""
    azure_base_url = os.getenv("AZURE_BASE_URL")
    
    if "/openai/deployments/" in azure_base_url:
        azure_endpoint = azure_base_url.split("/openai/deployments/")[0]
        deployment_name = azure_base_url.split("/openai/deployments/")[1].split("/")[0]
    else:
        azure_endpoint = azure_base_url.rstrip("/")
        deployment_name = "pharmaX"
    
    return {
        "endpoint": azure_endpoint,
        "deployment": deployment_name,
        "api_key": os.getenv("AZURE_API_KEY"),
        "api_version": os.getenv("AZURE_API_VERSION", "2024-08-01-preview"),
        "model": os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-mini")
    }

def initialize_llm():
    """Initialize Azure OpenAI LLM"""
    config = get_azure_config()
    
    llm = AzureOpenAI(
        deployment_name=config["deployment"],
        model=config["model"],
        api_key=config["api_key"],
        azure_endpoint=config["endpoint"],
        api_version=config["api_version"],
        temperature=0,
        max_tokens=1000
    )
    
    # Initialize embeddings
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    # Configure Settings
    Settings.llm = llm
    Settings.embed_model = embed_model
    
    return llm

# Initialize LLM on startup
llm = initialize_llm()

def encrypt_password(password):
    """Encrypt password for storage"""
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    """Decrypt stored password"""
    return cipher.decrypt(encrypted_password.encode()).decode()

def test_postgres_connection(host, port, user, password, database=None):
    """Test PostgreSQL connection"""
    try:
        conn_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password
        }
        
        if database:
            conn_params["database"] = database
        else:
            # Connect to default postgres database to list all databases
            conn_params["database"] = "postgres"
        
        conn = psycopg2.connect(**conn_params)
        conn.close()
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)

def get_databases_list(host, port, user, password):
    """Get list of all databases on the server"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres"  # Connect to default database
        )
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT datname 
            FROM pg_database 
            WHERE datistemplate = false 
            ORDER BY datname;
        """)
        
        databases = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return databases
    except Exception as e:
        raise Exception(f"Failed to list databases: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/connectors/postgres/test', methods=['POST'])
def test_connection():
    """Test PostgreSQL server connection and list databases"""
    data = request.json
    
    host = data.get('host')
    port = data.get('port', 5432)
    user = data.get('user')
    password = data.get('password')
    
    if not all([host, port, user, password]):
        return jsonify({
            "success": False,
            "message": "Missing required connection parameters"
        }), 400
    
    # Test connection
    success, message = test_postgres_connection(host, port, user, password)
    
    if not success:
        return jsonify({
            "success": False,
            "message": message
        }), 400
    
    try:
        # Get list of databases
        databases = get_databases_list(host, port, user, password)
        
        return jsonify({
            "success": True,
            "message": "Connection successful",
            "databases": databases
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/connectors/postgres/connect', methods=['POST'])
def connect_to_database():
    """Connect to a specific database and set up query engine"""
    data = request.json
    
    connection_name = data.get('connectionName')
    host = data.get('host')
    port = data.get('port', 5432)
    user = data.get('user')
    password = data.get('password')
    database = data.get('database')
    ssl_mode = data.get('ssl', False)
    
    if not all([connection_name, host, port, user, password, database]):
        return jsonify({
            "success": False,
            "message": "Missing required parameters"
        }), 400
    
    try:
        # Build connection string
        password_encoded = urllib.parse.quote_plus(password)
        ssl_param = "?sslmode=require" if ssl_mode else ""
        connection_string = (
            f"postgresql://{user}:{password_encoded}@"
            f"{host}:{port}/{database}{ssl_param}"
        )
        
        # Create engine
        engine = create_engine(connection_string)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Create SQL database instance
        sql_database = SQLDatabase(engine)
        
        # Create query engine
        query_engine = NLSQLTableQueryEngine(
            sql_database=sql_database,
            llm=llm,
            verbose=True
        )
        
        # Generate connection ID
        connection_id = str(uuid.uuid4())
        
        # Store connection details
        with connection_lock:
            active_connections[connection_id] = {
                "id": connection_id,
                "name": connection_name,
                "database": database,
                "host": host,
                "port": port,
                "user": user,
                "password": encrypt_password(password),
                "engine": engine,
                "query_engine": query_engine,
                "created_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat()
            }
        
        # Get table information
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        return jsonify({
            "success": True,
            "message": f"Connected to database '{database}' successfully",
            "connectionId": connection_id,
            "connectionName": connection_name,
            "database": database,
            "tables": tables,
            "tableCount": len(tables)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to connect: {str(e)}"
        }), 500

@app.route('/api/connectors/postgres/query', methods=['POST'])
def query_database():
    """Execute natural language query on connected database"""
    data = request.json
    connection_id = data.get('connectionId')
    query = data.get('query')
    
    if not connection_id or not query:
        return jsonify({
            "success": False,
            "message": "Missing connectionId or query"
        }), 400
    
    connection = active_connections.get(connection_id)
    
    if not connection:
        return jsonify({
            "success": False,
            "message": "Connection not found. Please reconnect."
        }), 404
    
    try:
        # Update last used timestamp
        connection['last_used'] = datetime.now().isoformat()
        
        # Execute query using query engine
        response = connection['query_engine'].query(query)
        
        # Extract SQL query if available
        sql_query = None
        if hasattr(response, 'metadata') and response.metadata:
            sql_query = response.metadata.get('sql_query')
        
        return jsonify({
            "success": True,
            "result": str(response),
            "sql": sql_query,
            "database": connection['database']
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Query failed: {str(e)}"
        }), 500

@app.route('/api/connectors/postgres/execute', methods=['POST'])
def execute_sql():
    """Execute raw SQL query"""
    data = request.json
    connection_id = data.get('connectionId')
    sql_query = data.get('sql')
    
    if not connection_id or not sql_query:
        return jsonify({
            "success": False,
            "message": "Missing connectionId or SQL query"
        }), 400
    
    connection = active_connections.get(connection_id)
    
    if not connection:
        return jsonify({
            "success": False,
            "message": "Connection not found"
        }), 404
    
    try:
        engine = connection['engine']
        
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            
            # Handle SELECT queries
            if result.returns_rows:
                rows = [dict(row._mapping) for row in result]
                return jsonify({
                    "success": True,
                    "rows": rows,
                    "rowCount": len(rows),
                    "database": connection['database']
                })
            else:
                # Handle INSERT, UPDATE, DELETE
                return jsonify({
                    "success": True,
                    "rowCount": result.rowcount,
                    "message": f"Query executed successfully. {result.rowcount} rows affected.",
                    "database": connection['database']
                })
                
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"SQL execution failed: {str(e)}"
        }), 500

@app.route('/api/connectors/postgres/tables/<connection_id>', methods=['GET'])
def get_tables(connection_id):
    """Get list of tables in the connected database"""
    connection = active_connections.get(connection_id)
    
    if not connection:
        return jsonify({
            "success": False,
            "message": "Connection not found"
        }), 404
    
    try:
        engine = connection['engine']
        inspector = inspect(engine)
        
        tables = []
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            tables.append({
                "name": table_name,
                "columns": [
                    {
                        "name": col['name'],
                        "type": str(col['type']),
                        "nullable": col['nullable']
                    } for col in columns
                ]
            })
        
        return jsonify({
            "success": True,
            "tables": tables,
            "database": connection['database']
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to get tables: {str(e)}"
        }), 500

@app.route('/api/connectors/postgres/status/<connection_id>', methods=['GET'])
def get_connection_status(connection_id):
    """Get connection status"""
    connection = active_connections.get(connection_id)
    
    if not connection:
        return jsonify({
            "success": False,
            "message": "Connection not found"
        }), 404
    
    try:
        # Test if connection is still active
        engine = connection['engine']
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return jsonify({
            "success": True,
            "status": "active",
            "connectionName": connection['name'],
            "database": connection['database'],
            "createdAt": connection['created_at'],
            "lastUsed": connection['last_used']
        })
        
    except Exception as e:
        return jsonify({
            "success": True,
            "status": "disconnected",
            "error": str(e)
        })

@app.route('/api/connectors/postgres/disconnect', methods=['POST'])
def disconnect():
    """Disconnect and cleanup connection"""
    data = request.json
    connection_id = data.get('connectionId')
    
    if not connection_id:
        return jsonify({
            "success": False,
            "message": "Missing connectionId"
        }), 400
    
    with connection_lock:
        connection = active_connections.get(connection_id)
        
        if not connection:
            return jsonify({
                "success": False,
                "message": "Connection not found"
            }), 404
        
        try:
            # Close engine
            connection['engine'].dispose()
            
            # Remove from active connections
            del active_connections[connection_id]
            
            return jsonify({
                "success": True,
                "message": "Disconnected successfully"
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Failed to disconnect: {str(e)}"
            }), 500

@app.route('/api/connectors/postgres/connections', methods=['GET'])
def list_connections():
    """List all active connections"""
    connections = []
    
    for conn_id, conn in active_connections.items():
        connections.append({
            "id": conn_id,
            "name": conn['name'],
            "database": conn['database'],
            "host": conn['host'],
            "createdAt": conn['created_at'],
            "lastUsed": conn['last_used']
        })
    
    return jsonify({
        "success": True,
        "connections": connections
    })

# Cleanup inactive connections periodically
def cleanup_inactive_connections():
    """Remove inactive connections after 30 minutes"""
    while True:
        time.sleep(300)  # Check every 5 minutes
        
        with connection_lock:
            current_time = datetime.now()
            to_remove = []
            
            for conn_id, conn in active_connections.items():
                last_used = datetime.fromisoformat(conn['last_used'])
                if (current_time - last_used).seconds > 1800:  # 30 minutes
                    try:
                        conn['engine'].dispose()
                        to_remove.append(conn_id)
                    except:
                        pass
            
            for conn_id in to_remove:
                del active_connections[conn_id]
                print(f"Cleaned up inactive connection: {conn_id}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_inactive_connections, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    app.run(debug=True, port=5000)