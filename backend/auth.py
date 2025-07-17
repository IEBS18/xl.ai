# from flask import Flask, Blueprint, request, jsonify, make_response
# from werkzeug.security import generate_password_hash, check_password_hash
# from flask_cors import CORS
# import os
# import logging
# from dotenv import load_dotenv
# import datetime
# import psycopg2
# from psycopg2.extras import DictCursor

# # Load environment variables
# load_dotenv()

# # Blueprint for Auth functionality
# auth_blueprint = Blueprint('auth', __name__)

# # Database configuration
# DB_HOST = os.getenv('DB_HOST')
# DB_NAME = os.getenv('DB_NAME')
# DB_USER = os.getenv('DB_USER')
# DB_PASSWORD = os.getenv('DB_PASSWORD')
# DB_PORT = os.getenv('DB_PORT', '5432')

# def get_db_connection():
#     """Create and return a database connection."""
#     try:
#         conn = psycopg2.connect(
#             host=DB_HOST,
#             database=DB_NAME,
#             user=DB_USER,
#             password=DB_PASSWORD,
#             port=DB_PORT
#         )
#         return conn
#     except Exception as e:
#         logging.error(f"Database connection error: {e}")
#         raise
    
# def init_db():
#     """Initialize the database tables if they don't exist."""
#     logging.info("Initializing database tables...")
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     try:
#         # Create users table
#         logging.info("Creating users table if it doesn't exist...")
#         cursor.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id SERIAL PRIMARY KEY,
#             first_name VARCHAR(100) NOT NULL,
#             last_name VARCHAR(100) NOT NULL,
#             email VARCHAR(100) UNIQUE NOT NULL,
#             password_hash VARCHAR(255) NOT NULL,
#             signup_time TIMESTAMP NOT NULL,
#             signup_ip VARCHAR(50) NOT NULL
#         )
#         ''')
        
#         # Create login_history table
#         logging.info("Creating login_history table if it doesn't exist...")
#         cursor.execute('''
#         CREATE TABLE IF NOT EXISTS login_history (
#             id SERIAL PRIMARY KEY,
#             user_id INTEGER REFERENCES users(id),
#             login_time TIMESTAMP NOT NULL,
#             ip_address VARCHAR(50) NOT NULL,
#             user_agent TEXT,
#             session_id VARCHAR(50) NOT NULL
#         )
#         ''')
        
#         conn.commit()
#         logging.info("Database tables initialized successfully")
#     except Exception as e:
#         conn.rollback()
#         logging.error(f"Error initializing database: {e}")
#         raise  # Re-raise the exception to see the full error
#     finally:
#         cursor.close()
#         conn.close()

# @auth_blueprint.route('/signup', methods=['POST'])
# def signup():
#     data = request.get_json()

#     first_name = data.get('firstName')
#     last_name = data.get('lastName')
#     email = data.get('email')
#     password = data.get('password')

#     if not first_name or not last_name or not email or not password:
#         return jsonify({"error": "All fields are required!"}), 400

#     conn = get_db_connection()
#     cursor = conn.cursor(cursor_factory=DictCursor)
    
#     try:
#         # Check for duplicate email
#         cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
#         if cursor.fetchone():
#             return jsonify({"error": "Email already exists!"}), 400

#         hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
#         ip_address = request.remote_addr
#         current_time = datetime.datetime.now()

#         # Insert new user
#         cursor.execute(
#             "INSERT INTO users (first_name, last_name, email, password_hash, signup_time, signup_ip) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
#             (first_name, last_name, email, hashed_password, current_time, ip_address)
#         )
#         user_row = cursor.fetchone()
#         if not user_row:
#             conn.rollback()
#             logging.error("Failed to fetch user ID after insert.")
#             return jsonify({"error": "Failed to create account. Please try again."}), 500
#         user_id = user_row[0]
#         conn.commit()

