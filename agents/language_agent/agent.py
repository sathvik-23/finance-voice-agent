"""
Language Agent for natural language generation and understanding.
"""
import os
import logging
from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime
import agno
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LanguageAgent:
    """Agent for language generation and understanding."""
    
    def __init__(self, openai_api_key: Optional[str] = None, model_name: str = "gpt-4"):
        """
        Initialize the Language Agent.
        
        Args:
            openai_api_key: OpenAI API key
            model_name: Name of the LLM model to use
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OpenAI API key not provided. Language agent will not function.")
        
        self.model_name = model_name
        self.client = OpenAI(api_key=self.openai_api_key)
        
        # Initialize Agno toolset
        self.toolkit = agno.ToolKit()
        
        # Add Agno tools
        self.setup_agno_tools()
    
    def setup_agno_tools(self):
        """Set up Agno tools for the language agent."""
        
        # Market brief generation tool
        @self.toolkit.add
        def generate_market_brief(data: Dict[str, Any]) -> str:
            """
            Generate a market brief from financial data.
            
            Args:
                data: Dictionary with financial data
                
            Returns:
                Market brief text
            """
            # Extract key components
            asia_tech = data.get("asia_tech", {})
            earnings = data.get("earnings", {})
            sentiment = data.get("sentiment", {})
            yields = data.get("yields", {})
            
            # Generate brief using OpenAI
            prompt = self._create_market_brief_prompt(asia_tech, earnings, sentiment, yields)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a financial analyst providing a concise market brief."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        
        # Query understanding tool
        @self.toolkit.add
        def understand_query(query: str) -> Dict[str, Any]:
            """
            Understand a financial query and extract key components.
            
            Args:
                query: User query text
                
            Returns:
                Dictionary with extracted components
            """
            prompt = f"""
            Analyze the following financial query and extract key components:
            
            Query: "{query}"
            
            Determine:
            1. What assets/tickers are being asked about
            2. What type of information is being requested (e.g., price, performance, risk, earnings)
            3. What time period is relevant
            4. Any specific metrics or indicators mentioned
            
            Format the response as a JSON object with these keys:
            - tickers: list of ticker symbols mentioned or implied
            - information_type: what kind of information is being asked for
            - time_period: relevant time period
            - metrics: specific metrics or indicators mentioned
            - sentiment_analysis: is the query asking about sentiment or opinions
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a financial query analyzer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        
        # Generate earnings summary
        @self.toolkit.add
        def generate_earnings_summary(earnings_data: Dict[str, Any]) -> str:
            """
            Generate a summary of earnings surprises.
            
            Args:
                earnings_data: Dictionary with earnings data
                
            Returns:
                Earnings summary text
            """
            prompt = f"""
            Generate a concise summary of the following earnings data:
            
            {json.dumps(earnings_data, indent=2)}
            
            Focus on:
            1. Notable beats or misses
            2. Patterns or trends
            3. Implications for the market
            
            Keep the summary under 100 words.
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a financial analyst summarizing earnings data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content
    
    def _create_market_brief_prompt(self, 
                                  asia_tech: Dict[str, Any], 
                                  earnings: Dict[str, Any],
                                  sentiment: Dict[str, Any],
                                  yields: Dict[str, Any]) -> str:
        """
        Create a prompt for market brief generation.
        
        Args:
            asia_tech: Asia tech exposure data
            earnings: Earnings data
            sentiment: Market sentiment data
            yields: Yield data
            
        Returns:
            Prompt text
        """
        prompt = f"""
        Generate a concise market brief for a portfolio manager focused on Asia tech stocks.
        
        Here's the key data:
        
        1. Asia Tech Allocation:
        {json.dumps(asia_tech, indent=2)}
        
        2. Earnings Surprises:
        {json.dumps(earnings, indent=2)}
        
        3. Market Sentiment:
        {json.dumps(sentiment, indent=2)}
        
        4. Yield Environment:
        {json.dumps(yields, indent=2)}
        
        Format the brief like this:
        - Start with allocation changes (current vs previous)
        - Mention key earnings surprises
        - Describe regional sentiment
        - End with any relevant yield information that impacts the outlook
        
        Keep the brief under 150 words, focused, and actionable.
        """
        
        return prompt
    
    def generate_market_brief(self, 
                            asia_tech: Dict[str, Any], 
                            earnings: Dict[str, Any],
                            sentiment: Dict[str, Any],
                            yields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a market brief using Agno.
        
        Args:
            asia_tech: Asia tech exposure data
            earnings: Earnings data
            sentiment: Market sentiment data
            yields: Yield data
            
        Returns:
            Dictionary with market brief
        """
        try:
            # Prepare data for Agno
            data = {
                "asia_tech": asia_tech,
                "earnings": earnings,
                "sentiment": sentiment,
                "yields": yields
            }
            
            # Call Agno tool
            result = self.toolkit.tools.generate_market_brief(data)
            
            return {
                "success": True,
                "brief": result
            }
            
        except Exception as e:
            logger.error(f"Error generating market brief: {e}")
            return {"success": False, "error": str(e)}
    
    def understand_query(self, query: str) -> Dict[str, Any]:
        """
        Understand a user query using Agno.
        
        Args:
            query: User query text
            
        Returns:
            Dictionary with query understanding results
        """
        try:
            # Call Agno tool
            result = self.toolkit.tools.understand_query(query)
            
            return {
                "success": True,
                "understanding": result
            }
            
        except Exception as e:
            logger.error(f"Error understanding query: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_earnings_summary(self, earnings_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an earnings summary using Agno.
        
        Args:
            earnings_data: Earnings data
            
        Returns:
            Dictionary with earnings summary
        """
        try:
            # Call Agno tool
            result = self.toolkit.tools.generate_earnings_summary(earnings_data)
            
            return {
                "success": True,
                "summary": result
            }
            
        except Exception as e:
            logger.error(f"Error generating earnings summary: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_response(self, prompt: str, system_message: str = "") -> Dict[str, Any]:
        """
        Generate a response using the LLM.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            
        Returns:
            Dictionary with response
        """
        try:
            # Set default system message if not provided
            if not system_message:
                system_message = "You are a helpful financial assistant providing accurate, concise information."
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {"success": False, "error": str(e)}
    
    def synthesize_from_retrieved_context(self, 
                                        query: str, 
                                        context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize a response from retrieved context.
        
        Args:
            query: User query
            context: List of retrieved context chunks
            
        Returns:
            Dictionary with synthesized response
        """
        try:
            # Format context for the prompt
            context_text = ""
            for i, ctx in enumerate(context):
                context_text += f"\nContext {i+1}:\n{ctx.get('text', '')}\n"
            
            # Create prompt
            prompt = f"""
            Based on the following retrieved context, answer this question:
            
            Question: {query}
            
            {context_text}
            
            Use only the information in the provided context. If the context doesn't contain
            enough information to answer the question fully, say so and explain what additional
            information would be needed.
            """
            
            # Generate response
            system_message = "You are a financial expert providing accurate information based only on the given context."
            return self.generate_response(prompt, system_message)
            
        except Exception as e:
            logger.error(f"Error synthesizing from context: {e}")
            return {"success": False, "error": str(e)}
