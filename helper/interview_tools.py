"""
Interview Exercise Tools Module
Handles interview generation, analysis, and validation.
"""

from typing import Dict, List, Optional, Tuple


class InterviewValidator:
    """Validate interview data and transcripts"""
    
    MIN_TRANSCRIPT_LENGTH = 10
    INSUFFICIENT_DATA_THRESHOLD = 0.5  # 50% questions must be answered
    PARTIAL_DATA_THRESHOLD = 0.9  # 90% for complete data
    
    @staticmethod
    def validate_transcript(transcript: str) -> bool:
        """Check if transcript is valid"""
        if not transcript:
            return False
        
        transcript = transcript.strip()
        
        # Check for placeholder text
        invalid_phrases = [
            'No transcription available',
            'No answer provided',
            'No transcript available'
        ]
        
        if transcript in invalid_phrases:
            return False
        
        # Check minimum length
        if len(transcript) < InterviewValidator.MIN_TRANSCRIPT_LENGTH:
            return False
        
        return True
    
    @staticmethod
    def analyze_completeness(answers: List[Dict]) -> Dict:
        """
        Analyze interview completeness.
        
        Args:
            answers: List of answer dictionaries with 'answer_text' field
            
        Returns:
            Dict with completeness metrics
        """
        total_questions = len(answers)
        answered_questions = 0
        
        for answer in answers:
            if InterviewValidator.validate_transcript(answer.get('answer_text', '')):
                answered_questions += 1
        
        completion_rate = answered_questions / total_questions if total_questions > 0 else 0
        
        # Determine data quality
        if completion_rate >= InterviewValidator.PARTIAL_DATA_THRESHOLD:
            data_quality = 'COMPLETE'
        elif completion_rate >= InterviewValidator.INSUFFICIENT_DATA_THRESHOLD:
            data_quality = 'PARTIAL'
        else:
            data_quality = 'INSUFFICIENT_DATA'
        
        return {
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'completion_rate': round(completion_rate * 100, 1),
            'data_quality': data_quality
        }
    
    @staticmethod
    def should_return_incomplete(completeness: Dict) -> bool:
        """Determine if interview should be marked as incomplete"""
        return completeness['data_quality'] == 'INSUFFICIENT_DATA'


class BARSScoring:
    """BARS (Behaviorally Anchored Rating Scales) scoring utilities"""
    
    # BARS rating to percentage mapping
    BARS_TO_PERCENTAGE = {
        'EXCEPTIONAL': 95,
        'STRONG': 80,
        'SATISFACTORY': 65,
        'DEVELOPING': 45,
        'UNSATISFACTORY': 25,
        'N/A': 0
    }
    
    # Score ranges for BARS ratings
    SCORE_RANGES = {
        'EXCEPTIONAL': (90, 100),
        'STRONG': (75, 89),
        'SATISFACTORY': (60, 74),
        'DEVELOPING': (40, 59),
        'UNSATISFACTORY': (1, 39),
        'N/A': (0, 0)
    }
    
    @staticmethod
    def get_percentage(bars_rating: str) -> int:
        """Convert BARS rating to percentage"""
        return BARSScoring.BARS_TO_PERCENTAGE.get(bars_rating, 0)
    
    @staticmethod
    def validate_score(score: int, rating: str) -> bool:
        """Validate that numerical score matches BARS rating"""
        if rating not in BARSScoring.SCORE_RANGES:
            return False
        
        min_score, max_score = BARSScoring.SCORE_RANGES[rating]
        return min_score <= score <= max_score
    
    @staticmethod
    def get_rating_from_score(score: int) -> str:
        """Get BARS rating from numerical score"""
        if score >= 90:
            return 'EXCEPTIONAL'
        elif score >= 75:
            return 'STRONG'
        elif score >= 60:
            return 'SATISFACTORY'
        elif score >= 40:
            return 'DEVELOPING'
        elif score > 0:
            return 'UNSATISFACTORY'
        else:
            return 'N/A'
    
    @staticmethod
    def get_color_class(rating: str) -> str:
        """Get CSS color class for rating"""
        color_map = {
            'EXCEPTIONAL': 'success',
            'STRONG': 'info',
            'SATISFACTORY': 'primary',
            'DEVELOPING': 'warning',
            'UNSATISFACTORY': 'danger',
            'N/A': 'secondary'
        }
        return color_map.get(rating, 'secondary')


