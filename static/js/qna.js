// Unified Q&A functionality for datasets, documents, and YouTube

// ============= DATASET Q&A =============
const uploadForm = document.getElementById('uploadForm');
const questionForm = document.getElementById('questionForm');
const chatMessages = document.getElementById('chatMessages');
const clearDatasetSession = document.getElementById('clearDatasetSession');

if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData();
        const files = document.getElementById('fileInput').files;
        
        if (files.length === 0) {
            toast.show('Please select at least one file', 'warning');
            return;
        }
        
        for (let file of files) {
            formData.append('files[]', file);
        }
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                displayUploadedFiles(data.files);
                // Show chat section after successful upload
                document.getElementById('datasetChatSection').style.display = 'block';
                toast.show('Files uploaded successfully!', 'success');
            } else {
                toast.show('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            toast.show('Error: ' + error.message, 'danger');
        }
    });
}

if (questionForm) {
    questionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const questionInput = document.getElementById('questionInput');
        const question = questionInput.value.trim();
        
        if (!question) return;
        
        questionInput.disabled = true;
        addMessage('user', question, chatMessages);
        questionInput.value = '';
        
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(typingIndicator);
        
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            
            const data = await response.json();
            typingIndicator.remove();
            
            if (response.ok) {
                let answerHtml = data.answer || data.error || 'No response';
                if (data.sql_query) {
                    answerHtml = `<div class="mb-2"><strong>SQL Query:</strong><pre>${escapeHtml(data.sql_query)}</pre></div>` + answerHtml;
                }
                if (data.query_result) {
                    answerHtml += `<div class="mt-2"><strong>Results:</strong>${data.query_result}</div>`;
                }
                addMessage('assistant', answerHtml, chatMessages);
            } else {
                toast.show('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            typingIndicator.remove();
            toast.show('Error: ' + error.message, 'danger');
        } finally {
            questionInput.disabled = false;
            questionInput.focus();
        }
    });
}

if (clearDatasetSession) {
    clearDatasetSession.addEventListener('click', async () => {
        if (confirm('Clear all uploaded datasets?')) {
            await clearSession();
            location.reload();
        }
    });
}

function displayUploadedFiles(files) {
    const container = document.getElementById('uploadedFilesInfo');
    if (!container) return;
    
    let html = '<div class="mt-3"><h6>Uploaded Files:</h6><div class="dataset-tabs-container"><ul class="nav nav-tabs dataset-tabs" role="tablist">';
    
    files.forEach((file, index) => {
        html += `
            <li class="nav-item" role="presentation">
                <button class="nav-link ${index === 0 ? 'active' : ''}" data-bs-toggle="tab" 
                        data-bs-target="#dataset${index}" type="button">
                    ${file.filename}
                </button>
            </li>`;
    });
    
    html += '</ul><div class="tab-content dataset-tab-content">';
    
    files.forEach((file, index) => {
        html += `
            <div class="tab-pane fade ${index === 0 ? 'show active' : ''}" id="dataset${index}">
                <div class="dataset-info">
                    <p><strong>Rows:</strong> ${file.rows}</p>
                    <p><strong>Columns:</strong> ${file.columns}</p>
                </div>
                ${file.preview}
            </div>`;
    });
    
    html += '</div></div></div>';
    container.innerHTML = html;
}

// ============= DOCUMENT Q&A =============
const docUploadForm = document.getElementById('docUploadForm');
const docQuestionForm = document.getElementById('docQuestionForm');
const docChatMessages = document.getElementById('docChatMessages');
const clearDocSession = document.getElementById('clearDocSession');

