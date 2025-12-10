"""
YouTube Transcriber using Whisper (Open Source Speech Recognition).

This method uses OpenAI's Whisper model to transcribe audio directly from YouTube videos.
It's efficient, free, and doesn't require API keys, pre-generated captions, or ffmpeg.
Works for all videos regardless of caption availability.

NOTE: This script uses open-source tools (yt-dlp + Whisper) without youtube-transcript-api
or ffmpeg. Uses PyAV for pure Python audio extraction and conversion.
"""

import os
import logging
import re
import sys
import subprocess
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class YouTubeTranscriber:
    """Transcribe YouTube videos using Whisper (open-source speech recognition)."""
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize the transcriber.
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large).
                       Larger models are more accurate but slower.
        """
        self.model_name = model_name
        self._ensure_dependencies()
        logger.info(f"YouTube Transcriber initialized using Whisper ({model_name} model).")
    
    def _ensure_dependencies(self):
        """Install required packages if not already installed."""
        packages = ['openai-whisper', 'av', 'yt-dlp', 'scipy', 'numpy']
        
        for package in packages:
            try:
                __import__(package.replace('-', '_'))
                logger.debug(f"✓ {package} is already installed")
            except ImportError:
                logger.info(f"Installing {package}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])
                logger.info(f"✓ {package} installed successfully")
    
    def extract_video_id(self, video_url: str) -> str:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract video ID from URL: {video_url}")
    
    def _download_audio(self, video_url: str, output_path: str = "downloads") -> str:
        """
        Download audio from YouTube video using yt-dlp WITHOUT postprocessing.
        
        Args:
            video_url: YouTube video URL
            output_path: Directory to save audio file
            
        Returns:
            Path to the downloaded audio file
        """
        os.makedirs(output_path, exist_ok=True)
        
        logger.info(f"Downloading audio from: {video_url}")
        
        try:
            video_id = self.extract_video_id(video_url)
            output_template = os.path.join(output_path, "%(title)s.%(ext)s")
            
            # Download audio stream directly without postprocessing
            cmd = [
                'yt-dlp',
                '--extractor-args', 'youtube:player_client=web',
                '-f', 'bestaudio',
                '-o', output_template,
                '--no-post-overwrites',
                video_url
            ]
            
            logger.info("Downloading audio stream with yt-dlp...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.warning(f"Attempt with player_client=web failed, trying default...")
                cmd = [
                    'yt-dlp',
                    '-f', 'bestaudio',
                    '-o', output_template,
                    '--no-post-overwrites',
                    video_url
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"yt-dlp error: {result.stderr}")
            
            # Find the downloaded file
            audio_files = list(Path(output_path).glob("*"))
            audio_files = [f for f in audio_files if f.is_file() and f.suffix in ['.m4a', '.webm', '.opus', '.mp3', '.wav', '.mkv']]
            
            if audio_files:
                audio_file = str(audio_files[0])
                logger.info(f"✓ Audio downloaded: {audio_file}")
                return audio_file
            else:
                raise FileNotFoundError("No audio file found after download")
        
        except subprocess.TimeoutExpired:
            logger.error("Download timed out")
            raise Exception("Download timed out - video may be too long or connection is slow")
        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            raise Exception(f"Failed to download audio: {str(e)}")
    
    def _load_audio_as_numpy(self, input_file: str) -> tuple:
        """
        Load audio file directly as numpy array using PyAV.
        This avoids Whisper trying to use ffmpeg.
        
        Args:
            input_file: Path to input audio file
            
        Returns:
            Tuple of (audio_array, sample_rate)
        """
        try:
            import av
            import numpy as np
            
            logger.info(f"Loading audio file as numpy array using PyAV...")
            
            # Open the media file with PyAV
            container = av.open(input_file)
            
            # Get audio stream
            audio_stream = None
            for stream in container.streams:
                if stream.type == 'audio':
                    audio_stream = stream
                    break
            
            if audio_stream is None:
                raise Exception("No audio stream found in the file")
            
            # Extract audio samples
            audio_data = []
            sample_rate = audio_stream.sample_rate
            
            logger.info(f"Extracting audio frames (sample rate: {sample_rate} Hz)...")
            
            for frame in container.decode(audio_stream):
                # Convert frame to numpy array
                audio_data.append(frame.to_ndarray())
            
            logger.info(f"Extracted {len(audio_data)} audio frames")
            
            # Concatenate all audio frames
            if audio_data:
                audio_array = np.concatenate(audio_data, axis=1)
                
                logger.info(f"Audio shape before mono conversion: {audio_array.shape}")
                
                # Convert to mono if stereo
                if audio_array.shape[0] > 1:
                    audio_array = np.mean(audio_array, axis=0)
                else:
                    audio_array = audio_array[0]
                
                logger.info(f"Audio shape after mono conversion: {audio_array.shape}")
                logger.info(f"Audio dtype: {audio_array.dtype}, min: {audio_array.min()}, max: {audio_array.max()}")
                
                # Normalize to float32 in range [-1, 1] for Whisper
                if audio_array.dtype == np.int16:
                    # Convert from int16 to float32
                    audio_array = audio_array.astype(np.float32) / 32768.0
                elif audio_array.dtype == np.int32:
                    audio_array = audio_array.astype(np.float32) / 2147483648.0
                elif audio_array.dtype not in [np.float32, np.float64]:
                    audio_array = audio_array.astype(np.float32)
                
                # Ensure it's float32
                audio_array = audio_array.astype(np.float32)
                
                # Clip to [-1, 1] range
                audio_array = np.clip(audio_array, -1.0, 1.0)
                
                logger.info(f"Audio after normalization - dtype: {audio_array.dtype}, min: {audio_array.min()}, max: {audio_array.max()}")
                
                return audio_array, sample_rate
            else:
                raise Exception("No audio data extracted from file")
        
        except Exception as e:
            logger.error(f"Error loading audio: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise Exception(f"Failed to load audio: {str(e)}")
    
    def _transcribe_audio(self, audio_array, sample_rate: int) -> dict:
        """
        Transcribe audio using Whisper.
        
        Args:
            audio_array: numpy array of audio data (float32, mono, [-1, 1] range)
            sample_rate: Sample rate of the audio
            
        Returns:
            dict with transcription result
        """
        logger.info(f"Transcribing audio using Whisper ({self.model_name} model)...")
        logger.info("This may take a few minutes depending on video length and model size...")
        
        try:
            import whisper
            import numpy as np
            
            # Resample to 16kHz if needed (Whisper expects 16kHz)
            if sample_rate != 16000:
                logger.info(f"Resampling audio from {sample_rate} Hz to 16000 Hz...")
                import scipy.signal
                num_samples = int(len(audio_array) * 16000 / sample_rate)
                audio_array = scipy.signal.resample(audio_array, num_samples)
                sample_rate = 16000
            
            logger.info(f"Audio shape for Whisper: {audio_array.shape}, dtype: {audio_array.dtype}")
            
            # Load model and transcribe
            logger.info(f"Loading Whisper {self.model_name} model...")
            model = whisper.load_model(self.model_name)
            
            logger.info(f"Starting transcription...")
            # Pass audio as numpy array directly to avoid ffmpeg
            result = model.transcribe(audio_array, language=None)
            
            logger.info("✓ Transcription completed!")
            return result
        
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise Exception(f"Transcription failed: {str(e)}")
    
    def transcribe(self, video_url: str, language: str = None) -> dict:
        """
        Transcribe a YouTube video using Whisper.
        
        Args:
            video_url: YouTube video URL
            language: Optional language code (e.g., 'en', 'id'). 
                     Whisper auto-detects if not specified.
            
        Returns:
            dict with 'text', 'segments', and 'language' containing transcription
        """
        try:
            video_id = self.extract_video_id(video_url)
            logger.info(f"Extracted video ID: {video_id}")
            
            # Create temporary directory for this video
            temp_dir = os.path.join("downloads", video_id)
            
            # Download audio
            audio_file = self._download_audio(video_url, output_path=temp_dir)
            
            # Load audio as numpy array
            audio_array, sample_rate = self._load_audio_as_numpy(audio_file)
            
            # Transcribe
            result = self._transcribe_audio(audio_array, sample_rate)
            
            # Extract segments
            segments = result.get('segments', [])
            full_text = result.get('text', '')
            
            # Detect language from result
            detected_lang = result.get('language', language or 'en')
            
            logger.info(f"Transcript fetched successfully ({len(segments)} segments). Language: {detected_lang}")
            
            return {
                'text': full_text,
                'segments': segments,
                'language': detected_lang
            }
            
        except ValueError as e:
            logger.error(f"Invalid URL: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during transcription: {e}")
            raise Exception(f"Transcription failed: {str(e)}")
    
    def transcribe_to_chunks(self, video_url: str, chunk_duration: int = 60) -> list:
        """
        Transcribe video and organize into time-based chunks.
        
        Args:
            video_url: YouTube video URL
            chunk_duration: Duration of each chunk in seconds
            
        Returns:
            List of dictionaries with 'text', 'start', and 'end' times
        """
        result = self.transcribe(video_url)
        segments = result['segments']
        
        chunks = []
        current_chunk = {
            'text': '',
            'start': 0,
            'end': 0
        }
        
        if segments:
            current_chunk['start'] = segments[0]['start']
        
        for segment in segments:
            # Check if adding this segment would exceed the chunk duration
            if segment['start'] - current_chunk['start'] >= chunk_duration:
                if current_chunk['text']:
                    current_chunk['text'] = current_chunk['text'].strip()
                    chunks.append(current_chunk)
                
                current_chunk = {
                    'text': segment['text'].strip() + ' ',
                    'start': segment['start'],
                    'end': segment['start'] + segment.get('duration', 0)
                }
            else:
                current_chunk['text'] += segment['text'].strip() + ' '
                current_chunk['end'] = segment['start'] + segment.get('duration', 0)
        
        if current_chunk['text']:
            current_chunk['text'] = current_chunk['text'].strip()
            chunks.append(current_chunk)
        
        logger.info(f"Created {len(chunks)} time-based chunks")
        return chunks


if __name__ == "__main__":
    # YouTube URL to transcribe
    youtube_url = "https://www.youtube.com/watch?v=X4EcUcoo0r4"
    
    # Model size: tiny, base, small, medium, large
    # Larger models are more accurate but slower
    model_size = "base"
    
    # Initialize transcriber
    transcriber = YouTubeTranscriber(model_name=model_size)
    
    # Transcribe the video
    result = transcriber.transcribe(youtube_url)
    
    # Display results
    print("\n" + "=" * 60)
    print("✅ Transcription Complete!")
    print("=" * 60)
    print(f"\nLanguage: {result['language']}")
    print(f"Segments: {len(result['segments'])}")
    print(f"\nTranscription Preview (first 500 characters):")
    print("-" * 60)
    text_preview = result['text'][:500] + "..." if len(result['text']) > 500 else result['text']
    print(text_preview)
    print("-" * 60)
    
    # Save full transcription
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "transcription.txt"), 'w', encoding='utf-8') as f:
        f.write(result['text'])
    
    print(f"\n💾 Full transcription saved to: {os.path.join(output_dir, 'transcription.txt')}")