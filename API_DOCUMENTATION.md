# UIL Tutor AI - API Documentation

Complete REST API documentation for UIL Tutor AI backend server.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Currently, no authentication is required. For production, implement API keys or JWT tokens.

## Response Format

All responses are in JSON format:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message describing what went wrong",
  "code": "ERROR_CODE"
}
```

## Endpoints

### 1. Health Check

**Endpoint:** `GET /api/health`

**Description:** Check if API server is running and healthy

**Parameters:** None

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-21T10:30:45.123456",
  "service": "UIL Tutor AI API"
}
```

**Status Code:** 200

---

### 2. Train Model

**Endpoint:** `POST /api/train`

**Description:** Upload training data (questions and answer keys) to train the AI model

**Content-Type:** `multipart/form-data`

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| questions | File | Yes | Question paper (PDF, JPG, PNG) |
| answers | File | Yes | Answer key (PDF, JPG, PNG) |

**Example cURL:**
```bash
curl -X POST http://localhost:5000/api/train \
  -F "questions=@questions.pdf" \
  -F "answers=@answers.pdf"
```

**Response:**
```json
{
  "success": true,
  "message": "Training data uploaded successfully",
  "questions_file": "questions_1711000245.123_sample.pdf",
  "answers_file": "answers_1711000245.456_answer_key.pdf",
  "timestamp": "2026-03-21T10:30:45.123456"
}
```

**Status Codes:**
- 200: Success
- 400: Missing or invalid files
- 500: Server error

**File Constraints:**
- Supported types: PDF, JPG, PNG
- Maximum size: 16MB per file
- Recommended: 1-5MB for optimal performance

---

### 3. Evaluate Student

**Endpoint:** `POST /api/evaluate`

**Description:** Evaluate a student's performance based on their answer sheet

**Content-Type:** `multipart/form-data`

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| student_id | String | Yes | Unique student identifier |
| answers | File | Yes | Student answer sheet (PDF, JPG, PNG) |

**Example cURL:**
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -F "student_id=JD2024" \
  -F "answers=@student_answers.pdf"
