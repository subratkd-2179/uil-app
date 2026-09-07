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
import base64
from io import BytesIO
from datetime import datetime
import json
import sqlite3
import logging

try:
    import requests
except Exception:
    requests = None

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
print(f"Loading environment variables from {ENV_PATH}")
load_dotenv(ENV_PATH, override=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('uil_tutor_api')
logger.setLevel(logging.INFO)

for key in ('CHATGPT_API_KEY', 'OPENAI_API_KEY'):
    value = os.environ.get(key)
    if value:
        logger.info('Loaded %s from environment.', key)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS.update({
    'bmp', 'dib', 'gif', 'ico', 'jif', 'jfif', 'jpe', 'tif', 'tiff', 'webp'
})
MAX_AI_PDF_PAGES = int(os.environ.get('MAX_AI_PDF_PAGES', '50'))

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create uploads folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database (SQLite fallback)
DB_PATH = os.environ.get('DATABASE_FILE', 'uil_tutor.db')

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

def db_execute(cursor, query, params=None):
    """
    Execute SQL using the correct placeholder style.

    SQLite uses:
        ?

    MySQL Connector uses:
        %s
    """

    params = params or ()

    # Detect whether this is a MySQL cursor
    cursor_module = cursor.__class__.__module__.lower()

    if "mysql" in cursor_module:
        query = query.replace("?", "%s")

    cursor.execute(query, params)

    return cursor


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


CHATGPT_PROMPT = """
You are the evaluation engine for a UIL academic competition tutoring system. I have attached a student answer sheet containing the questions, the student's responses, and the teacher's marks/comments.

Review the entire sheet carefully before judging anything. Use the teacher's evaluation as your main reference point, then independently compare each student answer to its corresponding question. For every question, determine whether the answer is correct, partially correct, or incorrect, and identify specific mistakes, missing information, weak reasoning, or unclear responses. Where relevant, suggest improvements in a constructive way.

Base your evaluation strictly on what is present in the sheet. Do not invent information, scores, or content that isn't there. Keep the tone respectful, encouraging, and constructive throughout.

Keep `student_answer_summary` to at most 8 words, `feedback` to at most 16 words, and each `missing_points` item to at most 8 words. Include no more than two missing points per question. This keeps a full multi-question evaluation within the response limit.

Return ONLY valid JSON, with no markdown fences, code blocks, or extra text before or after it. The output must match this exact structure:

```
{
  "total_questions": 0,
  "correct_answers": 0,
  "wrong_answers": 0,
    "accuracy": 0,
  "focus_areas": [],
  "missed_questions": [],
  "unclear_questions": [],
  "summary": "",
  "question_details": [
    {
      "question_number": 1,
      "teacher_score": "",
      "student_answer_summary": "",
      "status": "correct",
      "feedback": "",
      "missing_points": []
    }
  ]
}
```

Follow these rules exactly:
- `total_questions` must equal the total number of questions found on the sheet.
- `correct_answers`, `wrong_answers`, and `accuracy` must be internally consistent with each other and with `question_details`.
- `accuracy` must be calculated as (correct_answers / total_questions) * 100, rounded to two decimal places.
- `missed_questions` must list the numbers of questions the student got wrong or left unanswered.
- `unclear_questions` must list the numbers of questions that are unreadable or ambiguous on the sheet.
- `focus_areas` must list the main topics or skills the student needs to improve, based on patterns across the wrong or weak answers.
- `summary` must be a short overview of the student's overall performance.
- `question_details` must contain exactly one object per question on the sheet, in order.
- If a question is unclear or unreadable, set its `status` to "unclear" and explain why in `feedback`.

"""


AI_EVALUATION_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'total_questions': {'type': 'integer', 'minimum': 0},
        'correct_answers': {'type': 'integer', 'minimum': 0},
        'wrong_answers': {'type': 'integer', 'minimum': 0},
        'accuracy': {'type': 'number', 'minimum': 0, 'maximum': 100},
        'focus_areas': {'type': 'array', 'items': {'type': 'string'}},
        'missed_questions': {'type': 'array', 'items': {'type': 'integer'}},
        'unclear_questions': {'type': 'array', 'items': {'type': 'integer'}},
        'summary': {'type': 'string'},
        'question_details': {
            'type': 'array',
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'question_number': {'type': 'integer', 'minimum': 1},
                    'teacher_score': {'type': 'string'},
                    'student_answer_summary': {'type': 'string'},
                    'status': {'type': 'string', 'enum': ['correct', 'partially_correct', 'wrong', 'unclear']},
                    'feedback': {'type': 'string'},
                    'missing_points': {'type': 'array', 'items': {'type': 'string'}},
                },
                'required': [
                    'question_number', 'teacher_score', 'student_answer_summary',
                    'status', 'feedback', 'missing_points'
                ],
            },
        },
    },
    'required': [
        'total_questions', 'correct_answers', 'wrong_answers', 'accuracy',
        'focus_areas', 'missed_questions', 'unclear_questions', 'summary',
        'question_details'
    ],
}


