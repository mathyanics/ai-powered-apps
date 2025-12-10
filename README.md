# 🎓 AI Learning Hub

A comprehensive Flask-based AI platform that combines intelligent Q&A, interactive coding exercises, and AI-powered video interviews - all in one unified application.

## 🎯 Overview

Transform how you learn and prepare for technical careers with this all-in-one AI platform:

- 📊 **Dataset Analysis** - Natural language queries on CSV/Excel/JSON files
- 📄 **Document Q&A** - Extract insights from PDFs and PowerPoint presentations
- 🎥 **YouTube Analysis** - Question answering on video transcripts
- 💻 **Coding Practice** - AI-generated exercises in 13 programming languages with real-time execution
- 🎤 **Mock Interviews** - Video interview practice with BARS-based AI assessment in 15 languages

## 🚀 Features

### 1. Dataset Q&A
- Upload multiple datasets (CSV, Excel, JSON)
- Natural language to SQL query conversion
- Visual data preview with tabbed interface
- Interactive chat-based Q&A

### 2. Document Q&A
- PDF and PowerPoint file support
- Text extraction and chunking
- RAG (Retrieval-Augmented Generation) with FAISS vector store
- Source excerpt tracking with relevance scores

### 3. YouTube Q&A
- Automatic transcript fetching using youtube-transcript-api
- Video embedding with iframe preview
- Semantic search through video content
- Context-aware answers with source timestamps

### 4. AI-Powered Coding Exercise
- **Generate Custom Exercises**: Create coding challenges based on topic, difficulty, and programming language
- **Interactive Code Editor**: Write and submit solutions with syntax-highlighted editor
- **Multi-Language Execution**: Run code in 13 languages using Piston API:
  - Python, JavaScript, TypeScript, Java, C++, C#
  - Go, Rust, PHP, Ruby, Kotlin, Swift, R
- **AI Feedback**: Get comprehensive code reviews with:
  - Correctness analysis
  - Code quality assessment
  - Efficiency evaluation
  - Specific improvement suggestions
  - Alternative approaches
- **Smart Hints**: Request hints without revealing the solution
- **Complete Solutions**: View detailed solutions with step-by-step explanations

### 5. Video Interview
- **Mock Interview Sessions**: Practice for real job interviews with AI-powered questions
- **Multiple Interview Types**: Technical, HR/Behavioral, Mixed
- **Role-Specific Questions**: Tailored for various roles (AI Engineer, Product Manager, Software Engineer, Data Scientist, etc.)
- **Webcam Recording**: Record video responses for each question with live preview
- **Real-Time Speech-to-Text**: Automatic transcription with Web Speech API (15 languages):
  - English (US/UK), Spanish (Spain/Mexico), French, German, Italian
  - Portuguese (Brazil/Portugal), Japanese, Korean, Chinese (Simplified/Traditional)
  - Hindi, Arabic
- **Audio Level Monitoring**: Real-time microphone input visualization
- **Interview Timer**: 30-minute overall countdown with color-coded warnings
- **BARS Methodology**: Behaviorally Anchored Rating Scales assessment
- **Comprehensive AI Analysis**:
  - 5-Dimension Spider Chart: Communication, Technical, Analytical, Role Fit, Behavioral Presence
  - Domain-specific scoring with strict validation rules
  - Prevents hallucination (e.g., technical scores only from technical questions)
  - Question-by-question feedback with video playback
  - Hiring recommendation with detailed behavioral observations
  - Actionable improvement suggestions

## 🛠️ Technical Stack

**Backend:**
- Flask 3.0.0 - Web framework
- Python 3.11+ - Runtime environment

**AI/ML:**
- LangChain - Framework for LLM applications
- HuggingFace API - LLM inference
- FAISS - Vector database for similarity search
- Sentence Transformers - Document embeddings

**Frontend:**
- Bootstrap 5 - UI framework
- Chart.js 4.4.0 - Spider chart visualization
- Web Speech API - Browser-native speech recognition
- MediaRecorder API - Video/audio recording

**Data Processing:**
- Pandas - Dataframe operations
- pandasql - SQL queries on dataframes
- PyPDF2 - PDF text extraction
- python-pptx - PowerPoint processing

**Code Execution:**
- Piston API - Remote code execution in 13 languages

## 🛠️ Installation & Setup

### 1. Clone or Navigate to Project Directory

```bash
cd "ai-powered-apps"
```

### 2. Create Virtual Environment

**Using venv:**
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Linux/Mac
```

**Using Conda:**
```bash
conda create -n ai-apps python=3.11
conda activate ai-apps
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required: HuggingFace API Token
HF_TOKEN=your_huggingface_token_here
CEREBRAS_API_KEY=your_cerebras_token_here
```

**Get your HuggingFace token:**
1. Create account at https://huggingface.co/
2. Go to Settings → Access Tokens: https://huggingface.co/settings/tokens
3. Create a new token with "Read" permissions
4. Copy token to `.env` file

**Get your Cerebras API key:**
1. Sign up at https://www.cerebras.net/
2. Navigate to API section and generate a key
3. Copy key to `.env` file

## 🚀 Running the Application

### Start the Flask Server
```bash
python app.py
```

The application will be available at:
- **Web Interface**: http://localhost:5000
- **Home Page**: http://localhost:5000/
- **Q&A Interface**: http://localhost:5000/qna

## 📖 Usage Guide

### Dataset Q&A
1. Click on "Dataset Q&A" tab
2. Upload CSV, Excel, or JSON files
3. View data preview with statistics
4. Ask questions in natural language
5. Get SQL queries and formatted results

### Document Q&A
1. Switch to "Document Q&A" tab
2. Upload PDF or PowerPoint files
3. Wait for processing and chunking
4. Ask questions about the document
5. View answers with source excerpts

### YouTube Q&A
1. Navigate to "YouTube Q&A" tab
2. Paste a YouTube video URL
3. Click "Analyze Video Content"
4. Ask questions about the video
5. Get answers with relevant segments

### Coding Exercise
1. Go to "Coding Exercise" tab
2. **Generate Exercise:**
   - Enter a topic (e.g., "Binary Search", "Recursion")
   - Select difficulty level (Beginner/Intermediate/Advanced)
   - Choose programming language (13 languages available)
   - Click "Generate Exercise"
3. **Write Your Solution:**
   - Read the problem description and test cases
   - Write your code in the editor
   - Click "Run Code" to execute in real-time (Piston API)
   - Click "Submit & Validate" for AI feedback
4. **Get Help:**
   - Click "Hint" for guidance without spoilers
   - Click "Solution" to view complete answer with explanation
5. **Review Feedback:**
   - Receive detailed analysis of your code
   - Get suggestions for improvement
   - Learn alternative approaches

### Video Interview
1. Navigate to "Interview" tab
2. **Setup Interview:**
   - Enter your target role (e.g., "AI Engineer", "Product Manager", "Software Developer")
   - Select interview type:
     - **Technical Interview**: Focus on domain expertise and problem-solving
     - **HR/Behavioral**: Focus on soft skills and situational judgment
     - **Mixed Interview**: Balanced combination of both
   - Choose speech recognition language (15 supported: English, Spanish, French, German, etc.)
   - Add any additional context (optional: company culture, specific technologies)
   - Click "Start Interview"
3. **Grant Permissions:**
   - Allow webcam access when browser prompts
   - Allow microphone access when browser prompts
   - Verify video preview shows your camera feed
   - Check audio level indicator responds to your voice (green bars)
4. **Answer Questions (5 Total):**
   - **Overall Timer**: 30 minutes for entire interview (blue → yellow at 10 min → red at 5 min)
   - **Per Question**: Read question carefully, then:
     - Click "Start Recording" button
     - Speak naturally - your answer is transcribed in real-time
     - Watch the audio level indicator to ensure microphone is capturing
     - Question timer: 2 minutes per question
     - Click "Stop Recording" when finished (or auto-stops at 2 min)
     - Review your transcript before moving on
     - Click "Next Question" to continue
5. **Complete Interview:**
   - Click "Finish Interview" after answering all 5 questions
   - Processing takes 10-15 seconds for AI analysis
6. **Review Detailed Results:**
   - **5-Dimension Spider Chart**:
     - Communication Effectiveness (0-100)
     - Technical/Domain Knowledge (0-100)
     - Analytical Ability (0-100)
     - Role Fit (0-100)
     - Behavioral Presence (0-100)
   - **BARS Ratings**: Each dimension rated as EXCEPTIONAL/STRONG/SATISFACTORY/DEVELOPING/UNSATISFACTORY
   - **Clickable Badges**: Click any dimension to see detailed reasoning
   - **Question-by-Question Review**:
     - Tabs for each of the 5 questions
     - Video playback of your recorded response
     - Transcript of what you said
     - Question-specific BARS rating
     - Observable behaviors demonstrated
     - Development areas with actionable suggestions
   - **Overall Assessment**:
     - Hiring recommendation (Strong Hire/Hire/Maybe/No Hire)
     - Top 4-5 strengths with specific examples
     - Top 4-5 areas for improvement with actionable advice
     - Detailed summary and next steps

## 🎓 Example Workflows

### Coding Exercise Example
```
1. Generate Exercise:
   Topic: "Binary Search Tree"
   Difficulty: Intermediate
   Language: Python

2. Receive Problem:
   - Clear problem statement
   - Input/output format
   - 3 visible test cases
   - 5 hidden test cases
   - Constraints

3. Write Solution:
   - Use syntax-highlighted editor
   - Test with provided examples
   - Submit for validation

4. Get AI Feedback:
   ✓ Correctness: 9/10
   ✓ Code Quality: Clean and readable
   ✓ Efficiency: O(log n) time, O(h) space
   ✓ Suggestions: Handle edge cases
   ✓ Alternative: Iterative approach

5. Request Hints/Solution if needed
6. Iterate and Improve!
```

### Video Interview Example
```
1. Setup:
   Role: "AI Engineer"
   Type: "Technical Interview"
   Language: "English (US)"

2. Interview Questions (5 total):
   Q1: Tell me about yourself and your experience with AI
   Q2: Explain the difference between supervised and unsupervised learning
   Q3: How would you handle class imbalance in a dataset?
   Q4: Walk me through your approach to deploying an ML model to production
   Q5: Describe a challenging AI project you've worked on

3. Answer Each Question:
   - Record 2-minute video response
   - Real-time speech-to-text transcription
   - Audio level monitoring

4. Receive AI Analysis:
   ✓ Overall: STRONG (82/100)
   ✓ Technical: STRONG (85/100) - "Demonstrated solid ML fundamentals..."
   ✓ Communication: SATISFACTORY (75/100) - "Clear articulation..."
   ✓ Analytical: STRONG (80/100) - "Structured problem-solving..."
   ✓ Role Fit: STRONG (78/100) - "Relevant experience..."
   ✓ Behavioral: SATISFACTORY (72/100) - "Engaged responses..."
   
   Recommendation: HIRE
   
5. Review & Improve:
   - Watch video playback
   - Read detailed feedback
   - Identify improvement areas
   - Practice weak dimensions
```

## 📊 Project Structure

```
QnA with Datasets/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (not in repo)
├── README.md                      # This file
│
├── constants/
│   └── constants.py               # All LLM prompts centralized
│
├── helper/
│   ├── llm_engine.py             # LLM API integration
│   ├── utils.py                  # Utility functions
│   ├── speech_recognition.py    # Speech config & validation
│   ├── interview_tools.py       # BARS scoring & validation
│   └── embedding_tools.py       # Vector store management
│
├── templates/                     # HTML templates
│   ├── home.html                 # Landing page
│   ├── qna.html                  # Unified Q&A interface
│   ├── interview_results.html   # Interview results page
│   └── about.html                # About page
│
├── static/                        # Static assets
│   ├── css/
│   │   └── style.css            # Custom styles
│   └── js/
│       └── qna.js               # Frontend logic
│
├── uploads/                       # User uploads (auto-created)
│   ├── datasets/                 # Uploaded CSV/Excel/JSON
│   ├── documents/                # Uploaded PDFs/PPTx
│   ├── videos/                   # Interview recordings
│   └── *_vector_store_*/        # FAISS indices
│
└── downloads/                     # Generated files (auto-created)
```

## 🔧 Configuration Options

### Supported Languages for Coding Exercises
- Python
- JavaScript
- TypeScript
- Java
- C++
- C
- C#
- Go
- Rust
- PHP
- Ruby
- Kotlin
- Swift

### Supported Languages for Speech Recognition
1. English (US) - `en-US`
2. English (UK) - `en-GB`
3. Spanish (Spain) - `es-ES`
4. Spanish (Mexico) - `es-MX`
5. French - `fr-FR`
6. German - `de-DE`
7. Italian - `it-IT`
8. Portuguese (Brazil) - `pt-BR`
9. Portuguese (Portugal) - `pt-PT`
10. Japanese - `ja-JP`
11. Korean - `ko-KR`
12. Chinese (Simplified) - `zh-CN`
13. Chinese (Traditional) - `zh-TW`
14. Hindi - `hi-IN`
15. Arabic - `ar-SA`

## 🐛 Troubleshooting

### Issue: "HuggingFace token not found"
**Solution:** Ensure `.env` file exists with valid `HF_TOKEN`

### Issue: "Cerebras API key missing"
**Solution:** Add `CEREBRAS_API_KEY` to `.env` file

### Issue: Video not showing in interview
**Solution:** 
- Grant camera permissions in browser
- Check browser console for errors
- Try refreshing the page

### Issue: Speech recognition not capturing voice
**Solution:**
- Grant microphone permissions
- Check audio level indicator (green bars should appear when speaking)
- Ensure correct language selected
- Try using Chrome/Edge (best Web Speech API support)

### Issue: Coding exercise not executing
**Solution:**
- Check internet connection (uses Piston API)
- Verify code syntax is correct
- Try a different language if persistent issues

### Issue: Document upload fails
**Solution:**
- Check file size (max 16MB)
- Ensure file format is PDF or PPTX
- Verify file is not corrupted

## 🚀 Deployment

### Local Development
```bash
python app.py
# Access at http://localhost:5000
```

### Production (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

## 📝 License

This project is for educational purposes. Please ensure you comply with the terms of service of all third-party APIs used (HuggingFace, Piston, etc.).

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional programming languages
- More interview question types
- Enhanced code analysis
- Additional document formats
- Performance optimizations

## 📧 Support

For issues, questions, or suggestions, please create an issue in the repository.

---

**Built with ❤️ using Flask, LangChain, and HuggingFace**
