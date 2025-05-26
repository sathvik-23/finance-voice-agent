"""
FastAPI service for the Orchestrator.
"""
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from .orchestrator import Orchestrator

# Load environment variables
load_dotenv()

# Initialize Orchestrator
orchestrator = Orchestrator()

# Create FastAPI app
app = FastAPI(title="Finance Voice Agent Orchestrator", 
              description="Orchestrator for the multi-agent finance assistant")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request and response models
class TextQueryRequest(BaseModel):
    query: str

class VoiceQueryRequest(BaseModel):
    audio_data: str

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
async def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "orchestrator"}

@app.post("/query", response_model=ApiResponse)
async def process_text_query(request: TextQueryRequest):
    """Process a text query."""
    try:
        result = await orchestrator.process_market_brief_query(request.query)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/voice-query", response_model=ApiResponse)
async def process_voice_query(request: VoiceQueryRequest):
    """Process a voice query."""
    try:
        result = await orchestrator.process_voice_query(request.audio_data)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice query: {str(e)}")

@app.post("/market-brief", response_model=ApiResponse)
async def get_market_brief():
    """Get the morning market brief."""
    try:
        query = "What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"
        result = await orchestrator.process_market_brief_query(query)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating market brief: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await orchestrator.close()
