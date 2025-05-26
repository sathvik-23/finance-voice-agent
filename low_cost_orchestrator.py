"""
Production-ready orchestrator for the Finance Voice Agent.
Uses OpenAI's Whisper for speech-to-text and TTS for text-to-speech.
Optimized for lower cost models.
"""
import os
import logging
import tempfile
import base64
from typing import Dict, List, Any, Optional, Union, BinaryIO
from fastapi import FastAPI, HTTPException, Body, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
from openai import OpenAI
from dotenv import load_dotenv
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create FastAPI app
app = FastAPI(title="Finance Voice Agent Orchestrator", 
              description="Production orchestrator for the finance assistant")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Financial data cache (in a production app, use Redis or another proper cache)
financial_data = {
    "portfolio": {
        "asia_tech_allocation": 22,
        "previous_allocation": 18,
        "total_aum": 1250000000,
        "currency": "USD"
    },
    "market_data": {
        "tsmc": {
            "ticker": "TSM",
            "earnings_surprise": 4.0,
            "direction": "positive"
        },
        "samsung": {
            "ticker": "005930.KS",
            "earnings_surprise": -2.0,
            "direction": "negative"
        },
        "market_sentiment": "neutral with caution",
        "yields": {
            "10y_treasury": 4.2,
            "trend": "rising"
        }
    }
}

@app.get("/")
async def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "production_orchestrator"}

@app.post("/query", response_model=ApiResponse)
async def process_query(request: QueryRequest):
    """Process a text query and generate response."""
    try:
        # Extract key entities from the query to determine what financial data to access
        query = request.query.lower()
        
        # Using a simpler model to understand the query (gpt-3.5-turbo is more economical)
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Changed from gpt-4o-mini to gpt-3.5-turbo
            messages=[
                {"role": "system", "content": """You are a financial assistant AI. 
                Analyze the query to understand what financial information is being requested.
                Respond with concise, professional financial insights."""},
                {"role": "user", "content": f"Query: {request.query}\n\nCurrent portfolio data: {json.dumps(financial_data)}"}
            ]
        )
        
        # Get the response text
        text_response = completion.choices[0].message.content
        
        # Generate voice response using a lower-cost TTS model
        voice_response = await generate_voice_response(text_response)
        
        return {
            "success": True,
            "data": {
                "text_response": text_response,
                "voice_response": voice_response
            }
        }
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return {"success": False, "error": str(e)}

@app.post("/market-brief", response_model=ApiResponse)
async def get_market_brief():
    """Get the morning market brief."""
    try:
        # Use GPT-3.5-Turbo to generate a market brief from our financial data
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Changed from gpt-4o-mini to gpt-3.5-turbo
            messages=[
                {"role": "system", "content": """You are a financial assistant AI.
                Generate a concise market brief focusing on Asia tech exposure and recent earnings surprises.
                Use the provided financial data to inform your response."""},
                {"role": "user", "content": f"Generate a market brief. Financial data: {json.dumps(financial_data)}"}
            ]
        )
        
        # Get the response text
        text_response = completion.choices[0].message.content
        
        # Generate voice response using a lower-cost TTS model
        voice_response = await generate_voice_response(text_response)
        
        return {
            "success": True,
            "data": {
                "text_response": text_response,
                "voice_response": voice_response
            }
        }
    except Exception as e:
        logger.error(f"Error generating market brief: {e}")
        return {"success": False, "error": str(e)}
@app.post("/transcribe", response_model=ApiResponse)
async def transcribe_audio(audio_data: str = Body(...)):
    """Transcribe audio to text using OpenAI's Whisper API."""
    try:
        # Decode base64 audio data
        if "," in audio_data:
            # It's a data URI
            _, encoded = audio_data.split(",", 1)
            audio_bytes = base64.b64decode(encoded)
        else:
            # It's already base64 encoded
            audio_bytes = base64.b64decode(audio_data)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
            temp_file.write(audio_bytes)
            temp_file.flush()
            
            # Use OpenAI's Whisper API for transcription
            with open(temp_file.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",  # whisper-1 is the most economical model
                    file=audio_file
                )
            
            logger.info(f"Transcription result: {transcript.text}")
            
            return {
                "success": True,
                "data": {
                    "text": transcript.text
                }
            }
    
    except Exception as e:
        logger.error(f"Error in transcription: {e}")
        return {"success": False, "error": str(e)}

@app.post("/upload-audio", response_model=ApiResponse)
async def upload_audio(file: UploadFile = File(...)):
    """Handle audio file uploads and transcribe them."""
    try:
        # Read the file
        audio_bytes = await file.read()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
            temp_file.write(audio_bytes)
            temp_file.flush()
            
            # Use OpenAI's Whisper API for transcription
            with open(temp_file.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",  # whisper-1 is the most economical model
                    file=audio_file
                )
            
            logger.info(f"Transcription result: {transcript.text}")
            
            # Process the query
            query_response = await process_query(QueryRequest(query=transcript.text))
            
            return {
                "success": True,
                "data": {
                    "transcription": transcript.text,
                    "response": query_response.get("data", {})
                }
            }
    
    except Exception as e:
        logger.error(f"Error processing audio upload: {e}")
        return {"success": False, "error": str(e)}

async def generate_voice_response(text: str, voice: str = "alloy") -> Dict[str, Any]:
    """Generate a voice response using OpenAI's TTS API."""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as temp_file:
            # Use OpenAI's TTS API with the most economical model
            response = client.audio.speech.create(
                model="tts-1",  # Changed from gpt-4o-mini-tts to tts-1
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
            
            return {
                "audio_data": audio_base64,
                "format": "mp3"
            }
    
    except Exception as e:
        logger.error(f"Error generating voice response: {e}")
        return None

# Fallback responses for offline mode or when API is unavailable
def get_fallback_response(query: str) -> Dict[str, Any]:
    """Get a fallback response when OpenAI API is unavailable."""
    if "risk exposure" in query.lower() and "asia tech" in query.lower():
        return {
            "text_response": "Today, your Asia tech allocation is 22% of AUM, up from 18% yesterday. TSMC beat estimates by 4%, Samsung missed by 2%. Regional sentiment is neutral with a cautionary tilt due to rising yields."
        }
    else:
        return {
            "text_response": f"I understand you asked about: {query}\n\nHowever, I'm operating in fallback mode and can only provide general information. In production, I would connect to real-time financial data sources."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