```

**Response:**
```json
{
  "success": true,
  "correct": 47,
  "wrong": 3,
  "total": 50,
  "accuracy": 94.0,
  "focus_areas": [
    "Maintain consistency",
    "Try advanced problem sets"
  ],
  "timestamp": "2026-03-21T10:30:45.123456"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid student ID or missing file
- 500: Server error

**Validation Rules:**
- Student ID: 3-50 alphanumeric characters
- File must be PDF or image format

---

### 4. Get Student Evaluation History

**Endpoint:** `GET /api/student/{student_id}/history`

**Description:** Retrieve past evaluations for a student (last 10 by default)

**Parameters:**
| Name | Type | Location | Description |
|------|------|----------|-------------|
| student_id | String | URL | Unique student identifier |

**Example:**
```bash
curl http://localhost:5000/api/student/JD2024/history
```

**Response:**
```json
{
  "history": [
    {
      "correct": 47,
      "wrong": 3,
      "accuracy": 94.0,
      "date": "2026-03-21T10:30:45"
    },
    {
      "correct": 45,
      "wrong": 5,
      "accuracy": 90.0,
      "date": "2026-03-20T14:15:30"
    }
  ]
}
```

**Status Codes:**
- 200: Success (with empty list if no evaluations)
- 400: Invalid student ID
- 500: Server error

---

### 5. Get Student Statistics

**Endpoint:** `GET /api/student/{student_id}/stats`

**Description:** Get comprehensive statistics for a student

**Parameters:**
| Name | Type | Location | Description |
|------|------|----------|-------------|
| student_id | String | URL | Unique student identifier |

**Example:**
```bash
curl http://localhost:5000/api/student/JD2024/stats
```

**Response:**
```json
{
  "tests_taken": 10,
  "avg_correct": 45.5,
  "avg_wrong": 4.5,
  "avg_accuracy": 91.0,
  "best_accuracy": 96.0
}
```

**Status Codes:**
- 200: Success
- 400: Invalid student ID
- 500: Server error

---

### 6. Get All Students

**Endpoint:** `GET /api/students`

**Description:** Retrieve list of all students in the system

**Parameters:** None

**Example:**
```bash
curl http://localhost:5000/api/students
```

**Response:**
```json
{
  "students": [
    {
      "student_id": "JD2024",
      "evaluation_count": 5,
      "last_evaluation": "2026-03-21T10:30:45"
    },
    {
      "student_id": "SM2024",
      "evaluation_count": 3,
      "last_evaluation": "2026-03-21T09:15:20"
    }
  ]
}
```

**Status Codes:**
- 200: Success
- 500: Server error

---

### 7. Get Training Data Status

**Endpoint:** `GET /api/training/status`

**Description:** View status of uploaded training data

**Parameters:** None

**Example:**
```bash
curl http://localhost:5000/api/training/status
```

**Response:**
```json
{
  "training_data": [
    {
      "filename": "questions_1711000245.123_sample.pdf",
      "type": "questions",
      "status": "processing",
      "upload_date": "2026-03-21T10:30:45"
    },
    {
      "filename": "answers_1711000245.456_answer_key.pdf",
      "type": "answers",
      "status": "processing",
      "upload_date": "2026-03-21T10:30:45"
    }
  ]
}
```

**Status Codes:**
- 200: Success
- 500: Server error

---

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters or missing required fields |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Internal Server Error | Server error occurred |

## Error Handling

### Common Error Responses

**Missing Required Field:**
```json
{
  "error": "Missing required fields"
}
```

**Invalid File Type:**
```json
{
  "error": "Invalid file type. Only PDF and images allowed."
}
```

**File Size Exceeded:**
```json
{
  "error": "File exceeds maximum size limit of 16MB"
}
```

**Invalid Student ID:**
```json
{
  "error": "Invalid student ID format"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. For production, consider:
- 100 requests per minute per IP
- 1 file upload per second per IP
- 10MB/s bandwidth limit

---

## Batch Operations

### Bulk Student Evaluation

To evaluate multiple students efficiently:

```bash
# Evaluate student 1
curl -X POST http://localhost:5000/api/evaluate \
  -F "student_id=STU001" \
  -F "answers=@student1.pdf"

# Evaluate student 2
curl -X POST http://localhost:5000/api/evaluate \
  -F "student_id=STU002" \
  -F "answers=@student2.pdf"
```

---

## Webhooks (Future Feature)

Planned webhooks for automated notifications:
- `on_evaluation_complete` - Triggered when student evaluation finishes
- `on_training_complete` - Triggered when AI training completes
- `on_error` - Triggered when operation fails

---

## Testing

### Using Python Requests Library

```python
import requests

# Health check
response = requests.get('http://localhost:5000/api/health')
print(response.json())

# Train model
files = {
    'questions': open('questions.pdf', 'rb'),
    'answers': open('answers.pdf', 'rb')
}
response = requests.post('http://localhost:5000/api/train', files=files)
print(response.json())

# Evaluate student
files = {'answers': open('student_answers.pdf', 'rb')}
data = {'student_id': 'JD2024'}
response = requests.post('http://localhost:5000/api/evaluate', files=files, data=data)
print(response.json())

# Get history
response = requests.get('http://localhost:5000/api/student/JD2024/history')
print(response.json())
```

---

## API Versioning

Current version: **v1.0**

Future versions may include:
- v2.0: Authentication and user roles
- v3.0: Advanced analytics and reporting
- v4.0: Machine learning model improvements

---

## Support & Issues

For API issues:
1. Check server is running: `curl http://localhost:5000/api/health`
2. Review request parameters
3. Check browser console for error messages (F12)
4. Verify file formats and sizes
5. Check database file exists

---

## Change Log

### Version 1.0.0 (March 2026)
- Initial release
- Basic training endpoint
- Student evaluation endpoint
- History and statistics retrieval
- Training data management

---

**Last Updated:** March 21, 2026
**API Status:** ✅ Active
