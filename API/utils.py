"""
UIL Tutor AI - Utility Functions
Helper functions for file processing, validation, and analysis
"""

import os
import json
from datetime import datetime
from pathlib import Path
import sqlite3

class FileHandler:
    """Handle file upload and validation"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    
    @staticmethod
    def is_allowed_file(filename):
        """Check if file has allowed extension"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in FileHandler.ALLOWED_EXTENSIONS
    
    @staticmethod
    def is_valid_size(file_size):
        """Check if file size is within limits"""
        return file_size <= FileHandler.MAX_FILE_SIZE
    
    @staticmethod
    def get_file_extension(filename):
        """Get file extension"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else None
    
    @staticmethod
    def get_file_size_mb(file_size):
        """Convert bytes to MB"""
        return round(file_size / (1024 * 1024), 2)


class AnalysisEngine:
    """Analyze student performance and generate insights"""
    
    @staticmethod
    def calculate_accuracy(correct, total):
        """Calculate accuracy percentage"""
        if total == 0:
            return 0
        return round((correct / total) * 100, 2)
    
    @staticmethod
    def calculate_improvement(prev_accuracy, current_accuracy):
        """Calculate improvement percentage"""
        if prev_accuracy == 0:
            return 0
        return round(((current_accuracy - prev_accuracy) / prev_accuracy) * 100, 2)
    
    @staticmethod
    def identify_weak_areas(correct, total, accuracy):
        """Identify areas that need improvement"""
        weak_areas = []
        
        if accuracy < 60:
            weak_areas = [
                "Fundamental Concepts - Review basic principles and definitions",
                "Problem-Solving Techniques - Practice step-by-step approaches",
                "Time Management - Work on speed and efficiency",
                "Error Analysis - Review common mistakes and avoid them"
            ]
        elif accuracy < 75:
            weak_areas = [
                "Advanced Concepts - Deepen understanding of complex topics",
                "Mental Math - Improve calculation speed",
                "Pattern Recognition - Practice identifying problem types",
                "Special Cases - Review edge cases and exceptions"
            ]
        elif accuracy < 85:
            weak_areas = [
                "Precision - Double-check calculations",
                "Complex Problems - Work on multi-step challenges",
                "Time Optimization - Solve problems faster",
                "Rare Topics - Practice less common question types"
            ]
        elif accuracy < 95:
            weak_areas = [
                "Maintain Consistency - Keep up the good work",
                "Challenging Problems - Tackle the hardest questions",
                "Competition Strategy - Practice under time pressure",
                "Advanced Techniques - Learn optimization strategies"
            ]
        else:
            weak_areas = [
                "Excellence Achieved - Continue consistent practice",
                "Mentor Others - Help other students improve",
                "Challenge Yourself - Try advanced problem sets",
                "Perfect Your Speed - Aim for fastest solution times"
            ]
        
        return weak_areas
    
    @staticmethod
    def generate_report(student_id, correct, total, history=None):
        """Generate comprehensive evaluation report"""
        accuracy = AnalysisEngine.calculate_accuracy(correct, total)
        weak_areas = AnalysisEngine.identify_weak_areas(correct, total, accuracy)
        
        report = {
            'student_id': student_id,
            'evaluation_date': datetime.now().isoformat(),
            'performance': {
                'correct_answers': correct,
                'wrong_answers': total - correct,
                'total_questions': total,
                'accuracy': accuracy
            },
            'weak_areas': weak_areas,
            'recommendations': AnalysisEngine.get_recommendations(accuracy)
        }
        
        if history and len(history) > 0:
            prev_accuracy = history[0]['accuracy']
            improvement = AnalysisEngine.calculate_improvement(prev_accuracy, accuracy)
            report['progress'] = {
                'previous_accuracy': prev_accuracy,
                'improvement_percentage': improvement,
                'trend': 'improving' if improvement > 0 else 'declining' if improvement < 0 else 'stable'
            }
        
        return report
    
    @staticmethod
    def get_recommendations(accuracy):
        """Get study recommendations based on accuracy"""
        recommendations = []
        
        if accuracy < 50:
            recommendations = [
                "Start with fundamentals - Review basic concepts thoroughly",
                "Practice daily - Aim for 1-2 hours of focused study",
                "Work with a tutor - Get personalized guidance",
                "Do practice problems - Solve 20-30 problems daily"
            ]
        elif accuracy < 70:
            recommendations = [
                "Increase practice frequency - Study 1-2 hours daily",
                "Focus on weak areas - Dedicate extra time to problem areas",
                "Time yourself - Practice under timed conditions",
                "Review mistakes - Analyze every incorrect answer"
            ]
        elif accuracy < 85:
            recommendations = [
                "Consistent practice - Maintain 1 hour daily practice",
                "Targeted review - Focus on identified weak areas",
                "Speed drills - Work on improving solution speed",
                "Take practice tests - Do full-length tests weekly"
            ]
        else:
            recommendations = [
                "Maintain current pace - Continue your successful routine",
                "Challenge yourself - Try harder problem sets",
                "Help others - Teaching reinforces understanding",
                "Fine-tune technique - Work on speed and efficiency"
            ]
        
        return recommendations


class DatabaseManager:
    """Manage database operations"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_student_history(self, student_id, limit=10):
        """Get evaluation history for a student"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT correct_answers, wrong_answers, accuracy, created_at
                FROM evaluations
                WHERE student_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (student_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []
    
    def get_student_stats(self, student_id):
        """Get overall statistics for a student"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as tests_taken,
                    AVG(correct_answers) as avg_correct,
                    AVG(wrong_answers) as avg_wrong,
                    AVG(accuracy) as avg_accuracy,
                    MAX(accuracy) as best_accuracy,
                    MIN(accuracy) as worst_accuracy
                FROM evaluations
                WHERE student_id = ?
            ''', (student_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result or result[0] == 0:
                return None
            
            return {
                'tests_taken': int(result[0]),
                'avg_correct': round(result[1] or 0, 2),
                'avg_wrong': round(result[2] or 0, 2),
                'avg_accuracy': round(result[3] or 0, 2),
                'best_accuracy': round(result[4] or 0, 2),
                'worst_accuracy': round(result[5] or 0, 2)
            }
        except Exception as e:
            print(f"Error fetching stats: {e}")
            return None
    
    def save_evaluation(self, student_id, correct, total, weak_areas=None):
        """Save evaluation to database"""
        try:
            accuracy = AnalysisEngine.calculate_accuracy(correct, total)
            weak_areas_json = json.dumps(weak_areas) if weak_areas else json.dumps([])
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO evaluations 
                (student_id, correct_answers, wrong_answers, total_questions, accuracy, focus_areas)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_id, correct, total - correct, total, accuracy, weak_areas_json))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error saving evaluation: {e}")
            return False


class ValidationEngine:
    """Validate input data and file formats"""
    
    @staticmethod
    def validate_student_id(student_id):
        """Validate student ID format"""
        if not student_id:
            return False, "Student ID cannot be empty"
        
        if len(student_id) < 3:
            return False, "Student ID must be at least 3 characters"
        
        if len(student_id) > 50:
            return False, "Student ID must be less than 50 characters"
        
        # Allow alphanumeric and common separators
        if not all(c.isalnum() or c in '-_' for c in student_id):
            return False, "Student ID can only contain letters, numbers, hyphens, and underscores"
        
        return True, "Valid"
    
    @staticmethod
    def validate_file(file_obj):
        """Validate uploaded file"""
        if not file_obj:
            return False, "No file provided"
        
        if file_obj.filename == '':
            return False, "No file selected"
        
        if not FileHandler.is_allowed_file(file_obj.filename):
            return False, f"File type not allowed. Allowed types: {', '.join(FileHandler.ALLOWED_EXTENSIONS)}"
        
        file_obj.seek(0, os.SEEK_END)
        file_size = file_obj.tell()
        file_obj.seek(0)
        
        if not FileHandler.is_valid_size(file_size):
            max_size_mb = FileHandler.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File size exceeds {max_size_mb}MB limit"
        
        return True, "Valid"
    
    @staticmethod
    def validate_evaluation_data(correct, total):
        """Validate evaluation data"""
        if not isinstance(correct, int) or not isinstance(total, int):
            return False, "Correct and total must be integers"
        
        if correct < 0 or total < 0:
            return False, "Correct and total cannot be negative"
        
        if correct > total:
            return False, "Correct answers cannot exceed total questions"
        
        if total == 0:
            return False, "Total questions cannot be zero"
        
        return True, "Valid"


# Helper Functions

def format_timestamp(timestamp):
    """Format timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except:
        return timestamp

def get_performance_level(accuracy):
    """Get performance level label"""
    if accuracy >= 95:
        return "Excellent"
    elif accuracy >= 85:
        return "Very Good"
    elif accuracy >= 75:
        return "Good"
    elif accuracy >= 65:
        return "Satisfactory"
    elif accuracy >= 50:
        return "Needs Improvement"
    else:
        return "Critical"

def calculate_percentile(accuracy):
    """Calculate percentile rank (mock calculation)"""
    if accuracy >= 95:
        return 95
    elif accuracy >= 85:
        return 80
    elif accuracy >= 75:
        return 65
    elif accuracy >= 65:
        return 45
    else:
        return 25
