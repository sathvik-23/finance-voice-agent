"""
Analysis Agent for financial data analysis.
"""
import os
import logging
from typing import Dict, List, Any, Optional, Union
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisAgent:
    """Agent for analyzing financial data."""
    
    def __init__(self):
        """Initialize the Analysis Agent."""
        pass
    
    def analyze_stock_data(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze stock price data.
        
        Args:
            stock_data: Stock data from API Agent
            
        Returns:
            Dictionary with analysis results
        """
        try:
            if not stock_data.get("success", False):
                return {"success": False, "error": "Invalid stock data"}
            
            symbol = stock_data.get("symbol", "")
            latest_price = stock_data.get("latest_price")
            change_percent = stock_data.get("change_percent")
            history = stock_data.get("history", [])
            
            # Convert history to DataFrame if it's a list
            if isinstance(history, list):
                history_df = pd.DataFrame(history)
            else:
                # If it's already a DataFrame, use it as is
                history_df = history
            
            # Basic statistics
            analysis = {
                "symbol": symbol,
                "latest_price": latest_price,
                "change_percent": change_percent,
                "stats": {}
            }
            
            # Check if we have enough historical data
            if not history_df.empty and 'Close' in history_df.columns:
                # Calculate basic statistics
                close_prices = history_df['Close']
                analysis["stats"]["mean"] = float(close_prices.mean())
                analysis["stats"]["median"] = float(close_prices.median())
                analysis["stats"]["std"] = float(close_prices.std())
                analysis["stats"]["min"] = float(close_prices.min())
                analysis["stats"]["max"] = float(close_prices.max())
                
                # Calculate price movement
                if len(close_prices) > 1:
                    first_price = close_prices.iloc[0]
                    last_price = close_prices.iloc[-1]
                    price_change = last_price - first_price
                    price_change_percent = (price_change / first_price) * 100
                    
                    analysis["movement"] = {
                        "price_change": float(price_change),
                        "price_change_percent": float(price_change_percent),
                        "direction": "up" if price_change > 0 else "down" if price_change < 0 else "flat"
                    }
                
                # Calculate simple moving averages if we have enough data
                if len(close_prices) >= 5:
                    analysis["stats"]["sma_5"] = float(close_prices.rolling(window=5).mean().iloc[-1])
                
                if len(close_prices) >= 20:
                    analysis["stats"]["sma_20"] = float(close_prices.rolling(window=20).mean().iloc[-1])
                
                # Calculate volatility (standard deviation of percent changes)
                if len(close_prices) > 1:
                    pct_changes = close_prices.pct_change().dropna()
                    volatility = pct_changes.std() * 100  # Convert to percentage
                    analysis["stats"]["volatility"] = float(volatility)
                
                # Determine price trend
                if 'sma_5' in analysis["stats"] and 'sma_20' in analysis["stats"]:
                    sma_5 = analysis["stats"]["sma_5"]
                    sma_20 = analysis["stats"]["sma_20"]
                    
                    if sma_5 > sma_20:
                        analysis["trend"] = "bullish"
                    elif sma_5 < sma_20:
                        analysis["trend"] = "bearish"
                    else:
                        analysis["trend"] = "neutral"
                else:
                    # Simple trend based on recent movement
                    if "movement" in analysis:
                        if analysis["movement"]["price_change_percent"] > 1.0:
                            analysis["trend"] = "bullish"
                        elif analysis["movement"]["price_change_percent"] < -1.0:
                            analysis["trend"] = "bearish"
                        else:
                            analysis["trend"] = "neutral"
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing stock data: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_multiple_stocks(self, stocks_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze multiple stocks data.
        
        Args:
            stocks_data: Dictionary with stock data for multiple symbols
            
        Returns:
            Dictionary with analysis results
        """
        try:
            results = {}
            
            for symbol, data in stocks_data.items():
                if data.get("success", False):
                    analysis = self.analyze_stock_data(data)
                    if analysis["success"]:
                        results[symbol] = analysis["analysis"]
            
            # Calculate comparative metrics
            if len(results) > 1:
                # Find best and worst performers
                performances = []
                
                for symbol, analysis in results.items():
                    if "change_percent" in analysis:
                        performances.append((symbol, analysis["change_percent"]))
                
                performances.sort(key=lambda x: x[1], reverse=True)
                
                best_performer = performances[0][0] if performances else None
                worst_performer = performances[-1][0] if performances else None
                
                # Calculate average performance
                avg_performance = sum(p[1] for p in performances) / len(performances) if performances else 0
                
                comparative = {
                    "best_performer": {
                        "symbol": best_performer,
                        "change_percent": results[best_performer]["change_percent"] if best_performer else None
                    },
                    "worst_performer": {
                        "symbol": worst_performer,
                        "change_percent": results[worst_performer]["change_percent"] if worst_performer else None
                    },
                    "average_performance": avg_performance
                }
                
                return {
                    "success": True,
                    "individual_analyses": results,
                    "comparative": comparative
                }
            
            return {
                "success": True,
                "individual_analyses": results
            }
            
        except Exception as e:
            logger.error(f"Error analyzing multiple stocks: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_earnings_data(self, earnings_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze earnings data.
        
        Args:
            earnings_data: Earnings data from API Agent
            
        Returns:
            Dictionary with analysis results
        """
        try:
            if not earnings_data.get("success", False):
                return {"success": False, "error": "Invalid earnings data"}
            
            symbol = earnings_data.get("symbol", "")
            earnings_history = earnings_data.get("earnings_history", [])
            next_earnings = earnings_data.get("next_earnings", {})
            
            analysis = {
                "symbol": symbol,
                "earnings_analysis": {},
                "next_earnings": next_earnings
            }
            
            # Check if we have earnings history
            if earnings_history:
                # Convert to DataFrame for easier analysis
                if isinstance(earnings_history, list):
                    history_df = pd.DataFrame(earnings_history)
                else:
                    history_df = earnings_history
                
                # Calculate surprise metrics if we have the right columns
                if not history_df.empty and 'Reported EPS' in history_df.columns and 'Estimated EPS' in history_df.columns:
                    # Calculate surprise percentages
                    history_df['Surprise Percent'] = (history_df['Reported EPS'] - history_df['Estimated EPS']) / \
                                                    history_df['Estimated EPS'].abs() * 100
                    
                    # Count beats, meets, misses
                    beats = len(history_df[history_df['Surprise Percent'] > 1.0])
                    meets = len(history_df[(history_df['Surprise Percent'] <= 1.0) & (history_df['Surprise Percent'] >= -1.0)])
                    misses = len(history_df[history_df['Surprise Percent'] < -1.0])
                    
                    # Calculate average surprise
                    avg_surprise = history_df['Surprise Percent'].mean()
                    
                    analysis["earnings_analysis"] = {
                        "beats": beats,
                        "meets": meets,
                        "misses": misses,
                        "beat_ratio": beats / len(history_df) if len(history_df) > 0 else 0,
                        "average_surprise_percent": float(avg_surprise) if not pd.isna(avg_surprise) else 0,
                        "latest_result": "beat" if history_df['Surprise Percent'].iloc[0] > 1.0 else
                                         "miss" if history_df['Surprise Percent'].iloc[0] < -1.0 else "meet"
                                         if len(history_df) > 0 else "unknown"
                    }
                    
                    # Get latest surprise percentage
                    if len(history_df) > 0:
                        analysis["latest_surprise_percent"] = float(history_df['Surprise Percent'].iloc[0]) \
                                                             if not pd.isna(history_df['Surprise Percent'].iloc[0]) else 0
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing earnings data: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_sector_performance(self, sector_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sector performance data.
        
        Args:
            sector_data: Sector performance data from API Agent
            
        Returns:
            Dictionary with analysis results
        """
        try:
            if not sector_data.get("success", False):
                return {"success": False, "error": "Invalid sector data"}
            
            sectors = sector_data.get("sectors", {})
            
            # Convert to list of (sector, performance) tuples
            sector_performances = []
            
            for sector, data in sectors.items():
                if isinstance(data, dict) and "performance" in data:
                    performance = data["performance"]
                    sector_performances.append((sector, performance))
            
            # Sort sectors by performance
            sector_performances.sort(key=lambda x: x[1], reverse=True)
            
            # Calculate average performance
            avg_performance = sum(p[1] for s, p in sector_performances) / len(sector_performances) if sector_performances else 0
            
            # Group sectors by performance
            outperforming = [(s, p) for s, p in sector_performances if p > avg_performance]
            underperforming = [(s, p) for s, p in sector_performances if p <= avg_performance]
            
            return {
                "success": True,
                "analysis": {
                    "top_sectors": sector_performances[:3] if len(sector_performances) >= 3 else sector_performances,
                    "bottom_sectors": sector_performances[-3:] if len(sector_performances) >= 3 else sector_performances,
                    "average_performance": avg_performance,
                    "outperforming_sectors": outperforming,
                    "underperforming_sectors": underperforming
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sector performance: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_market_sentiment(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market sentiment data.
        
        Args:
            sentiment_data: Market sentiment data from API Agent
            
        Returns:
            Dictionary with analysis results
        """
        try:
            if not sentiment_data.get("success", False):
                return {"success": False, "error": "Invalid sentiment data"}
            
            sentiment_score = sentiment_data.get("sentiment_score", 0)
            sentiment_label = sentiment_data.get("sentiment_label", "neutral")
            factors = sentiment_data.get("factors", [])
            indices = sentiment_data.get("indices", {})
            
            # Analyze the factors affecting sentiment
            positive_factors = [f for f in factors if f.get("impact") == "positive"]
            negative_factors = [f for f in factors if f.get("impact") == "negative"]
            
            # Sort factors by score
            positive_factors.sort(key=lambda x: x.get("score", 0), reverse=True)
            negative_factors.sort(key=lambda x: abs(x.get("score", 0)), reverse=True)
            
            # Analyze index performances
            index_performances = []
            
            for idx_symbol, idx_data in indices.items():
                if idx_data.get("success", False):
                    index_performances.append({
                        "symbol": idx_symbol,
                        "name": idx_data.get("name", idx_symbol),
                        "price": idx_data.get("latest_price"),
                        "change_percent": idx_data.get("change_percent")
                    })
            
            # Sort indices by performance
            index_performances.sort(key=lambda x: x.get("change_percent", 0), reverse=True)
            
            return {
                "success": True,
                "analysis": {
                    "sentiment_score": sentiment_score,
                    "sentiment_label": sentiment_label,
                    "top_positive_factors": positive_factors[:3] if len(positive_factors) >= 3 else positive_factors,
                    "top_negative_factors": negative_factors[:3] if len(negative_factors) >= 3 else negative_factors,
                    "index_performances": index_performances,
                    "factor_count": {
                        "positive": len(positive_factors),
                        "negative": len(negative_factors)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market sentiment: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_asia_tech_exposure(self, exposure_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Asia tech exposure data.
        
        Args:
            exposure_data: Asia tech exposure data from API Agent
            
        Returns:
            Dictionary with analysis results
        """
        try:
            if not exposure_data.get("success", False):
                return {"success": False, "error": "Invalid Asia tech exposure data"}
            
            # Extract key data
            allocation = exposure_data.get("asia_tech_allocation", {})
            stock_data = exposure_data.get("stock_data", {})
            earnings_surprises = exposure_data.get("earnings_surprises", [])
            regional_sentiment = exposure_data.get("regional_sentiment", {})
            
            # Allocation change analysis
            current_allocation = allocation.get("current", 0)
            previous_allocation = allocation.get("previous", 0)
            allocation_change = allocation.get("change", 0)
            
            allocation_change_percent = (allocation_change / previous_allocation * 100) if previous_allocation > 0 else 0
            
            # Stock performance analysis
            stock_performances = []
            
            for symbol, data in stock_data.items():
                if data.get("success", False):
                    stock_performances.append({
                        "symbol": symbol,
                        "price": data.get("latest_price"),
                        "change_percent": data.get("change_percent")
                    })
            
            # Sort stocks by performance
            stock_performances.sort(key=lambda x: x.get("change_percent", 0), reverse=True)
            
            # Earnings surprises analysis
            positive_surprises = []
            negative_surprises = []
            
            for surprise in earnings_surprises:
                if surprise.get("surprise_percent", 0) > 0:
                    positive_surprises.append(surprise)
                else:
                    negative_surprises.append(surprise)
            
            # Sort surprises by magnitude
            positive_surprises.sort(key=lambda x: x.get("surprise_percent", 0), reverse=True)
            negative_surprises.sort(key=lambda x: x.get("surprise_percent", 0))
            
            # Regional sentiment analysis
            sentiment_label = regional_sentiment.get("label", "neutral")
            sentiment_detail = regional_sentiment.get("detail", "")
            avg_change = regional_sentiment.get("avg_change_percent", 0)
            up_stocks = regional_sentiment.get("up_stocks", 0)
            down_stocks = regional_sentiment.get("down_stocks", 0)
            
            return {
                "success": True,
                "analysis": {
                    "allocation": {
                        "current": current_allocation,
                        "previous": previous_allocation,
                        "change": allocation_change,
                        "change_percent": allocation_change_percent,
                        "direction": "increased" if allocation_change > 0 else "decreased" if allocation_change < 0 else "unchanged"
                    },
                    "stock_performance": {
                        "top_performers": stock_performances[:3] if len(stock_performances) >= 3 else stock_performances,
                        "bottom_performers": stock_performances[-3:] if len(stock_performances) >= 3 else [],
                        "average_change": avg_change
                    },
                    "earnings_surprises": {
                        "positive": positive_surprises,
                        "negative": negative_surprises
                    },
                    "sentiment": {
                        "label": sentiment_label,
                        "detail": sentiment_detail,
                        "up_down_ratio": up_stocks / down_stocks if down_stocks > 0 else float('inf')
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Asia tech exposure: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_yield_data(self, yield_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze yield data.
        
        Args:
            yield_data: Yield data from API Agent
            
        Returns:
            Dictionary with analysis results
        """
        try:
            if not yield_data.get("success", False):
                return {"success": False, "error": "Invalid yield data"}
            
            yields = yield_data.get("yields", {})
            trend = yield_data.get("trend", "mixed")
            ten_year = yield_data.get("ten_year_treasury")
            
            # Extract key yields
            key_yields = {}
            for name, data in yields.items():
                key_yields[name] = {
                    "current": data.get("current_yield"),
                    "change": data.get("change")
                }
            
            # Analyze yield curve (if we have enough data)
            yield_curve = "normal"
            if "10-Year Treasury Yield" in key_yields and "2-Year Treasury Yield" in key_yields:
                ten_year_yield = key_yields["10-Year Treasury Yield"]["current"]
                two_year_yield = key_yields["2-Year Treasury Yield"]["current"]
                
                if ten_year_yield < two_year_yield:
                    yield_curve = "inverted"
                    yield_diff = two_year_yield - ten_year_yield
                else:
                    yield_curve = "normal"
                    yield_diff = ten_year_yield - two_year_yield
            else:
                yield_diff = None
            
            # Analyze yield trend impact on equities
            equity_impact = "neutral"
            if trend == "strongly rising" or trend == "rising":
                equity_impact = "negative"
            elif trend == "strongly falling" or trend == "falling":
                equity_impact = "positive"
            
            return {
                "success": True,
                "analysis": {
                    "key_yields": key_yields,
                    "trend": trend,
                    "ten_year_treasury": ten_year,
                    "yield_curve": {
                        "shape": yield_curve,
                        "difference": yield_diff
                    },
                    "equity_market_impact": equity_impact
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing yield data: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_market_brief(self, 
                           asia_tech_data: Dict[str, Any],
                           earnings_data: Dict[str, Any],
                           market_sentiment: Dict[str, Any],
                           yield_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive market brief from multiple data sources.
        
        Args:
            asia_tech_data: Asia tech exposure data
            earnings_data: Earnings data for key stocks
            market_sentiment: Overall market sentiment
            yield_data: Yield data
            
        Returns:
            Dictionary with comprehensive analysis
        """
        try:
            # Analyze individual components
            asia_tech_analysis = self.analyze_asia_tech_exposure(asia_tech_data)
            market_sentiment_analysis = self.analyze_market_sentiment(market_sentiment)
            yield_analysis = self.analyze_yield_data(yield_data)
            
            # Check if analyses were successful
            if not all([asia_tech_analysis.get("success", False),
                       market_sentiment_analysis.get("success", False),
                       yield_analysis.get("success", False)]):
                return {"success": False, "error": "One or more analyses failed"}
            
            # Extract key metrics
            asia_tech = asia_tech_analysis["analysis"]
            sentiment = market_sentiment_analysis["analysis"]
            yields = yield_analysis["analysis"]
            
            # Build comprehensive brief
            brief = {
                "asia_tech_allocation": {
                    "current": asia_tech["allocation"]["current"],
                    "previous": asia_tech["allocation"]["previous"],
                    "change": asia_tech["allocation"]["change"],
                    "change_percent": asia_tech["allocation"]["change_percent"]
                },
                "earnings_surprises": asia_tech["earnings_surprises"],
                "regional_sentiment": {
                    "label": asia_tech["sentiment"]["label"],
                    "detail": asia_tech["sentiment"]["detail"]
                },
                "market_sentiment": {
                    "label": sentiment["sentiment_label"],
                    "score": sentiment["sentiment_score"],
                    "key_factors": sentiment["top_positive_factors"] + sentiment["top_negative_factors"]
                },
                "yield_environment": {
                    "trend": yields["trend"],
                    "ten_year": yields["ten_year_treasury"],
                    "equity_impact": yields["equity_market_impact"]
                }
            }
            
            return {
                "success": True,
                "brief": brief
            }
            
        except Exception as e:
            logger.error(f"Error generating market brief: {e}")
            return {"success": False, "error": str(e)}
