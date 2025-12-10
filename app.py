"""
QnA with Datasets - Flask Application
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import logging
from werkzeug.utils import secure_filename
import json
from dotenv import load_dotenv
from constants.constants import (
    DATASET_SQL_GENERATION_PROMPT,
    DATASET_ANSWER_GENERATION_PROMPT,
    INTERVIEW_QUESTION_GENERATION_PROMPT,
    INTERVIEW_ANALYSIS_PROMPT,
    CODING_EXERCISE_GENERATION_PROMPT,
    CODING_VALIDATION_PROMPT,
    CODING_HINT_GENERATION_PROMPT,
    CODING_SOLUTION_GENERATION_PROMPT,
    DOCUMENT_QA_PROMPT,
    YOUTUBE_QA_PROMPT
)
from helper.llm_engine import LLMEngine
from helper.utils import (
    load_dataset, build_dataframes_info, run_sql_query,
    get_output_instructions_by_language, get_example_code_by_language,
    clean_json_response, generate_variation_seed
)
from helper.speech_recognition import SpeechRecognitionConfig, TranscriptionValidator
from helper.interview_tools import (
    InterviewValidator,
    BARSScoring,
    InterviewScoreEnforcer,
    InterviewQuestionClassifier
)
from helper.embedding_tools import DocumentVectorStore, EmbeddingConfig

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Check for required environment variables
if not os.environ.get('HF_TOKEN'):
    logger.warning("HF_TOKEN not found in environment variables. LLM features may not work.")

class MainApp:
    """Main class for the QnA system with uploaded dataset."""
    
    def __init__(self):
        """Initialize the QnA system with LLM engine."""
        self.llm_chain = LLMEngine()
        logger.info("LLM Engine initialized.")

    def _llm_based_response(self, query: str) -> str:
        """Get recommendation from LLM based on query."""
        try:
            response = self.llm_chain.run(
                messages=[{"role": "user", "content": query}]
            )
            logger.info(f"LLM response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error during LLM inference: {e}")
            return "Error during LLM inference."

# Initialize the main app
main_app = MainApp()

@app.route('/')
def home():
    """Home page."""
    return render_template('home.html')

@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@app.route('/qna')
def qna():
    """Unified Q&A page for datasets, documents, and YouTube."""
    return render_template('qna.html')

@app.route('/interview-results')
def interview_results():
    """Dedicated page for interview analysis results."""
    return render_template('interview_results.html')

@app.route('/ask-question')
def ask_question():
    """Legacy route - redirect to unified Q&A."""
    return redirect(url_for('qna'))

@app.route('/youtube-qna')
def youtube_qna():
    """Legacy route - redirect to unified Q&A."""
    return redirect(url_for('qna'))

# --- VIDEO INTERVIEW FEATURE ENDPOINTS ---
@app.route('/interview-generate', methods=['POST'])
def interview_generate():
    """Generate AI-powered video interview questions."""
    data = request.json
    role = data.get('role', 'General Position')
    interview_type = data.get('interview_type', 'Technical Interview')
    additional_info = data.get('additional_info', '')
    
    # Add variation seed to prevent exact duplicate questions on retry
    variation_seed = generate_variation_seed()
    variation_note = f"\n\nIMPORTANT: Generate fresh questions (variation seed: {variation_seed}). Avoid repeating common interview questions verbatim."
    
    # Build additional info text
    additional_info_text = ""
    if additional_info:
        additional_info_text = f"Additional context: {additional_info}"
    additional_info_text += variation_note

    prompt = INTERVIEW_QUESTION_GENERATION_PROMPT.format(
        interview_type=interview_type,
        role=role,
        additional_info_text=additional_info_text
    )
    response = main_app._llm_based_response(prompt)
    import re, json
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            # Store only essential metadata in session to avoid cookie size limit
            session['current_interview'] = {
                'role': role,
                'interview_type': interview_type,
                'question_count': len(result.get('questions', [])),
                'answers': []  # Will store minimal answer data
            }
            session.modified = True
            # Return full questions to client (not stored in session)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Failed to parse interview questions: {e}")
            return jsonify({'error': 'Failed to parse interview questions.'}), 500
    return jsonify({'error': 'No valid interview questions generated.'}), 500

@app.route('/interview-submit-answer', methods=['POST'])
def interview_submit_answer():
    """Submit a video answer (transcribed text) for a question."""
    data = request.json
    question_id = data.get('question_id')
    answer_text = data.get('answer_text', '')
    duration = data.get('duration', 0)
    
    if 'current_interview' not in session:
        return jsonify({'error': 'No active interview session.'}), 400
    
    # Store minimal answer data (just count for validation)
    if 'current_interview' not in session:
        session['current_interview'] = {'answers': []}
    
    session['current_interview']['answers'].append({
        'question_id': question_id,
        'duration': duration,
        'has_transcript': bool(answer_text and answer_text.strip())
    })
    session.modified = True
    
    return jsonify({'success': True, 'message': 'Answer recorded successfully.'})

@app.route('/interview-analyze', methods=['POST'])
def interview_analyze():
    """Analyze all video answers and provide comprehensive feedback."""
    # Get interview data from request body instead of session
    data = request.json
    role = data.get('role')
    interview_type = data.get('interview_type')
    questions = data.get('questions', [])
    answers = data.get('answers', [])
    
    # Debug logging
    print(f"Received analysis request: role={role}, type={interview_type}, questions={len(questions)}, answers={len(answers)}")
    if not answers:
        print("DEBUG: Answers array is empty!")
        print(f"DEBUG: Request data keys: {list(data.keys())}")
    else:
        # Log each answer transcript
        print("\n=== ANSWER TRANSCRIPTS ===")
        for i, answer in enumerate(answers, 1):
            transcript = answer.get('answer_text', 'No answer provided')
            duration = answer.get('duration', 0)
            print(f"\nAnswer {i} (Duration: {duration:.1f}s):")
            print(f"Transcript: {transcript[:200]}{'...' if len(transcript) > 200 else ''}")
            print(f"Length: {len(transcript)} characters")
        print("=========================\n")
    
    if not role or not questions or not answers:
        error_msg = f"Missing interview data: role={'✓' if role else '✗'}, questions={'✓' if questions else '✗'}, answers={'✓' if answers else '✗'}"
        return jsonify({'error': error_msg}), 400
    
    # Build analysis prompt with question classification
    qa_pairs = []
    answered_questions = set()
    
    for i, answer in enumerate(answers):
        q_id = answer.get('question_id')
        question = next((q for q in questions if q.get('id') == q_id), {})
        answer_text = answer.get('answer_text', 'No answer provided')
        
        # Track which questions have real answers
        if answer_text and answer_text not in ['No answer provided', 'No transcription available'] and len(answer_text.strip()) >= 10:
            answered_questions.add(q_id)
        
        qa_pairs.append(f"""
