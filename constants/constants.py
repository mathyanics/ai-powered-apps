# ============= DATASET Q&A PROMPTS =============
DATASET_SQL_GENERATION_PROMPT = """
You are an expert data analyst and a helpful assistant. Your primary task is to analyze the user's question and determine if it can be answered using the provided dataset information.
Question: {question}
Dataset Information: {dataset_info}

Based on your analysis of the user's question, you must choose one of the following two options:

**Option 1: The question is related to the dataset.**
- If the question can be answered by querying the provided dataset, you must generate the appropriate SQL query (works for pandasql).
- The SQL query must be compatible with pandasql/sqlite3 syntax.
- Your response MUST follow this exact format:
text_to_sql: The SQL query that can be used to retrieve the answer from the dataset. Not include any explanation or additional text.

**Option 2: The question is NOT related to the dataset.**
- If the question is a greeting, a question about yourself, or any other topic not related to the dataset, you should provide a direct and helpful answer without generating a SQL query.
- Your response MUST follow this exact format:
answer_without_sql: A direct and helpful answer to the user's question.

IMPORTANT: Always respond in ENGLISH only.
"""

DATASET_ANSWER_GENERATION_PROMPT = """
You are an expert data analyst. Given the following question, provide a detailed and accurate answer based on the dataset provided.
Question: {question}
Retrived Query: {retrived_query}

You need to generate the final answer to answer the question.
Please ensure that your response is clear, concise, and directly addresses the question using insights derived from the dataset.
The response should be in the following format:
final_answer: The final answer to the question based on the query result.

IMPORTANT: Always respond in ENGLISH, regardless of the language in the data. Please humanize the answer and avoid being too technical. Don't change the key "final_answer".
"""

# ============= INTERVIEW EXERCISE PROMPTS =============
INTERVIEW_QUESTION_GENERATION_PROMPT = """
You are an expert interviewer conducting a {interview_type} for the role: {role}.
{additional_info_text}

Generate 5 interview questions suitable for video interview format.
Each question should:
- Be clear and concise (suitable for 2-3 minute video answers)
- Be relevant to the role and interview type
- Be progressively challenging

Return a JSON object with:
{{
    "questions": [
        {{"id": 1, "question": "First question text", "time_limit": 180}},
        {{"id": 2, "question": "Second question text", "time_limit": 180}},
        {{"id": 3, "question": "Third question text", "time_limit": 180}},
        {{"id": 4, "question": "Fourth question text", "time_limit": 180}},
        {{"id": 5, "question": "Fifth question text", "time_limit": 180}}
    ]
}}

IMPORTANT: Return ONLY valid JSON, no additional text.
"""