#         response = make_response(jsonify({
#             "user_insipredict_id": user_id,
#             "first_name": first_name,
#             "message": "Account created successfully!"
#         }), 201)

#         response.set_cookie(
#             'user_insipredict_id',
#             value=str(user_id),
#             max_age=60 * 60 * 24 * 7,  # Cookie valid for 1 week
#             samesite='Lax'
#         )
#         return response
        
#     except Exception as e:
#         conn.rollback()
#         logging.error(f"Error creating user: {e}")
#         return jsonify({"error": "Failed to create account. Please try again."}), 500
#     finally:
#         cursor.close()
#         conn.close()

# @auth_blueprint.route('/login', methods=['POST'])
# def login():
#     data = request.get_json()
#     email = data.get('email')
#     password = data.get('password')

#     conn = get_db_connection()
#     cursor = conn.cursor(cursor_factory=DictCursor)
    
#     try:
#         # Get user by email
#         cursor.execute(
#             "SELECT id, first_name, last_name, password_hash FROM users WHERE email = %s", 
#             (email,)
#         )
#         user = cursor.fetchone()

#         if user and check_password_hash(user['password_hash'], password):
#             # Get login metrics
#             ip_address = request.remote_addr
#             login_time = datetime.datetime.now()
#             user_agent = request.headers.get('User-Agent', 'Unknown')
#             session_id = os.urandom(16).hex()  # Generate a random session ID
            
#             # Record login history
#             cursor.execute(
#                 "INSERT INTO login_history (user_id, login_time, ip_address, user_agent, session_id) VALUES (%s, %s, %s, %s, %s)",
#                 (user['id'], login_time, ip_address, user_agent, session_id)
#             )
#             conn.commit()
            
#             # Successful login
#             response = make_response(jsonify({
#                 "user_insipredict_id": user['id'],
#                 "first_name": user['first_name'],
#                 "message": "Login successful!"
#             }), 200)

#             response.set_cookie(
#                 'user_insipredict_id',
#                 value=str(user['id']),
#                 max_age=60 * 60 * 24 * 7,  # Cookie valid for 1 week
#                 samesite='Lax'
#             )
#             return response
#         else:
#             # Invalid credentials
#             return jsonify({"error": "Invalid credentials!"}), 401
            
#     except Exception as e:
#         conn.rollback()
#         logging.error(f"Error during login: {e}")
#         return jsonify({"error": "Login failed. Please try again."}), 500
#     finally:
#         cursor.close()
#         conn.close()

# @auth_blueprint.route('/check_login', methods=['GET'])
# def check_login():
#     # Get user data from request headers
#     user_id = request.headers.get('user_insipredict_id')
#     first_name = request.headers.get('first_name_insipredict_user')

#     # If both user_id and first_name are found, user is logged in
#     if user_id and first_name:
#         logging.info(f"User with ID {user_id} and First Name {first_name} is logged in.")
#         return jsonify({'logged_in': True}), 200
#     else:
#         # If not, user is not logged in
#         logging.info("No user is logged in. Missing user data in request headers.")
#         return jsonify({'logged_in': True}), 400  # Return 200, indicating checked successfully
#         # return jsonify({'logged_in': False}), 400  # Return 200, indicating checked successfully

# @auth_blueprint.route('/user_info', methods=['GET'])
# def user_info():
#     user_id = request.headers.get('user_insipredict_id')
    
#     if not user_id:
#         return jsonify({"error": "Not authenticated"}), 401
    
#     conn = get_db_connection()
#     cursor = conn.cursor(cursor_factory=DictCursor)
    
#     try:
#         # Get user details
#         cursor.execute(
#             """
#             SELECT u.id, u.first_name, u.last_name, u.email, u.signup_time, u.signup_ip,
#                    lh.login_time, lh.ip_address, lh.user_agent, lh.session_id
#             FROM users u
#             LEFT JOIN (
#                 SELECT * FROM login_history
#                 WHERE user_id = %s
#                 ORDER BY login_time DESC
#                 LIMIT 1
#             ) lh ON u.id = lh.user_id
#             WHERE u.id = %s
#             """,
#             (user_id, user_id)
#         )
#         user_data = cursor.fetchone()
        