Question {q_id}: {question.get('question', 'N/A')}
Candidate's Answer: {answer_text}
Duration: {answer.get('duration', 0)} seconds
""")
    
    # Calculate completion rate
    completion_rate = len(answered_questions) / len(questions) if questions else 0
    print(f"Interview completion: {len(answered_questions)}/{len(questions)} questions answered ({completion_rate*100:.0f}%)")
    
    # Check for missing or empty transcripts
    empty_count = sum(1 for a in answers if not a.get('answer_text') or 
                      a.get('answer_text').strip() == '' or 
                      a.get('answer_text') == 'No answer provided' or
                      a.get('answer_text') == 'No transcription available' or
                      len(a.get('answer_text', '').strip()) < 10)  # Less than 10 chars is essentially empty
    
    print(f"Empty answer count: {empty_count} out of {len(answers)}")
    
    # Only return insufficient data if ALL answers are empty
    if empty_count == len(answers):
        print(f"WARNING: ALL {len(answers)} answers are empty - returning INSUFFICIENT_DATA")
        # All answers are empty - return N/A status
        return jsonify({{
            'overall_rating': 'N/A',
            'overall_score': 0,
            'data_quality': 'INSUFFICIENT_DATA',
            'strengths': ['Unable to assess - insufficient transcript data'],
            'improvements': ['Ensure microphone works and you speak clearly during recording'],
            'communication_rating': 'N/A',
            'communication_score': 0,
            'communication_reason': 'Insufficient transcript data',
            'technical_rating': 'N/A',
            'technical_score': 0,
            'technical_reason': 'Insufficient transcript data',
            'analytical_rating': 'N/A',
            'analytical_score': 0,
            'analytical_reason': 'Insufficient transcript data',
            'role_fit_rating': 'N/A',
            'role_fit_score': 0,
            'role_fit_reason': 'Insufficient transcript data',
            'behavioral_presence_rating': 'N/A',
            'behavioral_presence_score': 0,
            'behavioral_reason': 'Insufficient transcript data',
            'question_feedback': [{{
                'question_id': i+1,
                'question_text': q.get('question', 'N/A'),
                'rating': 'N/A',
                'feedback': 'No transcript available for assessment',
                'observable_behaviors': 'N/A',
                'development_areas': 'N/A'
            }} for i, q in enumerate(questions)],
            'recommendation': 'INCOMPLETE_DATA',
            'summary': 'Interview assessment incomplete due to missing transcript data. Please ensure proper audio capture and speech recognition functionality.',
            'next_steps': 'Retry interview with verified microphone and audio settings'
        }}), 200
    
    prompt = INTERVIEW_ANALYSIS_PROMPT.format(
        interview_type=interview_type,
        role=role,
        qa_pairs=''.join(qa_pairs)
    )
    
    # Log the prompt being sent to LLM for debugging
    print("\n=== PROMPT SENT TO LLM ===")
    print(f"Role: {role}")
    print(f"Interview Type: {interview_type}")
    print(f"Number of Q&A pairs: {len(qa_pairs)}")
    print("Q&A Preview:")
    for i, qa in enumerate(qa_pairs[:2], 1):  # Show first 2 Q&As
        print(f"\nQ{i}: {qa[:200]}...")
    print("==========================\n")
    
    response = main_app._llm_based_response(prompt)
    print(f"INFO:__main__:LLM response: {response[:500]}...")  # Show first 500 chars
    
    import re, json
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            
            # Post-processing validation to enforce scoring rules
            print("\n=== POST-PROCESSING VALIDATION ===")
            
            # Calculate actual answered questions
            actual_answered = len(answered_questions)
            total_questions = len(questions)
            
            print(f"Answered: {actual_answered}/{total_questions} questions")
            
            # Enforce incomplete data rules
            if actual_answered < total_questions * 0.5:
                print(f"OVERRIDE: Less than 50% answered ({actual_answered}/{total_questions}) - forcing INSUFFICIENT_DATA")
                result['overall_rating'] = 'N/A'
                result['overall_score'] = 0
                result['data_quality'] = 'INSUFFICIENT_DATA'
                result['recommendation'] = 'INCOMPLETE_DATA'
                
                # Zero out domain-specific scores if relevant questions weren't answered
                if actual_answered <= 1:  # Only introduction answered
                    print("OVERRIDE: Only introduction answered - zeroing technical/analytical scores")
                    result['technical_score'] = 0
                    result['technical_rating'] = 'N/A'
                    result['technical_reason'] = 'No technical questions answered'
                    result['analytical_score'] = 0
                    result['analytical_rating'] = 'N/A'
                    result['analytical_reason'] = 'No analytical questions answered'
                    result['behavioral_presence_score'] = 0
                    result['behavioral_presence_rating'] = 'N/A'
            
            # Validate technical scores aren't inflated from introduction
            if actual_answered == 1 and result.get('technical_score', 0) > 0:
                print("OVERRIDE: Technical score detected with only 1 answer - forcing to 0")
                result['technical_score'] = 0
                result['technical_rating'] = 'N/A'
                result['technical_reason'] = 'Technical questions not answered'
            
            # Add metadata
            result['questions_answered'] = actual_answered
            result['questions_total'] = total_questions
            result['completion_rate'] = round(actual_answered / total_questions * 100, 1) if total_questions > 0 else 0
            
            print(f"Final ratings: Overall={result.get('overall_rating')}, Technical={result.get('technical_rating')}, Data Quality={result.get('data_quality')}")
            print("===================================\n")
            
            # Store feedback in session
            session['interview_feedback'] = result
            session.modified = True
            return jsonify(result)
        except Exception as e:
            logger.error(f"Failed to parse interview feedback: {e}")
            return jsonify({'error': 'Failed to parse feedback.'}), 500
    return jsonify({'error': 'No valid feedback generated.'}), 500

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads."""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    uploaded_data = []
    
    for file in files:
        if file.filename == '':
            continue
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                df = load_dataset(filepath)
                table_name = filename.split('.')[0]
                
                uploaded_data.append({
                    'filename': filename,
                    'table_name': table_name,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'preview': df.head().to_html(classes='table table-striped')
                })
                
            except Exception as e:
                logger.error(f"Error loading file {filename}: {e}")
                return jsonify({'error': f'Error loading file {filename}: {str(e)}'}), 400
    
    # Store uploaded files info in session
    session['uploaded_files'] = [item['filename'] for item in uploaded_data]
    session['messages'] = []
    
    return jsonify({'files': uploaded_data})

@app.route('/ask', methods=['POST'])
def ask():
    """Handle Q&A requests."""
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    if 'uploaded_files' not in session or not session['uploaded_files']:
        return jsonify({'error': 'No datasets uploaded'}), 400
    
    try:
        # Load datasets
        dfs = []
        table_names = []
        for filename in session['uploaded_files']:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            df = load_dataset(filepath)
            dfs.append(df)
            table_names.append(filename.split('.')[0])
        
        # Build dataset info
        datasets_info = build_dataframes_info(dfs, table_names)
        
        # Generate SQL query
        sql_prompt = DATASET_SQL_GENERATION_PROMPT.format(dataset_info=datasets_info, question=question)
        sql_response = main_app._llm_based_response(sql_prompt)
        
        response_data = {}
        
        if "text_to_sql" in sql_response:
            parts = sql_response.split(":", 1)
            sql_query = parts[1].strip()
            sql_query = sql_query.replace("```sql", "").replace("```", "").replace("|", "").strip()
            
            response_data['sql_query'] = sql_query
            
            try:
                query_result = run_sql_query(dfs, sql_query, table_names)
                response_data['query_result'] = query_result.to_html(classes='table table-striped')
                
                # Generate final answer
                final_prompt = DATASET_ANSWER_GENERATION_PROMPT.format(retrived_query=query_result.to_dict(), question=question)
                final_response = main_app._llm_based_response(final_prompt)
                
                if "final_answer" in final_response:
                    parts = final_response.split(":", 1)
                    final_answer = parts[1].strip()
                    # Format the answer for better display
                    response_data['answer'] = format_llm_response(final_answer)
                else:
                    response_data['answer'] = "LLM did not return a valid final answer."
                    
            except Exception as e:
                logger.error(f"Error executing SQL query: {e}")
                response_data['error'] = f"Error executing SQL query: {str(e)}"
                
        elif "answer_without_sql" in sql_response:
            parts = sql_response.split(":", 1)
            answer = parts[1].strip()
            response_data['answer'] = format_llm_response(answer)
        else:
            response_data['error'] = "LLM did not return a valid response."
        
        # Store in session
        if 'messages' not in session:
            session['messages'] = []
        session['messages'].append({'role': 'user', 'content': question})
        session['messages'].append({'role': 'assistant', 'content': response_data.get('answer', 'Error')})
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear-session', methods=['POST'])
def clear_session():
    """Clear session data."""
    session.clear()
    return jsonify({'success': True})

@app.route('/check-languages', methods=['GET'])
def check_languages():
    """Check which programming languages are available for execution."""
    from helper.code_executor import CodeExecutor
    
    languages = ['python', 'javascript', 'java', 'cpp', 'csharp', 'go', 'typescript', 'kotlin', 'rust', 'ruby', 'php', 'swift']
    available = {}
    
    # Check if Piston API is available
    piston_available = CodeExecutor.is_piston_available()
    
    for lang in languages:
        if lang == 'python':
            # Python uses local execution
            available[lang] = CodeExecutor.is_language_available(lang)
        else:
            # Other languages use Piston API
            available[lang] = piston_available and lang in CodeExecutor.LANGUAGE_MAP
    
    return jsonify({
        'available': available,
        'piston_status': piston_available,
        'message': 'Python: local execution. Others: cloud-based via Piston API.'
    })

