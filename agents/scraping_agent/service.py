"""
FastAPI service for the Scraping Agent.
"""
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from .agent import ScrapingAgent

# Load environment variables
load_dotenv()

# Initialize the Scraping Agent
scraping_agent = ScrapingAgent()

# Create FastAPI app
app = FastAPI(title="Scraping Agent Service", 
              description="Financial filings and news scraping agent")

# Define request and response models
class SecFilingsRequest(BaseModel):
    ticker: str
    filing_type: str = "10-K,10-Q,8-K"
    limit: int = 5

class FilingContentRequest(BaseModel):
    url: str

class NewsSearchRequest(BaseModel):
    query: str
    limit: int = 5

class EarningsCalendarRequest(BaseModel):
    days: int = 7

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
async def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "scraping_agent"}

@app.post("/sec-filings", response_model=ApiResponse)
async def search_sec_filings(request: SecFilingsRequest):
    """Search SEC filings for a company."""
    result = scraping_agent.search_sec_filings(
        request.ticker, request.filing_type, request.limit
    )
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/filing-content", response_model=ApiResponse)
async def get_filing_content(request: FilingContentRequest):
    """Get content from an SEC filing URL."""
    result = scraping_agent.scrape_filing_content(request.url)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/news", response_model=ApiResponse)
async def search_financial_news(request: NewsSearchRequest):
    """Search for financial news."""
    result = scraping_agent.search_financial_news(request.query, request.limit)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/earnings-calendar", response_model=ApiResponse)
async def get_earnings_calendar(request: EarningsCalendarRequest):
    """Get upcoming earnings calendar."""
    result = scraping_agent.scrape_earnings_calendar(request.days)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.get("/asia-tech-news", response_model=ApiResponse)
async def get_asia_tech_news():
    """Get news about Asian tech companies."""
    result = scraping_agent.get_asia_tech_news()
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}