INTERVIEW_ANALYSIS_PROMPT = """
You are an expert interviewer analyzing a {interview_type} interview for the role: {role}.

Here are the questions and candidate's video responses (transcribed):

{qa_pairs}

IMPORTANT: Use Behaviorally Anchored Rating Scales (BARS) instead of arbitrary percentages. Assess based on OBSERVABLE BEHAVIORS only.

CRITICAL SCORING RULES:
1. Question 1 typically asks about background/introduction - use ONLY for Communication and Role Fit assessment
2. Questions 2-5 typically assess technical/domain knowledge - use ONLY for Technical, Analytical, and Behavioral Presence
3. If a question is unanswered (missing transcript, <10 chars, or "No transcription available"), mark it as N/A
4. Domain-specific scores (Technical, Analytical) MUST be based on relevant technical questions, NOT introduction
5. If 50% or more questions are missing, set overall_rating to "N/A" and data_quality to "INSUFFICIENT_DATA"
6. Score only what is actually demonstrated - do NOT infer technical knowledge from job titles mentioned in introductions

Provide a COMPREHENSIVE and DETAILED analysis using BARS methodology:

1. Overall Performance Rating: Use BARS scale
   - "EXCEPTIONAL" (5): Consistently exceeds all expectations with concrete examples
   - "STRONG" (4): Frequently exceeds expectations in most areas
   - "SATISFACTORY" (3): Meets expectations consistently
   - "DEVELOPING" (2): Shows potential but needs improvement in key areas
   - "UNSATISFACTORY" (1): Falls below expectations in most areas
   - "N/A": Insufficient answered questions to assess (use when <50% answered)

2. Detailed Strengths (4-5 specific OBSERVABLE behaviors with examples from transcript)

3. Areas for Improvement (4-5 specific ACTIONABLE suggestions based on observable gaps)

4. BARS Ratings for Each Dimension (STRICT RULES):
   
   A. COMMUNICATION EFFECTIVENESS:
      - Assess from: ALL answered questions
      - Observable: Clear articulation, structured responses, active listening cues
      - If no answers: N/A, score 0
   
   B. TECHNICAL/DOMAIN KNOWLEDGE:
      - Assess from: ONLY technical questions (typically Q2-Q5, NOT introduction)
      - Observable: Accurate terminology, depth of explanations, practical examples
      - If no technical questions answered: N/A, score 0
      - NEVER infer from job titles in introduction
   
   C. ANALYTICAL ABILITY:
      - Assess from: ONLY problem-solving/technical questions (NOT introduction)
      - Observable: Structured thinking, consideration of alternatives, logical reasoning
      - If no relevant questions answered: N/A, score 0
   
   D. ROLE FIT:
      - Assess from: Introduction + understanding demonstrated across all answered questions
      - Observable: Understanding of role requirements, relevant experience examples
      - If only introduction answered: Mark as PARTIAL data, score max 40
   
   E. BEHAVIORAL PRESENCE:
      - Assess from: ALL answered questions
      - Observable: Response completeness, engagement tone, question handling
      - If <3 questions answered: N/A, score 0

5. Question-by-Question Analysis:
   For EACH question:
   - BARS rating (EXCEPTIONAL/STRONG/SATISFACTORY/DEVELOPING/UNSATISFACTORY/N/A)
   - Detailed feedback (2-3 sentences citing SPECIFIC observable behaviors OR "No transcript available")
   - Observable strengths (specific behaviors demonstrated OR "N/A")
   - Development areas (specific behaviors to improve OR "N/A")

6. Final Recommendation Logic:
   - If <50% questions answered: "INCOMPLETE_DATA"
   - If only introduction answered: "INCOMPLETE_DATA"
   - Otherwise: ["Strong Hire", "Hire", "Maybe", "No Hire"] with behavioral justification

7. Detailed Summary (3-4 sentences covering observable performance patterns, note missing questions)

8. Next Steps (specific behavioral development actions OR request to complete missing questions)

CRITICAL VALIDATION:
- If answer is empty/missing: Use "N/A" rating, 0 score, note "Insufficient data - no transcript available"
- If only Q1 answered: Technical score = 0, Analytical score = 0, overall_rating = "N/A", recommendation = "INCOMPLETE_DATA"
- If <3 questions answered: overall_rating = "N/A", data_quality = "INSUFFICIENT_DATA"
- NEVER give technical scores based solely on introduction question

Return JSON with this EXACT structure (MUST include both categorical BARS ratings AND numerical scores 0-100):
{{
    "overall_rating": <"EXCEPTIONAL"|"STRONG"|"SATISFACTORY"|"DEVELOPING"|"UNSATISFACTORY"|"N/A">,
    "overall_score": <0-100 numerical score, or 0 if N/A>,
    "data_quality": <"COMPLETE" if all answered | "PARTIAL" if 50-90% answered | "INSUFFICIENT_DATA" if <50% answered>,
    "questions_answered": <number of questions with real transcripts>,
    "questions_total": <total number of questions>,
    "strengths": [<array of observable behavior strings>],
    "improvements": [<array of actionable behavioral strings>],
    "communication_rating": <BARS rating>,
    "communication_score": <0-100>,
    "communication_reason": <detailed observable behaviors>,
    "technical_rating": <BARS rating>,
    "technical_score": <0-100>,
    "technical_reason": <detailed observable behaviors>,
    "analytical_rating": <BARS rating>,
    "analytical_score": <0-100>,
    "analytical_reason": <detailed observable behaviors>,
    "role_fit_rating": <BARS rating>,
    "role_fit_score": <0-100>,
    "role_fit_reason": <detailed observable behaviors>,
    "behavioral_presence_rating": <BARS rating (not confidence)>,
    "behavioral_presence_score": <0-100>,
    "behavioral_reason": <detailed observable behaviors>,
    "question_feedback": [
        {{
            "question_id": <number>,
            "question_text": <string>,
            "rating": <BARS rating or "N/A" if empty>,
            "feedback": <detailed behavioral observation or "No transcript available">,
            "observable_behaviors": <specific behaviors demonstrated or "N/A">,
            "development_areas": <specific behaviors to improve or "N/A">
        }}
    ],
    "recommendation": <"Strong Hire"|"Hire"|"Maybe"|"No Hire">,
    "summary": <detailed multi-sentence behavioral summary>,
    "next_steps": <specific behavioral development actions>
}}

Score Guidelines (0-100):
- EXCEPTIONAL: 90-100 (Outstanding, consistently exceeds all expectations with concrete examples)
- STRONG: 75-89 (Above average, frequently exceeds expectations in most areas)
- SATISFACTORY: 60-74 (Meets expectations consistently and adequately)
- DEVELOPING: 40-59 (Below expectations, shows potential but needs improvement)
- UNSATISFACTORY: 1-39 (Well below expectations in most areas)
- N/A: 0 (Insufficient data to assess)

Return ONLY the valid JSON object.
"""

