"""
UIL Tutor AI - Flask Backend API
Main application server for handling training and evaluations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import secrets
import os
from datetime import datetime
import json
import sqlite3
import logging

# MySQL support
try:
    import mysql.connector
    from mysql.connector import errorcode
except Exception:
    mysql = None
from pathlib import Path

# ==========================================
# Initialize Flask App
# ==========================================

app = Flask(__name__)
CORS(app)

ENV_PATH = Path(__file__).resolve().parent / '.env'
load_dotenv(ENV_PATH)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('uil_tutor_api')
logger.setLevel(logging.INFO)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create uploads folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database (SQLite fallback)
DB_PATH = 'uil_tutor.db'

@app.before_request
def log_request_debug():
    logger.info("Incoming %s %s", request.method, request.path)
    if request.is_json:
        logger.info("Request JSON: %s", request.get_json(silent=True))
    elif request.form:
        logger.info("Request form: %s", dict(request.form))
    else:
        logger.info("Request args: %s", dict(request.args))

@app.after_request
def log_response_debug(response):
    logger.info("Completed %s %s with status %s", request.method, request.path, response.status_code)
    return response

# MySQL configuration
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', 'admin'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'database': os.environ.get('MYSQL_DATABASE', 'uil_tutor'),
}

# ==========================================
# Database Setup
# ==========================================

def init_db():
    """Initialize database with required tables"""
    logger.info("Starting database initialization...")
    logger.info(
        "Initializing database. MySQL target: host=%s port=%s user=%s database=%s",
        MYSQL_CONFIG['host'],
        MYSQL_CONFIG['port'],
        MYSQL_CONFIG['user'],
        MYSQL_CONFIG['database'],
    )

    # Try MySQL first
    if mysql is not None:
        sql_file = Path(__file__).resolve().parent / 'mysql_init.sql'
        if sql_file.exists():
            try:
                with sql_file.open('r', encoding='utf-8') as f:
                    sql = f.read()

                # Connect without database to ensure CREATE DATABASE runs
                cfg = MYSQL_CONFIG.copy()
                cfg_no_db = cfg.copy()
                cfg_no_db.pop('database', None)
                conn = mysql.connector.connect(**cfg_no_db)
                cursor = conn.cursor()
                logger.info("MySQL connection established successfully.")
                statements = [s.strip() for s in sql.split(';') if s.strip()]
                for stmt in statements:
                    try:
                        cursor.execute(stmt)
                    except mysql.connector.Error as e:
                        logger.warning("MySQL statement warning: %s", e)

                conn.commit()
                cursor.close()
                conn.close()
                logger.info("Database connection successful using MySQL.")
                logger.info("MySQL schema applied (if not already present).")
                return
            except Exception as e:
                logger.warning("MySQL initialization failed: %s. Falling back to SQLite.", e)
        else:
            logger.warning("MySQL init SQL not found: %s", sql_file)
    else:
        logger.warning("mysql-connector not installed. Falling back to SQLite.")

    # SQLite fallback
    logger.info("Using SQLite database at %s", DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Evaluations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            correct_answers INTEGER,
            wrong_answers INTEGER,
            total_questions INTEGER,
            accuracy REAL,
            focus_areas TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')
    
    # Training data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_type TEXT,
            status TEXT DEFAULT 'processing'
        )
    ''')

    # Users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database connection successful using SQLite.")
    logger.info("SQLite tables initialized successfully.")

# Initialize database automatically when the backend starts
try:
    init_db()
    logger.info("Database initialization completed successfully.")
except Exception as exc:
    logger.error("Database startup initialization failed: %s", exc)

# ==========================================
# Utility Functions
# ==========================================

def _convert_placeholders_for_mysql(query):
    """Convert SQLite ? placeholders to MySQL %s placeholders."""
    result = []
    in_single_quote = False
    in_double_quote = False
    escaped = False

    for char in query:
        if char == "'" and not in_double_quote and not escaped:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote and not escaped:
            in_double_quote = not in_double_quote

        if char == '?' and not in_single_quote and not in_double_quote:
            result.append('%s')
        else:
            result.append(char)

        escaped = (char == '\\' and not escaped)

    return ''.join(result)

def db_execute(cursor, query, params=None):
    """Execute a SQL statement using the correct placeholder style."""

    if params is None:
        params = ()

    print(f"Original query : {query}")
    print(f"Cursor type    : {type(cursor)}")

    # Detect mysql.connector
    if cursor.__class__.__module__.startswith("mysql.connector"):
        query = _convert_placeholders_for_mysql(query)
        print(f"MySQL query    : {query}")

    print(f"Parameters     : {params}")

    return cursor.execute(query, params)



def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    """Get database connection - tries MySQL first, falls back to SQLite"""
    # Try MySQL first
    if mysql is not None:
        try:
            cfg = MYSQL_CONFIG.copy()
            conn = mysql.connector.connect(**cfg)
            logger.info(
                "Database connection established using MySQL: host=%s port=%s user=%s database=%s",
                MYSQL_CONFIG['host'],
                MYSQL_CONFIG['port'],
                MYSQL_CONFIG['user'],
                MYSQL_CONFIG['database'],
            )
            return conn
        except Exception as e:
            logger.warning("MySQL connection failed: %s. Falling back to SQLite.", e)
    else:
        logger.warning("mysql-connector not installed; using SQLite database at %s", DB_PATH)

    # SQLite fallback
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    logger.info("Database connection established using SQLite: %s", DB_PATH)
    return conn

def calculate_accuracy(correct, total):
    """Calculate accuracy percentage"""
    if total == 0:
        return 0
    return round((correct / total) * 100, 2)

def analyze_weak_areas(correct, total):
    """Analyze and return weak areas based on performance"""
    accuracy = calculate_accuracy(correct, total)
    weak_areas = []
    
    # Mock analysis - in production, this would use ML models
    if accuracy < 80:
        weak_areas = [
            "Roman numbers - Practice conversion between Roman and Arabic numerals",
            "Square Roots - Focus on mental calculation techniques for perfect squares",
            "Volume unit conversions - Review metric and imperial volume relationships"
        ]
    elif accuracy < 90:
        weak_areas = [
            "Decimal operations - Practice precise calculations",
            "Fraction simplification - Work on reducing fractions to lowest terms"
        ]
    else:
        weak_areas = [
            "Continue practicing to maintain high performance",
            "Try advanced problem sets for further improvement"
        ]
    
    return weak_areas

# ==========================================
# API Routes
# ==========================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'UIL Tutor AI API'
    }), 200


@app.route('/api/swagger.json', methods=['GET'])
def swagger_json():
    """Return a minimal OpenAPI spec describing the main endpoints."""
    spec = {
        'openapi': '3.0.0',
        'info': {
            'title': 'UIL Tutor AI API',
            'version': '1.0.0',
            'description': 'API for training, evaluation and user authentication'
        },
        'servers': [
            {'url': request.host_url.rstrip('/') + '/api'}
        ],
        'paths': {
            '/health': {
                'get': {
                    'summary': 'Health check',
                    'responses': {'200': {'description': 'OK'}}
                }
            },
            '/register': {
                'post': {
                    'summary': 'Register a new user',
                    'requestBody': {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'username': {'type': 'string'},
                                        'password': {'type': 'string'},
                                        'email': {'type': 'string'}
                                    },
                                    'required': ['username','password']
                                }
                            }
                        }
                    },
                    'responses': {
                        '201': {'description': 'Created'},
                        '400': {'description': 'Bad Request'}
                    }
                }
            },
            '/login': {
                'post': {
                    'summary': 'Login user',
                    'requestBody': {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'username': {'type': 'string'},
                                        'password': {'type': 'string'}
                                    },
                                    'required': ['username','password']
                                }
                            }
                        }
                    },
                    'responses': {'200': {'description': 'OK'}, '401': {'description': 'Unauthorized'}}
                }
            },
            '/train': {
                'post': {
                    'summary': 'Upload training data (files)',
                    'responses': {'200': {'description': 'Uploaded'}, '400': {'description': 'Bad Request'}}
                }
            },
            '/evaluate': {
                'post': {
                    'summary': 'Evaluate student answers (multipart form)',
                    'responses': {'200': {'description': 'Evaluation result'}, '400': {'description': 'Bad Request'}}
                }
            },
            '/student/{student_id}/history': {
                'get': {
                    'summary': 'Get student evaluation history',
                    'parameters': [{
                        'name': 'student_id', 'in': 'path', 'required': True, 'schema': {'type': 'string'}
                    }],
                    'responses': {'200': {'description': 'History'}}
                }
            },
            '/student/{student_id}/stats': {
                'get': {
                    'summary': 'Get student stats',
                    'parameters': [{
                        'name': 'student_id', 'in': 'path', 'required': True, 'schema': {'type': 'string'}
                    }],
                    'responses': {'200': {'description': 'Stats'}}
                }
            },
            '/students': {
                'get': {
                    'summary': 'List all students',
                    'responses': {'200': {'description': 'List'}}
                }
            },
            '/training/status': {
                'get': {
                    'summary': 'List recent training uploads',
                    'responses': {'200': {'description': 'List'}}
                }
            }
        }
    }

    # Return spec
    return jsonify(spec)


@app.route('/api/docs', methods=['GET'])
def swagger_ui():
    """Serve a minimal Swagger UI that loads /api/swagger.json"""
    # Use the official swagger-ui CDN
    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>UIL Tutor AI API Docs</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.18.0/swagger-ui.css" />
      </head>
      <body>
        <div id="swagger-ui"></div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.18.0/swagger-ui-bundle.js"></script>
        <script>
          window.onload = function() {{
            const ui = SwaggerUIBundle({{
              url: '{request.host_url.rstrip('/')}/api/swagger.json',
              dom_id: '#swagger-ui',
              presets: [SwaggerUIBundle.presets.apis],
              layout: 'BaseLayout'
            }});
          }}
        </script>
      </body>
    </html>
    """

    return html, 200, {'Content-Type': 'text/html'}


