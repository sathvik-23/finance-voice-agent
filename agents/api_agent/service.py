"""
FastAPI service for the API Agent.
"""
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from .agent import APIAgent

# Load environment variables
load_dotenv()

# Initialize the API Agent
api_agent = APIAgent(alpha_vantage_key=os.getenv("ALPHAVANTAGE_API_KEY"))

# Create FastAPI app
app = FastAPI(title="API Agent Service", 
              description="Financial data API agent for fetching market data")

# Define request and response models
class StockRequest(BaseModel):
    symbol: str
    period: str = "1d"

class MultipleStockRequest(BaseModel):
    symbols: List[str]
    period: str = "1d"

class EarningsRequest(BaseModel):
    symbol: str

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
async def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "api_agent"}

@app.post("/stock", response_model=ApiResponse)
async def get_stock_data(request: StockRequest):
    """Get stock data for a single symbol."""
    result = api_agent.get_stock_data(request.symbol, request.period)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/stocks", response_model=ApiResponse)
async def get_multiple_stocks(request: MultipleStockRequest):
    """Get stock data for multiple symbols."""
    results = api_agent.get_multiple_stocks(request.symbols, request.period)
    return {"success": True, "data": results}

@app.post("/earnings", response_model=ApiResponse)
async def get_earnings_data(request: EarningsRequest):
    """Get earnings data for a stock."""
    result = api_agent.get_earnings_data(request.symbol)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.get("/sector-performance", response_model=ApiResponse)
async def get_sector_performance():
    """Get sector performance data."""
    result = api_agent.get_sector_performance()
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.get("/market-sentiment", response_model=ApiResponse)
async def get_market_sentiment():
    """Get overall market sentiment."""
    result = api_agent.get_market_sentiment()
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.get("/asia-tech-exposure", response_model=ApiResponse)
async def get_asia_tech_exposure():
    """Get Asia tech exposure data."""
    result = api_agent.get_asia_tech_exposure()
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.get("/yield-data", response_model=ApiResponse)
async def get_yield_data():
    """Get current yield data."""
    result = api_agent.get_yield_data()
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}
