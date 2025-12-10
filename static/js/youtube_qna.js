// YouTube Q&A page functionality

const youtubeForm = document.getElementById('youtubeForm');
const ytQuestionForm = document.getElementById('ytQuestionForm');
const videoPreview = document.getElementById('videoPreview');
const youtubeQaSection = document.getElementById('youtubeQaSection');
const ytChatMessages = document.getElementById('ytChatMessages');
const ytLoadingSpinner = document.getElementById('ytLoadingSpinner');

let videoProcessed = false;
let currentVideoId = null;

// Handle YouTube URL submission with validation
youtubeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const videoUrlInput = document.getElementById('videoUrl');
    const videoUrl = videoUrlInput.value.trim();
    const videoId = extractVideoId(videoUrl);
    
    if (!videoId) {
        toast.show('Invalid YouTube URL. Please enter a valid URL.', 'danger');
        videoUrlInput.focus();
        return;
    }
    
    // Disable submit button
    const submitBtn = youtubeForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Analyzing...';
    
    // Show video preview with animation
    videoPreview.innerHTML = `
        <div class="video-container fade-in">
            <iframe src="https://www.youtube.com/embed/${videoId}" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
            </iframe>
        </div>
    `;
    
    ytLoadingSpinner.style.display = 'block';
    
    // Call backend to analyze video
    try {
        const response = await fetch('/youtube-analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ video_url: videoUrl })
        });
        
        const data = await response.json();
        
        ytLoadingSpinner.style.display = 'none';
        
        if (response.ok) {
            youtubeQaSection.style.display = 'block';
            youtubeQaSection.classList.add('fade-in');
            videoProcessed = true;
            currentVideoId = videoId;
            
            ytChatMessages.innerHTML = `<div class="alert alert-success"><i class="bi bi-check-circle"></i> Video analyzed successfully! Found ${data.chunks} text segments. Ask me anything about this video.</div>`;
            toast.show('Video analyzed successfully!', 'success');
            
            // Focus on question input
            document.getElementById('ytQuestionInput').focus();
        } else {
            toast.show('Error: ' + data.error, 'danger');
            ytChatMessages.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> ${data.error}</div>`;
        }
        
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-play-circle"></i> Analyze Video Content';
        
    } catch (error) {
        ytLoadingSpinner.style.display = 'none';
        toast.show('Error: ' + error.message, 'danger');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-play-circle"></i> Analyze Video Content';
    }
});

// Handle question submission for YouTube with typing indicator
ytQuestionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!videoProcessed) {
        toast.show('Please analyze a video first', 'warning');
        return;
    }
    
    const questionInput = document.getElementById('ytQuestionInput');
    const question = questionInput.value.trim();
    
    if (!question) return;
    
    // Disable input while processing
    questionInput.disabled = true;
    ytQuestionForm.querySelector('button[type="submit"]').disabled = true;
    
    // Add user message
    addYtMessage('user', question);
    questionInput.value = '';
    
    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = '<span></span><span></span><span></span>';
    ytChatMessages.appendChild(typingIndicator);
    ytChatMessages.scrollTop = ytChatMessages.scrollHeight;
    
    // Call backend to ask question
    try {
        const response = await fetch('/youtube-ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
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
                            <h2 class="accordion-header" id="heading${index}">
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
            
            addYtMessage('assistant', answerHtml);
        } else {
            toast.show('Error: ' + data.error, 'danger');
            addYtMessage('assistant', `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> ${data.error}</div>`);
        }
        
    } catch (error) {
        typingIndicator.remove();
        toast.show('Error: ' + error.message, 'danger');
        addYtMessage('assistant', `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> ${error.message}</div>`);
    } finally {
        questionInput.disabled = false;
        ytQuestionForm.querySelector('button[type="submit"]').disabled = false;
        questionInput.focus();
    }
});

// Auto-submit on Enter key
const ytQuestionInput = document.getElementById('ytQuestionInput');
if (ytQuestionInput) {
    ytQuestionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            ytQuestionForm.dispatchEvent(new Event('submit'));
        }
    });
}

// Add message to YouTube chat
function addYtMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    if (role === 'user') {
        messageDiv.innerHTML = `<div class="message-label">You</div><div>${escapeHtml(content)}</div>`;
    } else {
        messageDiv.innerHTML = `<div class="message-label">Assistant</div><div>${content}</div>`;
    }
    
    ytChatMessages.appendChild(messageDiv);
    ytChatMessages.scrollTop = ytChatMessages.scrollHeight;
}

// Extract video ID from YouTube URL
function extractVideoId(url) {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : null;
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
