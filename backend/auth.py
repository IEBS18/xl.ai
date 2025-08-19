from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from dotenv import load_dotenv
import datetime
import psycopg2
from psycopg2.extras import DictCursor
import secrets
import string
from flask_mail import Mail, Message

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

# Email configuration
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = int(os.getenv('MAIL_PORT'))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'True').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_FROM = os.getenv('MAIL_FROM', MAIL_USERNAME)
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost')

# JWT Secret (for future use if needed)
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')

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

def generate_verification_code():
    """Generate a 6-digit verification code."""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def generate_reset_token():
    """Generate a secure reset token."""
    return secrets.token_urlsafe(32)

def send_email(mail_app, to_email, subject, body_html, body_text=None):
    """Send email using Flask-Mail."""
    try:
        with mail_app.app_context():
            msg = Message(
                subject=subject,
                sender=MAIL_FROM,
                recipients=[to_email]
            )
            msg.html = body_html
            if body_text:
                msg.body = body_text
            
            mail = Mail(mail_app)
            mail.send(msg)
            return True
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return False

def init_db():
    """Initialize the database tables if they don't exist."""
    logging.info("Initializing database tables...")
    
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        logging.warning("Database credentials not found. Skipping database initialization.")
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table with email verification
        logging.info("Creating users table if it doesn't exist...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_verified BOOLEAN DEFAULT FALSE,
            verification_code VARCHAR(10),
            verification_code_expires TIMESTAMP,
            signup_time TIMESTAMP NOT NULL,
            signup_ip VARCHAR(50) NOT NULL,
            remember_token VARCHAR(255),
            remember_token_expires TIMESTAMP
        )
        ''')
        
        # Create password reset tokens table
        logging.info("Creating password_reset_tokens table if it doesn't exist...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            token VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            session_id VARCHAR(50) NOT NULL,
            remember_me BOOLEAN DEFAULT FALSE
        )
        ''')
        
        conn.commit()
        logging.info("Database tables initialized successfully")
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_verification_code ON users(verification_code);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_remember_token ON users(remember_token);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON login_history(user_id);')
        conn.commit()
        
        logging.info("Database indexes created successfully")
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logging.error(f"Error initializing database: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@auth_blueprint.route('/signup', methods=['POST'])
def signup():
    """Handle user signup with email verification."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided!"}), 400

    first_name = data.get('firstName', '').strip()
    last_name = data.get('lastName', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    # Validation
    if not first_name or not last_name or not email or not password:
        return jsonify({"error": "All fields are required!"}), 400
    
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long!"}), 400
    
    if '@' not in email or '.' not in email:
        return jsonify({"error": "Please enter a valid email address!"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Check for duplicate email
        cursor.execute("SELECT id, is_verified FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            if existing_user['is_verified']:
                return jsonify({"error": "Email already exists!"}), 400
            else:
                # User exists but not verified, update their info and resend verification
                verification_code = generate_verification_code()
                verification_expires = datetime.datetime.now() + datetime.timedelta(minutes=15)
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                
                cursor.execute(
                    """UPDATE users SET 
                       first_name = %s, last_name = %s, password_hash = %s,
                       verification_code = %s, verification_code_expires = %s
                       WHERE email = %s RETURNING id""",
                    (first_name, last_name, hashed_password, verification_code, verification_expires, email)
                )
                user_id = cursor.fetchone()[0]
        else:
            # Create new user
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            ip_address = request.remote_addr or 'unknown'
            current_time = datetime.datetime.now()
            verification_code = generate_verification_code()
            verification_expires = current_time + datetime.timedelta(minutes=15)

            cursor.execute(
                """INSERT INTO users 
                   (first_name, last_name, email, password_hash, verification_code, 
                    verification_code_expires, signup_time, signup_ip) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (first_name, last_name, email, hashed_password, verification_code, 
                 verification_expires, current_time, ip_address)
            )
            user_id = cursor.fetchone()[0]

        conn.commit()

        # Send verification email
        mail_app = request.environ.get('mail_app')
        if mail_app:
            verification_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #333;">Welcome to InsiPredict!</h1>
                </div>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="color: #333; margin-top: 0;">Verify Your Email Address</h2>
                    <p>Hi {first_name},</p>
                    <p>Thank you for signing up for InsiPredict! To complete your registration, please use the verification code below:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <span style="background-color: #007bff; color: white; padding: 15px 30px; border-radius: 5px; font-size: 24px; font-weight: bold; letter-spacing: 3px;">{verification_code}</span>
                    </div>
                    <p>This code will expire in 15 minutes.</p>
                    <p>If you didn't create an account with us, please ignore this email.</p>
                </div>
                <div style="text-align: center; color: #666; font-size: 12px;">
                    <p>© 2025 InsiPredict. All rights reserved.</p>
                </div>
            </body>
            </html>
            """
            
            send_email(
                mail_app,
                email,
                "Verify Your InsiPredict Account",
                verification_html
            )

        return jsonify({
            "message": "Account created successfully! Please check your email for verification code.",
            "email": email,
            "requires_verification": True
        }), 201
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logging.error(f"Error creating user: {e}")
        return jsonify({"error": "Failed to create account. Please try again."}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@auth_blueprint.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email with verification code."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided!"}), 400
    
    email = data.get('email', '').strip().lower()
    verification_code = data.get('code', '').strip()
    
    if not email or not verification_code:
        return jsonify({"error": "Email and verification code are required!"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Find user with matching email and verification code
        cursor.execute(
            """SELECT id, first_name, last_name, verification_code_expires, is_verified
               FROM users WHERE email = %s AND verification_code = %s""",
            (email, verification_code)
        )
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"error": "Invalid verification code!"}), 400
        
        if user['is_verified']:
            return jsonify({"error": "Email already verified!"}), 400
        
        if datetime.datetime.now() > user['verification_code_expires']:
            return jsonify({"error": "Verification code has expired!"}), 400
        
        # Verify the user
        cursor.execute(
            """UPDATE users SET is_verified = TRUE, verification_code = NULL, 
               verification_code_expires = NULL WHERE email = %s""",
            (email,)
        )
        conn.commit()
        
        # Set login cookie
        response = make_response(jsonify({
            "user_insipredict_id": user['id'],
            "first_name": user['first_name'],
            "last_name": user['last_name'],
            "email": email,
            "message": "Email verified successfully!"
        }), 200)

        response.set_cookie(
            'user_insipredict_id',
            value=str(user['id']),
            max_age=60 * 60 * 24 * 7,
            samesite='Lax',
            secure=False
        )
        
        return response
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logging.error(f"Error verifying email: {e}")
        return jsonify({"error": "Failed to verify email. Please try again."}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@auth_blueprint.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification code."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided!"}), 400
    
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({"error": "Email is required!"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        cursor.execute(
            "SELECT id, first_name, is_verified FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"error": "User not found!"}), 404
        
        if user['is_verified']:
            return jsonify({"error": "Email already verified!"}), 400
        
        # Generate new verification code
        verification_code = generate_verification_code()
        verification_expires = datetime.datetime.now() + datetime.timedelta(minutes=15)
        
        cursor.execute(
            """UPDATE users SET verification_code = %s, verification_code_expires = %s 
               WHERE email = %s""",
            (verification_code, verification_expires, email)
        )
        conn.commit()
        
        # Send verification email
        mail_app = request.environ.get('mail_app')
        if mail_app:
            verification_html = f"""
            <html>
            <body style="margin: 0; padding: 0; background-color: #f4f4f4;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4;">
                    <tr>
                        <td align="center" style="padding: 40px 0;">
                            <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <!-- Header -->
                                <tr>
                                    <td align="center" style="padding: 40px 30px 30px 30px;">
                                        <h1 style="color: #333333; font-family: Arial, sans-serif; font-size: 28px; font-weight: bold; margin: 0;">InsiPredict</h1>
                                    </td>
                                </tr>
                                
                                <!-- Content -->
                                <tr>
                                    <td style="padding: 0 30px 30px 30px;">
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="background-color: #f8f9fa; padding: 30px; border-radius: 8px;">
                                                    <h2 style="color: #333333; font-family: Arial, sans-serif; font-size: 24px; font-weight: bold; margin: 0 0 20px 0;">New Verification Code</h2>
                                                    
                                                    <p style="color: #333333; font-family: Arial, sans-serif; font-size: 16px; line-height: 1.5; margin: 0 0 15px 0;">Hi {user['first_name']},</p>
                                                    
                                                    <p style="color: #333333; font-family: Arial, sans-serif; font-size: 16px; line-height: 1.5; margin: 0 0 30px 0;">Here's your new verification code:</p>
                                                    
                                                    <!-- Verification Code -->
                                                    <table width="100%" cellpadding="0" cellspacing="0">
                                                        <tr>
                                                            <td align="center" style="padding: 20px 0;">
                                                                <table cellpadding="0" cellspacing="0">
                                                                    <tr>
                                                                        <td style="background-color: #007bff; border-radius: 5px; padding: 15px 30px;">
                                                                            <span style="color: #ffffff; font-family: Arial, sans-serif; font-size: 24px; font-weight: bold; letter-spacing: 3px;">{verification_code}</span>
                                                                        </td>
                                                                    </tr>
                                                                </table>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    
                                                    <p style="color: #333333; font-family: Arial, sans-serif; font-size: 16px; line-height: 1.5; margin: 20px 0 0 0;">This code will expire in 15 minutes.</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            send_email(
                mail_app,
                email,
                "New Verification Code - InsiPredict",
                verification_html
            )
        
        return jsonify({"message": "Verification code sent successfully!"}), 200
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logging.error(f"Error resending verification: {e}")
        return jsonify({"error": "Failed to resend verification code."}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@auth_blueprint.route('/login', methods=['POST'])
def login():
    """Handle user login with email verification check."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided!"}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    remember_me = data.get('rememberMe', False)

    if not email or not password:
        return jsonify({"error": "Email and password are required!"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Get user by email
        cursor.execute(
            """SELECT id, first_name, last_name, email, password_hash, is_verified 
               FROM users WHERE email = %s""", 
            (email,)
        )
        user = cursor.fetchone()

        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({"error": "Invalid email or password!"}), 401
        
        # Check if email is verified
        if not user['is_verified']:
            return jsonify({
                "error": "Please verify your email before logging in.",
                "requires_verification": True,
                "email": email
            }), 403
        
        # Generate remember token if remember me is checked
        remember_token = None
        remember_token_expires = None
        if remember_me:
            remember_token = secrets.token_urlsafe(32)
            remember_token_expires = datetime.datetime.now() + datetime.timedelta(days=30)
            
            cursor.execute(
                """UPDATE users SET remember_token = %s, remember_token_expires = %s 
                   WHERE id = %s""",
                (remember_token, remember_token_expires, user['id'])
            )
        
        # Record login history
        ip_address = request.remote_addr or 'unknown'
        login_time = datetime.datetime.now()
        user_agent = request.headers.get('User-Agent', 'Unknown')
        session_id = secrets.token_hex(16)
        
        cursor.execute(
            """INSERT INTO login_history 
               (user_id, login_time, ip_address, user_agent, session_id, remember_me) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user['id'], login_time, ip_address, user_agent, session_id, remember_me)
        )
        conn.commit()
        
        # Create response
        response = make_response(jsonify({
            "user_insipredict_id": user['id'],
            "first_name": user['first_name'],
            "last_name": user['last_name'],
            "email": user['email'],
            "message": "Login successful!"
        }), 200)

        # Set cookies
        cookie_max_age = 60 * 60 * 24 * 30 if remember_me else 60 * 60 * 24 * 7
        
        response.set_cookie(
            'user_insipredict_id',
            value=str(user['id']),
            max_age=cookie_max_age,
            samesite='Lax',
            secure=False
        )
        
        if remember_token:
            response.set_cookie(
                'remember_token',
                value=remember_token,
                max_age=60 * 60 * 24 * 30,
                samesite='Lax',
                secure=False
            )
        
        return response
            
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logging.error(f"Error during login: {e}")
        return jsonify({"error": "Login failed. Please try again."}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@auth_blueprint.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Handle forgot password request."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided!"}), 400
    
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({"error": "Email is required!"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Check if user exists and is verified
        cursor.execute(
            "SELECT id, first_name, is_verified FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()
        
        if not user:
            # Don't reveal if email exists or not
            return jsonify({"message": "If an account exists, you will receive a password reset email."}), 200
        
        if not user['is_verified']:
            return jsonify({"error": "Please verify your email first."}), 400
        
        # Generate reset token
        reset_token = generate_reset_token()
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)
        
        # Store reset token
        cursor.execute(
            """INSERT INTO password_reset_tokens (user_id, token, expires_at) 
               VALUES (%s, %s, %s)""",
            (user['id'], reset_token, expires_at)
        )
        conn.commit()
        
        # Send reset email
        mail_app = request.environ.get('mail_app')
        if mail_app:
            # Create reset URL that opens the modal instead of a separate page
            reset_url = f"{FRONTEND_URL}?reset_token={reset_token}&action=reset_password"
            reset_html = f"""
            <html>
            <body style="margin: 0; padding: 0; background-color: #f4f4f4;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4;">
                    <tr>
                        <td align="center" style="padding: 40px 0;">
                            <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <!-- Header -->
                                <tr>
                                    <td align="center" style="padding: 40px 30px 30px 30px;">
                                        <h1 style="color: #333333; font-family: Arial, sans-serif; font-size: 28px; font-weight: bold; margin: 0;">InsiPredict</h1>
                                    </td>
                                </tr>
                                
                                <!-- Content -->
                                <tr>
                                    <td style="padding: 0 30px 30px 30px;">
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="background-color: #f8f9fa; padding: 30px; border-radius: 8px;">
                                                    <h2 style="color: #333333; font-family: Arial, sans-serif; font-size: 24px; font-weight: bold; margin: 0 0 20px 0;">Reset Your Password</h2>
                                                    
                                                    <p style="color: #333333; font-family: Arial, sans-serif; font-size: 16px; line-height: 1.5; margin: 0 0 15px 0;">Hi {user['first_name']},</p>
                                                    
                                                    <p style="color: #333333; font-family: Arial, sans-serif; font-size: 16px; line-height: 1.5; margin: 0 0 30px 0;">You requested to reset your password. Click the button below to create a new password:</p>
                                                    
                                                    <!-- Button -->
                                                    <table width="100%" cellpadding="0" cellspacing="0">
                                                        <tr>
                                                            <td align="center" style="padding: 20px 0;">
                                                                <table cellpadding="0" cellspacing="0">
                                                                    <tr>
                                                                        <td style="background-color: #007bff; border-radius: 5px;">
                                                                            <a href="{reset_url}" style="display: inline-block; padding: 15px 30px; color: #ffffff; font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; text-decoration: none;">Reset Password</a>
                                                                        </td>
                                                                    </tr>
                                                                </table>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    
                                                    <p style="color: #333333; font-family: Arial, sans-serif; font-size: 16px; line-height: 1.5; margin: 20px 0 0 0;">This link will expire in 1 hour.</p>
                                                    
                                                    <p style="color: #666666; font-family: Arial, sans-serif; font-size: 12px; margin: 30px 0 10px 0;">Or copy and paste this link in your browser:</p>
                                                    
                                                    <div style="background-color: #f1f3f4; padding: 15px; border-radius: 4px; margin: 0 0 20px 0;">
                                                        <p style="color: #007bff; font-family: Arial, sans-serif; font-size: 12px; margin: 0; word-break: break-all;">{reset_url}</p>
                                                    </div>
                                                    
                                                    <p style="color: #666666; font-family: Arial, sans-serif; font-size: 14px; line-height: 1.5; margin: 0;">If you didn't request a password reset, please ignore this email.</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            send_email(
                mail_app,
                email,
                "Reset Your Password - InsiPredict",
                reset_html
            )
        
        return jsonify({"message": "If an account exists, you will receive a password reset email."}), 200
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logging.error(f"Error in forgot password: {e}")
        return jsonify({"error": "Failed to process request. Please try again."}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# In your auth.py file, update the reset_password function to return user email:

@auth_blueprint.route('/reset-password', methods=['POST'])
def reset_password():
    """Handle password reset."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided!"}), 400
    
    token = data.get('token', '').strip()
    new_password = data.get('password', '')
    
    if not token or not new_password:
        return jsonify({"error": "Token and new password are required!"}), 400
    
    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long!"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Find valid reset token and get user email
        cursor.execute(
            """SELECT prt.user_id, u.email, u.first_name FROM password_reset_tokens prt
               JOIN users u ON prt.user_id = u.id
               WHERE prt.token = %s AND prt.expires_at > %s AND prt.used = FALSE""",
            (token, datetime.datetime.now())
        )
        reset_data = cursor.fetchone()
        
        if not reset_data:
            return jsonify({"error": "Invalid or expired reset token!"}), 400
        
        # Update password
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (hashed_password, reset_data['user_id'])
        )
        
        # Mark token as used
        cursor.execute(
            "UPDATE password_reset_tokens SET used = TRUE WHERE token = %s",
            (token,)
        )
        
        conn.commit()
        
        # Return success with user email for auto-login
        return jsonify({
            "message": "Password reset successfully!",
            "email": reset_data['email'],
            "first_name": reset_data['first_name']
        }), 200
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logging.error(f"Error resetting password: {e}")
        return jsonify({"error": "Failed to reset password. Please try again."}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@auth_blueprint.route('/logout', methods=['POST'])
def logout():
    """Handle user logout."""
    user_id = request.headers.get('user_insipredict_id')
    
    if user_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Clear remember token
            cursor.execute(
                """UPDATE users SET remember_token = NULL, remember_token_expires = NULL 
                   WHERE id = %s""",
                (user_id,)
            )
            conn.commit()
            
        except Exception as e:
            logging.error(f"Error during logout: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    response = make_response(jsonify({"message": "Logged out successfully!"}))
    response.set_cookie('user_insipredict_id', '', expires=0)
    response.set_cookie('remember_token', '', expires=0)
    return response

@auth_blueprint.route('/check_login', methods=['GET'])
def check_login():
    """Check if user is logged in via cookie or remember token."""
    user_id = request.headers.get('user_insipredict_id')
    remember_token = request.cookies.get('remember_token')
    
    if user_id:
        return jsonify({'logged_in': True}), 200
    
    if remember_token:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=DictCursor)
            
            cursor.execute(
                """SELECT id, first_name, last_name, email FROM users 
                   WHERE remember_token = %s AND remember_token_expires > %s""",
                (remember_token, datetime.datetime.now())
            )
            user = cursor.fetchone()
            
            if user:
                return jsonify({
                    'logged_in': True,
                    'user': {
                        'id': user['id'],
                        'first_name': user['first_name'],
                        'last_name': user['last_name'],
                        'email': user['email']
                    }
                }), 200
                
        except Exception as e:
            logging.error(f"Error checking remember token: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    return jsonify({'logged_in': False}), 200

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)