@app.route('/api/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Stores user data in the 'users' table (see schema.sql for full schema).
    
    Request body (JSON):
    {
        "username": "string (required, unique)",
        "password": "string (required, will be hashed)",
        "email": "string (optional, unique)"
    }
    
    Database fields populated:
    - username: TEXT UNIQUE NOT NULL
    - email: TEXT UNIQUE
    - password_hash: TEXT NOT NULL (hashed using generate_password_hash)
    - token: TEXT (set to NULL on registration, populated on login)
    - created_at: TIMESTAMP (auto-set to current time)
    
    Response: 201 Created or 400 Bad Request or 500 Server Error
    """
    try:
        # Parse JSON request body
        data = request.get_json() or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        email = (data.get('email') or '').strip() or None

        # Validate required fields
        if not username or not password:
            return jsonify({'error': 'username and password are required'}), 400

        conn = get_db()
        print("Database connection established for registration.",conn)
        cursor = conn.cursor()

        # Check if username already exists (UNIQUE constraint)
        print("Checking if username exists in database for registration 111.",cursor)
        db_execute(cursor, 'SELECT id FROM users WHERE username = ?', (username,))
        print("Checking if username exists in database for registration.",cursor)
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'username already exists'}), 400

        if email:
            db_execute(cursor, 'SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'email already exists'}), 400

        # Hash password before storing
        password_hash = generate_password_hash(password)
        
        # INSERT into users table: username, email, password_hash
        # (token and created_at are handled by database defaults)
        logger.info("Inserting new user into database: username=%s, email=%s", username, email)
        db_execute(cursor,
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        logger.info("User %s registered successfully", username)
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'User registered successfully'}), 201

    except Exception as e:
        error_message = str(e)
        logger.error("Registration failed: %s", error_message)
        if 'UNIQUE constraint failed: users.email' in error_message:
            return jsonify({'error': 'email already exists'}), 400
        if 'UNIQUE constraint failed: users.username' in error_message:
            return jsonify({'error': 'username already exists'}), 400
        if 'database is locked' in error_message.lower():
            logger.error("Database lock detected during registration")
            return jsonify({'error': 'database is locked'}), 500
        return jsonify({'error': error_message}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """Login user. Expects JSON: username, password. Returns a session token."""
    try:
        data = request.get_json() or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()

        if not username or not password:
            return jsonify({'error': 'username and password are required'}), 400

        conn = get_db()
        cursor = conn.cursor()
        db_execute(cursor, 'SELECT id, password_hash FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401

        user_id = row[0]
        pw_hash = row[1]

        if not check_password_hash(pw_hash, password):
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401

        # Generate a simple token and store it (stateless JWTs could be used instead)
        token = secrets.token_hex(32)
        db_execute(cursor, 'UPDATE users SET token = ? WHERE id = ?', (token, user_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'token': token}), 200

    except Exception as e:
        error_message = str(e)
        logger.error("Login failed: %s", error_message)
        if 'database is locked' in error_message.lower():
            logger.error("Database lock detected during login")
            return jsonify({'error': 'database is locked'}), 500
        return jsonify({'error': error_message}), 500

@app.route('/api/train', methods=['POST'])
def train_model():
    """
    Handle training data upload
    Expects: questions file and answer key file
    """
    try:
        # Check if files are in request
        if 'questions' not in request.files or 'answers' not in request.files:
            return jsonify({'error': 'Missing required files'}), 400
        
        questions_file = request.files['questions']
        answers_file = request.files['answers']
        
        # Validate files
        if questions_file.filename == '' or answers_file.filename == '':
            return jsonify({'error': 'No selected files'}), 400
        
        if not (allowed_file(questions_file.filename) and allowed_file(answers_file.filename)):
            return jsonify({'error': 'Invalid file type. Only PDF and images allowed.'}), 400
        
        # Save files
        questions_filename = secure_filename(f"questions_{datetime.now().timestamp()}_{questions_file.filename}")
        answers_filename = secure_filename(f"answers_{datetime.now().timestamp()}_{answers_file.filename}")
        
        questions_path = os.path.join(app.config['UPLOAD_FOLDER'], questions_filename)
        answers_path = os.path.join(app.config['UPLOAD_FOLDER'], answers_filename)
        
        questions_file.save(questions_path)
        answers_file.save(answers_path)
        
        # Record in database
        conn = get_db()
        cursor = conn.cursor()
        
        db_execute(cursor, '''
            INSERT INTO training_data (filename, file_type, status)
            VALUES (?, ?, ?)
        ''', (questions_filename, 'questions', 'processing'))
        
        db_execute(cursor, '''
            INSERT INTO training_data (filename, file_type, status)
            VALUES (?, ?, ?)
        ''', (answers_filename, 'answers', 'processing'))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Training data uploaded successfully',
            'questions_file': questions_filename,
            'answers_file': answers_filename,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluate', methods=['POST'])
def evaluate_student():
    """
    Handle student evaluation
    Expects: student_id and answer sheet file
    """
    try:
        # Validate request
        if 'student_id' not in request.form or 'answers' not in request.files:
            return jsonify({'error': 'Missing required fields'}), 400
        
        student_id = request.form['student_id'].strip()
        answers_file = request.files['answers']
        
        if not student_id:
            return jsonify({'error': 'Student ID cannot be empty'}), 400
        
        if answers_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(answers_file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save answer sheet
        filename = secure_filename(f"answers_{student_id}_{datetime.now().timestamp()}_{answers_file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        answers_file.save(filepath)
        
        # Mock evaluation logic - in production, use ML model
        # This would analyze the student's answers against training data
        total_questions = 50  # Example
        correct_answers = 47  # Mock result
        wrong_answers = total_questions - correct_answers
        
        accuracy = calculate_accuracy(correct_answers, total_questions)
        weak_areas = analyze_weak_areas(correct_answers, total_questions)
        
        # Store in database
        conn = get_db()
        cursor = conn.cursor()
        
        # Create or get student
        db_execute(cursor, 'SELECT * FROM students WHERE student_id = ?', (student_id,))
        student = cursor.fetchone()
        
        if not student:
            db_execute(cursor, 'INSERT INTO students (student_id) VALUES (?)', (student_id,))
        
        # Record evaluation
        db_execute(cursor, '''
            INSERT INTO evaluations 
            (student_id, correct_answers, wrong_answers, total_questions, accuracy, focus_areas)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, correct_answers, wrong_answers, total_questions, accuracy, json.dumps(weak_areas)))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'correct': correct_answers,
            'wrong': wrong_answers,
            'total': total_questions,
            'accuracy': accuracy,
            'focus_areas': weak_areas,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/student/<student_id>/history', methods=['GET'])
def get_student_history(student_id):
    """Get evaluation history for a student"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        db_execute(cursor, '''
            SELECT correct_answers, wrong_answers, accuracy, created_at
            FROM evaluations
            WHERE student_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (student_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return jsonify({'history': [], 'message': 'No evaluations found'}), 200
        
        history = []
        for row in rows:
            history.append({
                'correct': row[0],
                'wrong': row[1],
                'accuracy': row[2],
                'date': row[3]
            })
        
        return jsonify({'history': history}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/student/<student_id>/stats', methods=['GET'])
def get_student_stats(student_id):
    """Get overall statistics for a student"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        db_execute(cursor, '''
            SELECT 
                COUNT(*) as tests_taken,
                AVG(correct_answers) as avg_correct,
                AVG(wrong_answers) as avg_wrong,
                AVG(accuracy) as avg_accuracy,
                MAX(accuracy) as best_accuracy
            FROM evaluations
            WHERE student_id = ?
        ''', (student_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or result[0] == 0:
            return jsonify({
                'tests_taken': 0,
                'avg_correct': 0,
                'avg_wrong': 0,
                'avg_accuracy': 0,
                'best_accuracy': 0
            }), 200
        
        return jsonify({
            'tests_taken': int(result[0]),
            'avg_correct': round(result[1] or 0, 2),
            'avg_wrong': round(result[2] or 0, 2),
            'avg_accuracy': round(result[3] or 0, 2),
            'best_accuracy': round(result[4] or 0, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_all_students():
    """Get list of all students"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        db_execute(cursor, '''
            SELECT student_id, COUNT(id) as eval_count, MAX(created_at) as last_eval
            FROM students s
            LEFT JOIN evaluations e ON s.student_id = e.student_id
            GROUP BY s.student_id
            ORDER BY last_eval DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        students = []
        for row in rows:
            students.append({
                'student_id': row[0],
                'evaluation_count': int(row[1]) if row[1] else 0,
                'last_evaluation': row[2]
            })
        
        return jsonify({'students': students}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/training/status', methods=['GET'])
def training_status():
    """Get status of training data uploads"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        db_execute(cursor, '''
            SELECT filename, file_type, status, upload_date
            FROM training_data
            ORDER BY upload_date DESC
            LIMIT 20
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        training_data = []
        for row in rows:
            training_data.append({
                'filename': row[0],
                'type': row[1],
                'status': row[2],
                'upload_date': row[3]
            })
        
        return jsonify({'training_data': training_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# ==========================================
# Application Entry Point
# ==========================================

if __name__ == '__main__':
    logger.info("Starting UIL Tutor AI backend server...")
    
    # Run the application
    print("=" * 50)
    print("UIL Tutor AI - Backend API Server")
    print("=" * 50)
    print("API running on: http://localhost:5000")
    print("API Documentation available at: /api/docs")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )
