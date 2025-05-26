"""
FastAPI service for the Language Agent.
"""
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from .agent import LanguageAgent

# Load environment variables
load_dotenv()

# Initialize the Language Agent
language_agent = LanguageAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model_name=os.getenv("MODEL_NAME", "gpt-4")
)

# Create FastAPI app
app = FastAPI(title="Language Agent Service", 
              description="Natural language generation and understanding agent")

# Define request and response models
class MarketBriefRequest(BaseModel):
    asia_tech: Dict[str, Any]
    earnings: Dict[str, Any]
    sentiment: Dict[str, Any]
    yields: Dict[str, Any]

class QueryRequest(BaseModel):
    query: str

class EarningsSummaryRequest(BaseModel):
    earnings_data: Dict[str, Any]

class ResponseRequest(BaseModel):
    prompt: str
    system_message: str = ""

class ContextRequest(BaseModel):
    query: str
    context: List[Dict[str, Any]]

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
async def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "language_agent"}

@app.post("/market-brief", response_model=ApiResponse)
async def generate_market_brief(request: MarketBriefRequest):
    """Generate a market brief."""
    result = language_agent.generate_market_brief(
        request.asia_tech,
        request.earnings,
        request.sentiment,
        request.yields
    )
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/understand-query", response_model=ApiResponse)
async def understand_query(request: QueryRequest):
    """Understand a user query."""
    result = language_agent.understand_query(request.query)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/earnings-summary", response_model=ApiResponse)
async def generate_earnings_summary(request: EarningsSummaryRequest):
    """Generate an earnings summary."""
    result = language_agent.generate_earnings_summary(request.earnings_data)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/generate-response", response_model=ApiResponse)
async def generate_response(request: ResponseRequest):
    """Generate a response using the LLM."""
    result = language_agent.generate_response(request.prompt, request.system_message)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/synthesize-context", response_model=ApiResponse)
async def synthesize_from_context(request: ContextRequest):
    """Synthesize a response from retrieved context."""
    result = language_agent.synthesize_from_retrieved_context(request.query, request.context)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}
