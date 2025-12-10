"""
Speech Recognition Tool Module
Handles browser-based Web Speech API integration for real-time transcription.
"""

class SpeechRecognitionConfig:
    """Configuration for Web Speech API"""
    
    # Supported languages for speech recognition
    SUPPORTED_LANGUAGES = {
        'en-US': 'English (United States)',
        'en-GB': 'English (United Kingdom)',
        'es-ES': 'Spanish (Spain)',
        'fr-FR': 'French (France)',
        'de-DE': 'German (Germany)',
        'it-IT': 'Italian (Italy)',
        'pt-BR': 'Portuguese (Brazil)',
        'ru-RU': 'Russian',
        'ja-JP': 'Japanese',
        'ko-KR': 'Korean',
        'zh-CN': 'Chinese (Mandarin, Simplified)',
        'ar-SA': 'Arabic (Saudi Arabia)',
        'hi-IN': 'Hindi (India)',
        'th-TH': 'Thai (Thailand)',
        'vi-VN': 'Vietnamese'
    }
    
    # Default configuration
    DEFAULT_LANGUAGE = 'en-US'
    CONTINUOUS_MODE = True
    INTERIM_RESULTS = True
    MAX_ALTERNATIVES = 1
    
    # Error types
    ERROR_TYPES = {
        'no-speech': 'No speech was detected',
        'audio-capture': 'Audio capture failed',
        'not-allowed': 'Microphone permission denied',
        'network': 'Network error occurred',
        'aborted': 'Speech recognition aborted',
        'service-not-allowed': 'Speech recognition service not allowed'
    }
    
    @staticmethod
    def get_language_list():
        """Return list of supported languages"""
        return [
            {'code': code, 'name': name} 
            for code, name in SpeechRecognitionConfig.SUPPORTED_LANGUAGES.items()
        ]
    
    @staticmethod
    def validate_language(language_code):
        """Validate if language code is supported"""
        return language_code in SpeechRecognitionConfig.SUPPORTED_LANGUAGES
    
    @staticmethod
    def get_error_message(error_type):
        """Get user-friendly error message for error type"""
        return SpeechRecognitionConfig.ERROR_TYPES.get(
            error_type, 
            f'Unknown error: {error_type}'
        )


class TranscriptionValidator:
    """Validate transcription quality and completeness"""
    
    MIN_TRANSCRIPT_LENGTH = 10  # Minimum characters for valid transcript
    
    @staticmethod
    def is_valid_transcript(transcript):
        """Check if transcript is valid and not empty"""
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
        if len(transcript) < TranscriptionValidator.MIN_TRANSCRIPT_LENGTH:
            return False
        
        return True
    
    @staticmethod
    def calculate_transcript_quality(transcript, duration_seconds):
        """
        Calculate quality score for transcript.
        
        Args:
            transcript: The transcribed text
            duration_seconds: Duration of the recording
            
        Returns:
            dict with quality metrics
        """
        if not TranscriptionValidator.is_valid_transcript(transcript):
            return {
                'quality': 'invalid',
                'score': 0,
                'words_per_minute': 0,
                'character_count': 0
            }
        
        word_count = len(transcript.split())
        char_count = len(transcript)
        
        # Calculate words per minute
        wpm = (word_count / duration_seconds * 60) if duration_seconds > 0 else 0
        
        # Determine quality based on WPM
        # Normal speech: 120-150 WPM
        # Fast speech: 150-180 WPM
        # Slow speech: 80-120 WPM
        if 80 <= wpm <= 180:
            quality = 'good'
            score = 90
        elif 60 <= wpm < 80 or 180 < wpm <= 200:
            quality = 'acceptable'
            score = 70
        elif wpm < 60 or wpm > 200:
            quality = 'questionable'
            score = 50
        else:
            quality = 'unknown'
            score = 0
        
        return {
            'quality': quality,
            'score': score,
            'words_per_minute': round(wpm, 1),
            'word_count': word_count,
            'character_count': char_count
        }
    
    @staticmethod
    def get_empty_transcript_message():
        """Return standard message for empty transcripts"""
        return 'No transcription available'