@app.route('/coding-generate', methods=['POST'])
def coding_generate():
    """Generate a coding exercise based on topic and difficulty."""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        difficulty = data.get('difficulty', 'beginner')
        language = data.get('language', 'python')
        
        if not topic:
            return jsonify({'error': 'Please provide a topic'}), 400
        
        logger.info(f"Generating {difficulty} {language} exercise for topic: {topic}")
        
        # Get previously generated exercise titles to avoid repetition
        previous_exercises = session.get('previous_exercises', [])
        previous_titles = [ex.get('title', '') for ex in previous_exercises if ex.get('topic') == topic and ex.get('difficulty') == difficulty]
        
        # Build context about previous exercises
        previous_context = ""
        if previous_titles:
            previous_context = f"""

IMPORTANT: You have previously generated these exercises for this topic and difficulty:
{chr(10).join(['- ' + title for title in previous_titles])}

You MUST create a COMPLETELY DIFFERENT exercise. Use different:
- Problem statement and scenario
- Function names
- Input/output requirements
- Edge cases and examples
DO NOT repeat any of the above exercises.
"""
        
        # Create prompt for exercise generation with JSON response
        # Get language-specific output instructions from utility
        output_instructions = get_output_instructions_by_language()
        output_note = output_instructions.get(language, 'Use appropriate output method for your language')
        
        # Prepare example code snippets based on language from utility
        example_codes = get_example_code_by_language()
        example_code = example_codes.get(language, 'output(functionName(testInput));')
        
        generate_prompt = CODING_EXERCISE_GENERATION_PROMPT.format(
            topic=topic,
            difficulty=difficulty,
            language=language,
            language_upper=language.upper(),
            previous_context=previous_context,
            output_note=output_note,
            example_code=example_code,
            example_output='Expected output value'
        )
        
        # Get response from LLM
        response = main_app._llm_based_response(generate_prompt)
        
        # Parse JSON response
        import json
        
        try:
            # Clean response using utility function
            cleaned_response = clean_json_response(response)
            exercise_data = json.loads(cleaned_response)
            
            # Validate required fields
            required_fields = ['title', 'description', 'input_format', 'output_format', 
                             'constraints', 'examples', 'visible_test_cases', 'hidden_test_cases', 'hints', 'starter_code']
            missing_fields = [field for field in required_fields if field not in exercise_data]
            if missing_fields:
                logger.warning(f"Missing fields in exercise data: {missing_fields}")
                # Set defaults for missing fields
                if 'visible_test_cases' not in exercise_data:
                    exercise_data['visible_test_cases'] = []
                if 'hidden_test_cases' not in exercise_data:
                    exercise_data['hidden_test_cases'] = []
            
            visible_count = len(exercise_data.get('visible_test_cases', []))
            hidden_count = len(exercise_data.get('hidden_test_cases', []))
            logger.info(f"Parsed exercise with {visible_count} visible and {hidden_count} hidden test cases")
            
            # Format the description for display
            # The description already contains markdown formatting including code blocks
            formatted_description = f"""
# {exercise_data.get('title', 'Coding Exercise')}

{exercise_data.get('description', '')}

## Input Format
{exercise_data.get('input_format', '')}

## Output Format
{exercise_data.get('output_format', '')}

## Constraints
{chr(10).join(['* ' + c for c in exercise_data.get('constraints', [])])}

## Example Test Cases
"""
            
            for i, example in enumerate(exercise_data.get('examples', []), 1):
                formatted_description += f"""
#### Example {i}
**Input:**
```{language}
{example.get('input', '')}
```

**Output:**
```
{example.get('output', '')}
```
"""
                if example.get('explanation'):
                    formatted_description += f"\n**Explanation:** {example['explanation']}\n"
            
            if exercise_data.get('hints'):
                formatted_description += "\n## Hints\n"
                formatted_description += chr(10).join([f"{i}. {h}" for i, h in enumerate(exercise_data.get('hints', []), 1)])
            
            formatted_description += f"""

## Starter Code
```{language}
{exercise_data.get('starter_code', '')}
```
"""
            
            # Store exercise in session for validation
            session['current_exercise'] = {
                'topic': topic,
                'difficulty': difficulty,
                'language': language,
                'content': exercise_data,
                'raw_data': exercise_data,
                'title': exercise_data.get('title', '')
            }
            # Store detailed exercise data for prompts
            session['current_exercise_data'] = exercise_data
            session['current_language'] = language
            session['hint_attempts'] = 0  # Reset hint counter
            
            # Track previously generated exercises to avoid repetition
            if 'previous_exercises' not in session:
                session['previous_exercises'] = []
            
            session['previous_exercises'].append({
                'topic': topic,
                'difficulty': difficulty,
                'language': language,
                'title': exercise_data.get('title', '')
            })
            
            # Keep only last 10 exercises to prevent session from growing too large
            if len(session['previous_exercises']) > 10:
                session['previous_exercises'] = session['previous_exercises'][-10:]
            
            session.modified = True
            
            logger.info("Exercise generated successfully from JSON")
            return jsonify({
                'exercise': format_llm_response(formatted_description),
                'starter_code': exercise_data.get('starter_code', ''),
                'visible_test_cases': exercise_data.get('visible_test_cases', []),
                'hidden_test_cases': exercise_data.get('hidden_test_cases', []),
                'title': exercise_data.get('title', ''),
                'topic': topic,
                'difficulty': difficulty,
                'language': language
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response}")
            # Fallback to old method if JSON parsing fails
            return jsonify({'error': 'Failed to generate structured exercise. Please try again.'}), 500
        
    except Exception as e:
        logger.error(f"Error generating exercise: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/coding-validate', methods=['POST'])
def coding_validate():
    """Validate user's code solution."""
    try:
        data = request.json
        user_code = data.get('code', '').strip()
        language = data.get('language', 'python')
        
        if not user_code:
            return jsonify({'error': 'Please provide your code'}), 400
        
        if 'current_exercise' not in session:
            return jsonify({'error': 'No active exercise. Generate an exercise first.'}), 400
        
        exercise = session['current_exercise']
        exercise_data = session.get('current_exercise_data', {})
        
        logger.info(f"Validating {language} code solution")
        
        # Create prompt for code validation
        validate_prompt = CODING_VALIDATION_PROMPT.format(
            title=exercise_data.get('title', 'Coding Exercise'),
            language=language,
            user_code=user_code,
            test_results="Validation in progress..."
        )
        
        # Get response from LLM
        response = main_app._llm_based_response(validate_prompt)
        
        # Parse JSON response
        try:
            import json
            cleaned_response = clean_json_response(response)
            validation_data = json.loads(cleaned_response)
            
            # Format validation feedback
            status = validation_data.get('validation_status', 'unknown')
            score = validation_data.get('score', 0)
            
            # Status badge
            badge_class = 'success' if status == 'pass' else 'danger'
            feedback_html = f'<div class="alert alert-{badge_class}">'
            feedback_html += f'<h5>Status: {status.upper()} (Score: {score}/100)</h5>'
            feedback_html += '</div>'
            
            # Feedback
            feedback_text = validation_data.get('feedback', '')
            feedback_html += f'<h5>Feedback:</h5><p>{feedback_text}</p>'
            
            # Suggestions
            suggestions = validation_data.get('suggestions', [])
            if suggestions:
                feedback_html += '<h5>Suggestions for Improvement:</h5><ul class="formatted-list">'
                for suggestion in suggestions:
                    feedback_html += f'<li>{suggestion}</li>'
                feedback_html += '</ul>'
            
            logger.info("Code validation completed")
            return jsonify({'feedback': feedback_html})
        except json.JSONDecodeError:
            # Fallback to plain text formatting
            logger.warning("Could not parse validation JSON, using plain text")
            return jsonify({'feedback': format_llm_response(response)})
        
    except Exception as e:
        logger.error(f"Error validating code: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/coding-hint', methods=['POST'])
def coding_hint():
    """Get a hint for the current exercise."""
    try:
        if 'current_exercise' not in session:
            return jsonify({'error': 'No active exercise. Generate an exercise first.'}), 400
        
        exercise = session['current_exercise']
        
        logger.info("Generating hint for current exercise")
        
        # Get exercise details from session
        exercise_data = session.get('current_exercise_data', {})
        attempt_count = session.get('hint_attempts', 0) + 1
        session['hint_attempts'] = attempt_count
        
        # Create prompt for hint generation
        hint_prompt = CODING_HINT_GENERATION_PROMPT.format(
            title=exercise_data.get('title', 'Coding Exercise'),
            description=exercise_data.get('description', exercise.get('content', '')),
            language=session.get('current_language', 'python'),
            attempt=attempt_count,
            num_hints=3
        )
        
        # Get response from LLM
        response = main_app._llm_based_response(hint_prompt)
        
        # Parse JSON response
        try:
            import json
            cleaned_response = clean_json_response(response)
            hint_data = json.loads(cleaned_response)
            
            # Format hints as numbered list
            hints_html = '<h5>Progressive Hints:</h5><ol class="formatted-list">'
            for hint in hint_data.get('hints', []):
                hints_html += f'<li>{hint}</li>'
            hints_html += '</ol>'
            
            logger.info("Hint generated successfully")
            return jsonify({'hint': hints_html})
        except json.JSONDecodeError:
            # Fallback to plain text formatting
            logger.warning("Could not parse hint JSON, using plain text")
            return jsonify({'hint': format_llm_response(response)})
        
    except Exception as e:
        logger.error(f"Error generating hint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/coding-run', methods=['POST'])
def coding_run():
    """Run user's code with all test cases."""
    try:
        data = request.json
        user_code = data.get('code', '').strip()
        language = data.get('language', 'python')
        
        if not user_code:
            return jsonify({'error': 'Please provide code to run'}), 400
        
        if 'current_exercise' not in session:
            return jsonify({'error': 'No active exercise. Generate an exercise first.'}), 400
        
        exercise = session['current_exercise']
        exercise_data = exercise.get('raw_data', {})
        visible_tests = exercise_data.get('visible_test_cases', [])
        hidden_tests = exercise_data.get('hidden_test_cases', [])
        
        logger.info(f"Running {language} code with {len(visible_tests)} visible and {len(hidden_tests)} hidden test cases")
        
        # Import code executor
        from helper.code_executor import CodeExecutor
        
        # Check if language is supported
        if language not in CodeExecutor.LANGUAGE_MAP:
            return jsonify({
                'error': f'{language.capitalize()} is not supported. Please choose a supported language.'
            }), 400
        
        # Real code execution for all supported languages
        if language in CodeExecutor.LANGUAGE_MAP:
            import html
            
            all_tests = visible_tests + hidden_tests
            results = []
            passed_count = 0
            
            try:
                # Run each test case
                for idx, test in enumerate(all_tests):
                    test_code = test.get('code', '')
                    expected = test.get('expected_output', '').strip()
                    is_visible = idx < len(visible_tests)
                    
                    # Unescape escape sequences from JSON
                    test_code = test_code.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                    expected = expected.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                    
                    # Clean test code - remove markdown code blocks if present
                    test_code = test_code.strip()
                    if test_code.startswith('```'):
                        # Remove markdown code fences
                        lines = test_code.split('\n')
                        # Remove first line (```language)
                        if lines[0].startswith('```'):
                            lines = lines[1:]
                        # Remove last line (```)
                        if lines and lines[-1].strip() == '```':
                            lines = lines[:-1]
                        test_code = '\n'.join(lines)
                    
                    # Smart code combination based on language
                    if language == 'csharp':
                        # For C#, extract using statements and combine properly
                        user_lines = user_code.split('\n')
                        test_lines = test_code.split('\n')
                        
                        # Separate using statements from rest
                        user_usings = [line for line in user_lines if line.strip().startswith('using ')]
                        user_rest = [line for line in user_lines if not line.strip().startswith('using ')]
                        test_usings = [line for line in test_lines if line.strip().startswith('using ')]
                        test_rest = [line for line in test_lines if not line.strip().startswith('using ')]
                        
                        # Combine: all usings first, then user code, then test code
                        all_usings = list(dict.fromkeys(user_usings + test_usings))  # Remove duplicates
                        full_code = '\n'.join(all_usings) + '\n\n' + '\n'.join(user_rest) + '\n\n// Test execution\n' + '\n'.join(test_rest)
                    
                    elif language == 'java':
                        # For Java, extract imports and combine properly
                        user_lines = user_code.split('\n')
                        test_lines = test_code.split('\n')
                        
                        user_imports = [line for line in user_lines if line.strip().startswith('import ')]
                        user_rest = [line for line in user_lines if not line.strip().startswith('import ')]
                        test_imports = [line for line in test_lines if line.strip().startswith('import ')]
                        test_rest = [line for line in test_lines if not line.strip().startswith('import ')]
                        
                        all_imports = list(dict.fromkeys(user_imports + test_imports))
                        full_code = '\n'.join(all_imports) + '\n\n' + '\n'.join(user_rest) + '\n\n// Test execution\n' + '\n'.join(test_rest)
                    
                    else:
                        # For other languages, simple concatenation
                        comment_syntax = {
                            'python': '#',
                            'javascript': '//',
                            'typescript': '//',
                            'cpp': '//',
                            'c': '//',
                            'go': '//',
                            'rust': '//',
                            'kotlin': '//',
                            'swift': '//',
                            'php': '//',
                            'ruby': '#'
                        }.get(language, '//')
                        
                        full_code = user_code + f'\n\n{comment_syntax} Test execution\n' + test_code
                    
                    # Execute the code using the unified executor
                    exec_result = CodeExecutor.execute(full_code, language)
                    
                    # Check if output matches expected
                    actual = exec_result['output']
                    passed = exec_result['success'] and actual == expected
                    if passed:
                        passed_count += 1
                    
                    results.append({
                        'test_num': idx + 1,
                        'visible': is_visible,
                        'passed': passed,
                        'actual': actual if is_visible else '(hidden)',
                        'expected': expected if is_visible else '(hidden)',
                        'error': exec_result['error'] if not exec_result['success'] else None,
                        'code': test_code if is_visible else '(hidden)'
                    })
                
                # Format results HTML
                output_html = '<div class="test-results">'
                output_html += f'<h5 class="mb-3">Test Results: {passed_count}/{len(all_tests)} Passed</h5>'
                
                # Progress bar
                pass_percentage = (passed_count / len(all_tests)) * 100
                bar_color = 'success' if pass_percentage == 100 else ('warning' if pass_percentage >= 60 else 'danger')
                output_html += f'''
                <div class="progress mb-4" style="height: 25px;">
                    <div class="progress-bar bg-{bar_color}" role="progressbar" 
                         style="width: {pass_percentage}%;" 
                         aria-valuenow="{passed_count}" aria-valuemin="0" aria-valuemax="{len(all_tests)}">
                        {passed_count}/{len(all_tests)}
                    </div>
                </div>
                '''
                
                # Visible test cases
                output_html += '<h6><i class="bi bi-eye"></i> Visible Test Cases:</h6>'
                for r in results[:len(visible_tests)]:
                    status_icon = '✓' if r['passed'] else '✗'
                    status_class = 'success' if r['passed'] else 'danger'
                    output_html += f'''
                    <div class="card mb-2 border-{status_class}">
                        <div class="card-header bg-{status_class} text-white">
                            <strong>{status_icon} Test Case {r['test_num']}</strong>
                        </div>
                        <div class="card-body">
                            <p><strong>Code:</strong></p>
                            <pre class="bg-light p-2 border rounded"><code>{html.escape(r['code'])}</code></pre>
                            <p><strong>Expected:</strong> <code>{html.escape(r['expected'])}</code></p>
                            <p><strong>Actual:</strong> <code>{html.escape(r['actual'])}</code></p>
                            {f'<p class="text-danger"><strong>Error:</strong> {html.escape(r["error"])}</p>' if r['error'] else ''}
                        </div>
                    </div>
                    '''
                
                # Hidden test cases summary
                output_html += '<h6 class="mt-4"><i class="bi bi-eye-slash"></i> Hidden Test Cases:</h6>'
                hidden_passed = sum(1 for r in results[len(visible_tests):] if r['passed'])
                hidden_total = len(hidden_tests)
                output_html += f'<p class="text-muted">{hidden_passed}/{hidden_total} hidden test cases passed</p>'
                
                output_html += '</div>'
                
                logger.info(f"Code executed: {passed_count}/{len(all_tests)} tests passed")
                return jsonify({
                    'result': output_html,
                    'passed': passed_count,
                    'total': len(all_tests),
                    'all_passed': passed_count == len(all_tests)
                })
                
            except Exception as exec_error:
                logger.error(f"Error during code execution: {exec_error}")
                return jsonify({'error': f'Execution error: {str(exec_error)}'}), 500
        else:
            # Unsupported language - fall back to AI simulation
            return jsonify({
                'error': f'Real execution not supported for {language}. Please use Python, JavaScript, Java, C++, C#, or Go.'
            }), 400
        
    except Exception as e:
        logger.error(f"Error running code: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/coding-solution', methods=['POST'])
def coding_solution():
    """Get the complete solution with explanation."""
    try:
        if 'current_exercise' not in session:
            return jsonify({'error': 'No active exercise. Generate an exercise first.'}), 400
        
        exercise = session['current_exercise']
        exercise_data = session.get('current_exercise_data', {})
        language = session.get('current_language', exercise.get('language', 'python'))
        
        logger.info("Generating solution for current exercise")
        
        # Create prompt for solution generation
        solution_prompt = CODING_SOLUTION_GENERATION_PROMPT.format(
            title=exercise_data.get('title', 'Coding Exercise'),
            description=exercise_data.get('description', exercise.get('content', '')),
            language=language
        )
        
        # Get response from LLM
        response = main_app._llm_based_response(solution_prompt)
        
        # Parse JSON response
        try:
            import json
            cleaned_response = clean_json_response(response)
            solution_data = json.loads(cleaned_response)
            
            # Format solution with sections
            solution_html = f'<h4>Complete Solution</h4>'
            
            # Code
            code = solution_data.get('solution_code', '')
            solution_html += f'<h5>Solution Code:</h5>'
            solution_html += f'<pre><code class="language-{language}">{code}</code></pre>'
            
            # Explanation
            explanation = solution_data.get('explanation', '')
            solution_html += f'<h5>Explanation:</h5><p>{explanation}</p>'
            
            # Complexity
            complexity = solution_data.get('complexity', '')
            solution_html += f'<h5>Complexity Analysis:</h5><p>{complexity}</p>'
            
            # Alternatives
            alternatives = solution_data.get('alternatives', [])
            if alternatives:
                solution_html += '<h5>Alternative Approaches:</h5><ul class="formatted-list">'
                for alt in alternatives:
                    solution_html += f'<li>{alt}</li>'
                solution_html += '</ul>'
            
            logger.info("Solution generated successfully")
            return jsonify({'solution': solution_html})
        except json.JSONDecodeError:
            # Fallback to plain text formatting
            logger.warning("Could not parse solution JSON, using plain text")
            return jsonify({'solution': format_llm_response(response)})
        
    except Exception as e:
        logger.error(f"Error generating solution: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/document-upload', methods=['POST'])
def document_upload():
    """Handle document upload and processing."""
    try:
        if 'document' not in request.files:
            return jsonify({'error': 'No document provided'}), 400
        
        file = request.files['document']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.ppt', '.pptx')):
            return jsonify({'error': 'Only PDF and PowerPoint files are supported'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logger.info(f"Processing document: {filename}")
        
        # Import required libraries
        from helper.document_processor import DocumentProcessor
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        
        # Process document
        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
        result = processor.process_document(filepath, filename)
        
        # Create embeddings
        # WARNING: Model must match in /document-ask endpoint to avoid dimension mismatch!
        hf_token = os.environ.get('HF_TOKEN')
        if not hf_token:
            return jsonify({'error': 'HuggingFace token not found'}), 400
        
        # Using google/embeddinggemma-300m for documents (300 dimensions)
        embeddings = HuggingFaceEndpointEmbeddings(
            model="google/embeddinggemma-300m",
            huggingfacehub_api_token=hf_token
        )
        
        # Create vector store
        logger.info("Creating vector store for document...")
        vector_store = FAISS.from_documents(result['chunks'], embeddings)
        
        # Save vector store
        import uuid
        session_id = session.get('doc_id', str(uuid.uuid4()))
        session['doc_id'] = session_id
        
        vector_store_path = os.path.join(app.config['UPLOAD_FOLDER'], f'doc_vector_store_{session_id}')
        os.makedirs(vector_store_path, exist_ok=True)
        vector_store.save_local(vector_store_path)
        
        session['doc_vector_store_path'] = vector_store_path
        session['doc_filename'] = filename
        session['doc_metadata'] = result['metadata']
        
        logger.info("Document processed successfully")
        
        return jsonify({
            'success': True,
            'metadata': result['metadata'],
            'message': 'Document processed successfully!'
        })
        
    except Exception as e:
        logger.error(f"Error processing document: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/document-ask', methods=['POST'])
def document_ask():
    """Ask questions about uploaded document."""
    try:
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        if 'doc_vector_store_path' not in session:
            return jsonify({'error': 'Please upload a document first'}), 400
        
        logger.info(f"Processing document question: {question}")
        
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        
        # Check for HF_TOKEN
        hf_token = os.environ.get('HF_TOKEN')
        if not hf_token:
            return jsonify({'error': 'HuggingFace token not found'}), 400
        
        # Load vector store with same model as during creation (google/embeddinggemma-300m)
        embeddings = HuggingFaceEndpointEmbeddings(
            model="google/embeddinggemma-300m",
            huggingfacehub_api_token=hf_token
        )
        
        vector_store = FAISS.load_local(
            session['doc_vector_store_path'],
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Search for relevant chunks
        logger.info("Searching for relevant context...")
        relevant_docs_with_scores = vector_store.similarity_search_with_score(question, k=3)
        
        relevant_docs = [doc for doc, score in relevant_docs_with_scores]
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Create augmented prompt
        augmented_prompt = DOCUMENT_QA_PROMPT.format(
            context=context_text,
            question=question
        )
        
        # Get response from LLM
        logger.info("Generating answer with LLM...")
        response = main_app._llm_based_response(augmented_prompt)
        
        # Format sources
        sources = []
        for i, (doc, score) in enumerate(relevant_docs_with_scores):
            sources.append({
                'segment': i + 1,
                'content': doc.page_content[:300] + '...' if len(doc.page_content) > 300 else doc.page_content,
                'relevance': f"{(1 - score) * 100:.1f}%"
            })
        
        logger.info("Document question answered successfully")
        return jsonify({
            'answer': format_llm_response(response),
            'sources': sources
        })
        
    except Exception as e:
        logger.error(f"Error processing document question: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/youtube-analyze', methods=['POST'])
def youtube_analyze():
    """Analyze YouTube video and create vector store using open-source tools."""
    try:
        data = request.json
        video_url = data.get('video_url')
        
        if not video_url:
            return jsonify({'error': 'No video URL provided'}), 400
        
        logger.info(f"Starting YouTube analysis for URL: {video_url}")
        
        # Import required libraries
        from helper.youtube_transcriber import YouTubeTranscriber
        from langchain_core.documents import Document
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        
        logger.info("Libraries imported successfully")
        
        # Step 1: Transcribe video using youtube-transcript-api
        logger.info("Initializing YouTube transcriber...")
        transcriber = YouTubeTranscriber(model_name="base")
        
        logger.info("Fetching YouTube transcript...")
        transcription_result = transcriber.transcribe(video_url)
        full_text = transcription_result['text']
        detected_language = transcription_result.get('language', 'unknown')
        
        logger.info(f"Transcription completed. Language: {detected_language}")
        logger.info(f"Transcript length: {len(full_text)} characters")
        
        # Create a document from the transcript
        docs = [Document(
            page_content=full_text,
            metadata={
                'source': video_url,
                'language': detected_language
            }
        )]
        
        # Step 2: Split text into chunks using RecursiveCharacterTextSplitter
        logger.info("Splitting text into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        splits = text_splitter.split_documents(docs)
        logger.info(f"Created {len(splits)} text chunks")
        
        # Step 3: Create embeddings using HuggingFace API
        # WARNING: Model must match in /youtube-ask endpoint to avoid dimension mismatch!
        logger.info("Creating embeddings with HuggingFace API...")
        hf_token = os.environ.get('HF_TOKEN')
        if not hf_token:
            return jsonify({'error': 'HuggingFace token not found. Please set HF_TOKEN in .env file'}), 400
        
        # Using sentence-transformers/all-MiniLM-L6-v2 for YouTube (384 dimensions)
        embeddings = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=hf_token
        )
        
        logger.info("Building FAISS vector store...")
        # Create vector store
        vector_store = FAISS.from_documents(splits, embeddings)
        logger.info("Vector store created successfully")
        
        # Store vector store in session (serialize it)
        import uuid
        session_id = session.get('id', str(uuid.uuid4()))
        session['id'] = session_id
        
        vector_store_path = os.path.join(app.config['UPLOAD_FOLDER'], f'vector_store_{session_id}')
        os.makedirs(vector_store_path, exist_ok=True)
        vector_store.save_local(vector_store_path)
        
        session['vector_store_path'] = vector_store_path
        session['current_video_url'] = video_url
        
        logger.info("YouTube analysis completed successfully!")
        return jsonify({
            'success': True,
            'chunks': len(splits),
            'language': detected_language,
            'message': f'Video transcribed and analyzed successfully! Language: {detected_language}'
        })
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return jsonify({'error': f'Missing required library: {str(e)}. Please install: pip install -r requirements.txt'}), 500
    except Exception as e:
        logger.error(f"Error analyzing YouTube video: {e}", exc_info=True)
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/youtube-ask', methods=['POST'])
def youtube_ask():
    """Ask questions about the analyzed YouTube video using local embeddings."""
    try:
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        if 'vector_store_path' not in session:
            return jsonify({'error': 'Please analyze a video first'}), 400
        
        logger.info(f"Processing YouTube question: {question}")
        
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        
        # Check for HF_TOKEN
        hf_token = os.environ.get('HF_TOKEN')
        if not hf_token:
            return jsonify({'error': 'HuggingFace token not found'}), 400
        
        # Load vector store with HuggingFace API embeddings
        # IMPORTANT: Must use same model as during vector store creation
        logger.info("Loading vector store with HuggingFace API embeddings...")
        embeddings = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=hf_token
        )
        
        vector_store = FAISS.load_local(
            session['vector_store_path'],
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Search for relevant documents with similarity scores
        logger.info("Searching for relevant context...")
        relevant_docs_with_scores = vector_store.similarity_search_with_score(question, k=4)
        
        # Extract documents and format context
        relevant_docs = [doc for doc, score in relevant_docs_with_scores]
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Create augmented prompt
        augmented_prompt = YOUTUBE_QA_PROMPT.format(
            context=context_text,
            question=question
        )
        
        # Get response from LLM
        logger.info("Generating answer with LLM...")
        response = main_app._llm_based_response(augmented_prompt)
        
        # Format sources with similarity scores
        sources = []
        for i, (doc, score) in enumerate(relevant_docs_with_scores):
            sources.append({
                'segment': i + 1,
                'content': doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content,
                'relevance': f"{(1 - score) * 100:.1f}%"  # Convert distance to similarity percentage
            })
        
        logger.info("YouTube question answered successfully")
        return jsonify({
            'answer': format_llm_response(response),
            'sources': sources
        })
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return jsonify({'error': f'Missing required library: {str(e)}. Please install: pip install -r requirements.txt'}), 500
    except Exception as e:
        logger.error(f"Error processing YouTube question: {e}", exc_info=True)
        return jsonify({'error': f'Question processing failed: {str(e)}'}), 500

def allowed_file(filename):
    """Check if file extension is allowed."""
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'json'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_llm_response(text):
    """Format LLM response text for better HTML display."""
    import re
    import html
    
    # First escape HTML to prevent XSS, but we'll selectively unescape our formatted content
    # Store code blocks temporarily to avoid processing them
    code_blocks = []
    def store_code_block(match):
        code_blocks.append(match.group(0))
        return f"___CODE_BLOCK_{len(code_blocks) - 1}___"
    
    # Temporarily replace code blocks
    formatted = re.sub(r'```(\w+)?\n(.*?)```', store_code_block, text, flags=re.DOTALL)
    
    # Handle LaTeX math expressions BEFORE other formatting
    # Inline math: \( ... \) or $ ... $
    formatted = re.sub(r'\\\((.*?)\\\)', r'<span class="math-inline">\(\1\)</span>', formatted)
    formatted = re.sub(r'(?<!\$)\$(?!\$)([^\$]+?)\$(?!\$)', r'<span class="math-inline">$\1$</span>', formatted)
    
    # Display math: \[ ... \] or $$ ... $$
    formatted = re.sub(r'\\\[(.*?)\\\]', r'<div class="math-display">$$\1$$</div>', formatted, flags=re.DOTALL)
    formatted = re.sub(r'\$\$([^\$]+?)\$\$', r'<div class="math-display">$$\1$$</div>', formatted)
    
    # Replace ** bold ** with <strong> tags
    formatted = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', formatted)
    
    # Handle inline code with single backticks (not inside code blocks)
    # Preserve content exactly as-is
    formatted = re.sub(r'`([^`]+)`', r'<code>\1</code>', formatted)
    
    # Restore code blocks
    for i, block in enumerate(code_blocks):
        match = re.match(r'```(\w+)?\n(.*?)```', block, re.DOTALL)
        if match:
            lang = match.group(1) or 'text'
            code_content = html.escape(match.group(2))
            formatted = formatted.replace(f"___CODE_BLOCK_{i}___", 
                f'<pre><code class="language-{lang}">{code_content}</code></pre>')
        else:
            formatted = formatted.replace(f"___CODE_BLOCK_{i}___", block)
    
    # Split into lines for processing
    lines = formatted.split('\n')
    processed_lines = []
    in_list = False
    in_code_block = False
    in_table = False
    table_in_body = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip lines already in code blocks
        if '<pre>' in line or '</pre>' in line or in_code_block:
            if '<pre>' in line:
                in_code_block = True
            if '</pre>' in line:
                in_code_block = False
            processed_lines.append(line)
            continue
        
        # Handle markdown horizontal rules (---, ___, ***)
        if re.match(r'^[\-_*]{3,}$', stripped):
            if in_list:
                processed_lines.append('</ol>' if in_list == 'ordered' else '</ul>')
                in_list = False
            processed_lines.append('<hr class="section-divider">')
            continue
        
        # Handle tables (basic markdown table detection)
        if '|' in stripped and not in_list:
            if not in_table:
                processed_lines.append('<div class="table-responsive"><table class="table table-bordered table-hover"><thead>')
                in_table = True
                table_in_body = False  # Track if we're in tbody
            
            # Check if it's a separator row (|---|---|)
            if re.match(r'^\|[\s\-:]+\|', stripped):
                processed_lines.append('</thead><tbody>')
                table_in_body = True
            else:
                cells = [cell.strip() for cell in stripped.split('|')[1:-1]]
                if not any('---' in cell for cell in cells):
                    # Use table_in_body flag to determine tag type
                    tag = 'td' if table_in_body else 'th'
                    row = '<tr>' + ''.join(f'<{tag}>{cell}</{tag}>' for cell in cells) + '</tr>'
                    processed_lines.append(row)
            continue
        elif in_table and '|' not in stripped:
            processed_lines.append('</tbody></table></div>')
            in_table = False
            table_in_body = False
        
        # Detect indentation level for nested lists
        indent_match = re.match(r'^(\s*)', line)
        indent_level = len(indent_match.group(1)) if indent_match else 0
        
        # Check for bullet points (-, *, •)
        if re.match(r'^[\-\*•]\s+', stripped):
            if not in_list:
                processed_lines.append('<ul class="formatted-list">')
                in_list = True
            # Remove bullet marker and wrap in <li>
            content = re.sub(r'^[\-\*•]\s+', '', stripped)
            processed_lines.append(f'<li>{content}</li>')
        # Check for numbered lists (1., 2., etc.) - only at start of line (indent < 4)
        elif re.match(r'^\d+\.\s+', stripped) and indent_level < 4:
            if in_list and in_list != 'ordered':
                processed_lines.append('</ul>')
                in_list = False
            if not in_list:
                processed_lines.append('<ol class="formatted-list">')
                in_list = 'ordered'
            # Remove number and wrap in <li>
            content = re.sub(r'^\d+\.\s+', '', stripped)
            processed_lines.append(f'<li>{content}</li>')
        # Check if this is a continuation line (indented, no list marker)
        elif in_list and indent_level >= 4 and stripped:
            # This is continuation content for the previous list item
            # Append to the last <li> instead of creating a new one
            if processed_lines and processed_lines[-1].startswith('<li>'):
                # Remove the closing </li> tag
                last_item = processed_lines[-1]
                if last_item.endswith('</li>'):
                    processed_lines[-1] = last_item[:-5] + '<br>' + stripped + '</li>'
                else:
                    processed_lines[-1] = last_item + '<br>' + stripped
            else:
                processed_lines.append(f'<div class="ms-4">{stripped}</div>')
        else:
            # Close any open list
            if in_list:
                if in_list == 'ordered':
                    processed_lines.append('</ol>')
                else:
                    processed_lines.append('</ul>')
                in_list = False
            
            # Add line breaks for empty lines or wrap content in paragraphs
            if not stripped:
                processed_lines.append('<br>')
            else:
                # Handle different heading levels with ###, ##, #
                heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
                if heading_match:
                    level = len(heading_match.group(1))
                    content = heading_match.group(2)
                    if level == 1:
                        processed_lines.append(f'<h3 class="exercise-title">{content}</h3>')
                    elif level == 2:
                        processed_lines.append(f'<h4 class="exercise-section">{content}</h4>')
                    else:
                        processed_lines.append(f'<h5 class="exercise-subsection">{content}</h5>')
                # Check if line is a header (starts with capital letters and ends with colon or is all caps)
                elif re.match(r'^[A-Z][A-Z\s]+:?$', stripped) or (stripped.endswith(':') and len(stripped.split()) <= 5):
                    processed_lines.append(f'<h6 class="section-header">{stripped}</h6>')
                else:
                    processed_lines.append(f'<p class="mb-2">{stripped}</p>')
    
    # Close any remaining open structures
    if in_list:
        processed_lines.append('</ol>' if in_list == 'ordered' else '</ul>')
    if in_table:
        processed_lines.append('</tbody></table></div>')
    
    formatted = '\n'.join(processed_lines)
    
    # Wrap everything in a container div
    formatted = f'<div class="formatted-response">{formatted}</div>'
    
    return formatted

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)