"""
FastAPI service for the Retriever Agent.
"""
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from .agent import RetrieverAgent

# Load environment variables
load_dotenv()

# Initialize the Retriever Agent
retriever_agent = RetrieverAgent()

# Create FastAPI app
app = FastAPI(title="Retriever Agent Service", 
              description="Financial data retrieval agent")

# Define request and response models
class DocumentRequest(BaseModel):
    text: str
    metadata: Dict[str, Any]
    chunk_size: int = 512
    chunk_overlap: int = 128

class SearchRequest(BaseModel):
    query: str
    k: int = 5
    filters: Optional[Dict[str, Any]] = None

class CompanySearchRequest(BaseModel):
    ticker: str
    query: str
    k: int = 5

class FinancialDataRequest(BaseModel):
    data: Dict[str, Any]
    source: str

class FilingRequest(BaseModel):
    filing_data: Dict[str, Any]
    content: str

class NewsArticleRequest(BaseModel):
    article: Dict[str, Any]

class FinancialContextRequest(BaseModel):
    query: str
    tickers: Optional[List[str]] = None
    k: int = 5

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
async def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "retriever_agent"}

@app.post("/document", response_model=ApiResponse)
async def add_document(request: DocumentRequest):
    """Add a document to the index."""
    result = retriever_agent.add_document(
        request.text, request.metadata, request.chunk_size, request.chunk_overlap
    )
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/search", response_model=ApiResponse)
async def search(request: SearchRequest):
    """Search for relevant documents."""
    result = retriever_agent.search(request.query, request.k, request.filters)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.get("/document/{document_id}", response_model=ApiResponse)
async def get_document(document_id: int):
    """Get a document by ID."""
    result = retriever_agent.get_document(document_id)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/clear", response_model=ApiResponse)
async def clear_index():
    """Clear the index."""
    result = retriever_agent.clear_index()
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.get("/stats", response_model=ApiResponse)
async def get_stats():
    """Get index statistics."""
    result = retriever_agent.get_stats()
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/company/search", response_model=ApiResponse)
async def search_by_company(request: CompanySearchRequest):
    """Search for documents about a specific company."""
    result = retriever_agent.search_by_company(request.ticker, request.query, request.k)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/financial-data", response_model=ApiResponse)
async def add_financial_data(request: FinancialDataRequest):
    """Add financial data to the index."""
    result = retriever_agent.add_financial_data(request.data, request.source)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/filing", response_model=ApiResponse)
async def add_filing(request: FilingRequest):
    """Add an SEC filing to the index."""
    result = retriever_agent.add_filing(request.filing_data, request.content)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/news-article", response_model=ApiResponse)
async def add_news_article(request: NewsArticleRequest):
    """Add a news article to the index."""
    result = retriever_agent.add_news_article(request.article)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}

@app.post("/financial-context", response_model=ApiResponse)
async def query_financial_context(request: FinancialContextRequest):
    """Get financial context for a query."""
    result = retriever_agent.query_financial_context(request.query, request.tickers, request.k)
    if result["success"]:
        return {"success": True, "data": result}
    else:
        return {"success": False, "error": result.get("error", "Unknown error")}
