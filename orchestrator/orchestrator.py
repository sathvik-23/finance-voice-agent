"""
Main Orchestrator for the Finance Voice Agent.
"""
import os
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
import httpx
from dotenv import load_dotenv
import agno
from agno import TaskGraph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Orchestrator:
    """Main orchestrator for coordinating all agents."""
    
    def __init__(self):
        """Initialize the Orchestrator."""
        # Service URLs (default to localhost for development)
        self.api_agent_url = os.getenv("API_AGENT_URL", "http://localhost:8080")
        self.scraping_agent_url = os.getenv("SCRAPING_AGENT_URL", "http://localhost:8081")
        self.retriever_agent_url = os.getenv("RETRIEVER_AGENT_URL", "http://localhost:8082")
        self.analysis_agent_url = os.getenv("ANALYSIS_AGENT_URL", "http://localhost:8083")
        self.language_agent_url = os.getenv("LANGUAGE_AGENT_URL", "http://localhost:8084")
        self.voice_agent_url = os.getenv("VOICE_AGENT_URL", "http://localhost:8085")
        
        # HTTP client for making requests to agent services
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Initialize Agno TaskGraph for orchestration
        self.task_graph = TaskGraph()
        
        # Set up Agno tasks
        self.setup_tasks()
    
    def setup_tasks(self):
        """Set up Agno tasks for orchestration."""
        
        # Voice input processing task
        @self.task_graph.add_task
        async def process_voice_input(audio_data: str) -> Dict[str, Any]:
            """Process voice input to text."""
            response = await self.client.post(
                f"{self.voice_agent_url}/speech-to-text/base64",
                json={"audio_data": audio_data}
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]
            else:
                raise Exception(result.get("error", "Voice processing failed"))
        
        # Query understanding task
        @self.task_graph.add_task
        async def understand_query(query: str) -> Dict[str, Any]:
            """Understand the user query."""
            response = await self.client.post(
                f"{self.language_agent_url}/understand-query",
                json={"query": query}
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]["understanding"]
            else:
                raise Exception(result.get("error", "Query understanding failed"))
        
        # Get Asia tech exposure task
        @self.task_graph.add_task
        async def get_asia_tech_exposure() -> Dict[str, Any]:
            """Get Asia tech exposure data from API agent."""
            response = await self.client.get(
                f"{self.api_agent_url}/asia-tech-exposure"
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]
            else:
                raise Exception(result.get("error", "Failed to get Asia tech data"))
        
        # Get earnings data task
        @self.task_graph.add_task
        async def get_earnings_data(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
            """Get earnings data for specific tickers."""
            results = {}
            
            for ticker in tickers:
                response = await self.client.post(
                    f"{self.api_agent_url}/earnings",
                    json={"symbol": ticker}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        results[ticker] = result["data"]
            
            return results
        
        # Get market sentiment task
        @self.task_graph.add_task
        async def get_market_sentiment() -> Dict[str, Any]:
            """Get overall market sentiment."""
            response = await self.client.get(
                f"{self.api_agent_url}/market-sentiment"
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]
            else:
                raise Exception(result.get("error", "Failed to get market sentiment"))
        
        # Get yield data task
        @self.task_graph.add_task
        async def get_yield_data() -> Dict[str, Any]:
            """Get yield curve data."""
            response = await self.client.get(
                f"{self.api_agent_url}/yield-data"
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]
            else:
                raise Exception(result.get("error", "Failed to get yield data"))
        
        # Analyze Asia tech data task
        @self.task_graph.add_task
        async def analyze_asia_tech(exposure_data: Dict[str, Any]) -> Dict[str, Any]:
            """Analyze Asia tech exposure data."""
            response = await self.client.post(
                f"{self.analysis_agent_url}/asia-tech",
                json={"exposure_data": exposure_data}
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]["analysis"]
            else:
                raise Exception(result.get("error", "Failed to analyze Asia tech data"))
        
        # Analyze earnings data task
        @self.task_graph.add_task
        async def analyze_earnings(earnings_data: Dict[str, Any]) -> Dict[str, Any]:
            """Analyze earnings data for surprises."""
            # Flatten multiple ticker data into a single object for analysis
            combined_data = {
                "symbol": "MULTIPLE",
                "success": True,
                "earnings_history": []
            }
            
            for ticker, data in earnings_data.items():
                if data.get("success"):
                    history = data.get("earnings_history", [])
                    for entry in history:
                        entry_with_ticker = entry.copy()
                        entry_with_ticker["ticker"] = ticker
                        combined_data["earnings_history"].append(entry_with_ticker)
            
            response = await self.client.post(
                f"{self.analysis_agent_url}/earnings",
                json={"earnings_data": combined_data}
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]["analysis"]
            else:
                raise Exception(result.get("error", "Failed to analyze earnings data"))
        
        # Analyze market sentiment task
        @self.task_graph.add_task
        async def analyze_sentiment(sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
            """Analyze market sentiment data."""
            response = await self.client.post(
                f"{self.analysis_agent_url}/sentiment",
                json={"sentiment_data": sentiment_data}
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]["analysis"]
            else:
                raise Exception(result.get("error", "Failed to analyze sentiment data"))
        
        # Analyze yield data task
        @self.task_graph.add_task
        async def analyze_yields(yield_data: Dict[str, Any]) -> Dict[str, Any]:
            """Analyze yield curve data."""
            response = await self.client.post(
                f"{self.analysis_agent_url}/yields",
                json={"yield_data": yield_data}
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]["analysis"]
            else:
                raise Exception(result.get("error", "Failed to analyze yield data"))
        
        # Generate market brief task
        @self.task_graph.add_task
        async def generate_market_brief(
            asia_tech: Dict[str, Any],
            earnings: Dict[str, Any],
            sentiment: Dict[str, Any],
            yields: Dict[str, Any]
        ) -> str:
            """Generate a market brief from all analyzed data."""
            response = await self.client.post(
                f"{self.language_agent_url}/market-brief",
                json={
                    "asia_tech": asia_tech,
                    "earnings": earnings,
                    "sentiment": sentiment,
                    "yields": yields
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]["brief"]
            else:
                raise Exception(result.get("error", "Failed to generate market brief"))
        
        # Generate voice response task
        @self.task_graph.add_task
        async def generate_voice_response(text: str, voice: str = "default") -> Dict[str, Any]:
            """Generate a voice response from text."""
            response = await self.client.post(
                f"{self.voice_agent_url}/generate-response",
                json={"text": text, "voice": voice}
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]
            else:
                raise Exception(result.get("error", "Failed to generate voice response"))
        
        # Get Asia tech news task
        @self.task_graph.add_task
        async def get_asia_tech_news() -> Dict[str, Any]:
            """Get news about Asian tech companies."""
            response = await self.client.get(
                f"{self.scraping_agent_url}/asia-tech-news"
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]
            else:
                raise Exception(result.get("error", "Failed to get Asia tech news"))
        
        # Retrieve financial context task
        @self.task_graph.add_task
        async def retrieve_financial_context(query: str, tickers: Optional[List[str]] = None) -> Dict[str, Any]:
            """Retrieve relevant financial context for a query."""
            response = await self.client.post(
                f"{self.retriever_agent_url}/financial-context",
                json={"query": query, "tickers": tickers, "k": 5}
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]
            else:
                raise Exception(result.get("error", "Failed to retrieve context"))
        
        # Synthesize response from context task
        @self.task_graph.add_task
        async def synthesize_response(query: str, context: Dict[str, Any]) -> str:
            """Synthesize a response from retrieved context."""
            response = await self.client.post(
                f"{self.language_agent_url}/synthesize-context",
                json={"query": query, "context": context["results"]}
            )
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return result["data"]["response"]
            else:
                raise Exception(result.get("error", "Failed to synthesize response"))
    
    async def process_market_brief_query(self, query: str) -> Dict[str, Any]:
        """
        Process a market brief query.
        
        Args:
            query: User query text
            
        Returns:
            Dictionary with response data
        """
        try:
            # Check if query is about Asia tech risk exposure
            if "risk exposure" in query.lower() and "asia tech" in query.lower():
                # Define Agno workflow for this specific query
                workflow = (
                    self.task_graph.workflow()
                    .get_asia_tech_exposure()
                    .get_market_sentiment()
                    .get_yield_data()
                )
                
                # Add tasks to get earnings data for key Asia tech stocks
                asia_tech_tickers = ["TSM", "BABA", "SONY", "JD", "BIDU"]
                workflow = workflow.get_earnings_data(asia_tech_tickers)
                
                # Execute the data collection tasks in parallel
                result = await workflow.execute()
                
                # Extract results
                asia_tech_data = result["get_asia_tech_exposure"]
                sentiment_data = result["get_market_sentiment"]
                yield_data = result["get_yield_data"]
                earnings_data = result["get_earnings_data"]
                
                # Define analysis workflow
                analysis_workflow = (
                    self.task_graph.workflow()
                    .analyze_asia_tech(asia_tech_data)
                    .analyze_sentiment(sentiment_data)
                    .analyze_yields(yield_data)
                    .analyze_earnings(earnings_data)
                )
                
                # Execute analysis tasks in parallel
                analysis_result = await analysis_workflow.execute()
                
                # Extract analysis results
                asia_tech_analysis = analysis_result["analyze_asia_tech"]
                sentiment_analysis = analysis_result["analyze_sentiment"]
                yields_analysis = analysis_result["analyze_yields"]
                earnings_analysis = analysis_result["analyze_earnings"]
                
                # Generate market brief
                brief_workflow = (
                    self.task_graph.workflow()
                    .generate_market_brief(
                        asia_tech_analysis, 
                        earnings_analysis, 
                        sentiment_analysis, 
                        yields_analysis
                    )
                )
                
                brief_result = await brief_workflow.execute()
                brief_text = brief_result["generate_market_brief"]
                
                # Generate voice response
                voice_workflow = (
                    self.task_graph.workflow()
                    .generate_voice_response(brief_text)
                )
                
                voice_result = await voice_workflow.execute()
                voice_data = voice_result["generate_voice_response"]
                
                return {
                    "success": True,
                    "text_response": brief_text,
                    "voice_response": voice_data,
                    "data": {
                        "asia_tech": asia_tech_analysis,
                        "earnings": earnings_analysis,
                        "sentiment": sentiment_analysis,
                        "yields": yields_analysis
                    }
                }
            
            else:
                # For other queries, use a more generic approach
                # First understand the query
                workflow = (
                    self.task_graph.workflow()
                    .understand_query(query)
                )
                
                result = await workflow.execute()
                understanding = result["understand_query"]
                
                # Extract tickers if any
                tickers = understanding.get("tickers", [])
                
                # Retrieve relevant context
                context_workflow = (
                    self.task_graph.workflow()
                    .retrieve_financial_context(query, tickers)
                )
                
                context_result = await context_workflow.execute()
                context = context_result["retrieve_financial_context"]
                
                # Check if we have good context
                if context.get("confidence", 0) > 0.7:
                    # Synthesize response from context
                    response_workflow = (
                        self.task_graph.workflow()
                        .synthesize_response(query, context)
                    )
                    
                    response_result = await response_workflow.execute()
                    response_text = response_result["synthesize_response"]
                    
                    # Generate voice response
                    voice_workflow = (
                        self.task_graph.workflow()
                        .generate_voice_response(response_text)
                    )
                    
                    voice_result = await voice_workflow.execute()
                    voice_data = voice_result["generate_voice_response"]
                    
                    return {
                        "success": True,
                        "text_response": response_text,
                        "voice_response": voice_data,
                        "data": {
                            "context": context,
                            "understanding": understanding
                        }
                    }
                else:
                    # Not enough context, give a fallback response
                    fallback_text = (
                        "I don't have enough information to answer that question confidently. "
                        "Would you like me to provide general market information instead?"
                    )
                    
                    # Generate voice response
                    voice_workflow = (
                        self.task_graph.workflow()
                        .generate_voice_response(fallback_text)
                    )
                    
                    voice_result = await voice_workflow.execute()
                    voice_data = voice_result["generate_voice_response"]
                    
                    return {
                        "success": True,
                        "text_response": fallback_text,
                        "voice_response": voice_data,
                        "data": {
                            "context": context,
                            "understanding": understanding,
                            "confidence": "low"
                        }
                    }
        
        except Exception as e:
            logger.error(f"Error processing market brief query: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_voice_query(self, audio_data: str) -> Dict[str, Any]:
        """
        Process a voice query.
        
        Args:
            audio_data: Base64 encoded audio data
            
        Returns:
            Dictionary with response data
        """
        try:
            # Convert voice to text
            voice_workflow = (
                self.task_graph.workflow()
                .process_voice_input(audio_data)
            )
            
            voice_result = await voice_workflow.execute()
            voice_text = voice_result["process_voice_input"]["text"]
            
            # Process the text query
            response = await self.process_market_brief_query(voice_text)
            
            # Add the transcribed query to the response
            response["query"] = voice_text
            
            return response
        
        except Exception as e:
            logger.error(f"Error processing voice query: {e}")
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Close resources."""
        await self.client.aclose()
