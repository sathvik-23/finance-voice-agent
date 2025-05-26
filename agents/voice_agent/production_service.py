"""
FastAPI service for the Voice Agent.
"""
import os
import logging
import tempfile
import base64
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Body, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import our Voice Agent
from .production_agent import VoiceAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Voice Agent
voice_agent = VoiceAgent()

# Create FastAPI app
app = FastAPI(title="Voice Agent Service", 
              description="Service for speech-to-text and text-to-speech operations")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextToSpeechRequest(BaseModel):
    text: str
    voice: str = "alloy"

class ApiResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = None
    error: str = None

@app.get("/")
async def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "voice_agent"}

@app.post("/transcribe", response_model=ApiResponse)
async def transcribe_audio(audio_data: str = Body(...)):
    """
    Transcribe audio to text.
    
    Args:
        audio_data: Base64-encoded audio data
        
    Returns:
        Transcription result
    """
    try:
        # Process with the voice agent
        result = voice_agent.speech_to_text(audio_data)
        
        if result["success"]:
            return {"success": True, "data": {"text": result["text"]}}
        else:
            return {"success": False, "error": result["error"]}
    
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/speak", response_model=ApiResponse)
async def text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech.
    
    Args:
        request: Request with text and voice
        
    Returns:
        Audio data
    """
    try:
        # Process with the voice agent
        result = voice_agent.text_to_speech(request.text, request.voice)
        
        if result["success"]:
            return {"success": True, "data": {
                "audio_data": result["audio_data"],
                "format": result["format"]
            }}
        else:
            return {"success": False, "error": result["error"]}
    
    except Exception as e:
        logger.error(f"Error converting text to speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-audio", response_model=ApiResponse)
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload and transcribe audio.
    
    Args:
        file: Audio file
        
    Returns:
        Transcription result
    """
    try:
        # Read the file
        audio_bytes = await file.read()
        
        # Process with the voice agent
        result = voice_agent.speech_to_text(audio_bytes)
        
        if result["success"]:
            return {"success": True, "data": {"text": result["text"]}}
        else:
            return {"success": False, "error": result["error"]}
    
    except Exception as e:
        logger.error(f"Error processing audio upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