def prepare_ai_images(uploaded_file):
    """Return ``(images, error)`` with image bytes suitable for vision input.

    OpenAI vision inputs must be images.  PDFs are therefore rendered page by
    page with the supported ``pymupdf`` import (not the deprecated ``fitz``
    alias).  Do not use ``Document.is_empty`` here: it is not part of the
    PyMuPDF Document API and caused the reported AttributeError.
    """
    filename = getattr(uploaded_file, 'filename', '') or ''

    if not filename.lower().endswith('.pdf'):
        try:
            from PIL import Image

            uploaded_file.seek(0)
            image = Image.open(uploaded_file)
            image.load()
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGBA' if 'transparency' in image.info else 'RGB')

            output = BytesIO()
            image.save(output, format='PNG', optimize=True)
            return [(output.getvalue(), f'{Path(filename).stem}.png', 'image/png')], None
        except Exception as exc:
            logger.warning('Failed to convert image for AI grading: %s', exc)
            return [], 'The uploaded image could not be read. Please upload a valid image.'
        finally:
            uploaded_file.seek(0)

    try:
        import pymupdf
    except ImportError:
        return [], 'PDF grading requires PyMuPDF. Install dependencies from requirements.txt.'

    try:
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        document = pymupdf.open(stream=pdf_bytes, filetype='pdf')
        try:
            if document.page_count == 0:
                return [], 'The uploaded PDF has no pages.'

            if MAX_AI_PDF_PAGES > 0 and document.page_count > MAX_AI_PDF_PAGES:
                return [], (
                    f'The uploaded PDF has {document.page_count} pages. '
                    f'AI grading supports up to {MAX_AI_PDF_PAGES} pages per upload.'
                )

            images = []
            # 144 DPI provides readable handwriting while keeping the request
            # substantially smaller than an unnecessarily high-resolution render.
            matrix = pymupdf.Matrix(2, 2)
            for page_number, page in enumerate(document, start=1):
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                images.append((
                    pixmap.tobytes('png'),
                    f'{Path(filename).stem}_page_{page_number}.png',
                    'image/png',
                ))
            return images, None
        finally:
            document.close()
    except Exception as exc:
        logger.warning('Failed to convert PDF for AI grading: %s', exc)
        return [], 'The uploaded PDF could not be read. Please upload a valid, unlocked PDF.'
    finally:
        uploaded_file.seek(0)