if (docUploadForm) {
    docUploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(docUploadForm);
        const submitBtn = docUploadForm.querySelector('button[type="submit"]');
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Processing...';
        
        try {
            const response = await fetch('/document-upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-upload"></i> Upload & Process';
            
            if (response.ok) {
                displayDocInfo(data.metadata);
                // Show chat section after successful upload
                document.getElementById('documentChatSection').style.display = 'block';
                toast.show(data.message, 'success');
                document.getElementById('docFileInput').value = '';
            } else {
                toast.show('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-upload"></i> Upload & Process';
            toast.show('Error: ' + error.message, 'danger');
        }
    });
}

if (docQuestionForm) {
    docQuestionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const questionInput = document.getElementById('docQuestionInput');
        const question = questionInput.value.trim();
        
        if (!question) return;
        
        questionInput.disabled = true;
        addMessage('user', question, docChatMessages);
        questionInput.value = '';
        
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        docChatMessages.appendChild(typingIndicator);
        
        try {
            const response = await fetch('/document-ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            
            const data = await response.json();
            typingIndicator.remove();
            
            if (response.ok) {
                let answerHtml = `<div class="mb-3">${data.answer}</div>`;
                
                if (data.sources && data.sources.length > 0) {
                    answerHtml += `<div class="mt-3"><strong><i class="bi bi-card-text"></i> Source Excerpts:</strong></div>`;
                    answerHtml += `<div class="accordion" id="docSourcesAccordion">`;
                    
                    data.sources.forEach((source, index) => {
                        const relevanceBadge = source.relevance ? `<span class="badge bg-success ms-2">${source.relevance} relevant</span>` : '';
                        answerHtml += `
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                            data-bs-target="#docCollapse${index}">
                                        Excerpt ${source.segment}${relevanceBadge}
                                    </button>
                                </h2>
                                <div id="docCollapse${index}" class="accordion-collapse collapse" 
                                     data-bs-parent="#docSourcesAccordion">
                                    <div class="accordion-body">
                                        <small class="text-muted">${source.content}</small>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    answerHtml += `</div>`;
                }
                
                addMessage('assistant', answerHtml, docChatMessages);
            } else {
                toast.show('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            typingIndicator.remove();
            toast.show('Error: ' + error.message, 'danger');
        } finally {
            questionInput.disabled = false;
            questionInput.focus();
        }
    });
}

if (clearDocSession) {
    clearDocSession.addEventListener('click', async () => {
        if (confirm('Clear uploaded document?')) {
            await clearSession();
            location.reload();
        }
    });
}

function displayDocInfo(metadata) {
    const container = document.getElementById('docInfo');
    if (!container || !metadata) return;
    
    container.innerHTML = `
        <div class="card mt-3">
            <div class="card-header"><h6>Document Info</h6></div>
            <div class="card-body">
                <p class="mb-1"><strong>File:</strong> ${metadata.filename}</p>
                <p class="mb-1"><strong>Words:</strong> ${metadata.word_count.toLocaleString()}</p>
                <p class="mb-1"><strong>Characters:</strong> ${metadata.character_count.toLocaleString()}</p>
                <p class="mb-1"><strong>Est. Reading Time:</strong> ${metadata.estimated_reading_time} min</p>
                <p class="mb-0"><strong>Chunks:</strong> ${metadata.chunk_count}</p>
            </div>
        </div>
    `;
}

// ============= YOUTUBE Q&A =============
const youtubeForm = document.getElementById('youtubeForm');
const ytQuestionForm = document.getElementById('ytQuestionForm');
const videoPreview = document.getElementById('videoPreview');
const youtubeQaSection = document.getElementById('youtubeQaSection');
const ytChatMessages = document.getElementById('ytChatMessages');
const ytLoadingSpinner = document.getElementById('ytLoadingSpinner');
const clearYoutubeSession = document.getElementById('clearYoutubeSession');

if (youtubeForm) {
    youtubeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const videoUrl = document.getElementById('videoUrl').value.trim();
        const videoId = extractVideoId(videoUrl);
        
        if (!videoId) {
            toast.show('Invalid YouTube URL', 'danger');
            return;
        }
        
        const submitBtn = youtubeForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Analyzing...';
        
        videoPreview.innerHTML = `
            <div class="video-container fade-in mt-3">
                <iframe src="https://www.youtube.com/embed/${videoId}" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen>
                </iframe>
            </div>
        `;
        
        ytLoadingSpinner.style.display = 'block';
        
        try {
            const response = await fetch('/youtube-analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_url: videoUrl })
            });
            
            const data = await response.json();
            
            ytLoadingSpinner.style.display = 'none';
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-play-circle"></i> Analyze Video Content';
            
            if (response.ok) {
                youtubeQaSection.style.display = 'block';
                youtubeQaSection.classList.add('fade-in');
                ytChatMessages.innerHTML = `<div class="alert alert-success"><i class="bi bi-check-circle"></i> Video analyzed successfully! Found ${data.chunks} text segments. Ask me anything about this video.</div>`;
                toast.show('Video analyzed successfully!', 'success');
                document.getElementById('ytQuestionInput').focus();
            } else {
                toast.show('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            ytLoadingSpinner.style.display = 'none';
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-play-circle"></i> Analyze Video Content';
            toast.show('Error: ' + error.message, 'danger');
        }
    });
}

if (ytQuestionForm) {
    ytQuestionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const questionInput = document.getElementById('ytQuestionInput');
        const question = questionInput.value.trim();
        
        if (!question) return;
        
        questionInput.disabled = true;
        addMessage('user', question, ytChatMessages);
        questionInput.value = '';
        
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        ytChatMessages.appendChild(typingIndicator);
        
        try {
            const response = await fetch('/youtube-ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            
            const data = await response.json();
            typingIndicator.remove();
            
            if (response.ok) {
                let answerHtml = `<div class="mb-3">${data.answer}</div>`;
                
                if (data.sources && data.sources.length > 0) {
                    answerHtml += `<div class="mt-3"><strong><i class="bi bi-card-text"></i> Source Segments:</strong></div>`;
                    answerHtml += `<div class="accordion" id="sourcesAccordion">`;
                    
                    data.sources.forEach((source, index) => {
                        const relevanceBadge = source.relevance ? `<span class="badge bg-success ms-2">${source.relevance} relevant</span>` : '';
                        answerHtml += `
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                            data-bs-target="#collapse${index}">
                                        Segment ${source.segment}${relevanceBadge}
                                    </button>
                                </h2>
                                <div id="collapse${index}" class="accordion-collapse collapse" 
                                     data-bs-parent="#sourcesAccordion">
                                    <div class="accordion-body">
                                        <small class="text-muted">${source.content}</small>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    answerHtml += `</div>`;
                }
                
                addMessage('assistant', answerHtml, ytChatMessages);
            } else {
                toast.show('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            typingIndicator.remove();
            toast.show('Error: ' + error.message, 'danger');
        } finally {
            questionInput.disabled = false;
            questionInput.focus();
        }
    });
}

if (clearYoutubeSession) {
    clearYoutubeSession.addEventListener('click', async () => {
        if (confirm('Clear video analysis?')) {
            await clearSession();
            location.reload();
        }
    });
}

// ============= TAB NAVIGATION =============
document.addEventListener('DOMContentLoaded', function() {
    // Handle initial load with hash from URL
    const initialHash = window.location.hash.slice(1);
    if (initialHash) {
        const targetTab = document.getElementById(initialHash + '-tab');
        if (targetTab) {
            const tab = new bootstrap.Tab(targetTab);
            tab.show();
        }
    }
    
    // Update URL hash when tab changes
    const tabElements = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabElements.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            const targetId = event.target.getAttribute('data-bs-target').substring(1);
            history.pushState(null, null, '#' + targetId);
        });
    });
    
    // Check language availability for coding exercise
    checkLanguageAvailability();
});

