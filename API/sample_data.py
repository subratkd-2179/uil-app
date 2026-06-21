"""
UIL Tutor AI - Sample Data Generator
Generate sample data for testing the application
"""

import sqlite3
from datetime import datetime, timedelta
import random
import json

DB_PATH = 'uil_tutor.db'

def generate_sample_data():
    """Generate sample student data and evaluations"""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Sample students
        students = [
            ('JD2024', 'John Doe'),
            ('SM2024', 'Sarah Miller'),
            ('RJ2024', 'Robert Johnson'),
            ('EM2024', 'Emma Wilson'),
            ('AC2024', 'Alex Chen'),
            ('OA2024', 'Olivia Anderson'),
        ]
        
        # Insert students
        for student_id, name in students:
            cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO students (student_id, name) VALUES (?, ?)', 
                              (student_id, name))
        
        # Generate sample evaluations
        base_date = datetime.now() - timedelta(days=30)
        
        for student_id, name in students:
            # Create 5 evaluations for each student over the past month
            for i in range(5):
                correct = random.randint(40, 50)
                total = 50
                accuracy = round((correct / total) * 100, 2)
                
                # Generate focus areas
                accuracy_threshold = accuracy
                if accuracy_threshold < 80:
                    focus_areas = [
                        "Roman numbers - Practice conversion between Roman and Arabic numerals",
                        "Square Roots - Focus on mental calculation techniques",
                        "Volume conversions - Review metric and imperial relationships"
                    ]
                else:
                    focus_areas = [
                        "Continue consistent practice",
                        "Try advanced problem sets"
                    ]
                
                eval_date = base_date + timedelta(days=i*6)
                
                cursor.execute('''
                    INSERT INTO evaluations 
                    (student_id, correct_answers, wrong_answers, total_questions, accuracy, focus_areas, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (student_id, correct, total - correct, total, accuracy, 
                      json.dumps(focus_areas), eval_date.isoformat()))
        
        conn.commit()
        
        print("Sample data generated successfully!")
        print(f"Created {len(students)} students with evaluations")
        print("\nStudent IDs for testing:")
        for student_id, name in students:
            print(f"  {student_id} - {name}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error generating sample data: {e}")

def clear_evaluations():
    """Clear all evaluations (keep students)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM evaluations')
        conn.commit()
        
        print("All evaluations cleared!")
        conn.close()
        
    except Exception as e:
        print(f"Error clearing evaluations: {e}")

def view_data():
    """View all data in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # View students
        print("\n" + "="*60)
        print("STUDENTS")
        print("="*60)
        cursor.execute('SELECT * FROM students')
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, Name: {row[1]}, Created: {row[2]}")
        
        # View evaluations
        print("\n" + "="*60)
        print("EVALUATIONS")
        print("="*60)
        cursor.execute('''
            SELECT student_id, correct_answers, wrong_answers, accuracy, created_at 
            FROM evaluations 
            ORDER BY created_at DESC
        ''')
        for row in cursor.fetchall():
            print(f"Student: {row[0]}, Correct: {row[1]}, Wrong: {row[2]}, "
                  f"Accuracy: {row[3]}%, Date: {row[4]}")
        
        # View training data
        print("\n" + "="*60)
        print("TRAINING DATA")
        print("="*60)
        cursor.execute('SELECT * FROM training_data')
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"File: {row[1]}, Type: {row[2]}, Status: {row[3]}, "
                      f"Date: {row[4]}")
        else:
            print("No training data uploaded yet")
        
        conn.close()
        
    except Exception as e:
        print(f"Error viewing data: {e}")

def reset_database():
    """Reset database to initial state"""
    try:
        import os
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(f"Database {DB_PATH} deleted successfully!")
            print("It will be recreated on next server start.")
    except Exception as e:
        print(f"Error resetting database: {e}")

if __name__ == '__main__':
    print("\nUIL Tutor AI - Database Utility")
    print("="*60)
    print("1. Generate Sample Data")
    print("2. View Database Data")
    print("3. Clear All Evaluations")
    print("4. Reset Database")
    print("5. Exit")
    print("="*60)
    
    choice = input("\nSelect an option (1-5): ").strip()
    
    if choice == '1':
        generate_sample_data()
    elif choice == '2':
        view_data()
    elif choice == '3':
        confirm = input("Are you sure? (yes/no): ").strip().lower()
        if confirm == 'yes':
            clear_evaluations()
    elif choice == '4':
        confirm = input("This will delete all data! Are you sure? (yes/no): ").strip().lower()
        if confirm == 'yes':
            reset_database()
    elif choice == '5':
        print("Goodbye!")
    else:
        print("Invalid option!")
