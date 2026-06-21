"""
UIL Tutor AI - Flask Backend API
Main application server for handling training and evaluations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json
import sqlite3
from pathlib import Path

# ==========================================
# Initialize Flask App
# ==========================================

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create uploads folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database
DB_PATH = 'uil_tutor.db'

# ==========================================
# Database Setup
# ==========================================

def init_db():
    """Initialize database with required tables"""
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
    
    conn.commit()
    conn.close()

# ==========================================
# Utility Functions
# ==========================================

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
        
        cursor.execute('''
            INSERT INTO training_data (filename, file_type, status)
            VALUES (?, ?, ?)
        ''', (questions_filename, 'questions', 'processing'))
        
        cursor.execute('''
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
        cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.execute('INSERT INTO students (student_id) VALUES (?)', (student_id,))
        
        # Record evaluation
        cursor.execute('''
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
        
        cursor.execute('''
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
        
        cursor.execute('''
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
        
        cursor.execute('''
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
        
        cursor.execute('''
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
    # Initialize database
    init_db()
    
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
