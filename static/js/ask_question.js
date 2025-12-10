// Ask a Question page functionality

const uploadForm = document.getElementById('uploadForm');
const questionForm = document.getElementById('questionForm');
const clearBtn = document.getElementById('clearBtn');
const uploadedFiles = document.getElementById('uploadedFiles');
const chatSection = document.getElementById('chatSection');
const chatMessages = document.getElementById('chatMessages');
const loadingSpinner = document.getElementById('loadingSpinner');
const uploadProgress = document.createElement('div');
uploadProgress.className = 'upload-progress';
uploadProgress.innerHTML = '<div class="upload-progress-bar"></div>';

// Add progress bar after upload form
uploadForm.parentNode.insertBefore(uploadProgress, uploadForm.nextSibling);

// Handle file upload with progress
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    const files = document.getElementById('datasetFiles').files;
    
    if (files.length === 0) {
        toast.show('Please select at least one file', 'warning');
        return;
    }
    
    // Validate file sizes
    let totalSize = 0;
    for (let i = 0; i < files.length; i++) {
        totalSize += files[i].size;
        formData.append('files[]', files[i]);
    }
    
    if (totalSize > 16 * 1024 * 1024) {
        toast.show('Total file size exceeds 16MB limit', 'danger');
        return;
    }
    
    loadingSpinner.style.display = 'block';
    uploadProgress.style.display = 'block';
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            toast.show(`Successfully uploaded ${data.files.length} file(s)`, 'success');
            displayUploadedFiles(data.files);
            chatSection.style.display = 'block';
            chatSection.classList.add('fade-in');
            chatMessages.innerHTML = '<div class="alert alert-info"><i class="bi bi-info-circle"></i> Hello! How can I help you with the dataset(s) above?</div>';
            
            // Reset file input
            document.getElementById('datasetFiles').value = '';
        } else {
            toast.show('Error: ' + data.error, 'danger');
        }
    } catch (error) {
        toast.show('Error uploading files: ' + error.message, 'danger');
    } finally {
        loadingSpinner.style.display = 'none';
        uploadProgress.style.display = 'none';
    }
});

// Display uploaded files with tabbed interface
function displayUploadedFiles(files) {
    if (files.length === 0) return;
    
    uploadedFiles.innerHTML = `
        <h5 class="mt-3 mb-3"><i class="bi bi-folder2-open"></i> Uploaded Datasets (${files.length})</h5>
        <div class="dataset-tabs-container">
            <ul class="nav nav-tabs" id="datasetTabs" role="tablist"></ul>
            <div class="tab-content" id="datasetTabContent"></div>
        </div>
    `;
    
    const tabsNav = uploadedFiles.querySelector('#datasetTabs');
    const tabsContent = uploadedFiles.querySelector('#datasetTabContent');
    
    files.forEach((file, index) => {
        const tabId = `dataset-tab-${index}`;
        const isActive = index === 0 ? 'active' : '';
        const isSelected = index === 0 ? 'true' : 'false';
        
        // Create tab button
        const tabButton = document.createElement('li');
        tabButton.className = 'nav-item';
        tabButton.innerHTML = `
            <button class="nav-link ${isActive}" id="${tabId}-tab" data-bs-toggle="tab" 
                    data-bs-target="#${tabId}" type="button" role="tab" 
                    aria-controls="${tabId}" aria-selected="${isSelected}">
                <i class="bi bi-file-earmark-text"></i> ${file.filename}
            </button>
        `;
        tabsNav.appendChild(tabButton);
        
        // Create tab content
        const tabPane = document.createElement('div');
        tabPane.className = `tab-pane fade ${isActive} show`;
        tabPane.id = tabId;
        tabPane.setAttribute('role', 'tabpanel');
        tabPane.setAttribute('aria-labelledby', `${tabId}-tab`);
        tabPane.innerHTML = `
            <div class="dataset-info-card mt-3">
                <div class="row g-3">
                    <div class="col-md-4">
                        <div class="info-stat">
                            <i class="bi bi-file-earmark text-primary"></i>
                            <div class="stat-content">
                                <div class="stat-label">Filename</div>
                                <div class="stat-value">${file.filename}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="info-stat">
                            <i class="bi bi-list-ol text-success"></i>
                            <div class="stat-content">
                                <div class="stat-label">Total Rows</div>
                                <div class="stat-value">${file.rows.toLocaleString()}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="info-stat">
                            <i class="bi bi-grid text-info"></i>
                            <div class="stat-content">
                                <div class="stat-label">Columns</div>
                                <div class="stat-value">${file.columns}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="mt-3">
                    <button class="btn btn-sm btn-outline-primary" type="button" 
                            data-bs-toggle="collapse" data-bs-target="#preview-${index}">
                        <i class="bi bi-eye"></i> Toggle Data Preview
                    </button>
                </div>
                <div class="collapse mt-3" id="preview-${index}">
                    <div class="table-responsive">
                        ${file.preview}
                    </div>
                </div>
            </div>
        `;
        tabsContent.appendChild(tabPane);
    });
    
    uploadedFiles.classList.add('fade-in');
}