class InterviewScoreEnforcer:
    """Enforce scoring rules to prevent hallucination"""
    
    @staticmethod
    def enforce_technical_scoring_rules(
        result: Dict,
        answered_questions: int,
        total_questions: int
    ) -> Dict:
        """
        Enforce rules for technical/analytical scoring.
        
        Rules:
        - If only introduction (Q1) answered: Technical/Analytical = 0
        - If <50% answered: All scores = 0, overall = N/A
        """
        completion_rate = answered_questions / total_questions if total_questions > 0 else 0
        
        # Rule 1: Less than 50% answered
        if completion_rate < 0.5:
            result['overall_rating'] = 'N/A'
            result['overall_score'] = 0
            result['data_quality'] = 'INSUFFICIENT_DATA'
            result['recommendation'] = 'INCOMPLETE_DATA'
            
            # Zero out all dimension scores
            for dimension in ['communication', 'technical', 'analytical', 'role_fit', 'behavioral_presence']:
                result[f'{dimension}_score'] = 0
                result[f'{dimension}_rating'] = 'N/A'
        
        # Rule 2: Only introduction answered (1 question)
        elif answered_questions == 1:
            # Technical and analytical cannot be assessed from introduction
            result['technical_score'] = 0
            result['technical_rating'] = 'N/A'
            result['technical_reason'] = 'No technical questions answered'
            
            result['analytical_score'] = 0
            result['analytical_rating'] = 'N/A'
            result['analytical_reason'] = 'No analytical questions answered'
            
            result['behavioral_presence_score'] = 0
            result['behavioral_presence_rating'] = 'N/A'
            
            # Overall should reflect incomplete data
            result['overall_rating'] = 'N/A'
            result['overall_score'] = 0
            result['data_quality'] = 'INSUFFICIENT_DATA'
            result['recommendation'] = 'INCOMPLETE_DATA'
        
        # Rule 3: Validate technical score isn't inflated from introduction only
        elif answered_questions == 1 and result.get('technical_score', 0) > 0:
            result['technical_score'] = 0
            result['technical_rating'] = 'N/A'
            result['technical_reason'] = 'Technical questions not answered'
        
        return result
    
    @staticmethod
    def add_metadata(
        result: Dict,
        answered_questions: int,
        total_questions: int
    ) -> Dict:
        """Add completeness metadata to result"""
        completion_rate = answered_questions / total_questions if total_questions > 0 else 0
        
        result['questions_answered'] = answered_questions
        result['questions_total'] = total_questions
        result['completion_rate'] = round(completion_rate * 100, 1)
        
        return result


class InterviewQuestionClassifier:
    """Classify interview questions by type"""
    
    QUESTION_TYPES = {
        'introduction': 1,  # Q1 typically
        'technical': [2, 3, 4, 5],  # Q2-Q5 typically
        'behavioral': [2, 3, 4, 5]
    }
    
    @staticmethod
    def get_question_type(question_id: int) -> str:
        """Determine question type based on ID"""
        if question_id == 1:
            return 'introduction'
        else:
            return 'technical'
    
    @staticmethod
    def can_assess_technical(answered_question_ids: List[int]) -> bool:
        """Check if technical assessment is possible"""
        technical_questions = set(InterviewQuestionClassifier.QUESTION_TYPES['technical'])
        answered_set = set(answered_question_ids)
        
        # Need at least one technical question answered
        return len(technical_questions.intersection(answered_set)) > 0
    
    @staticmethod
    def get_dimension_requirements() -> Dict:
        """Get minimum question requirements for each dimension"""
        return {
            'communication': {
                'min_questions': 1,
                'question_types': ['introduction', 'technical']
            },
            'technical': {
                'min_questions': 1,
                'question_types': ['technical']
            },
            'analytical': {
                'min_questions': 1,
                'question_types': ['technical']
            },
            'role_fit': {
                'min_questions': 1,
                'question_types': ['introduction', 'technical']
            },
            'behavioral_presence': {
                'min_questions': 3,
                'question_types': ['introduction', 'technical']
            }
        }