// ============= UTILITY FUNCTIONS =============
function addMessage(role, content, container) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    if (role === 'user') {
        messageDiv.innerHTML = `<div class="message-label">You</div><div>${escapeHtml(content)}</div>`;
    } else {
        messageDiv.innerHTML = `<div class="message-label">Assistant</div><div>${content}</div>`;
    }
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function extractVideoId(url) {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : null;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function checkLanguageAvailability() {
    try {
        const response = await fetch('/check-languages');
        const data = await response.json();
        
        if (response.ok && data.available) {
            const languageSelect = document.getElementById('codingLanguage');
            const languageInfo = document.getElementById('languageInfo');
            
            if (languageSelect && languageInfo) {
                const options = languageSelect.querySelectorAll('option');
                const availableCount = Object.values(data.available).filter(v => v).length;
                
                // Update option labels with availability status
                options.forEach(option => {
                    const lang = option.value;
                    if (data.available[lang]) {
                        option.textContent = option.textContent.replace(' ✓', '').replace(' (cloud)', '') + ' ✓';
                        option.style.color = '#28a745';
                        option.title = lang === 'python' ? 'Local execution' : 'Cloud execution via Piston API';
                    } else {
                        option.textContent = option.textContent.replace(' ✓', '') + ' (unavailable)';
                        option.style.color = '#6c757d';
                        option.disabled = true;
                    }
                });
                
                languageInfo.innerHTML = `<i class="bi bi-cloud-check"></i> ${availableCount} language${availableCount !== 1 ? 's' : ''} available (Python: local, others: cloud-based)`;
                languageInfo.style.color = '#28a745';
            }
        }
    } catch (error) {
        console.error('Error checking language availability:', error);
        const languageInfo = document.getElementById('languageInfo');
        if (languageInfo) {
            languageInfo.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Unable to check language availability';
            languageInfo.style.color = '#dc3545';
        }
    }
}

async function clearSession() {
    try {
        await fetch('/clear-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
    } catch (error) {
        console.error('Error clearing session:', error);
    }
}

// ============= CODING EXERCISE =============
const codingGenerateForm = document.getElementById('codingGenerateForm');
const codingSubmitForm = document.getElementById('codingSubmitForm');
const getHintBtn = document.getElementById('getHintBtn');
const getSolutionBtn = document.getElementById('getSolutionBtn');
const regenerateChallengeBtn = document.getElementById('regenerateChallengeBtn');

// Regenerate Challenge button handler
if (regenerateChallengeBtn) {
    regenerateChallengeBtn.addEventListener('click', () => {
        // Show generate form and hide regenerate button
        document.getElementById('generateExerciseCard').style.display = 'block';
        document.getElementById('regenerateChallengeCard').style.display = 'none';
        
        // Hide all exercise-related displays
        document.getElementById('exerciseDisplay').style.display = 'none';
        document.getElementById('testCasesDisplay').style.display = 'none';
        document.getElementById('codingSolutionBoard').style.display = 'none';
        document.getElementById('feedbackDisplay').style.display = 'none';
        document.getElementById('hintDisplay').style.display = 'none';
        document.getElementById('solutionDisplay').style.display = 'none';
        document.getElementById('testResultsDisplay').style.display = 'none';
        
        // Clear form and editor
        document.getElementById('codingTopic').value = '';
        document.getElementById('codeEditor').value = '';
        
        // Scroll to form
        document.getElementById('generateExerciseCard').scrollIntoView({ behavior: 'smooth' });
    });
}

if (codingGenerateForm) {
    codingGenerateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const topic = document.getElementById('codingTopic').value.trim();
        const difficulty = document.getElementById('codingDifficulty').value;
        const language = document.getElementById('codingLanguage').value;
        
        const submitBtn = codingGenerateForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Generating...';
        
        try {
            const response = await fetch('/coding-generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, difficulty, language })
            });
            
            const data = await response.json();
            
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-stars"></i> Generate Exercise';
            
            if (response.ok) {
                // Hide generate form and show regenerate button
                document.getElementById('generateExerciseCard').style.display = 'none';
                document.getElementById('regenerateChallengeCard').style.display = 'block';
                
                // Display exercise (unescape any remaining escape sequences in HTML content)
                document.getElementById('exerciseDisplay').style.display = 'block';
                let exerciseHtml = data.exercise
                    .replace(/\\n/g, '\n')
                    .replace(/\\t/g, '\t')
                    .replace(/\\"/g, '"');
                document.getElementById('exerciseContent').innerHTML = exerciseHtml;
                
                // Show hint and solution buttons
                document.getElementById('exerciseButtons').style.display = 'block';
                
                // Show solution board
                document.getElementById('codingSolutionBoard').style.display = 'block';
                
                // Clear previous results
                document.getElementById('feedbackDisplay').style.display = 'none';
                document.getElementById('hintDisplay').style.display = 'none';
                document.getElementById('solutionDisplay').style.display = 'none';
                document.getElementById('testResultsDisplay').style.display = 'none';
                
                // Populate code editor with starter code
                const codeEditor = document.getElementById('codeEditor');
                if (data.starter_code) {
                    // Unescape newlines and other escape sequences
                    let code = data.starter_code
                        .replace(/\\n/g, '\n')
                        .replace(/\\t/g, '\t')
                        .replace(/\\"/g, '"')
                        .replace(/\\\\/g, '\\');
                    codeEditor.value = code;
                } else {
                    codeEditor.value = '';
                }
                
                // Display visible test cases if available
                console.log('Visible test cases:', data.visible_test_cases);
                console.log('Hidden test cases:', data.hidden_test_cases);
                
                if (data.visible_test_cases && data.visible_test_cases.length > 0) {
                    const testCasesDisplay = document.getElementById('testCasesDisplay');
                    const testCasesContent = document.getElementById('testCasesContent');
                    
                    // Show test cases section
                    testCasesDisplay.style.display = 'block';
                    
                    // Display visible test cases
                    let casesHtml = '<div class="test-cases-list">';
                    casesHtml += '<p class="text-muted mb-3"><i class="bi bi-info-circle"></i> Your code will be tested with these visible test cases and additional hidden test cases.</p>';
                    
                    data.visible_test_cases.forEach((testCase, index) => {
                        // Unescape code for display
                        let unescapedCode = testCase.code
                            .replace(/\\n/g, '\n')
                            .replace(/\\t/g, '\t')
                            .replace(/\\"/g, '"')
                            .replace(/\\\\/g, '\\');
                        
                        casesHtml += `<div class="card mb-3">
                            <div class="card-header bg-light">
                                <strong>Test Case ${index + 1}</strong>
                            </div>
                            <div class="card-body">
                                <p><strong>Code:</strong></p>
                                <pre class="bg-light p-2 border rounded"><code>${escapeHtml(unescapedCode)}</code></pre>
                                <p><strong>Expected Output:</strong> <code>${escapeHtml(testCase.expected_output)}</code></p>
                            </div>
                        </div>`;
                    });
                    
                    const hiddenCount = data.hidden_test_cases ? data.hidden_test_cases.length : 0;
                    casesHtml += `<div class="alert alert-info">
                        <i class="bi bi-eye-slash"></i> <strong>${hiddenCount} hidden test case${hiddenCount !== 1 ? 's' : ''}</strong> will also be evaluated when you run your code.
                    </div>`;
                    
                    casesHtml += '</div>';
                    testCasesContent.innerHTML = casesHtml;
                } else {
                    document.getElementById('testCasesDisplay').style.display = 'none';
                }
                
                toast.show(`${difficulty} exercise generated! Happy coding!`, 'success');
                
                // Scroll to exercise
                document.getElementById('exerciseDisplay').scrollIntoView({ behavior: 'smooth' });
            } else {
                toast.show('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-stars"></i> Generate Exercise';
            toast.show('Error: ' + error.message, 'danger');
        }
    });
}

// Run Code button handler
const runCodeBtn = document.getElementById('runCodeBtn');
if (runCodeBtn) {
    runCodeBtn.addEventListener('click', async () => {
        const code = document.getElementById('codeEditor').value.trim();
        const language = document.getElementById('codingLanguage').value;
        
        if (!code) {
            toast.show('Please write your code first!', 'warning');
            return;
        }
        
        runCodeBtn.disabled = true;
        runCodeBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Running all test cases...';
        
        try {
            const response = await fetch('/coding-run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language })
            });
            
            const data = await response.json();
            
            runCodeBtn.disabled = false;
            runCodeBtn.innerHTML = '<i class="bi bi-play-circle"></i> Run Code';
            
            if (response.ok) {
                // Display test results
                document.getElementById('testResultsDisplay').style.display = 'block';
                document.getElementById('testResultsContent').innerHTML = data.result;
                
                const message = data.all_passed ? 
                    `All ${data.total} test cases passed! 🎉` : 
                    `${data.passed}/${data.total} test cases passed`;
                    
                toast.show(message, data.all_passed ? 'success' : 'warning');
                
                // Scroll to results
                document.getElementById('testResultsDisplay').scrollIntoView({ behavior: 'smooth' });
            } else {
                toast.show('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            runCodeBtn.disabled = false;
            runCodeBtn.innerHTML = '<i class="bi bi-play-circle"></i> Run Code';
            toast.show('Error: ' + error.message, 'danger');
        }
    });
}

if (codingSubmitForm) {
    codingSubmitForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const code = document.getElementById('codeEditor').value.trim();
        const language = document.getElementById('codingLanguage').value;
        
        if (!code) {
            toast.show('Please write your code first!', 'warning');
            return;
        }
        
        const submitBtn = codingSubmitForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Validating...';
        
        // Hide previous results
        document.getElementById('hintDisplay').style.display = 'none';
        document.getElementById('solutionDisplay').style.display = 'none';
        
        try {
            const response = await fetch('/coding-validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language })
            });
            
            const data = await response.json();
            
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-check2-circle"></i> Submit & Get AI Feedback';
            
            if (response.ok) {
                // Hide test results when getting AI feedback
                document.getElementById('testResultsDisplay').style.display = 'none';
                
                // Display feedback (collapsed by default)
                const feedbackDisplay = document.getElementById('feedbackDisplay');
                feedbackDisplay.style.display = 'block';
                document.getElementById('feedbackContent').innerHTML = data.feedback;
                document.getElementById('feedbackContent').classList.remove('collapsed');
                document.getElementById('feedbackToggleIcon').classList.remove('bi-chevron-down');
                document.getElementById('feedbackToggleIcon').classList.add('bi-chevron-up');
                
                toast.show('AI feedback generated! Check below.', 'success');
                
                // Scroll to feedback
                feedbackDisplay.scrollIntoView({ behavior: 'smooth' });
            } else {
                toast.show('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-check2-circle"></i> Submit & Validate';
            toast.show('Error: ' + error.message, 'danger');
        }
    });
}

if (getHintBtn) {
    getHintBtn.addEventListener('click', async () => {
        getHintBtn.disabled = true;
        getHintBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Loading...';
        
        try {
            const response = await fetch('/coding-hint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            getHintBtn.disabled = false;
            getHintBtn.innerHTML = '<i class="bi bi-lightbulb"></i> Hint';
            
            if (response.ok) {
                const hintDisplay = document.getElementById('hintDisplay');
                const hintContent = document.getElementById('hintContent');
                const hintIcon = document.getElementById('hintToggleIcon');
                
                hintDisplay.style.display = 'block';
                hintContent.innerHTML = data.hint;
                hintContent.classList.remove('collapsed');
                hintIcon.classList.remove('bi-chevron-down');
                hintIcon.classList.add('bi-chevron-up');
                
                toast.show('Hint loaded!', 'info');
                
                // Scroll to hint
                hintDisplay.scrollIntoView({ behavior: 'smooth' });
            } else {
                toast.show('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            getHintBtn.disabled = false;
            getHintBtn.innerHTML = '<i class="bi bi-lightbulb"></i> Hint';
            toast.show('Error: ' + error.message, 'danger');
        }
    });
}

if (getSolutionBtn) {
    getSolutionBtn.addEventListener('click', async () => {
        if (!confirm('Are you sure? Viewing the solution will reveal the complete answer.')) {
            return;
        }
        
        getSolutionBtn.disabled = true;
        getSolutionBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Loading...';
        
        try {
            const response = await fetch('/coding-solution', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            getSolutionBtn.disabled = false;
            getSolutionBtn.innerHTML = '<i class="bi bi-check-circle"></i> Solution';
            
            if (response.ok) {
                const solutionDisplay = document.getElementById('solutionDisplay');
                const solutionContent = document.getElementById('solutionContent');
                const solutionIcon = document.getElementById('solutionToggleIcon');
                
                solutionDisplay.style.display = 'block';
                solutionContent.innerHTML = data.solution;
                solutionContent.classList.remove('collapsed');
                solutionIcon.classList.remove('bi-chevron-down');
                solutionIcon.classList.add('bi-chevron-up');
                
                toast.show('Solution loaded!', 'success');
                
                // Scroll to solution
                solutionDisplay.scrollIntoView({ behavior: 'smooth' });
            } else {
                toast.show('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            getSolutionBtn.disabled = false;
            getSolutionBtn.innerHTML = '<i class="bi bi-check-circle"></i> Solution';
            toast.show('Error: ' + error.message, 'danger');
        }
    });
}

// Toggle functions for hint, solution, and feedback
function toggleFeedback() {
    const content = document.getElementById('feedbackContent');
    const icon = document.getElementById('feedbackToggleIcon');
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        icon.classList.remove('bi-chevron-down');
        icon.classList.add('bi-chevron-up');
    } else {
        content.classList.add('collapsed');
        icon.classList.remove('bi-chevron-up');
        icon.classList.add('bi-chevron-down');
    }
}

function toggleHint() {
    const content = document.getElementById('hintContent');
    const icon = document.getElementById('hintToggleIcon');
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        icon.classList.remove('bi-chevron-down');
        icon.classList.add('bi-chevron-up');
    } else {
        content.classList.add('collapsed');
        icon.classList.remove('bi-chevron-up');
        icon.classList.add('bi-chevron-down');
    }
}

function toggleSolution() {
    const content = document.getElementById('solutionContent');
    const icon = document.getElementById('solutionToggleIcon');
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        icon.classList.remove('bi-chevron-down');
        icon.classList.add('bi-chevron-up');
    } else {
        content.classList.add('collapsed');
        icon.classList.remove('bi-chevron-up');
        icon.classList.add('bi-chevron-down');
    }
}

function toggleTestResults() {
    const content = document.getElementById('testResultsContent');
    const icon = document.getElementById('testResultsToggleIcon');
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        icon.classList.remove('bi-chevron-down');
        icon.classList.add('bi-chevron-up');
    } else {
        content.classList.add('collapsed');
        icon.classList.remove('bi-chevron-up');
        icon.classList.add('bi-chevron-down');
    }
}

// ============= VIDEO INTERVIEW EXERCISE =============
let interviewState = {
    questions: [],
    currentQuestionIndex: 0,
    answers: [],
    mediaRecorder: null,
    recordedChunks: [],
    recordedBlobs: [],
    stream: null,
    timerInterval: null,
    recordingStartTime: 0,
    recognition: null,
    currentTranscription: '',
    language: 'en-US',
    role: '',
    interview_type: '',
    audioLevelCheck: null,
    audioMonitor: null,
    audioContext: null,
    overallStartTime: 0,
    overallTimerInterval: null,
    maxInterviewTime: 1800 // 30 minutes default
};

document.addEventListener('DOMContentLoaded', function() {
    const interviewSetupForm = document.getElementById('interviewSetupForm');
    const startRecordingBtn = document.getElementById('startRecordingBtn');
    const stopRecordingBtn = document.getElementById('stopRecordingBtn');
    const nextQuestionBtn = document.getElementById('nextQuestionBtn');
    const finishInterviewBtn = document.getElementById('finishInterviewBtn');
    const newInterviewBtn = document.getElementById('newInterviewBtn');

    // Step 1: Setup Interview
    if (interviewSetupForm) {
        interviewSetupForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const role = document.getElementById('interviewRole').value;
            const interview_type = document.getElementById('interviewType').value;
            const interview_language = document.getElementById('interviewLanguage').value;
            const additional_info = document.getElementById('interviewAdditionalInfo').value;

            // Store language for speech recognition
            interviewState.language = interview_language;

            // Show loading
            toast.show('Generating interview questions...', 'info');

            try {
                const response = await fetch('/interview-generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ role, interview_type, additional_info })
                });
                const data = await response.json();
                
                if (response.ok && data.questions) {
                    interviewState.questions = data.questions;
                    interviewState.currentQuestionIndex = 0;
                    interviewState.answers = [];
                    interviewState.role = role;
                    interviewState.interview_type = interview_type;
                    
                    // Start overall interview countdown timer (30 minutes max)
                    const MAX_INTERVIEW_TIME = 30 * 60; // 30 minutes in seconds
                    interviewState.overallStartTime = Date.now();
                    interviewState.maxInterviewTime = MAX_INTERVIEW_TIME;
                    
                    interviewState.overallTimerInterval = setInterval(() => {
                        const elapsed = Math.floor((Date.now() - interviewState.overallStartTime) / 1000);
                        const remaining = MAX_INTERVIEW_TIME - elapsed;
                        
                        if (remaining <= 0) {
                            clearInterval(interviewState.overallTimerInterval);
                            document.getElementById('overallTimer').textContent = '00:00';
                            document.getElementById('overallTimer').classList.add('text-danger');
                            toast.show('Time limit reached! Please finish your interview.', 'warning');
                            return;
                        }
                        
                        const minutes = Math.floor(remaining / 60);
                        const seconds = remaining % 60;
                        const timerElement = document.getElementById('overallTimer');
                        timerElement.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                        
                        // Warning colors
                        if (remaining <= 60) {
                            timerElement.className = 'mb-0 text-danger fw-bold';
                        } else if (remaining <= 300) {
                            timerElement.className = 'mb-0 text-warning fw-bold';
                        } else {
                            timerElement.className = 'mb-0 text-primary';
                        }
                    }, 1000);
                    
                    // Hide setup, show interview
                    document.getElementById('interviewSetup').style.display = 'none';
                    document.getElementById('interviewQuestions').style.display = 'block';
                    
                    // Initialize webcam
                    await initializeWebcam();
                    
                    // Display first question
                    displayQuestion(0);
                    
                    toast.show('Interview started! Enable camera and begin recording.', 'success');
                } else {
                    toast.show('Error: ' + (data.error || 'Failed to generate questions'), 'danger');
                }
            } catch (err) {
                toast.show('Error: ' + err.message, 'danger');
            }
        });
    }

    // Initialize webcam
    async function initializeWebcam() {
        try {
            const constraints = {
                video: { 
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100
                }
            };
            
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            interviewState.stream = stream;
            
            const videoElement = document.getElementById('videoPreview');
            if (!videoElement) {
                throw new Error('Video element not found');
            }
            
            console.log('📹 Initializing video stream...', stream);
            console.log('Stream tracks:', stream.getTracks().map(t => `${t.kind}: ${t.label}`));
            
            // Clear any existing stream first
            if (videoElement.srcObject) {
                console.log('Clearing existing video stream');
                videoElement.srcObject.getTracks().forEach(track => track.stop());
                videoElement.srcObject = null;
            }
            
            // Set stream to video element
            videoElement.srcObject = stream;
            
            // Set ALL critical video attributes
            videoElement.autoplay = true;
            videoElement.muted = true;
            videoElement.playsInline = true;
            videoElement.controls = false;
            
            console.log('Video element state:', {
                srcObject: !!videoElement.srcObject,
                paused: videoElement.paused,
                muted: videoElement.muted,
                autoplay: videoElement.autoplay,
                readyState: videoElement.readyState
            });
            
            // Handler 1: loadstart - earliest event
            videoElement.onloadstart = function() {
                console.log('📡 Video load started');
            };
            
            // Handler 2: loadedmetadata - critical event
            videoElement.onloadedmetadata = function() {
                console.log('✓ Video metadata loaded');
                console.log('  Dimensions:', videoElement.videoWidth, 'x', videoElement.videoHeight);
                console.log('  Duration:', videoElement.duration);
                console.log('  Paused:', videoElement.paused);
                
                // Immediate play attempt
                const playPromise = videoElement.play();
                if (playPromise !== undefined) {
                    playPromise.then(() => {
                        console.log('✓✓ Video PLAYING successfully');
                        toast.show('Camera preview active!', 'success');
                        
                        // Final verification
                        setTimeout(() => {
                            if (videoElement.paused) {
                                console.warn('⚠️ Video paused after play, retrying...');
                                videoElement.play();
                            } else {
                                console.log('✓✓✓ Video CONFIRMED playing at', videoElement.currentTime + 's');
                            }
                        }, 500);
                    }).catch(err => {
                        console.error('✗ Play failed:', err);
                        toast.show('Click the video to start preview', 'info');
                        // Allow manual click to play
                        videoElement.onclick = () => videoElement.play();
                    });
                }
            };
            
            // Handler 3: loadeddata - fallback
            videoElement.onloadeddata = function() {
                console.log('✓ Video data loaded, readyState:', videoElement.readyState);
                if (videoElement.paused) {
                    console.log('Attempting play from loadeddata...');
                    videoElement.play().catch(err => console.error('Loadeddata play failed:', err));
                }
            };
            
            // Handler 4: canplay - ready to play
            videoElement.oncanplay = function() {
                console.log('✓ Video can play');
                if (videoElement.paused) {
                    videoElement.play().catch(err => console.error('Canplay play failed:', err));
                }
            };
            
            // Handler 5: playing - actually playing
            videoElement.onplaying = function() {
                console.log('✓✓✓ VIDEO IS PLAYING!');
            };
            
            // Handler 6: error - catch any errors
            videoElement.onerror = function(e) {
                console.error('✗✗✗ Video error:', e);
                toast.show('Video element error. Try refreshing the page.', 'danger');
            };
            
            // Periodic health check
            const healthCheck = setInterval(() => {
                if (!videoElement.srcObject) {
                    console.error('✗ Stream lost! Restoring...');
                    videoElement.srcObject = stream;
                } else if (videoElement.paused && videoElement.readyState >= 2) {
                    console.warn('⚠️ Video paused but ready, attempting play...');
                    videoElement.play().catch(err => console.error('Health check play failed:', err));
                } else if (!videoElement.paused) {
                    console.log('✓ Health check: Video playing at', videoElement.currentTime.toFixed(1) + 's');
                    clearInterval(healthCheck); // Stop checking once confirmed playing
                }
            }, 1000);
            
            // Stop health check after 10 seconds
            setTimeout(() => clearInterval(healthCheck), 10000);
            
            // Setup continuous audio level monitoring
            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const audioSource = audioContext.createMediaStreamSource(stream);
                const analyser = audioContext.createAnalyser();
                analyser.fftSize = 256;
                audioSource.connect(analyser);
                
                const dataArray = new Uint8Array(analyser.frequencyBinCount);
                const audioLevelIndicator = document.getElementById('audioLevelIndicator');
                const audioLevelValue = document.getElementById('audioLevelValue');
                
                // Update audio level every 100ms
                const updateAudioLevel = () => {
                    analyser.getByteFrequencyData(dataArray);
                    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
                    const percentage = Math.min(100, Math.round((average / 128) * 100));
                    
                    if (audioLevelIndicator && audioLevelValue) {
                        audioLevelIndicator.style.width = percentage + '%';
                        audioLevelValue.textContent = percentage;
                        
                        // Change color based on level
                        if (percentage > 50) {
                            audioLevelIndicator.className = 'progress-bar bg-success';
                        } else if (percentage > 20) {
                            audioLevelIndicator.className = 'progress-bar bg-warning';
                        } else {
                            audioLevelIndicator.className = 'progress-bar bg-secondary';
                        }
                    }
                };
                
                // Start monitoring
                const audioMonitor = setInterval(updateAudioLevel, 100);
                
                // Store for cleanup
                interviewState.audioMonitor = audioMonitor;
                interviewState.audioContext = audioContext;
                
                console.log('✓ Audio level monitoring started');
            } catch (err) {
                console.error('Failed to setup audio monitoring:', err);
            }
            
            document.getElementById('startRecordingBtn').disabled = false;
            console.log('✓ Camera and microphone initialized, waiting for video to play...');
        } catch (err) {
            console.error('Error accessing media devices:', err);
            toast.show('Error accessing camera/microphone: ' + err.message, 'danger');
        }
    }

    // Display question
    function displayQuestion(index) {
        const question = interviewState.questions[index];
        document.getElementById('currentQuestionNum').textContent = index + 1;
        document.getElementById('totalQuestions').textContent = interviewState.questions.length;
        document.getElementById('questionText').querySelector('p').textContent = question.question;
        document.getElementById('questionTimeLimit').textContent = formatTime(question.time_limit);
        
        // Update progress
        updateProgress();
    }

    // Update progress tracker
    function updateProgress() {
        const progressDiv = document.getElementById('questionProgress');
        let html = '';
        interviewState.questions.forEach((q, idx) => {
            const status = idx < interviewState.currentQuestionIndex ? 'completed' : 
                          idx === interviewState.currentQuestionIndex ? 'active' : 'pending';
            const icon = status === 'completed' ? 'check-circle-fill' : 
                        status === 'active' ? 'record-circle' : 'circle';
            const color = status === 'completed' ? 'success' : 
                         status === 'active' ? 'primary' : 'secondary';
            html += `<div class="mb-2"><i class="bi bi-${icon} text-${color}"></i> Question ${idx + 1}</div>`;
        });
        progressDiv.innerHTML = html;
    }

    // Start recording
    if (startRecordingBtn) {
        startRecordingBtn.addEventListener('click', function() {
            startRecording();
        });
    }

    function startRecording() {
        const question = interviewState.questions[interviewState.currentQuestionIndex];
        interviewState.recordedChunks = [];
        interviewState.currentTranscription = '';
        
        // Setup MediaRecorder with proper options for audio capture
        let options = { mimeType: 'video/webm;codecs=vp8,opus' };
        
        // Try different codecs if not supported
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            console.warn('vp8,opus not supported, trying vp9,opus');
            options = { mimeType: 'video/webm;codecs=vp9,opus' };
        }
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            console.warn('vp9,opus not supported, trying h264');
            options = { mimeType: 'video/webm;codecs=h264' };
        }
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            console.warn('Using default codec');
            options = {};
        }
        
        console.log('MediaRecorder options:', options);
        
        try {
            interviewState.mediaRecorder = new MediaRecorder(interviewState.stream, options);
        } catch (err) {
            console.error('Failed to create MediaRecorder:', err);
            toast.show('Recording error: ' + err.message, 'danger');
            return;
        }
        
        // Monitor audio levels to verify capture
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const audioSource = audioContext.createMediaStreamSource(interviewState.stream);
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        audioSource.connect(analyser);
        
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        
        const checkAudioLevel = setInterval(() => {
            analyser.getByteFrequencyData(dataArray);
            const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
            if (average > 0) {
                console.log('Audio level detected:', average.toFixed(2));
            }
        }, 1000);
        
        interviewState.audioLevelCheck = checkAudioLevel;
        
        interviewState.mediaRecorder.ondataavailable = function(e) {
            if (e.data.size > 0) {
                console.log('Recording chunk received:', e.data.size, 'bytes');
                interviewState.recordedChunks.push(e.data);
            }
        };
        
        interviewState.mediaRecorder.onstop = function() {
            clearInterval(interviewState.audioLevelCheck);
            stopSpeechRecognition();
            processRecording();
        };
        
        interviewState.mediaRecorder.onerror = function(event) {
            console.error('MediaRecorder error:', event.error);
            toast.show('Recording error: ' + event.error, 'danger');
        };
        
        // Start recording with timeslice for progressive recording
        interviewState.mediaRecorder.start(1000); // Record in 1-second chunks
        interviewState.recordingStartTime = Date.now();
        
        console.log('MediaRecorder started, state:', interviewState.mediaRecorder.state);
        
        // Reset transcription for this question
        interviewState.currentTranscription = '';
        console.log('Reset transcription for new question');
        
        // Start speech recognition
        console.log('Calling startSpeechRecognition()...');
        startSpeechRecognition();
        console.log('startSpeechRecognition() called, recognition object:', interviewState.recognition);
        
        // Update UI
        document.getElementById('startRecordingBtn').style.display = 'none';
        document.getElementById('stopRecordingBtn').style.display = 'inline-block';
        document.getElementById('recordingTimer').style.display = 'block';
        
        // Start timer
        startTimer(question.time_limit);
    }

    // Start timer
    function startTimer(timeLimit) {
        let elapsed = 0;
        const timerDisplay = document.getElementById('timerDisplay');
        const timerProgress = document.getElementById('timerProgress');
        
        interviewState.timerInterval = setInterval(() => {
            elapsed++;
            const remaining = timeLimit - elapsed;
            
            if (remaining <= 0) {
                stopRecording();
                return;
            }
            
            timerDisplay.textContent = formatTime(remaining);
            const percentage = (elapsed / timeLimit) * 100;
            timerProgress.style.width = percentage + '%';
        }, 1000);
    }

    // Stop recording
    if (stopRecordingBtn) {
        stopRecordingBtn.addEventListener('click', function() {
            stopRecording();
        });
    }

    function stopRecording() {
        if (interviewState.mediaRecorder && interviewState.mediaRecorder.state !== 'inactive') {
            interviewState.mediaRecorder.stop();
        }
        
        clearInterval(interviewState.timerInterval);
        
        // Update UI
        document.getElementById('stopRecordingBtn').style.display = 'none';
        document.getElementById('recordingTimer').style.display = 'none';
    }

    // Process recorded video
    async function processRecording() {
        const blob = new Blob(interviewState.recordedChunks, { type: 'video/webm' });
        const duration = (Date.now() - interviewState.recordingStartTime) / 1000;
        
        // Get transcription from Web Speech API (collected during recording)
        const transcription = interviewState.currentTranscription.trim() || 'No transcription available';
        
        console.log('=== PROCESSING RECORDING ===');
        console.log('Duration:', duration.toFixed(1), 'seconds');
        console.log('Transcription length:', transcription.length, 'characters');
        console.log('Transcription preview:', transcription.substring(0, 100));
        console.log('===========================');
        
        if (transcription === 'No transcription available') {
            toast.show('Warning: No speech detected! Make sure you speak clearly during recording.', 'warning');
        }
        
        // Store video blob for later playback
        interviewState.recordedBlobs.push({
            questionId: interviewState.questions[interviewState.currentQuestionIndex].id,
            blob: blob,
            url: URL.createObjectURL(blob)
        });
        
        // Submit answer
        const question = interviewState.questions[interviewState.currentQuestionIndex];
        await submitAnswer(question.id, transcription, duration);
        
        // Show next/finish button
        if (interviewState.currentQuestionIndex < interviewState.questions.length - 1) {
            document.getElementById('nextQuestionBtn').style.display = 'inline-block';
        } else {
            document.getElementById('finishInterviewBtn').style.display = 'inline-block';
        }
        
        toast.show('Answer recorded successfully!', 'success');
    }

    // Submit answer to backend
    async function submitAnswer(questionId, answerText, duration) {
        try {
            // Store answer in client-side state for final analysis
            interviewState.answers.push({
                question_id: questionId,
                answer_text: answerText,
                duration: duration
            });
            
            const response = await fetch('/interview-submit-answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    question_id: questionId, 
                    answer_text: answerText, 
                    duration: duration 
                })
            });
            const data = await response.json();
            if (!response.ok) {
                toast.show('Error submitting answer', 'danger');
            }
        } catch (err) {
            toast.show('Error: ' + err.message, 'danger');
        }
    }

    // Next question
    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener('click', function() {
            interviewState.currentQuestionIndex++;
            displayQuestion(interviewState.currentQuestionIndex);
            
            // Clean up previous recognition object completely
            if (interviewState.recognition) {
                console.log('Cleaning up previous speech recognition object');
                try {
                    interviewState.recognition.stop();
                } catch (err) {
                    console.log('Recognition already stopped');
                }
                interviewState.recognition = null;
            }
            
            // Reset transcription for new question
            interviewState.currentTranscription = '';
            console.log('Reset for next question - transcription cleared');
            
            // Reset UI
            document.getElementById('nextQuestionBtn').style.display = 'none';
            document.getElementById('startRecordingBtn').style.display = 'inline-block';
            document.getElementById('startRecordingBtn').disabled = false;
            document.getElementById('timerDisplay').textContent = '00:00';
            document.getElementById('timerProgress').style.width = '0%';
        });
    }

    // Finish interview
    if (finishInterviewBtn) {
        finishInterviewBtn.addEventListener('click', async function() {
            toast.show('Analyzing your interview...', 'info');
            
            try {
                // Prepare full interview data for analysis
                const interviewData = {
                    role: interviewState.role,
                    interview_type: interviewState.interview_type,
                    questions: interviewState.questions,
                    answers: interviewState.answers
                };
                
                console.log('Sending interview data for analysis:', {
                    role: interviewData.role,
                    interview_type: interviewData.interview_type,
                    questions_count: interviewData.questions.length,
                    answers_count: interviewData.answers.length,
                    answers: interviewData.answers
                });
                
                const response = await fetch('/interview-analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(interviewData)
                });
                const data = await response.json();
                
                if (response.ok) {
                    // Stop overall timer
                    if (interviewState.overallTimerInterval) {
                        clearInterval(interviewState.overallTimerInterval);
                    }
                    
                    // Calculate total interview time
                    const totalTime = Math.floor((Date.now() - interviewState.overallStartTime) / 1000);
                    data.total_interview_time = totalTime;
                    
                    // Stop camera and audio monitoring
                    if (interviewState.stream) {
                        interviewState.stream.getTracks().forEach(track => track.stop());
                    }
                    if (interviewState.audioMonitor) {
                        clearInterval(interviewState.audioMonitor);
                    }
                    if (interviewState.audioContext) {
                        interviewState.audioContext.close();
                    }
                    if (interviewState.audioLevelCheck) {
                        clearInterval(interviewState.audioLevelCheck);
                    }
                    
                    // Store data and navigate to results page
                    displayFeedback(data);
                } else {
                    toast.show('Error: ' + (data.error || 'Failed to analyze interview'), 'danger');
                }
            } catch (err) {
                toast.show('Error: ' + err.message, 'danger');
            }
        });
    }

    // Display feedback
    function displayFeedback(data) {
        let html = `
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card text-center">
                        <div class="card-body">
                            <h2 class="display-4 text-primary">${data.overall_score}/10</h2>
                            <p class="text-muted">Overall Score</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3 class="text-success">${data.recommendation}</h3>
                            <p class="text-muted">Recommendation</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <h5><i class="bi bi-trophy"></i> Strengths</h5>
                    <ul>
                        ${data.strengths.map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
                <div class="col-md-6">
                    <h5><i class="bi bi-exclamation-triangle"></i> Areas for Improvement</h5>
                    <ul>
                        ${data.improvements.map(i => `<li>${i}</li>`).join('')}
                    </ul>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6>Communication Skills</h6>
                            <div class="progress" style="height: 25px;">
                                <div class="progress-bar bg-info" style="width: ${data.communication_score * 10}%">
                                    ${data.communication_score}/10
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6>Technical Knowledge</h6>
                            <div class="progress" style="height: 25px;">
                                <div class="progress-bar bg-success" style="width: ${data.technical_score * 10}%">
                                    ${data.technical_score}/10
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <h5><i class="bi bi-chat-left-text"></i> Question-by-Question Review</h5>
            <ul class="nav nav-tabs mb-3" id="questionTabs" role="tablist">
                ${data.question_feedback.map((qf, idx) => `
                    <li class="nav-item" role="presentation">
                        <button class="nav-link ${idx === 0 ? 'active' : ''}" 
                                id="question${idx}-tab" 
                                data-bs-toggle="tab" 
                                data-bs-target="#question${idx}" 
                                type="button" 
                                role="tab" 
                                aria-controls="question${idx}" 
                                aria-selected="${idx === 0 ? 'true' : 'false'}">
                            Q${idx + 1}
                        </button>
                    </li>
                `).join('')}
            </ul>
            <div class="tab-content" id="questionTabsContent">
                ${data.question_feedback.map((qf, idx) => {
                    const videoData = interviewState.recordedBlobs[idx];
                    return `
                        <div class="tab-pane fade ${idx === 0 ? 'show active' : ''}" 
                             id="question${idx}" 
                             role="tabpanel" 
                             aria-labelledby="question${idx}-tab">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Question:</h6>
                                    <p class="mb-3">${interviewState.questions[idx].question}</p>
                                    ${videoData ? `
                                        <h6 class="mt-3">Your Response (Video):</h6>
                                        <video controls style="width: 100%; max-height: 300px; background: #000; border-radius: 8px;" class="mb-3">
                                            <source src="${videoData.url}" type="video/webm">
                                            Your browser does not support video playback.
                                        </video>
                                    ` : ''}
                                </div>
                                <div class="col-md-6">
                                    <h6>Feedback:</h6>
                                    <p>${qf.feedback}</p>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
            
            <div class="alert alert-info mt-4">
                <h6><i class="bi bi-info-circle"></i> Summary</h6>
                <p>${data.summary}</p>
            </div>
        `;
        
        // Store feedback in sessionStorage for results page
        sessionStorage.setItem('interviewFeedback', JSON.stringify(data));
        sessionStorage.setItem('interviewQuestions', JSON.stringify(interviewState.questions));
        sessionStorage.setItem('recordedBlobs', JSON.stringify(
            interviewState.recordedBlobs.map(rb => ({
                questionId: rb.questionId,
                url: rb.url
            }))
        ));
        
        // Navigate to results page
        window.location.href = '/interview-results';
    }

    // New interview
    if (newInterviewBtn) {
        newInterviewBtn.addEventListener('click', function() {
            location.reload();
        });
    }

    // Speech Recognition Functions
    function startSpeechRecognition() {
        // Check if browser supports Web Speech API
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('Web Speech API not supported in this browser');
            toast.show('Speech recognition not available. Please use Chrome, Edge, or Safari.', 'warning');
            return;
        }
        
        // Stop and cleanup any existing recognition
        if (interviewState.recognition) {
            console.log('Stopping existing recognition before creating new one');
            try {
                interviewState.recognition.stop();
            } catch (err) {
                console.log('Previous recognition already stopped');
            }
            interviewState.recognition = null;
        }
        
        console.log('Creating NEW speech recognition object');
        interviewState.recognition = new SpeechRecognition();
        interviewState.recognition.continuous = true;
        interviewState.recognition.interimResults = true;
        interviewState.recognition.lang = interviewState.language || 'en-US';
        
        interviewState.recognition.onresult = function(event) {
            let transcript = '';
            let interimTranscript = '';
            
            console.log('Speech recognition result event:', event.results.length, 'results');
            
            // Get all results
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i];
                console.log(`Result ${i}: final=${result.isFinal}, confidence=${result[0].confidence}, text="${result[0].transcript}"`);
                
                if (result.isFinal) {
                    transcript += result[0].transcript + ' ';
                } else {
                    interimTranscript += result[0].transcript;
                }
            }
            
            // Append to current transcription
            if (transcript) {
                interviewState.currentTranscription += transcript;
                console.log('✓ Final transcription added:', transcript);
                console.log('✓ Total transcription length:', interviewState.currentTranscription.length, 'chars');
            }
            
            if (interimTranscript) {
                console.log('⋯ Interim (not saved):', interimTranscript);
            }
        };
        
        interviewState.recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            
            if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
                toast.show('Microphone access denied. Please allow microphone access.', 'danger');
            } else if (event.error === 'no-speech') {
                console.warn('No speech detected, will auto-restart');
                // Restart if no speech detected
                setTimeout(() => {
                    if (interviewState.mediaRecorder && interviewState.mediaRecorder.state === 'recording') {
                        try {
                            interviewState.recognition.start();
                        } catch (err) {
                            console.error('Failed to restart recognition:', err);
                        }
                    }
                }, 100);
            } else if (event.error === 'audio-capture') {
                toast.show('Microphone not working. Please check your audio settings.', 'danger');
            } else if (event.error === 'network') {
                toast.show('Network error. Speech recognition requires internet connection.', 'warning');
            }
        };
        
        interviewState.recognition.onend = function() {
            console.log('Speech recognition ended');
            console.log('MediaRecorder state:', interviewState.mediaRecorder ? interviewState.mediaRecorder.state : 'no recorder');
            
            // Auto-restart if still recording
            if (interviewState.mediaRecorder && interviewState.mediaRecorder.state === 'recording') {
                console.log('Restarting speech recognition...');
                setTimeout(() => {
                    try {
                        interviewState.recognition.start();
                        console.log('✓ Speech recognition restarted');
                    } catch (err) {
                        console.error('Failed to restart recognition:', err);
                    }
                }, 100);
            } else {
                console.log('Not restarting - recording is not active');
            }
        };
        
        interviewState.recognition.onstart = function() {
            console.log('✓✓✓ Speech recognition STARTED successfully');
            console.log('Language:', interviewState.recognition.lang);
            console.log('Continuous:', interviewState.recognition.continuous);
            console.log('Interim results:', interviewState.recognition.interimResults);
        };
        
        try {
            interviewState.recognition.start();
            console.log('Calling speech recognition start()...');
        } catch (err) {
            console.error('Failed to start speech recognition:', err);
            toast.show('Failed to start speech recognition: ' + err.message, 'danger');
        }
    }
    
    function stopSpeechRecognition() {
        if (interviewState.recognition) {
            interviewState.recognition.stop();
            console.log('Speech recognition stopped');
            console.log('Final transcription:', interviewState.currentTranscription);
        }
    }

    // Utility function to format time
    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
});
