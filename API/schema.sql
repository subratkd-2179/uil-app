-- UIL Tutor AI - Database Schema Documentation
-- This file documents the complete database structure

-- ==========================================
-- Users Table (Authentication)
-- ==========================================
-- Stores user credentials and session tokens
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    token VARCHAR(128),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- Students Table
-- ==========================================
-- Stores student information
CREATE TABLE students (
    student_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- Evaluations Table
-- ==========================================
-- Stores student evaluation results
CREATE TABLE evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(64) NOT NULL,
    correct_answers INTEGER,
    wrong_answers INTEGER,
    total_questions INTEGER,
    accuracy REAL,
    focus_areas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- ==========================================
-- Training Data Table
-- ==========================================
-- Stores uploaded training files metadata
CREATE TABLE training_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'processing'
);

-- ==========================================
-- Indexes for Performance
-- ==========================================
CREATE INDEX idx_evaluations_student ON evaluations(student_id);
CREATE INDEX idx_training_data_type ON training_data(file_type);
CREATE INDEX idx_users_username ON users(username);

-- ==========================================
-- Schema Summary
-- ==========================================
-- Total Tables: 4
-- 
-- 1. users
--    - Stores login/registration data
--    - POST /api/register → INSERT into users
--    - POST /api/login → SELECT from users
--
-- 2. students
--    - Stores student profiles
--    - Referenced by evaluations
--
-- 3. evaluations
--    - Stores test results and performance data
--    - POST /api/evaluate → INSERT into evaluations
--    - GET /api/student/<id>/history → SELECT from evaluations
--    - GET /api/student/<id>/stats → SELECT/COUNT from evaluations
--
-- 4. training_data
--    - Stores uploaded training file metadata
--    - POST /api/train → INSERT into training_data
--    - GET /api/training/status → SELECT from training_data