# ============= CODING EXERCISE PROMPTS =============
CODING_EXERCISE_GENERATION_PROMPT = """
Generate a coding exercise for the following requirements:

TOPIC: {topic}
DIFFICULTY: {difficulty}
PROGRAMMING LANGUAGE: {language}{previous_context}

CRITICAL INSTRUCTIONS FOR TEST CASES:
- ALL test case code MUST be written in valid {language_upper} syntax
- DO NOT use Python syntax if the language is not Python
- Output formatting: {output_note}
- Test cases must be EXECUTABLE code that calls the function and outputs the result
- Ensure proper JSON escaping for special characters in code strings

You MUST respond with ONLY a valid JSON object. Format your response as pure JSON without markdown code blocks.

Required JSON structure:
- title: string (clear problem title)
- description: string (markdown formatted explanation)
- input_format: string (what inputs the function accepts)
- output_format: string (what the function returns)
- constraints: array of strings (3+ constraints)
- examples: array of objects with input, output, explanation fields
- visible_test_cases: array of EXACTLY 3 test case objects
- hidden_test_cases: array of EXACTLY 5 test case objects  
- hints: array of strings (2-3 helpful hints)
- starter_code: string (function skeleton in {language})

Each test case object must have:
- code: string (executable {language} code with proper escaping)
- expected_output: string (exact output the code produces)

Example for {language}:
{{
    "title": "Problem Title",
    "description": "Problem description...",
    "visible_test_cases": [
        {{
            "code": "{example_code}",
            "expected_output": "{example_output}"
        }}
    ]
}}

IMPORTANT: Return ONLY valid JSON without markdown code blocks.
"""

CODING_VALIDATION_PROMPT = """
Validate the following code submission:

PROBLEM: {title}
LANGUAGE: {language}
USER'S CODE:
{user_code}

TEST RESULTS:
{test_results}

Provide detailed feedback in JSON format:
{{
    "validation_status": "pass" or "fail",
    "feedback": "Detailed explanation of what worked/didn't work",
    "suggestions": ["Specific improvement suggestion 1", "Suggestion 2", ...],
    "score": 0-100
}}

Return ONLY valid JSON.
"""

CODING_HINT_GENERATION_PROMPT = """
Generate progressive hints for this coding problem:

PROBLEM: {title}
DESCRIPTION: {description}
LANGUAGE: {language}
CURRENT ATTEMPT NUMBER: {attempt}

Provide {num_hints} hints that progressively reveal the solution:
- Hint 1: High-level approach
- Hint 2: Key algorithm/data structure
- Hint 3: Implementation details (if applicable)

Return JSON:
{{
    "hints": ["Hint 1 text", "Hint 2 text", "Hint 3 text"]
}}

Return ONLY valid JSON.
"""

CODING_SOLUTION_GENERATION_PROMPT = """
Generate a detailed solution for this coding problem:

PROBLEM TITLE: {title}
DESCRIPTION: {description}
LANGUAGE: {language}

Provide:
1. Complete working solution code
2. Explanation of approach (3-4 paragraphs)
3. Time/space complexity analysis
4. Alternative approaches (if applicable)

Return JSON:
{{
    "solution_code": "Complete working code",
    "explanation": "Detailed explanation...",
    "complexity": "Time: O(...), Space: O(...)",
    "alternatives": ["Alternative approach 1", "Alternative 2"]
}}

Return ONLY valid JSON.
"""

# ============= DOCUMENT Q&A PROMPTS =============
DOCUMENT_QA_PROMPT = """
You are a helpful assistant that answers questions based on document content.

DOCUMENT CONTEXT:
{context}

USER QUESTION: {question}

Instructions:
- Answer based ONLY on the provided context
- If the answer is not in the context, say "I cannot find that information in the document"
- Cite specific sections when possible
- Be concise but comprehensive

Answer:
"""

# ============= YOUTUBE Q&A PROMPTS =============
YOUTUBE_QA_PROMPT = """
You are a helpful assistant that answers questions based on YouTube video transcripts.

VIDEO TRANSCRIPT:
{transcript}

USER QUESTION: {question}

Instructions:
- Answer based ONLY on the video transcript
- If the answer is not in the transcript, say "That topic was not discussed in this video"
- Include timestamps when relevant
- Be concise but comprehensive

Answer:
"""

# Backward compatibility aliases
prompt_template_1 = DATASET_SQL_GENERATION_PROMPT
prompt_template_2 = DATASET_ANSWER_GENERATION_PROMPT
