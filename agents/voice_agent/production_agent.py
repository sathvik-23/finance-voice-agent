"""
Voice Agent implementation using OpenAI's Whisper and TTS APIs.
"""
import os
import logging
import tempfile
import base64
from typing import Dict, Any, Union, BinaryIO
import openai
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceAgent:
    """
    Agent for speech-to-text and text-to-speech operations using OpenAI APIs.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Voice Agent.
        
        Args:
            api_key: OpenAI API key
        """
        # Get API key from environment if not provided
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info("Voice Agent initialized")
    
    def speech_to_text(self, audio_data: Union[bytes, BinaryIO, str]) -> Dict[str, Any]:
        """
        Convert speech to text using OpenAI's Whisper API.
        
        Args:
            audio_data: Audio data in bytes, file-like object, or base64 string
            
        Returns:
            Dictionary with transcription result
        """
        try:
            # Handle different input types
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                if isinstance(audio_data, bytes):
                    temp_file.write(audio_data)
                    temp_file.flush()
                elif hasattr(audio_data, 'read'):
                    # It's a file-like object
                    temp_file.write(audio_data.read())
                    temp_file.flush()
                elif isinstance(audio_data, str) and audio_data.startswith("data:audio"):
                    # It's a base64 data URI
                    _, encoded = audio_data.split(",", 1)
                    temp_file.write(base64.b64decode(encoded))
                    temp_file.flush()
                elif isinstance(audio_data, str):
                    # Assume it's already base64 encoded
                    temp_file.write(base64.b64decode(audio_data))
                    temp_file.flush()
                else:
                    return {"success": False, "error": "Unsupported audio data format"}
                
                # Use OpenAI's Whisper API for transcription
                with open(temp_file.name, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                
                logger.info(f"Transcription successful: {transcript.text}")
                
                return {
                    "success": True,
                    "text": transcript.text,
                    "engine": "whisper"
                }
        
        except Exception as e:
            logger.error(f"Error in speech to text conversion: {e}")
            return {"success": False, "error": f"Speech recognition failed: {str(e)}"}
    
    def text_to_speech(self, text: str, voice: str = "alloy") -> Dict[str, Any]:
        """
        Convert text to speech using OpenAI's TTS API.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            
        Returns:
            Dictionary with audio data
        """
        try:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as temp_file:
                # Use OpenAI's TTS API
                response = self.client.audio.speech.create(
                    model="gpt-4o-mini-tts",  # Using the latest model
                    voice=voice,
                    input=text
                )
                
                # Save to temporary file
                response.stream_to_file(temp_file.name)
                
                # Read the file back
                with open(temp_file.name, "rb") as audio_file:
                    audio_data = audio_file.read()
                
                # Convert to base64 for web playback
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                
                logger.info(f"Text-to-speech successful, generated {len(audio_data)} bytes")
                
                return {
                    "success": True,
                    "audio_data": audio_base64,
                    "format": "mp3",
                    "engine": "openai"
                }
        
        except Exception as e:
            logger.error(f"Error in text to speech conversion: {e}")
            return {"success": False, "error": f"Text-to-speech failed: {str(e)}"}
    
    def process_voice_query(self, audio_data: Union[bytes, BinaryIO, str]) -> Dict[str, Any]:
        """
        Process a voice query by converting speech to text.
        
        Args:
            audio_data: Audio data
            
        Returns:
            Dictionary with query text
        """
        # Convert speech to text
        stt_result = self.speech_to_text(audio_data)
        
        if stt_result["success"]:
            return {
                "success": True,
                "query": stt_result["text"],
                "engine": stt_result["engine"]
            }
        else:
            return stt_result
    
    def generate_voice_response(self, text: str, voice: str = "alloy") -> Dict[str, Any]:
        """
        Generate a voice response from text.
        
        Args:
            text: Response text
            voice: Voice to use
            
        Returns:
            Dictionary with audio data
        """
        # Convert text to speech
        tts_result = self.text_to_speech(text, voice)
        
        if tts_result["success"]:
            return {
                "success": True,
                "response_text": text,
                "audio_data": tts_result["audio_data"],
                "format": tts_result["format"],
                "engine": tts_result["engine"]
            }
        else:
            return tts_result
