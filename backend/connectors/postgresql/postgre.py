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
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
import threading
import time
import logging
import traceback

load_dotenv()

app = Flask(__name__)
allowed_origins = [
    "http://localhost:5173", 
    "http://localhost", 
    "http://127.0.0.1:5173",
    "https://preview--data-scope-ai-lens.lovable.app",
    "https://*.lovable.app",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://20.197.12.172",
    "https://insipredict.ai",
    "https://www.insipredict.ai"
]
# Fix CORS to allow all common development origins
CORS(app, 
     origins=allowed_origins,  # Allow all origins in development
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Generate or load encryption key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    logger.warning("No ENCRYPTION_KEY found in environment, generating new key")
    # Save the generated key for reference
    print(f"Generated ENCRYPTION_KEY: {ENCRYPTION_KEY}")
    print("Add this to your .env file to persist: ENCRYPTION_KEY=" + ENCRYPTION_KEY)

cipher = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

# Store active connections in memory (use Redis in production)
active_connections = {}
connection_lock = threading.Lock()

# Azure OpenAI Configuration
def get_azure_config():
    """Extract Azure OpenAI configuration from environment variables"""
    # Fix: Check for both AZURE_API and AZURE_API_KEY
    azure_api_key = os.getenv("AZURE_API_KEY") or os.getenv("AZURE_API")
    azure_base_url = os.getenv("AZURE_BASE_URL")
    
    if not azure_base_url:
        logger.error("AZURE_BASE_URL not found in environment")
        return None
    
    if not azure_api_key:
        logger.error("AZURE_API_KEY (or AZURE_API) not found in environment")
        return None
    
    # Clean up the base URL to get the endpoint
    if "/openai/deployments/" in azure_base_url:
        azure_endpoint = azure_base_url.split("/openai/deployments/")[0]
        deployment_name = azure_base_url.split("/openai/deployments/")[1].split("/")[0]
    else:
        azure_endpoint = azure_base_url.rstrip("/")
        deployment_name = "pharmaX"
    
    config = {
        "endpoint": azure_endpoint,
        "deployment": deployment_name,
        "api_key": azure_api_key,
        "api_version": os.getenv("AZURE_API_VERSION", "2024-08-01-preview"),
        "model": os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-mini")
    }
    
    logger.info(f"Azure config loaded - Endpoint: {config['endpoint']}, Deployment: {config['deployment']}")
    return config

def initialize_llm():
    """Initialize Azure OpenAI LLM"""
    try:
        config = get_azure_config()
        
        if not config:
            logger.error("Failed to get Azure configuration")
            return None
        
        llm = AzureOpenAI(
            deployment_name=config["deployment"],
            model=config["model"],
            api_key=config["api_key"],
            azure_endpoint=config["endpoint"],
            api_version=config["api_version"],
            temperature=0,
            max_tokens=1000
        )
        
        # Test the LLM connection
        try:
            test_response = llm.complete("Say 'Hello'")
            logger.info(f"LLM test successful: {test_response.text.strip()}")
        except Exception as e:
            logger.error(f"LLM test failed: {str(e)}")
            # Try alternative initialization
            os.environ["AZURE_OPENAI_API_KEY"] = config["api_key"]
            os.environ["AZURE_OPENAI_ENDPOINT"] = config["endpoint"]
            os.environ["OPENAI_API_VERSION"] = config["api_version"]
            
            llm = AzureOpenAI(
                deployment_name=config["deployment"],
                model=config["model"],
                temperature=0,
                max_tokens=1000
            )
        
        # Initialize embeddings
        embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        # Configure Settings
        Settings.llm = llm
        Settings.embed_model = embed_model
        
        logger.info("LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {str(e)}")
        logger.error(traceback.format_exc())
        return None

# Initialize LLM on startup
llm = initialize_llm()
if not llm:
    logger.warning("Running without LLM - natural language queries will not be available")

def encrypt_password(password):
    """Encrypt password for storage"""
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    """Decrypt stored password"""
    return cipher.decrypt(encrypted_password.encode()).decode()

def test_postgres_connection(host, port, user, password, database=None):
    """Test PostgreSQL connection with better error handling"""
    try:
        conn_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "connect_timeout": 10
        }
        
        if database:
            conn_params["database"] = database
        else:
            # Connect to default postgres database to list all databases
            conn_params["database"] = "postgres"
        
        conn = psycopg2.connect(**conn_params)
        conn.close()
        return True, "Connection successful"
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg:
            return False, "Invalid username or password"
        elif "could not connect to server" in error_msg:
            return False, "Cannot connect to server. Please check host and port."
        elif "database" in error_msg and "does not exist" in error_msg:
            return False, "Database does not exist"
        else:
            return False, f"Connection error: {error_msg}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def get_databases_list(host, port, user, password):
    """Get list of all databases on the server"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres",
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT datname 
            FROM pg_database 
            WHERE datistemplate = false 
            AND datname NOT IN ('postgres')
            ORDER BY datname;
        """)
        
        databases = [row[0] for row in cursor.fetchall()]
        
        # Include postgres database as well if user wants to connect to it
        databases.insert(0, 'postgres')
        
        cursor.close()
        conn.close()
        
        return databases
    except Exception as e:
        logger.error(f"Failed to list databases: {str(e)}")
        raise Exception(f"Failed to list databases: {str(e)}")

