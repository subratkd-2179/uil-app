# UIL Tutor AI - Complete Application

An intelligent academic performance tracking system for Texas UIL (University Interscholastic League) students, featuring AI-powered evaluation, personalized feedback, and comprehensive analytics.

## Overview

UIL Tutor AI helps tutors and students excel in UIL tournaments by:
- **Training the AI Model**: Upload sample questions and answer keys to build the AI's knowledge base
- **Student Evaluation**: Evaluate student performance and generate personalized recommendations
- **Performance Analytics**: Track progress over time with detailed statistics and weak area identification
- **Personalized Feedback**: Get AI-powered insights into areas that need improvement

## Project Structure

```
UIL APP/
├── API/
│   ├── app.py                 # Flask backend API server
│   ├── requirements.txt       # Python dependencies
│   └── uploads/              # User uploaded files (auto-created)
│
└── UI/
    ├── uil-tutor-ai.html     # Main web interface
    ├── app.js                # Frontend JavaScript
    └── README.md             # This file
```

## Features

### 1. Train the Tutor
- Upload question papers (PDF, JPG, PNG)
- Upload corresponding answer keys
- AI learns from the uploaded training data
- Support for batch uploads (100+ papers recommended)

### 2. Student Evaluation
- Enter student ID
- Upload student answer sheet
- Instant performance evaluation
- Accuracy calculation and scoring
- Identification of weak areas
- Personalized improvement recommendations

### 3. Performance Analytics
- View evaluation history
- Track accuracy trends
- Identify consistent weak areas
- Monitor improvement over time
- Generate detailed reports

### 4. Data Management
- Secure file storage
- Student profile tracking
- Evaluation history
- Training data management

## System Requirements

### Frontend
- Modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- No additional software required

### Backend
- Python 3.8 or higher
- pip (Python package manager)
- 100MB disk space for uploads
- 512MB RAM minimum

## Installation & Setup

### Step 1: Install Python Dependencies

Navigate to the API folder and install required packages:

```bash
cd "c:\UIL APP\API"
pip install -r requirements.txt
```

### Step 2: Initialize the Database

The database is automatically initialized when you start the API server for the first time. It creates:
- `students` table - Student profile information
- `evaluations` table - Evaluation results and history
- `training_data` table - Uploaded training materials tracking

### Step 3: Start the Backend API Server

```bash
cd "c:\UIL APP\API"
python app.py
```

Expected output:
```
==================================================
UIL Tutor AI - Backend API Server
==================================================
API running on: http://localhost:5000
API Documentation available at: /api/docs
==================================================
```

**Keep this terminal window open while using the application.**

### Step 4: Open the Web Interface

1. Open `c:\UIL APP\UI\uil-tutor-ai.html` in your web browser
2. The application should load successfully
3. Start using the features!

## API Endpoints Reference

### Health Check
```
GET /api/health
```
Returns server health status.

### Training Data Upload
```
POST /api/train
Content-Type: multipart/form-data

Parameters:
- questions: File (PDF/JPG/PNG)
- answers: File (PDF/JPG/PNG)
```
Upload training data for the AI model.

### Student Evaluation
```
POST /api/evaluate
Content-Type: multipart/form-data

Parameters:
- student_id: String (required)
- answers: File (PDF/JPG/PNG)
```
Evaluate a student's performance.

### Student Evaluation History
```
GET /api/student/{student_id}/history
```
Retrieve evaluation history for a student (last 10 evaluations).

### Student Statistics
```
GET /api/student/{student_id}/stats
```
Get overall statistics for a student.

### All Students
```
GET /api/students
```
Get list of all students in the system.

### Training Status
```
GET /api/training/status
```
Get status of uploaded training data.

## Usage Guide

### Training the AI Model

1. Click "Train the Tutor" button
2. Upload a PDF/image of sample questions
3. Upload the corresponding answer key
4. Click "Upload & Train"
5. The AI will process and learn from the data
6. Repeat for more training data (100+ papers recommended for best results)

### Evaluating a Student

1. Click "Student Evaluation" button
2. Enter the student's ID (e.g., JD2024, ABC123)
3. Upload the student's answer sheet (PDF/image)
4. Click "Evaluate"
5. View results:
   - Correct answers count
   - Wrong answers count
   - Accuracy percentage
   - Areas needing improvement

### Viewing Detailed Results

1. After evaluation, click "View Detailed Evaluation"
2. See comprehensive analysis including:
   - Student name and ID
   - Overall accuracy score
   - Performance statistics
   - Focus areas for improvement
   - Previous test results