#         if not user_data:
#             return jsonify({"error": "User not found"}), 404
        
#         # Get login history
#         cursor.execute(
#             """
#             SELECT login_time, ip_address, user_agent, session_id
#             FROM login_history
#             WHERE user_id = %s
#             ORDER BY login_time DESC
#             LIMIT 10
#             """,
#             (user_id,)
#         )
#         login_history = [dict(row) for row in cursor.fetchall()]
        
#         # Format the response
#         user_info = {
#             "id": user_data['id'],
#             "first_name": user_data['first_name'],
#             "last_name": user_data['last_name'],
#             "email": user_data['email'],
#             "signup_time": user_data['signup_time'].isoformat() if user_data['signup_time'] else None,
#             "signup_ip": user_data['signup_ip'],
#             "last_login": {
#                 "login_time": user_data['login_time'].isoformat() if user_data['login_time'] else None,
#                 "ip_address": user_data['ip_address'],
#                 "user_agent": user_data['user_agent'],
#                 "session_id": user_data['session_id']
#             } if user_data['login_time'] else None,
#             "login_history": [{
#                 "login_time": item['login_time'].isoformat(),
#                 "ip_address": item['ip_address'],
#                 "user_agent": item['user_agent'],
#                 "session_id": item['session_id']
#             } for item in login_history]
#         }
        
#         return jsonify(user_info), 200
        
#     except Exception as e:
#         logging.error(f"Error retrieving user info: {e}")
#         return jsonify({"error": "Failed to retrieve user information"}), 500
#     finally:
#         cursor.close()
#         conn.close()

# # Create the Flask app instance, configure logging/CORS, and register the blueprint
# def create_app():
#     app = Flask(__name__)

#     # Configure Logging
#     log_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
#     os.makedirs(log_directory, exist_ok=True)
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s - %(levelname)s - %(message)s",
#         handlers=[
#             logging.FileHandler(os.path.join(log_directory, "app.log")),
#             logging.StreamHandler()
#         ]
#     )

#     # Set up CORS
#     CORS(
#         app,
#         supports_credentials=True,
#         origins=[
#             "http://localhost:5173",
#             "http://68.154.56.138:3000",
#             "http://localhost:5174",
#             "http://127.0.0.1:5000"
#         ]
#     )

#     # Initialize the database
#     init_db()

#     # Register Blueprint
#     app.register_blueprint(auth_blueprint)

#     return app



from flask import Flask, Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv
import datetime
import psycopg2
from psycopg2.extras import DictCursor

# Load environment variables
load_dotenv()

# Blueprint for Auth functionality
auth_blueprint = Blueprint('auth', __name__)

# Database configuration
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT', '5432')

def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        raise
    
