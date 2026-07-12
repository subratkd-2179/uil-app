# UIL Tutor AI - Quick Start Guide

Get up and running with UIL Tutor AI in 5 minutes!

## Prerequisites
- Python 3.8+ installed on your computer
- Any modern web browser
- Sample question papers (PDF or images)

## Quick Start (5 Minutes)

### Step 1: Install Dependencies (1 minute)

Open Command Prompt/PowerShell and run:

```bash
cd c:\UIL APP\API
pip install -r requirements.txt
```

Wait for installation to complete (you'll see "Successfully installed" messages).

### Step 2: Start the Server (30 seconds)

In the same Command Prompt, run:

```bash
python app.py
```

You should see:
```
==================================================
UIL Tutor AI - Backend API Server
==================================================
API running on: http://localhost:5000
==================================================
```

**Leave this window open!**

### Step 3: Open the Application (30 seconds)

Open this file in your web browser:
```
c:\UIL APP\UI\uil-tutor-ai.html
```

You should see the UIL Tutor AI homepage with three menu options.

### Step 4: Test the Application

#### Option A: Train the AI
1. Click "Train the Tutor"
2. Upload a sample question paper
3. Upload the answer key
4. Click "Upload & Train"

#### Option B: Evaluate a Student
1. Click "Student Evaluation"
2. Enter a student ID (e.g., "STUDENT001")
3. Upload the student's answer sheet
4. Click "Evaluate"
5. View the results!

## Features at a Glance

| Feature | Steps |
|---------|-------|
| **Train AI** | Click Menu → Train the Tutor → Upload Files → Process |
| **Evaluate** | Click Menu → Student Evaluation → Enter ID → Upload → Evaluate |
| **View History** | During Evaluation → View Prior Evaluations |
| **Detailed Report** | During Evaluation → View Detailed Evaluation |

## Common Issues & Quick Fixes

| Issue | Fix |
|-------|-----|
| "Connection refused" | Ensure Python server is still running |
| "File upload failed" | Check file is PDF/JPG/PNG and under 16MB |
| "Student not found" | Make sure student ID was evaluated first |
| "Page won't load" | Refresh browser (Ctrl+R) |

## Next Steps

1. **Read the full README**: See `c:\UIL APP\README.md` for complete documentation
2. **Prepare training data**: Gather 100+ past question papers for better accuracy
3. **Setup student database**: Evaluate multiple students to build history
4. **Review analytics**: Use "View Prior Evaluations" to track progress

## Keyboard Shortcuts

- `Ctrl+R` - Refresh the web page
- `F12` - Open browser developer tools (for debugging)
- `Ctrl+Shift+Delete` - Clear browser cache (if issues occur)


## File Locations

```
Important Files:
c:\UIL APP\UI\uil-tutor-ai.html     ← Main web app
c:\UIL APP\UI\app.js                ← Frontend code
c:\UIL APP\API\app.py               ← Backend server
c:\UIL APP\API\uploads\             ← Uploaded files (auto-created)
c:\UIL APP\API\uil_tutor.db         ← Database (auto-created)
```

## Support Commands

Keep these commands handy:

```bash
# Start the server(API)
cd c:\UIL APP\API
python app.py

#UI
cd "C:\UIL APP"
python -m http.server 8000

# Check if API is working
curl http://localhost:5000/api/health

# View uploaded files
dir c:\UIL APP\API\uploads\

# Reset database (deletes all data)
del c:\UIL APP\API\uil_tutor.db

# swagger url
http://localhost:5000/api/swagger.json
```

## Tips for Best Results

1. **High-Quality Uploads**: Use clear, properly oriented PDFs or images
2. **Consistent IDs**: Use format like "JD2024" or "STUDENT001"
3. **Regular Training**: Upload more practice papers for better accuracy
4. **Track Progress**: Evaluate the same student multiple times to see improvement
5. **Check Weak Areas**: Review focus areas to guide studying

## What's Next?

- Add more training data for improved accuracy
- Evaluate multiple students and compare performance
- Use detailed reports to plan targeted practice sessions
- Monitor improvement trends over time

---

Need help? Check the full README at: `c:\UIL APP\README.md`

**Questions? Check the browser console (F12) for error messages!**