def call_chatgpt(prompt, image_file=None):
    """
    Call ChatGPT using the OpenAI Responses API
    and parse the returned JSON.
    """

    if requests is None:
        return {
            'success': False,
            'error': 'requests library is not available',
            'accuracy': 0,
            'correct': 0,
            'wrong': 0,
            'total': 0,
            'focus_areas': ['Unable to call OpenAI'],
            'timestamp': datetime.now().isoformat()
        }

    # Support the descriptive key name as well as the existing OpenAI name.
    api_key = (
        os.environ.get('CHATGPT_API_KEY')
        or os.environ.get('OPENAI_API_KEY')
    )

    api_base = os.environ.get(
        'CHATGPT_BASE_URL',
        os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    )

    model_name = os.environ.get(
        'CHATGPT_MODEL',
        os.environ.get(
            'AI_MODEL',
            os.environ.get('OPENAI_MODEL', os.environ.get('MODEL', 'gpt-4o-mini'))
        )
    )

    if not api_key:
        logger.error("No ChatGPT/OpenAI API key is configured")

        return {
            'success': False,
            'error': 'CHATGPT_API_KEY or OPENAI_API_KEY is not configured',
            'accuracy': 0,
            'correct': 0,
            'wrong': 0,
            'total': 0,
            'focus_areas': ['Configure OpenAI API key'],
            'timestamp': datetime.now().isoformat()
        }

    # --------------------------------------------------
    # Build Responses API content
    # --------------------------------------------------
    logger.info('Preparing OpenAI request for model=%s.', model_name)
    content = [
        {
            'type': 'input_text',
            'text': prompt
        }
    ]

    # Add the uploaded image, or PNG renderings of every uploaded PDF page.
    if image_file is not None:
        image_inputs, conversion_error = prepare_ai_images(image_file)
        if conversion_error:
            return {
                'success': False,
                'error': conversion_error,
                'error_type': 'pdf_conversion',
                'accuracy': 0,
                'correct': 0,
                'wrong': 0,
                'total': 0,
                'focus_areas': [],
                'timestamp': datetime.now().isoformat()
            }

        for image_bytes, filename, mime_type in image_inputs:
            if mime_type is None:
                mime_type = 'image/png' if filename.lower().endswith('.png') else 'image/jpeg'

            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            content.append({
                'type': 'input_image',
                'image_url': f'data:{mime_type};base64,{encoded_image}'
            })

    # --------------------------------------------------
    # Responses API payload
    # --------------------------------------------------

    payload = {
        'model': model_name,

        'input': [
            {
                'role': 'user',
                'content': content
            }
        ],

        # Responses API uses max_output_tokens instead of max_tokens.  A
        # detailed evaluation can contain dozens of question objects; the old
        # 1,000-token limit cut the JSON off in the middle of question 13.
        'max_output_tokens': int(os.environ.get(
            'CHATGPT_MAX_OUTPUT_TOKENS',
            os.environ.get('OPENAI_MAX_OUTPUT_TOKENS', '12000')
        )),
        # Ask the API to guarantee syntactically valid JSON rather than relying
        # only on the prompt. Supported Responses models return this in the
        # normal output_text field handled below.
        'text': {
            'format': {
                'type': 'json_schema',
                'name': 'student_evaluation',
                'strict': True,
                'schema': AI_EVALUATION_SCHEMA,
            },
        },
    }

    endpoint = f"{api_base.rstrip('/')}/responses"

    try:

        logger.info(
            "Calling OpenAI model=%s endpoint=%s",
            model_name,
            endpoint
        )

        response = requests.post(
            endpoint,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=90
        )

        # --------------------------------------------------
        # IMPORTANT:
        # Print the REAL OpenAI error instead of only
        # "400 Client Error"
        # --------------------------------------------------

        if not response.ok:

            try:
                error_data = response.json()
                error_text = json.dumps(
                    error_data,
                    indent=2
                )
            except Exception:
                error_text = response.text

            logger.error(
                "OpenAI API ERROR %s:\n%s",
                response.status_code,
                error_text
            )

            return {
                'success': False,
                'error': (
                    f"OpenAI API returned "
                    f"{response.status_code}: "
                    f"{error_text}"
                ),
                'accuracy': 0,
                'correct': 0,
                'wrong': 0,
                'total': 0,
                'focus_areas': ['AI grading unavailable'],
                'timestamp': datetime.now().isoformat()
            }

        data = response.json()

        if data.get('status') == 'incomplete':
            reason = (data.get('incomplete_details') or {}).get('reason', 'unknown reason')
            logger.error('OpenAI response was incomplete: %s', reason)
            return {
                'success': False,
                'error': f'AI grading response was incomplete ({reason}). Please try again.',
                'accuracy': 0,
                'correct': 0,
                'wrong': 0,
                'total': 0,
                'focus_areas': ['AI grading unavailable'],
                'timestamp': datetime.now().isoformat()
            }

        # --------------------------------------------------
        # Extract output_text from Responses API
        # --------------------------------------------------

        raw = ''

        for output_item in data.get('output', []):

            if output_item.get('type') != 'message':
                continue

            for content_item in output_item.get('content', []):

                if content_item.get('type') == 'output_text':

                    raw += content_item.get('text', '')

        raw = raw.strip()

        if not raw:
            logger.error(
                "OpenAI returned no text. Full response: %s",
                json.dumps(data, indent=2)
            )

            raise ValueError(
                'Empty model response'
            )

        logger.info(
            "OpenAI response received successfully"
        )

        # --------------------------------------------------
        # Remove possible Markdown JSON fences
        # --------------------------------------------------

        json_text = raw.strip()

        if json_text.startswith('```json'):
            json_text = json_text[7:]

        elif json_text.startswith('```'):
            json_text = json_text[3:]

        if json_text.endswith('```'):
            json_text = json_text[:-3]

        json_text = json_text.strip()

        # --------------------------------------------------
        # Parse AI JSON
        # --------------------------------------------------

        try:
            parsed = json.loads(json_text)

        except json.JSONDecodeError as exc:

            logger.error(
                "AI returned invalid JSON.\n"
                "JSON error: %s\n"
                "Raw response:\n%s",
                exc,
                raw
            )

            return {
                'success': False,
                'error': (
                    'AI returned invalid JSON: '
                    + str(exc)
                ),
                'raw_response': raw,
                'accuracy': 0,
                'correct': 0,
                'wrong': 0,
                'total': 0,
                'focus_areas': ['AI response parsing failed'],
                'timestamp': datetime.now().isoformat()
            }

        # Add timestamp if AI didn't provide one
        parsed['timestamp'] = (
            parsed.get('timestamp')
            or datetime.now().isoformat()
        )

        # Default success if missing
        if 'success' not in parsed:
            parsed['success'] = True

        # The requested JSON uses descriptive field names, while the rest of
        # this API uses short names. Normalize the AI response in one place.
        parsed['total'] = parsed.get('total', parsed.get('total_questions', 0))
        parsed['correct'] = parsed.get('correct', parsed.get('correct_answers', 0))
        parsed['wrong'] = parsed.get('wrong', parsed.get('wrong_answers', 0))
        parsed['accuracy'] = parsed.get('accuracy', parsed.get('accuracy ', 0))

        return parsed

    except requests.exceptions.Timeout:

        logger.error(
            "OpenAI request timed out"
        )

        return {
            'success': False,
            'error': 'OpenAI request timed out',
            'accuracy': 0,
            'correct': 0,
            'wrong': 0,
            'total': 0,
            'focus_areas': ['AI grading unavailable'],
            'timestamp': datetime.now().isoformat()
        }

    except requests.exceptions.RequestException as exc:

        logger.error(
            "OpenAI network/request error: %s",
            exc
        )

        return {
            'success': False,
            'error': str(exc),
            'accuracy': 0,
            'correct': 0,
            'wrong': 0,
            'total': 0,
            'focus_areas': ['AI grading unavailable'],
            'timestamp': datetime.now().isoformat()
        }

    except Exception as exc:

        logger.exception(
            "Unexpected OpenAI error"
        )

        return {
            'success': False,
            'error': str(exc),
            'accuracy': 0,
            'correct': 0,
            'wrong': 0,
            'total': 0,
            'focus_areas': ['AI grading unavailable'],
            'timestamp': datetime.now().isoformat()
        }
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
        cursor = conn.cursor()

        # Check if username already exists (UNIQUE constraint)
        db_execute(cursor, 'SELECT id FROM users WHERE username = ?', (username,))
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
        db_execute(cursor,
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
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
    Handle student evaluation by grading the uploaded sheet with ChatGPT.
    """
    try:
        student_id = request.form.get('student_id', '').strip()
        answers_file = request.files.get('answers')

        if not student_id:
            student_id = f"anonymous-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"

        if not answers_file or answers_file.filename == '':
            return jsonify({'error': 'Please upload an answer sheet for AI grading.'}), 400

        if answers_file and answers_file.filename:
            if not allowed_file(answers_file.filename):
                return jsonify({'error': 'Invalid file type'}), 400

            filename = secure_filename(f"answers_{student_id}_{datetime.now().timestamp()}_{answers_file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            answers_file.save(filepath)

        ai_result = call_chatgpt(CHATGPT_PROMPT, answers_file)
        if not ai_result.get('success'):
            status_code = 400 if ai_result.get('error_type') == 'pdf_conversion' else 502
            return jsonify({
                'error': ai_result.get('error', 'AI grading failed'),
                'ai_result': ai_result
            }), status_code

        total_questions = ai_result.get('total', 0)
        correct_answers = ai_result.get('correct', 0)
        wrong_answers = ai_result.get('wrong', 0)
        accuracy = ai_result.get('accuracy', calculate_accuracy(correct_answers, total_questions))
        weak_areas = ai_result.get('focus_areas', [])

        conn = get_db()
        cursor = conn.cursor()
        db_execute(cursor, 'SELECT * FROM students WHERE student_id = ?', (student_id,))
        student = cursor.fetchone()
        if not student:
            db_execute(cursor, 'INSERT INTO students (student_id) VALUES (?)', (student_id,))

        db_execute(cursor, '''
            INSERT INTO evaluations 
            (student_id, correct_answers, wrong_answers, total_questions, accuracy, focus_areas)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, correct_answers, wrong_answers, total_questions, accuracy, json.dumps(weak_areas)))

        conn.commit()
        conn.close()

        response_data = {
            'success': True,
            'student_id': student_id,
            'correct': correct_answers,
            'wrong': wrong_answers,
            'total': total_questions,
            'accuracy': accuracy,
            'focus_areas': weak_areas,
            'ai_result': ai_result,
            'timestamp': datetime.now().isoformat()
        }
        response_data.update({
            key: value for key, value in ai_result.items()
            if key not in {'success', 'correct', 'wrong', 'total', 'accuracy', 'focus_areas', 'timestamp'}
        })
        return jsonify(response_data), 200

    except Exception as e:
        logger.error("Evaluation failed: %s", str(e))
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
        logger.info("Fetching recent training data uploads from database")
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
        logger.error("Error fetching training data status: %s", e)
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