"""
FastAPI service for the Analysis Agent.
"""
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from .agent import AnalysisAgent

# Load environment variables
load_dotenv()

# Initialize the Analysis Agent
analysis_agent = AnalysisAgent()

# Create FastAPI app
app = FastAPI(title="Analysis Agent Service", 
              description="Financial data analysis agent")

# Define request and response models
class StockDataRequest(BaseModel):
    stock_data: Dict[str, Any]

class StocksDataRequest(BaseModel):
    stocks_data: Dict[str, Dict[str, Any]]

class EarningsDataRequest(BaseModel):
    earnings_data: Dict[str, Any]

class SectorDataRequest(BaseModel):
    sector_data: Dict[str, Any]

class SentimentDataRequest(BaseModel):
    sentiment_data: Dict[str, Any]

class AsiaDataRequest(BaseModel):
    exposure_data: Dict[str, Any]

class YieldDataRequest(BaseModel):
    yield_data: Dict[str, Any]

class MarketBriefRequest(BaseModel):
    asia_tech_data: Dict[str, Any]
    earnings_data: Dict[str, Any]
    market_sentiment: Dict[str, Any]
    yield_data: Dict[str, Any]

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
async def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "analysis_agent"}

@app.post("/stock", response_model=ApiResponse)
async def analyze_stock(request: StockDataRequest):
    """Analyze stock data."""
    result = analysis_agent.analyze_stock_data(request.stock_data)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/stocks", response_model=ApiResponse)
async def analyze_stocks(request: StocksDataRequest):
    """Analyze multiple stocks data."""
    result = analysis_agent.analyze_multiple_stocks(request.stocks_data)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/earnings", response_model=ApiResponse)
async def analyze_earnings(request: EarningsDataRequest):
    """Analyze earnings data."""
    result = analysis_agent.analyze_earnings_data(request.earnings_data)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/sector", response_model=ApiResponse)
async def analyze_sector(request: SectorDataRequest):
    """Analyze sector performance data."""
    result = analysis_agent.analyze_sector_performance(request.sector_data)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/sentiment", response_model=ApiResponse)
async def analyze_sentiment(request: SentimentDataRequest):
    """Analyze market sentiment data."""
    result = analysis_agent.analyze_market_sentiment(request.sentiment_data)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/asia-tech", response_model=ApiResponse)
async def analyze_asia_tech(request: AsiaDataRequest):
    """Analyze Asia tech exposure data."""
    result = analysis_agent.analyze_asia_tech_exposure(request.exposure_data)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/yields", response_model=ApiResponse)
async def analyze_yields(request: YieldDataRequest):
    """Analyze yield data."""
    result = analysis_agent.analyze_yield_data(request.yield_data)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/market-brief", response_model=ApiResponse)
async def generate_market_brief(request: MarketBriefRequest):
    """Generate a comprehensive market brief."""
    result = analysis_agent.analyze_market_brief(
        request.asia_tech_data,
        request.earnings_data,
        request.market_sentiment,
        request.yield_data
    )
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}