### Tracking Progress

1. Enter student ID in the evaluation form
2. Click "View Prior Evaluations"
3. See all past evaluations with:
   - Date of evaluation
   - Accuracy achieved
   - Correct/wrong answer counts
   - Improvement trend

## File Upload Guidelines

### Supported Formats
- PDF (.pdf)
- JPEG Images (.jpg, .jpeg)
- PNG Images (.png)

### File Size Limits
- Maximum file size: 16 MB per file
- Recommended: 1-5 MB for optimal performance

### Naming Conventions
Files are automatically renamed with timestamps for organization:
- Questions: `questions_[timestamp]_[original_name]`
- Answers: `answers_[timestamp]_[original_name]`
- Student responses: `answers_[student_id]_[timestamp]_[original_name]`

## Data Storage

All uploaded files and evaluation data are stored locally:

```
API/
└── uploads/          # All uploaded files
└── uil_tutor.db      # SQLite database with evaluations and student data
```

## Configuration

### API Server Configuration
Edit `API/app.py` to modify:
- `UPLOAD_FOLDER`: Where files are stored (default: 'uploads')
- `MAX_FILE_SIZE`: Maximum file upload size (default: 16MB)
- `PORT`: Server port (default: 5000)
- `HOST`: Server host (default: 0.0.0.0)

### Frontend Configuration
Edit `UI/app.js` to modify:
- `API_BASE_URL`: Backend API URL (default: http://localhost:5000/api)
- Notification duration and styling
- Form validation rules

## Troubleshooting

### Issue: API connection refused
**Solution**: 
- Ensure the backend API server is running (see Step 3)
- Check that port 5000 is not blocked by firewall
- Verify `API_BASE_URL` in `app.js` matches your server

### Issue: File upload fails
**Solution**:
- Verify file is in supported format (PDF, JPG, PNG)
- Check file size is under 16MB
- Ensure upload folder has write permissions

### Issue: Evaluation returns error
**Solution**:
- Ensure student ID is entered correctly
- Check that the answer sheet is a clear image
- Verify API server is running and responding

### Issue: Database errors
**Solution**:
- Delete `uil_tutor.db` to reset the database
- Restart the API server
- The database will be recreated automatically

## Performance Tips

1. **Training Data**: Upload at least 100 past question papers for optimal AI accuracy
2. **File Quality**: Ensure uploaded images are clear and properly oriented
3. **Server Resources**: Run on a machine with at least 2GB RAM for multiple concurrent users
4. **Caching**: Clear browser cache if experiencing issues

## Security Considerations

- **File Uploads**: Only PDF and image files are accepted
- **Database**: Uses SQLite with local storage (consider upgrading to PostgreSQL for production)
- **API**: Currently runs on localhost (restrict access in production)
- **CORS**: Enabled for local development (restrict in production)

### Production Deployment Recommendations
1. Use environment variables for configuration
2. Enable HTTPS/SSL
3. Implement user authentication
4. Use a production-grade database (PostgreSQL)
5. Add rate limiting to API endpoints
6. Implement proper logging and monitoring
7. Regular database backups

## Supported Events (Current & Future)

### Currently Supported
- Number Sense
- Mathematics

### Future Expansions
- Debate
- Speech
- Science Olympiad
- Spelling & Vocabulary
- And more...

## Limitations & Disclaimers

- **AI Accuracy**: The AI evaluation accuracy depends on training data quality and quantity
- **Not a Replacement**: This tool supplements professional coaching, it doesn't replace human guidance
- **Browser Compatibility**: Works best on modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
- **Data Retention**: All uploaded files are stored locally - implement appropriate retention policies

## Contributing & Feedback

For bug reports, feature requests, or improvements:
1. Document the issue with clear steps to reproduce
2. Include error messages and screenshots
3. Specify your operating system and browser version
4. Submit to project maintainers

## License

© 2026 UIL Tutor AI - Built for Texas Academic Excellence

## Support

For technical support or questions:
- Check the Troubleshooting section above
- Review the API documentation
- Check browser console for error messages (F12)
- Ensure all files are properly in place

## Changelog

### Version 1.0.0 (Initial Release)
- Basic training and evaluation functionality
- Student history tracking
- Performance analytics
- File upload and management
- Responsive web interface
- RESTful API backend

---

**Built with dedication for Texas UIL students and tutors. Aiming for excellence!**
