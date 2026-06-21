# UIL Tutor AI - Developer Guide

Complete guide for developers to understand, modify, and extend UIL Tutor AI.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Code Organization](#code-organization)
3. [Development Setup](#development-setup)
4. [Key Components](#key-components)
5. [Adding Features](#adding-features)
6. [API Development](#api-development)
7. [Frontend Development](#frontend-development)
8. [Testing Guide](#testing-guide)
9. [Deployment Guide](#deployment-guide)
10. [Best Practices](#best-practices)

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser                           │
│            (uil-tutor-ai.html + app.js)                │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Flask Backend (app.py)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Training   │  │ Evaluation   │  │  Analytics   │  │
│  │   Endpoint   │  │  Endpoint    │  │  Endpoints   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         ↓                ↓                    ↓           │
│  ┌──────────────────────────────────────────────────┐   │
│  │        Utility Functions (utils.py)              │   │
│  │  FileHandler | AnalysisEngine | Validation      │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │ SQL
                     ↓
        ┌────────────────────────────┐
        │   SQLite Database          │
        │  (uil_tutor.db)            │
        │  ┌──────────────────────┐  │
        │  │ students             │  │
        │  │ evaluations          │  │
        │  │ training_data        │  │
        │  └──────────────────────┘  │
        └────────────────────────────┘
```

### Data Flow

1. **Training Flow:**
   ```
   HTML Form → app.js → POST /api/train → app.py → 
   File Validation → Database Storage → File System
   ```

2. **Evaluation Flow:**
   ```
   HTML Form → app.js → POST /api/evaluate → app.py → 
   File Processing → Analysis Engine → Database → Response
   ```

3. **History Flow:**
   ```
   User Request → app.js → GET /api/student/{id}/history → 
   app.py → Database Query → JSON Response → Display
   ```

---

## Code Organization

### Backend Structure

```
API/
├── app.py (500 lines)
│   ├── Flask app initialization
│   ├── Database setup
│   ├── Route handlers (7 endpoints)
│   └── Error handlers
│
├── utils.py (400 lines)
│   ├── FileHandler class
│   │   ├── is_allowed_file()
│   │   ├── is_valid_size()
│   │   └── get_file_extension()
│   │
│   ├── AnalysisEngine class
│   │   ├── calculate_accuracy()
│   │   ├── identify_weak_areas()
│   │   ├── generate_report()
│   │   └── get_recommendations()
│   │
│   ├── DatabaseManager class
│   │   ├── get_student_history()
│   │   ├── get_student_stats()
│   │   └── save_evaluation()
│   │
│   ├── ValidationEngine class
│   │   ├── validate_student_id()
│   │   ├── validate_file()
│   │   └── validate_evaluation_data()
│   │
│   └── Helper functions
│       ├── format_timestamp()
│       ├── get_performance_level()
│       └── calculate_percentile()
│
└── sample_data.py
    ├── generate_sample_data()
    ├── clear_evaluations()
    ├── view_data()
    └── reset_database()
```

### Frontend Structure

```
UI/
├── uil-tutor-ai.html (1000+ lines)
│   ├── HTML structure
│   ├── CSS styling (500+ lines)
│   │   ├── Variables & colors
│   ├── Modal definitions
│   │   ├── trainModal
│   │   ├── evalModal
│   │   └── detailedModal
│   └── Responsive design
│
└── app.js (500+ lines)
    ├── Modal Management
    │   ├── openModal()
    │   ├── closeModal()
    │   └── Window click handler
    │
    ├── File Upload
    │   ├── updateFileName()
    │   ├── setupDragAndDrop()
    │   └── File validation
    │
    ├── Training Module
    │   ├── handleTraining()
    │   ├── resetTrainingForm()
    │   └── API integration
    │
    ├── Evaluation Module
    │   ├── handleEvaluation()
    │   ├── displayEvaluationResults()
    │   ├── resetEvaluationForm()
    │   └── API integration
    │
    ├── Analytics
    │   ├── viewDetailedEval()
    │   ├── viewPriorEvals()
    │   └── updateDetailedStats()
    │
    ├── Utilities
    │   ├── showNotification()
    │   ├── showLoadingSpinner()
    │   └── Validation functions
    │
    └── Initialization
        ├── DOMContentLoaded
        └── Event setup
```

---

## Development Setup

### 1. Environment Setup

```bash
# Clone/navigate to project
cd "c:\UIL APP"

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
cd API
pip install -r requirements.txt
cd ..
```

### 2. IDE Setup

**Recommended IDE:** Visual Studio Code

**Extensions to Install:**
- Python
- Pylint
- Flask-specific extensions
- REST Client (for API testing)
- Live Server (for frontend)

**.vscode/settings.json:**
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "editor.formatOnSave": true,
    "python.formatting.provider": "autopep8"
}
```

### 3. Run Development Servers

```bash
# Terminal 1: Backend API
cd API
python app.py

# Terminal 2: Frontend (if using Live Server)
# Just open UI/uil-tutor-ai.html in browser
# Or use VS Code Live Server extension
```

---

## Key Components

### Flask Application (app.py)

**Initialization:**
```python
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
```

**Key Routes:**
```python
@app.route('/api/health', methods=['GET'])
@app.route('/api/train', methods=['POST'])
@app.route('/api/evaluate', methods=['POST'])
@app.route('/api/student/<student_id>/history', methods=['GET'])
```

### Database Initialization

```python
def init_db():
    """Initialize database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables with proper schema
    cursor.execute('''CREATE TABLE IF NOT EXISTS students ...''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS evaluations ...''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS training_data ...''')
    
    conn.commit()
    conn.close()
```

### Utility Classes

**FileHandler Example:**
```python
class FileHandler:
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    MAX_FILE_SIZE = 16 * 1024 * 1024
    
    @staticmethod
    def is_allowed_file(filename):
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in FileHandler.ALLOWED_EXTENSIONS
```

---

## Adding Features

### Adding a New API Endpoint

**Step 1: Create the handler function**
```python
@app.route('/api/new-feature', methods=['POST'])
def new_feature():
    try:
        # Validate input
        if 'required_param' not in request.form:
            return jsonify({'error': 'Missing parameter'}), 400
        
        # Process data
        param = request.form['required_param']
        result = process_data(param)
        
        # Return result
        return jsonify({'success': True, 'data': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Step 2: Add frontend call**
```javascript
async function callNewFeature(data) {
    try {
        const response = await fetch(`${API_BASE_URL}/new-feature`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (response.ok) {
            showNotification('Success!', 'success');
        } else {
            showNotification(result.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}
```

**Step 3: Document the endpoint**
```markdown
### New Feature

**Endpoint:** `POST /api/new-feature`

**Parameters:**
| Name | Type | Required |
|------|------|----------|
| param | String | Yes |

**Response:**
```json
{
    "success": true,
    "data": {...}
}
```
```

### Adding a New Utility Function

**In utils.py:**
```python
def new_utility_function(param1, param2):
    """
    Description of what this function does
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        Description of return value
    """
    # Implementation
    return result
```

### Adding Frontend Functionality

**In app.js:**
```javascript
// Add new function
function handleNewFeature(event) {
    event.preventDefault();
    
    // Get form data
    const data = new FormData(event.target);
    
    // Call API
    callNewFeature(Object.fromEntries(data));
}

// Add event listeners
document.addEventListener('DOMContentLoaded', function() {
    const element = document.getElementById('new-element');
    element.addEventListener('click', handleNewFeature);
});
```

---

## API Development

### Creating a New Endpoint

**Template:**
```python
@app.route('/api/endpoint-name', methods=['GET', 'POST'])
def endpoint_name():
    """
    Description of the endpoint
    
    Expected request:
        {
            "param": "value"
        }
    
    Returns:
        {
            "success": bool,
            "data": {...}
        }
    """
    try:
        # 1. Validate input
        if request.method == 'POST':
            data = request.get_json()
            if 'param' not in data:
                return jsonify({'error': 'Missing param'}), 400
        
        # 2. Process data
        result = process_data(data.get('param'))
        
        # 3. Return result
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Error Handling Pattern

```python
try:
    # Validation
    if not validate_input(input_data):
        return jsonify({'error': 'Invalid input'}), 400
    
    # Processing
    result = do_something(input_data)
    
    # Success response
    return jsonify({'success': True, 'data': result}), 200
    
except ValueError as e:
    return jsonify({'error': str(e)}), 400
except DatabaseError as e:
    return jsonify({'error': 'Database error'}), 500
except Exception as e:
    return jsonify({'error': 'Unexpected error'}), 500
```

---

## Frontend Development

### Module Organization

```javascript
// 1. Constants & Configuration
const API_BASE_URL = 'http://localhost:5000/api';
const NOTIFICATION_TIMEOUT = 3000;

// 2. State Management
let currentStudentData = null;
let studentEvaluationHistory = [];

// 3. UI Functions
function openModal(modalId) { ... }

// 4. API Integration
async function handleApiCall() { ... }

// 5. Event Handlers
document.addEventListener('DOMContentLoaded', () => { ... });
```

### API Integration Pattern

```javascript
async function apiCall(endpoint, method, data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Unknown error');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}
```

### Form Handling Pattern

```javascript
function handleFormSubmit(event) {
    event.preventDefault();
    
    // Get form data
    const formData = new FormData(event.target);
    
    // Validate
    if (!validateForm(formData)) {
        showNotification('Validation failed', 'error');
        return;
    }
    
    // Submit
    showLoadingSpinner();
    apiCall('/endpoint', 'POST', formData)
        .then(result => {
            showNotification('Success!', 'success');
            // Update UI
        })
        .catch(error => {
            showNotification(error.message, 'error');
        })
        .finally(() => hideLoadingSpinner());
}
```

---

## Testing Guide

### Manual Testing

**Test Endpoint:**
```bash
curl http://localhost:5000/api/health
```

**Test File Upload:**
```bash
curl -X POST http://localhost:5000/api/train \
  -F "questions=@questions.pdf" \
  -F "answers=@answers.pdf"
```

### Unit Testing

**Create test_app.py:**
```python
import unittest
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_check(self):
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json)
    
    def test_invalid_file_upload(self):
        response = self.app.post('/api/train')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

```bash
# Generate sample data
python API/sample_data.py

# Test all endpoints
python -m pytest tests/ -v
```

---

## Deployment Guide

### Local Development
```bash
python API/app.py
```

### Docker Development
```bash
docker build -t uil-tutor-api:dev API/
docker run -p 5000:5000 -v uploads:/app/uploads uil-tutor-api:dev
```

### Production Deployment

**Step 1: Environment Setup**
```bash
# Set environment variables
export FLASK_ENV=production
export FLASK_DEBUG=False
```

**Step 2: Install Production Server**
```bash
pip install gunicorn
```

**Step 3: Run with Gunicorn**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Step 4: Use Reverse Proxy (nginx)**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Best Practices

### Code Style

**Python (PEP 8):**
```python
# Good
def calculate_accuracy(correct, total):
    """Calculate accuracy percentage."""
    if total == 0:
        return 0
    return round((correct / total) * 100, 2)

# Bad
def calc_acc(c,t):
    if t==0:return 0
    return round((c/t)*100,2)
```

**JavaScript:**
```javascript
// Good
async function fetchStudentData(studentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/student/${studentId}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching student data:', error);
        throw error;
    }
}

// Bad
function fetchData(id){
    return fetch(API_BASE_URL + "/student/" + id).then(r => r.json());
}
```

### Error Handling

**Always validate input:**
```python
def process_request(user_input):
    if not user_input:
        return None, "Input cannot be empty"
    
    if not isinstance(user_input, str):
        return None, "Input must be string"
    
    if len(user_input) > 100:
        return None, "Input too long"
    
    # Process...
    return result, None
```

**Use meaningful error messages:**
```javascript
// Good
showNotification('Student ID must be 3-50 alphanumeric characters', 'error');

// Bad
showNotification('Error', 'error');
```

### Security

**SQL Injection Prevention:**
```python
# Good - parameterized queries
cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))

# Bad - string concatenation
cursor.execute(f'SELECT * FROM students WHERE student_id = {student_id}')
```

**File Validation:**
```python
# Always validate file type and size
if not allowed_file(filename):
    return error_response("File type not allowed")

if file_size > MAX_FILE_SIZE:
    return error_response("File too large")
```

### Documentation

**Function docstrings:**
```python
def analyze_performance(correct, total):
    """
    Analyze student performance and generate insights.
    
    Args:
        correct (int): Number of correct answers
        total (int): Total number of questions
    
    Returns:
        dict: Analysis results including accuracy and recommendations
    
    Raises:
        ValueError: If correct > total or values are negative
    """
    pass
```

---

## Contributing Guidelines

1. Fork the repository
2. Create feature branch: `git checkout -b feature/name`
3. Write code following style guide
4. Write tests for new features
5. Document changes
6. Submit pull request

---

## Performance Tips

1. **Database:** Use indexes for frequently queried columns
2. **Caching:** Cache student stats to reduce queries
3. **Files:** Implement file size limits and cleanup
4. **API:** Use pagination for large result sets
5. **Frontend:** Minimize DOM operations, use event delegation

---

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [MDN Web Docs](https://developer.mozilla.org/)
- [Python Style Guide (PEP 8)](https://www.python.org/dev/peps/pep-0008/)

---

**Last Updated:** March 21, 2026
**Version:** 1.0.0

Happy coding! 🚀