// Handle question submission with typing indicator
questionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();
    
    if (!question) return;
    
    // Disable input while processing
    questionInput.disabled = true;
    questionForm.querySelector('button[type="submit"]').disabled = true;
    
    // Add user message
    addMessage('user', question);
    questionInput.value = '';
    
    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(typingIndicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        typingIndicator.remove();
        
        if (response.ok) {
            let assistantMessage = '';
            
            if (data.sql_query) {
                assistantMessage += `<div class="mb-2"><strong><i class="bi bi-code-square"></i> Generated SQL Query:</strong></div>`;
                assistantMessage += `<div class="sql-query">${escapeHtml(data.sql_query)}</div>`;
            }
            
            if (data.query_result) {
                assistantMessage += `<div class="mb-2 mt-3"><strong><i class="bi bi-table"></i> Query Result:</strong></div>`;
                assistantMessage += `<div class="table-container">${data.query_result}</div>`;
            }
            
            if (data.answer) {
                assistantMessage += `<div class="mb-2 mt-3"><strong><i class="bi bi-chat-left-text"></i> Final Answer:</strong></div>`;
                assistantMessage += `<div>${data.answer}</div>`;
            }
            
            if (data.error) {
                assistantMessage += `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> ${data.error}</div>`;
                toast.show(data.error, 'danger');
            }
            
            addMessage('assistant', assistantMessage);
        } else {
            toast.show('Error: ' + data.error, 'danger');
            addMessage('assistant', `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> ${data.error}</div>`);
        }
    } catch (error) {
        typingIndicator.remove();
        toast.show('Error: ' + error.message, 'danger');
        addMessage('assistant', `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> ${error.message}</div>`);
    } finally {
        questionInput.disabled = false;
        questionForm.querySelector('button[type="submit"]').disabled = false;
        questionInput.focus();
    }
});

// Add message to chat with formatting
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    if (role === 'user') {
        messageDiv.innerHTML = `<div class="message-label">You</div><div>${escapeHtml(content)}</div>`;
    } else {
        // Format assistant message content
        const formattedContent = formatAssistantMessage(content);
        messageDiv.innerHTML = `<div class="message-label">Assistant</div><div>${formattedContent}</div>`;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format assistant message for better readability
function formatAssistantMessage(content) {
    // Convert markdown-style formatting to HTML
    let formatted = content;
    
    // Format headers (e.g., **Header:**)
    formatted = formatted.replace(/\*\*([^*]+):\*\*/g, '<h4>$1</h4>');
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Format numbered lists with bold titles
    formatted = formatted.replace(/(\d+\.\s+\*\*[^*]+\*\*)/g, '<strong style="color: #007bff;">$1</strong>');
    
    // Format inline code (backticks)
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Format code blocks
    formatted = formatted.replace(/```sql\n?([\s\S]*?)```/g, '<pre><code class="language-sql">$1</code></pre>');
    formatted = formatted.replace(/```(\w+)?\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    
    // Format bullet points
    formatted = formatted.replace(/^- (.+)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Format paragraphs (double newlines)
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    if (!formatted.startsWith('<')) {
        formatted = '<p>' + formatted + '</p>';
    }
    
    // Clean up extra paragraph tags around other elements
    formatted = formatted.replace(/<p>(<h\d|<ul|<pre|<div)/g, '$1');
    formatted = formatted.replace(/(<\/h\d>|<\/ul>|<\/pre>|<\/div>)<\/p>/g, '$1');
    
    return formatted;
}

// Clear session with confirmation
clearBtn.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear the session and remove all uploaded files?')) return;
    
    clearBtn.disabled = true;
    clearBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Clearing...';
    
    try {
        await fetch('/clear-session', { method: 'POST' });
        toast.show('Session cleared successfully', 'success');
        setTimeout(() => location.reload(), 1000);
    } catch (error) {
        toast.show('Error clearing session: ' + error.message, 'danger');
        clearBtn.disabled = false;
        clearBtn.innerHTML = '<i class="bi bi-trash"></i> Clear Session';
    }
});

// Auto-resize textarea on input
const questionInput = document.getElementById('questionInput');
if (questionInput) {
    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            questionForm.dispatchEvent(new Event('submit'));
        }
    });
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
