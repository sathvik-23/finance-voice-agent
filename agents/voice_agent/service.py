"""
FastAPI service for the Voice Agent.
"""
import os
import base64
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from .agent import VoiceAgent

# Load environment variables
load_dotenv()

# Initialize the Voice Agent
voice_agent = VoiceAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Create FastAPI app
app = FastAPI(title="Voice Agent Service", 
              description="Speech-to-text and text-to-speech conversion agent")

# Define request and response models
class TextToSpeechRequest(BaseModel):
    text: str
    voice: str = "default"

class Base64AudioRequest(BaseModel):
    audio_data: str

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
async def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "voice_agent"}

@app.post("/speech-to-text", response_model=ApiResponse)
async def speech_to_text_file(file: UploadFile = File(...)):
    """Convert speech to text from uploaded file."""
    try:
        audio_data = await file.read()
        result = voice_agent.speech_to_text(audio_data)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error processing audio: {str(e)}"}
        )

@app.post("/speech-to-text/base64", response_model=ApiResponse)
async def speech_to_text_base64(request: Base64AudioRequest):
    """Convert speech to text from base64 encoded audio."""
    try:
        result = voice_agent.speech_to_text(request.audio_data)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error processing audio: {str(e)}"}
        )

@app.post("/text-to-speech", response_model=ApiResponse)
async def text_to_speech(request: TextToSpeechRequest):
    """Convert text to speech."""
    try:
        result = voice_agent.text_to_speech(request.text, request.voice)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error generating speech: {str(e)}"}
        )

@app.post("/process-query", response_model=ApiResponse)
async def process_voice_query(file: UploadFile = File(...)):
    """Process a voice query from uploaded file."""
    try:
        audio_data = await file.read()
        result = voice_agent.process_voice_query(audio_data)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error processing query: {str(e)}"}
        )

@app.post("/process-query/base64", response_model=ApiResponse)
async def process_voice_query_base64(request: Base64AudioRequest):
    """Process a voice query from base64 encoded audio."""
    try:
        result = voice_agent.process_voice_query(request.audio_data)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error processing query: {str(e)}"}
        )

@app.post("/generate-response", response_model=ApiResponse)
async def generate_voice_response(request: TextToSpeechRequest):
    """Generate a voice response from text."""
    try:
        result = voice_agent.generate_voice_response(request.text, request.voice)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error generating response: {str(e)}"}
        )