def init_db():
    """Initialize the database tables if they don't exist."""
    logging.info("Initializing database tables...")
    
    # Check if database credentials are available
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        logging.warning("Database credentials not found. Skipping database initialization.")
        logging.warning("Auth functionality will be limited without database connection.")
        logging.warning("Please set DB_HOST, DB_NAME, DB_USER, and DB_PASSWORD in your .env file")
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        logging.info("Creating users table if it doesn't exist...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            signup_time TIMESTAMP NOT NULL,
            signup_ip VARCHAR(50) NOT NULL
        )
        ''')
        
        # Create login_history table
        logging.info("Creating login_history table if it doesn't exist...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            login_time TIMESTAMP NOT NULL,
            ip_address VARCHAR(50) NOT NULL,
            user_agent TEXT,
            session_id VARCHAR(50) NOT NULL
        )
        ''')
        
        conn.commit()
        logging.info("Database tables initialized successfully")
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON login_history(user_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_history_login_time ON login_history(login_time);')
        conn.commit()
        
        logging.info("Database indexes created successfully")
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logging.error(f"Error initializing database: {e}")
        raise  # Re-raise the exception to see the full error
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def add_cors_headers(response, origin=None):
    """Add CORS headers to response."""
    if origin is None:
        origin = request.headers.get('Origin', '*')
    response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@auth_blueprint.route('/signup', methods=['POST', 'OPTIONS'])
def signup():
    """Handle user signup with CORS support."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, user_insipredict_id, first_name_insipredict_user')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    data = request.get_json()
    
    if not data:
        response = jsonify({"error": "No data provided!"})
        return add_cors_headers(response), 400

    first_name = data.get('firstName', '').strip()
    last_name = data.get('lastName', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    # Validation
    if not first_name or not last_name or not email or not password:
        response = jsonify({"error": "All fields are required!"})
        return add_cors_headers(response), 400
    
    if len(password) < 6:
        response = jsonify({"error": "Password must be at least 6 characters long!"})
        return add_cors_headers(response), 400
    
    if '@' not in email or '.' not in email:
        response = jsonify({"error": "Please enter a valid email address!"})
        return add_cors_headers(response), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Check for duplicate email
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            response = jsonify({"error": "Email already exists!"})
            return add_cors_headers(response), 400

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        ip_address = request.remote_addr or 'unknown'
        current_time = datetime.datetime.now()

        # Insert new user
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, password_hash, signup_time, signup_ip) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (first_name, last_name, email, hashed_password, current_time, ip_address)
        )
        user_row = cursor.fetchone()
        if not user_row:
            conn.rollback()
            logging.error("Failed to fetch user ID after insert.")
            response = jsonify({"error": "Failed to create account. Please try again."})
            return add_cors_headers(response), 500
            
        user_id = user_row[0]
        conn.commit()

        response = make_response(jsonify({
            "user_insipredict_id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "message": "Account created successfully!"
        }), 201)

        # Set cookie
        response.set_cookie(
            'user_insipredict_id',
            value=str(user_id),
            max_age=60 * 60 * 24 * 7,  # Cookie valid for 1 week
            samesite='Lax',
            secure=False  # Set to True in production with HTTPS
        )
        
        return add_cors_headers(response)
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logging.error(f"Error creating user: {e}")
        response = jsonify({"error": "Failed to create account. Please try again."})
        return add_cors_headers(response), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@auth_blueprint.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """Handle user login with CORS support."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, user_insipredict_id, first_name_insipredict_user')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    data = request.get_json()
    
    if not data:
        response = jsonify({"error": "No data provided!"})
        return add_cors_headers(response), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        response = jsonify({"error": "Email and password are required!"})
        return add_cors_headers(response), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Get user by email
        cursor.execute(
            "SELECT id, first_name, last_name, email, password_hash FROM users WHERE email = %s", 
            (email,)
        )
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            # Get login metrics
            ip_address = request.remote_addr or 'unknown'
            login_time = datetime.datetime.now()
            user_agent = request.headers.get('User-Agent', 'Unknown')
            session_id = os.urandom(16).hex()  # Generate a random session ID
            
            # Record login history
            cursor.execute(
                "INSERT INTO login_history (user_id, login_time, ip_address, user_agent, session_id) VALUES (%s, %s, %s, %s, %s)",
                (user['id'], login_time, ip_address, user_agent, session_id)
            )
            conn.commit()
            
            # Successful login
            response = make_response(jsonify({
                "user_insipredict_id": user['id'],
                "first_name": user['first_name'],
                "last_name": user['last_name'],
                "email": user['email'],
                "message": "Login successful!"
            }), 200)

            # Set cookie
            response.set_cookie(
                'user_insipredict_id',
                value=str(user['id']),
                max_age=60 * 60 * 24 * 7,  # Cookie valid for 1 week
                samesite='Lax',
                secure=False  # Set to True in production with HTTPS
            )
            
            return add_cors_headers(response)
        else:
            # Invalid credentials
            response = jsonify({"error": "Invalid email or password!"})
            return add_cors_headers(response), 401
            
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logging.error(f"Error during login: {e}")
        response = jsonify({"error": "Login failed. Please try again."})
        return add_cors_headers(response), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@auth_blueprint.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    """Handle user logout with CORS support."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    response = make_response(jsonify({"message": "Logged out successfully!"}))
    
    # Clear cookies
    response.set_cookie('user_insipredict_id', '', expires=0)
    
    return add_cors_headers(response)

@auth_blueprint.route('/check_login', methods=['GET', 'OPTIONS'])
def check_login():
    """Check if user is logged in with CORS support."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, user_insipredict_id, first_name_insipredict_user')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    # Get user data from request headers
    user_id = request.headers.get('user_insipredict_id')
    first_name = request.headers.get('first_name_insipredict_user')

    response_data = {'logged_in': bool(user_id and first_name)}
    response = jsonify(response_data)
    
    if user_id and first_name:
        logging.info(f"User with ID {user_id} and First Name {first_name} is logged in.")
    else:
        logging.info("No user is logged in. Missing user data in request headers.")
    
    return add_cors_headers(response), 200

@auth_blueprint.route('/user_info', methods=['GET', 'OPTIONS'])
def user_info():
    """Get user information with CORS support."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, user_insipredict_id')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    user_id = request.headers.get('user_insipredict_id')
    
    if not user_id:
        response = jsonify({"error": "Not authenticated"})
        return add_cors_headers(response), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Get user details
        cursor.execute(
            """
            SELECT u.id, u.first_name, u.last_name, u.email, u.signup_time, u.signup_ip,
                   lh.login_time, lh.ip_address, lh.user_agent, lh.session_id
            FROM users u
            LEFT JOIN (
                SELECT * FROM login_history
                WHERE user_id = %s
                ORDER BY login_time DESC
                LIMIT 1
            ) lh ON u.id = lh.user_id
            WHERE u.id = %s
            """,
            (user_id, user_id)
        )
        user_data = cursor.fetchone()
        
        if not user_data:
            response = jsonify({"error": "User not found"})
            return add_cors_headers(response), 404
        
        # Get login history
        cursor.execute(
            """
            SELECT login_time, ip_address, user_agent, session_id
            FROM login_history
            WHERE user_id = %s
            ORDER BY login_time DESC
            LIMIT 10
            """,
            (user_id,)
        )
        login_history = [dict(row) for row in cursor.fetchall()]
        
        # Format the response
        user_info_data = {
            "id": user_data['id'],
            "first_name": user_data['first_name'],
            "last_name": user_data['last_name'],
            "email": user_data['email'],
            "signup_time": user_data['signup_time'].isoformat() if user_data['signup_time'] else None,
            "signup_ip": user_data['signup_ip'],
            "last_login": {
                "login_time": user_data['login_time'].isoformat() if user_data['login_time'] else None,
                "ip_address": user_data['ip_address'],
                "user_agent": user_data['user_agent'],
                "session_id": user_data['session_id']
            } if user_data['login_time'] else None,
            "login_history": [{
                "login_time": item['login_time'].isoformat(),
                "ip_address": item['ip_address'],
                "user_agent": item['user_agent'],
                "session_id": item['session_id']
            } for item in login_history]
        }
        
        response = jsonify(user_info_data)
        return add_cors_headers(response), 200
        
    except Exception as e:
        logging.error(f"Error retrieving user info: {e}")
        response = jsonify({"error": "Failed to retrieve user information"})
        return add_cors_headers(response), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@auth_blueprint.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint for auth service."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    response = jsonify({
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.datetime.now().isoformat()
    })
    return add_cors_headers(response), 200

# Configure logging for the auth module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)