# Add OPTIONS handler for CORS preflight
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        return response

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "llm_status": "active" if llm else "not configured",
        "active_connections": len(active_connections)
    })

@app.route('/api/connectors/postgres/test', methods=['POST', 'OPTIONS'])
def test_connection():
    """Test PostgreSQL server connection and list databases"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        data = request.json
        
        host = data.get('host', '').strip()
        port = data.get('port', 5432)
        user = data.get('user', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not all([host, port, user, password]):
            return jsonify({
                "success": False,
                "message": "Missing required connection parameters"
            }), 400
        
        # Validate port
        try:
            port = int(port)
            if port < 1 or port > 65535:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Invalid port number"
            }), 400
        
        logger.info(f"Testing connection to {host}:{port} as user {user}")
        
        # Test connection
        success, message = test_postgres_connection(host, port, user, password)
        
        if not success:
            logger.error(f"Connection test failed: {message}")
            return jsonify({
                "success": False,
                "message": message
            }), 400
        
        # Get list of databases
        databases = get_databases_list(host, port, user, password)
        
        logger.info(f"Connection successful, found {len(databases)} databases")
        
        return jsonify({
            "success": True,
            "message": "Connection successful",
            "databases": databases
        })
        
    except Exception as e:
        logger.error(f"Test connection error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/connectors/postgres/connect', methods=['POST', 'OPTIONS'])
def connect_to_database():
    """Connect to a specific database and set up query engine"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        data = request.json
        
        connection_name = data.get('connectionName', '').strip()
        host = data.get('host', '').strip()
        port = data.get('port', 5432)
        user = data.get('user', '').strip()
        password = data.get('password', '')
        database = data.get('database', '').strip()
        ssl_mode = data.get('ssl', False)
        
        # Validate input
        if not all([connection_name, host, port, user, password, database]):
            return jsonify({
                "success": False,
                "message": "Missing required parameters"
            }), 400
        
        # Validate port
        try:
            port = int(port)
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Invalid port number"
            }), 400
        
        logger.info(f"Connecting to database {database} at {host}:{port}")
        
        # Build connection string
        password_encoded = urllib.parse.quote_plus(password)
        ssl_param = "?sslmode=require" if ssl_mode else "?sslmode=prefer"
        connection_string = (
            f"postgresql://{user}:{password_encoded}@"
            f"{host}:{port}/{database}{ssl_param}"
        )
        
        # Create engine with connection pool
        engine = create_engine(
            connection_string,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Get table information
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
                        "nullable": col.get('nullable', True)
                    } for col in columns
                ],
                "expanded": False
            })
        
        # Create SQL database instance
        sql_database = SQLDatabase(engine)
        
        query_engine = None
        if llm:
            try:
                # Create query engine
                query_engine = NLSQLTableQueryEngine(
                    sql_database=sql_database,
                    llm=llm,
                    verbose=True
                )
                logger.info("Query engine created successfully")
            except Exception as e:
                logger.warning(f"Failed to create query engine: {str(e)}")
                query_engine = None
        else:
            logger.warning("LLM not available, query engine not created")
        
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
        
        logger.info(f"New connection established: {connection_id} - {database}")
        
        return jsonify({
            "success": True,
            "message": f"Connected to database '{database}' successfully",
            "connectionId": connection_id,
            "connectionName": connection_name,
            "database": database,
            "tables": tables,
            "tableCount": len(tables),
            "queryEngineEnabled": query_engine is not None
        })
        
    except Exception as e:
        logger.error(f"Connect to database error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Failed to connect: {str(e)}"
        }), 500

