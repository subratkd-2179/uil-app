// ==========================================
// UIL Tutor AI - Frontend Application
// ==========================================

const API_BASE_URL = 'http://localhost:5000/api';
let currentStudentData = null;
let studentEvaluationHistory = [];

// ==========================================
// Modal Management
// ==========================================

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}

// ==========================================
// File Upload Handlers
// ==========================================

function updateFileName(input, labelId) {
    const label = document.getElementById(labelId);
    const uploadDiv = input.parentElement;
    
    if (input.files.length > 0) {
        label.innerHTML = `<strong>${input.files[0].name}</strong><br><small>File uploaded successfully</small>`;
        uploadDiv.classList.add('has-file');
    }
}

function setupDragAndDrop(inputId) {
    const input = document.getElementById(inputId);
    const dropZone = input.parentElement;
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--primary)';
        dropZone.style.background = 'rgba(26, 84, 144, 0.05)';
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'var(--border)';
        dropZone.style.background = 'var(--bg-cream)';
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        input.files = e.dataTransfer.files;
        const labelId = dropZone.nextElementSibling?.id;
        if (labelId) updateFileName(input, labelId);
    });
}

// ==========================================
// Training Module
// ==========================================

async function handleTraining(event) {
    event.preventDefault();
    
    const questionsFile = document.getElementById('questionsFile').files[0];
    const answerFile = document.getElementById('answerFile').files[0];
    
    if (!questionsFile || !answerFile) {
        showNotification('Please upload both questions and answer key files.', 'error');
        return;
    }
    
    // Validate file types
    const validTypes = ['application/pdf', 'image/jpeg', 'image/png'];
    if (!validTypes.includes(questionsFile.type) || !validTypes.includes(answerFile.type)) {
        showNotification('Please upload PDF or image files only.', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('questions', questionsFile);
    formData.append('answers', answerFile);
    
    showLoadingSpinner('trainModal');
    
    try {
        const response = await fetch(`${API_BASE_URL}/train`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Training data uploaded successfully! The AI model is now learning from your question papers.', 'success');
            resetTrainingForm();
            closeModal('trainModal');
        } else {
            showNotification(result.error || 'Failed to process training data.', 'error');
        }
    } catch (error) {
        console.error('Training error:', error);
        showNotification('Error uploading training data. Please check your connection.', 'error');
    } finally {
        hideLoadingSpinner('trainModal');
    }
}

function resetTrainingForm() {
    document.getElementById('questionsFile').value = '';
    document.getElementById('answerFile').value = '';
    document.getElementById('questionsLabel').innerHTML = 'Click to upload or drag and drop<br><small>PDF, JPG, or PNG</small>';
    document.getElementById('answerLabel').innerHTML = 'Click to upload or drag and drop<br><small>PDF, JPG, or PNG</small>';
    document.getElementById('questionsFile').parentElement.classList.remove('has-file');
    document.getElementById('answerFile').parentElement.classList.remove('has-file');
}

// ==========================================
// Student Evaluation Module
// ==========================================

async function handleEvaluation(event) {
    event.preventDefault();
    
    const studentId = document.getElementById('studentId').value.trim();
    const answersFile = document.getElementById('studentAnswers').files[0];
    
    if (!studentId) {
        showNotification('Please enter a student ID.', 'error');
        return;
    }
    
    if (!answersFile) {
        showNotification('Please upload an answer sheet.', 'error');
        return;
    }
    
    // Validate student ID format
    if (!isValidStudentId(studentId)) {
        showNotification('Invalid student ID format.', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('student_id', studentId);
    formData.append('answers', answersFile);
    
    showLoadingSpinner('evalModal');
    
    try {
        const response = await fetch(`${API_BASE_URL}/evaluate`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            currentStudentData = {
                studentId: studentId,
                ...result
            };
            displayEvaluationResults(result);
            showNotification('Evaluation completed successfully!', 'success');
        } else {
            showNotification(result.error || 'Evaluation failed.', 'error');
        }
    } catch (error) {
        console.error('Evaluation error:', error);
        showNotification('Error evaluating student. Please check your connection.', 'error');
    } finally {
        hideLoadingSpinner('evalModal');
    }
}

function displayEvaluationResults(results) {
    document.getElementById('correctAnswers').textContent = results.correct || '0';
    document.getElementById('wrongAnswers').textContent = results.wrong || '0';
    document.getElementById('resultsSection').style.display = 'block';
}

function resetEvaluationForm() {
    document.getElementById('studentId').value = '';
    document.getElementById('studentAnswers').value = '';
    document.getElementById('studentLabel').innerHTML = 'Click to upload or drag and drop<br><small>PDF, JPG, or PNG</small>';
    document.getElementById('studentAnswers').parentElement.classList.remove('has-file');
    document.getElementById('resultsSection').style.display = 'none';
}

// ==========================================
// Detailed Evaluation Display
// ==========================================

function viewDetailedEval() {
    if (!currentStudentData) {
        showNotification('No evaluation data available.', 'error');
        return;
    }
    
    closeModal('evalModal');
    
    // Populate detailed modal with current student data
    const detailedModal = document.getElementById('detailedModal');
    const studentName = detailedModal.querySelector('.student-info h4');
    const studentIdText = detailedModal.querySelector('.student-info p');
    const scoreValue = detailedModal.querySelector('.score-badge');
    
    studentName.textContent = currentStudentData.studentName || 'Student';
    studentIdText.textContent = `Student ID: ${currentStudentData.studentId}`;
    scoreValue.innerHTML = `${Math.round((currentStudentData.correct / (currentStudentData.correct + currentStudentData.wrong)) * 100)}%<br><small style="font-size: 0.75rem; font-weight: 400;">Accuracy</small>`;
    
    // Update stats
    updateDetailedStats(currentStudentData);
    
    openModal('detailedModal');
}

function updateDetailedStats(data) {
    const total = (data.correct || 0) + (data.wrong || 0);
    const statsItems = document.querySelectorAll('.stat-item');
    
    if (statsItems.length >= 4) {
        statsItems[0].querySelector('.stat-value').textContent = '1';
        statsItems[1].querySelector('.stat-value').textContent = data.correct || '0';
        statsItems[2].querySelector('.stat-value').textContent = data.wrong || '0';
        statsItems[3].querySelector('.stat-value').textContent = '+0%';
    }
}

async function viewPriorEvals() {
    const studentId = document.getElementById('studentId').value.trim();
    
    if (!studentId) {
        showNotification('Please enter a student ID first.', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/student/${studentId}/history`);
        const result = await response.json();
        
        if (response.ok) {
            displayPriorEvaluations(result.history);
        } else {
            showNotification('No prior evaluations found.', 'info');
        }
    } catch (error) {
        console.error('Error fetching history:', error);
        showNotification('Error retrieving evaluation history.', 'error');
    }
}

function displayPriorEvaluations(history) {
    if (!history || history.length === 0) {
        showNotification('No prior evaluations found for this student.', 'info');
        return;
    }
    
    let html = '<div style="margin-top: 1.5rem;"><h4 style="font-family: \'Fraunces\', serif; color: var(--primary-dark); margin-bottom: 1rem;">Evaluation History</h4>';
    
    history.forEach((eval, index) => {
        const accuracy = ((eval.correct / (eval.correct + eval.wrong)) * 100).toFixed(2);
        html += `
            <div class="eval-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>Test ${index + 1}</strong><br>
                        <small style="color: var(--text-light);">${new Date(eval.date).toLocaleDateString()}</small>
                    </div>
                    <div class="score-badge" style="padding: 0.5rem 1rem; font-size: 1rem;">
                        ${accuracy}%
                    </div>
                </div>
                <div style="margin-top: 0.75rem; color: var(--text-medium); font-size: 0.9rem;">
                    Correct: ${eval.correct} | Wrong: ${eval.wrong}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    // Create a temporary modal to display history
    const historyModal = document.createElement('div');
    historyModal.className = 'modal active';
    historyModal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Evaluation History</h3>
                <button class="close-btn" onclick="this.parentElement.parentElement.parentElement.remove()">✕</button>
            </div>
            ${html}
            <button onclick="this.closest('.modal').classList.remove('active'); setTimeout(() => this.closest('.modal').remove(), 300);" style="margin-top: 1.5rem;">Close</button>
        </div>
    `;
    document.body.appendChild(historyModal);
}

// ==========================================
// Utility Functions
// ==========================================

function isValidStudentId(id) {
    // Allow alphanumeric IDs, adjust regex as needed
    return /^[A-Z0-9]{3,}$/i.test(id);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <style>
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                border-radius: 12px;
                font-weight: 500;
                z-index: 2000;
                animation: slideInRight 0.3s ease-out;
            }
            .notification-success {
                background: linear-gradient(135deg, var(--success), #48bb78);
                color: white;
            }
            .notification-error {
                background: linear-gradient(135deg, #e53e3e, #c53030);
                color: white;
            }
            .notification-info {
                background: linear-gradient(135deg, var(--primary), var(--primary-light));
                color: white;
            }
            @keyframes slideInRight {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOutRight {
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
        </style>
        ${message}
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showLoadingSpinner(containerId) {
    const container = document.getElementById(containerId);
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.innerHTML = `
        <style>
            .loading-spinner {
                text-align: center;
                padding: 1.5rem;
            }
            .spinner {
                border: 4px solid var(--border);
                border-top-color: var(--primary);
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        </style>
        <div class="spinner"></div>
        <p style="margin-top: 1rem; color: var(--text-light);">Processing...</p>
    `;
    container.appendChild(spinner);
}

function hideLoadingSpinner(containerId) {
    const spinner = document.getElementById(containerId).querySelector('.loading-spinner');
    if (spinner) spinner.remove();
}

function handleExit() {
    if (confirm('Are you sure you want to exit? Any unsaved changes will be lost.')) {
        showNotification('Thank you for using UIL Tutor AI! Keep practicing for excellence.', 'success');
        setTimeout(() => {
            window.close();
        }, 2000);
    }
}

// ==========================================
// Initialization
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    // Setup drag and drop for all file inputs
    setupDragAndDrop('questionsFile');
    setupDragAndDrop('answerFile');
    setupDragAndDrop('studentAnswers');
    
    // Setup answer sheet buttons
    const answerSheetButtons = document.querySelectorAll('.sheet-btn');
    answerSheetButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const sheetNum = this.textContent.trim();
            if (sheetNum !== '>') {
                showNotification(`Opening answer sheet ${sheetNum}...`, 'info');
            } else {
                showNotification('View more sheets feature coming soon!', 'info');
            }
        });
    });
    
    console.log('UIL Tutor AI application initialized successfully');
});