@app.route('/api/connectors/postgres/query', methods=['POST', 'OPTIONS'])
def query_database():
    """Execute natural language query on connected database"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
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
        
        # Update last used timestamp
        connection['last_used'] = datetime.now().isoformat()
        
        # Check if query engine is available
        if not connection.get('query_engine'):
            # Fallback: try to execute as SQL if it looks like SQL
            if any(keyword in query.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP']):
                logger.info("No query engine available, attempting direct SQL execution")
                return execute_sql_internal(connection_id, query)
            
            return jsonify({
                "success": False,
                "message": "Natural language query is not available. LLM not configured. Please write SQL queries directly."
            }), 503
        
        logger.info(f"Executing natural language query: {query}")
        
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
        logger.error(f"Query error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Query failed: {str(e)}"
        }), 500

def execute_sql_internal(connection_id, sql_query):
    """Internal function to execute SQL"""
    connection = active_connections.get(connection_id)
    if not connection:
        return jsonify({
            "success": False,
            "message": "Connection not found"
        }), 404
    
    engine = connection['engine']
    
    with engine.connect() as conn:
        result = conn.execute(text(sql_query))
        
        if result.returns_rows:
            rows = []
            for row in result:
                row_dict = {}
                for key, value in row._mapping.items():
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                    elif value is None:
                        row_dict[key] = None
                    else:
                        row_dict[key] = str(value) if not isinstance(value, (str, int, float, bool)) else value
                rows.append(row_dict)
            
            return jsonify({
                "success": True,
                "result": f"Query returned {len(rows)} rows",
                "rows": rows,
                "rowCount": len(rows),
                "database": connection['database']
            })
        else:
            conn.commit()
            return jsonify({
                "success": True,
                "result": f"Query executed successfully. {result.rowcount} rows affected.",
                "rowCount": result.rowcount,
                "database": connection['database']
            })

@app.route('/api/connectors/postgres/execute', methods=['POST', 'OPTIONS'])
def execute_sql():
    """Execute raw SQL query"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        data = request.json
        connection_id = data.get('connectionId')
        sql_query = data.get('sql')
        
        if not connection_id or not sql_query:
            return jsonify({
                "success": False,
                "message": "Missing connectionId or SQL query"
            }), 400
        
        return execute_sql_internal(connection_id, sql_query)
        
    except Exception as e:
        logger.error(f"SQL execution error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"SQL execution failed: {str(e)}"
        }), 500

@app.route('/api/connectors/postgres/tables/<connection_id>', methods=['GET', 'OPTIONS'])
def get_tables(connection_id):
    """Get list of tables in the connected database"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        connection = active_connections.get(connection_id)
        
        if not connection:
            return jsonify({
                "success": False,
                "message": "Connection not found"
            }), 404
        
        # Update last used timestamp
        connection['last_used'] = datetime.now().isoformat()
        
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
                        "nullable": col.get('nullable', True)
                    } for col in columns
                ],
                "expanded": False
            })
        
        return jsonify({
            "success": True,
            "tables": tables,
            "database": connection['database']
        })
        
    except Exception as e:
        logger.error(f"Get tables error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to get tables: {str(e)}"
        }), 500

@app.route('/api/connectors/postgres/status/<connection_id>', methods=['GET', 'OPTIONS'])
def get_connection_status(connection_id):
    """Get connection status"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        connection = active_connections.get(connection_id)
        
        if not connection:
            return jsonify({
                "success": False,
                "status": "disconnected",
                "message": "Connection not found"
            }), 404
        
        # Test if connection is still active
        try:
            engine = connection['engine']
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            status = "active"
        except Exception:
            status = "disconnected"
        
        return jsonify({
            "success": True,
            "status": status,
            "connectionName": connection['name'],
            "database": connection['database'],
            "createdAt": connection['created_at'],
            "lastUsed": connection['last_used']
        })
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({
            "success": False,
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/connectors/postgres/disconnect', methods=['POST', 'OPTIONS'])
def disconnect():
    """Disconnect and cleanup connection"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
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
            
            # Close engine
            try:
                connection['engine'].dispose()
            except Exception as e:
                logger.warning(f"Error disposing engine: {str(e)}")
            
            # Remove from active connections
            del active_connections[connection_id]
            
            logger.info(f"Connection disconnected: {connection_id}")
            
            return jsonify({
                "success": True,
                "message": "Disconnected successfully"
            })
            
    except Exception as e:
        logger.error(f"Disconnect error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to disconnect: {str(e)}"
        }), 500

@app.route('/api/connectors/postgres/connections', methods=['GET', 'OPTIONS'])
def list_connections():
    """List all active connections"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
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
            "connections": connections,
            "count": len(connections)
        })
    except Exception as e:
        logger.error(f"List connections error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# Cleanup inactive connections periodically
def cleanup_inactive_connections():
    """Remove inactive connections after 30 minutes"""
    while True:
        try:
            time.sleep(300)  # Check every 5 minutes
            
            with connection_lock:
                current_time = datetime.now()
                to_remove = []
                
                for conn_id, conn in active_connections.items():
                    last_used = datetime.fromisoformat(conn['last_used'])
                    if (current_time - last_used) > timedelta(minutes=30):
                        try:
                            conn['engine'].dispose()
                            to_remove.append(conn_id)
                            logger.info(f"Cleaning up inactive connection: {conn_id}")
                        except Exception as e:
                            logger.warning(f"Error cleaning up connection {conn_id}: {str(e)}")
                
                for conn_id in to_remove:
                    del active_connections[conn_id]
                    
        except Exception as e:
            logger.error(f"Cleanup thread error: {str(e)}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_inactive_connections, daemon=True)
cleanup_thread.start()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "success": False,
        "message": "Internal server error"
    }), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("PostgreSQL Connector Server Starting")
    print("="*50)
    print(f"LLM Status: {'Configured ✓' if llm else 'Not configured ✗'}")
    print(f"CORS: Enabled for all origins (development mode)")
    print(f"Server: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000, threaded=True, host='127.0.0.1')