"""
API Agent for fetching financial data from AlphaVantage and Yahoo Finance.
"""
import os
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIAgent:
    """Agent for fetching financial data from APIs."""
    
    def __init__(self, alpha_vantage_key: Optional[str] = None):
        """Initialize the API Agent with API keys."""
        self.alpha_vantage_key = alpha_vantage_key or os.getenv("ALPHAVANTAGE_API_KEY")
        if not self.alpha_vantage_key:
            logger.warning("AlphaVantage API key not provided. Some functionalities may be limited.")
        
        # Initialize AlphaVantage clients if key is available
        if self.alpha_vantage_key:
            self.ts = TimeSeries(key=self.alpha_vantage_key, output_format='pandas')
            self.fd = FundamentalData(key=self.alpha_vantage_key, output_format='pandas')
    
    def get_stock_data(self, symbol: str, period: str = "1d") -> Dict[str, Any]:
        """
        Get recent stock data using Yahoo Finance.
        
        Args:
            symbol: The stock symbol to fetch
            period: Time period to fetch (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            Dictionary with stock data
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            # Calculate basic metrics
            if not hist.empty:
                latest = hist.iloc[-1]
                prev_close = hist.iloc[-2].Close if len(hist) > 1 else None
                change = (latest.Close - prev_close) / prev_close * 100 if prev_close else None
                
                return {
                    "symbol": symbol,
                    "latest_price": latest.Close,
                    "change_percent": change,
                    "volume": latest.Volume,
                    "high": latest.High,
                    "low": latest.Low,
                    "timestamp": latest.name.strftime("%Y-%m-%d %H:%M:%S"),
                    "history": hist.to_dict(orient="records"),
                    "success": True
                }
            else:
                return {"symbol": symbol, "success": False, "error": "No data available"}
        
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return {"symbol": symbol, "success": False, "error": str(e)}
    
    def get_multiple_stocks(self, symbols: List[str], period: str = "1d") -> Dict[str, Dict[str, Any]]:
        """Get data for multiple stocks."""
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_data(symbol, period)
        return results
    
    def get_earnings_data(self, symbol: str) -> Dict[str, Any]:
        """Get earnings data for a stock."""
        try:
            ticker = yf.Ticker(symbol)
            earnings = ticker.earnings
            calendar = ticker.calendar
            
            # Check for earnings surprises
            if not earnings.empty:
                # Calculate surprise percentages
                earnings_dict = earnings.to_dict(orient="records")
                
                # Process calendar data if available
                next_earnings = {}
                if calendar is not None and not calendar.empty:
                    next_date = calendar.iloc[0].name
                    next_earnings = {
                        "date": next_date.strftime("%Y-%m-%d") if hasattr(next_date, "strftime") else str(next_date),
                        "estimate": float(calendar.iloc[0].get("EPS Estimate", 0)) if "EPS Estimate" in calendar.columns else None
                    }
                
                return {
                    "symbol": symbol,
                    "earnings_history": earnings_dict,
                    "next_earnings": next_earnings,
                    "success": True
                }
            else:
                return {"symbol": symbol, "success": False, "error": "No earnings data available"}
        
        except Exception as e:
            logger.error(f"Error fetching earnings data for {symbol}: {e}")
            return {"symbol": symbol, "success": False, "error": str(e)}
    
    def get_sector_performance(self) -> Dict[str, Any]:
        """Get sector performance data."""
        try:
            # Use AlphaVantage if available, otherwise fallback to Yahoo Finance sector ETFs
            if hasattr(self, "ts"):
                data, meta = self.ts.get_sector()
                return {
                    "sectors": data.to_dict(),
                    "metadata": meta,
                    "success": True
                }
            else:
                # Fallback to tracking sector ETFs
                sector_etfs = {
                    "Technology": "XLK",
                    "Financial": "XLF",
                    "Healthcare": "XLV",
                    "Consumer Discretionary": "XLY",
                    "Consumer Staples": "XLP",
                    "Energy": "XLE",
                    "Materials": "XLB",
                    "Industrials": "XLI",
                    "Utilities": "XLU",
                    "Real Estate": "XLRE",
                    "Communication Services": "XLC"
                }
                
                sector_data = {}
                for sector, etf in sector_etfs.items():
                    data = self.get_stock_data(etf, period="5d")
                    if data["success"]:
                        sector_data[sector] = {
                            "etf": etf,
                            "performance": data["change_percent"],
                            "latest_price": data["latest_price"]
                        }
                
                return {
                    "sectors": sector_data,
                    "success": True
                }
        
        except Exception as e:
            logger.error(f"Error fetching sector performance: {e}")
            return {"success": False, "error": str(e)}
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        """
        Get overall market sentiment based on key indices.
        
        Returns:
            Dictionary with sentiment data
        """
        try:
            # Track major indices
            indices = ["^GSPC", "^DJI", "^IXIC", "^VIX"]
            index_names = {
                "^GSPC": "S&P 500",
                "^DJI": "Dow Jones",
                "^IXIC": "NASDAQ",
                "^VIX": "VIX (Volatility Index)"
            }
            
            index_data = self.get_multiple_stocks(indices, period="5d")
            
            # Calculate overall sentiment score (-1 to 1)
            sentiment_score = 0.0
            sentiment_factors = []
            
            # Process each index
            for idx, data in index_data.items():
                if data["success"]:
                    # Different weight for VIX (inverse relationship)
                    if idx == "^VIX":
                        if data["change_percent"] > 0:
                            sentiment_factors.append({
                                "factor": f"{index_names[idx]} up {data['change_percent']:.2f}%",
                                "impact": "negative",
                                "score": -min(data["change_percent"] * 0.05, 0.3)
                            })
                            sentiment_score -= min(data["change_percent"] * 0.05, 0.3)
                        else:
                            sentiment_factors.append({
                                "factor": f"{index_names[idx]} down {abs(data['change_percent']):.2f}%",
                                "impact": "positive",
                                "score": min(abs(data["change_percent"]) * 0.05, 0.3)
                            })
                            sentiment_score += min(abs(data["change_percent"]) * 0.05, 0.3)
                    else:
                        # Regular indices
                        if data["change_percent"] > 0:
                            sentiment_factors.append({
                                "factor": f"{index_names[idx]} up {data['change_percent']:.2f}%",
                                "impact": "positive",
                                "score": min(data["change_percent"] * 0.03, 0.2)
                            })
                            sentiment_score += min(data["change_percent"] * 0.03, 0.2)
                        else:
                            sentiment_factors.append({
                                "factor": f"{index_names[idx]} down {abs(data['change_percent']):.2f}%",
                                "impact": "negative",
                                "score": -min(abs(data["change_percent"]) * 0.03, 0.2)
                            })
                            sentiment_score -= min(abs(data["change_percent"]) * 0.03, 0.2)
            
            # Normalize score to -1 to 1 range
            sentiment_score = max(min(sentiment_score, 1.0), -1.0)
            
            # Map score to sentiment label
            sentiment_label = "neutral"
            sentiment_detail = "neutral"
            if sentiment_score > 0.6:
                sentiment_label = "very bullish"
                sentiment_detail = "strongly positive"
            elif sentiment_score > 0.2:
                sentiment_label = "bullish"
                sentiment_detail = "positive"
            elif sentiment_score > -0.2:
                sentiment_label = "neutral"
                if sentiment_score > 0:
                    sentiment_detail = "neutral with slight positive bias"
                else:
                    sentiment_detail = "neutral with slight negative bias"
            elif sentiment_score > -0.6:
                sentiment_label = "bearish"
                sentiment_detail = "negative"
            else:
                sentiment_label = "very bearish"
                sentiment_detail = "strongly negative"
                
            return {
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "sentiment_detail": sentiment_detail,
                "factors": sentiment_factors,
                "indices": {k: v for k, v in index_data.items() if v["success"]},
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error calculating market sentiment: {e}")
            return {"success": False, "error": str(e)}
    
    def get_asia_tech_exposure(self) -> Dict[str, Any]:
        """
        Get specific data about Asia tech stocks exposure.
        
        Returns:
            Dictionary with Asia tech exposure data
        """
        # Key Asia tech stocks to track
        asia_tech_stocks = [
            "TSM",    # Taiwan Semiconductor
            "BABA",   # Alibaba
            "BIDU",   # Baidu
            "JD",     # JD.com
            "PDD",    # PDD Holdings
            "NTES",   # NetEase
            "SE",     # Sea Limited
            "SONY",   # Sony
            "9988.HK", # Alibaba Hong Kong
            "9618.HK", # JD.com Hong Kong
            "3690.HK", # Meituan
            "700.HK"   # Tencent
        ]
        
        # Stocks that have earnings to check
        stocks_with_earnings = ["TSM", "BABA", "SONY", "JD", "BIDU"]
        
        try:
            # Get stock data
            stock_data = self.get_multiple_stocks(asia_tech_stocks, period="5d")
            
            # Get earnings data for key stocks
            earnings_data = {}
            for stock in stocks_with_earnings:
                earnings_data[stock] = self.get_earnings_data(stock)
            
            # Calculate overall performance metrics
            total_stocks = len([s for s, d in stock_data.items() if d["success"]])
            up_stocks = len([s for s, d in stock_data.items() if d["success"] and d["change_percent"] > 0])
            down_stocks = len([s for s, d in stock_data.items() if d["success"] and d["change_percent"] < 0])
            
            # Find earnings surprises
            earnings_surprises = []
            for stock, data in earnings_data.items():
                if data["success"] and "earnings_history" in data and len(data["earnings_history"]) > 0:
                    latest = data["earnings_history"][-1]
                    if "Surprise" in latest and latest["Surprise"] is not None:
                        surprise_pct = (latest["Reported EPS"] - latest["Estimated EPS"]) / abs(latest["Estimated EPS"]) * 100 if latest["Estimated EPS"] else 0
                        earnings_surprises.append({
                            "symbol": stock,
                            "surprise_percent": surprise_pct,
                            "estimated_eps": latest["Estimated EPS"],
                            "reported_eps": latest["Reported EPS"],
                            "surprise": latest["Surprise"]
                        })
            
            # Calculate region sentiment
            avg_change = sum([d["change_percent"] for s, d in stock_data.items() if d["success"]]) / total_stocks if total_stocks else 0
            
            sentiment = "neutral"
            if avg_change > 3:
                sentiment = "very bullish"
            elif avg_change > 1:
                sentiment = "bullish"
            elif avg_change > -1:
                sentiment = "neutral"
            elif avg_change > -3:
                sentiment = "bearish"
            else:
                sentiment = "very bearish"
                
            sentiment_detail = ""
            if up_stocks > down_stocks * 2:
                sentiment_detail = "strongly positive with most stocks trending upward"
            elif up_stocks > down_stocks:
                sentiment_detail = "positive with more stocks up than down"
            elif down_stocks > up_stocks * 2:
                sentiment_detail = "strongly negative with most stocks trending downward"
            elif down_stocks > up_stocks:
                sentiment_detail = "negative with more stocks down than up"
            else:
                sentiment_detail = "mixed with an equal number of stocks up and down"
            
            # For the mock portfolio, we'll simulate an allocation and calculate metrics
            # In a real scenario, this would come from a portfolio management system
            
            # Mock portfolio data
            mock_portfolio = {
                "previous_allocation": 18.0,  # percent of AUM
                "current_allocation": 22.0,   # percent of AUM
                "holdings": {
                    "TSM": {"weight": 5.2, "shares": 1000},
                    "BABA": {"weight": 4.1, "shares": 800},
                    "700.HK": {"weight": 3.8, "shares": 1200},
                    "9988.HK": {"weight": 2.5, "shares": 1500},
                    "SE": {"weight": 2.2, "shares": 600},
                    "SONY": {"weight": 2.0, "shares": 400},
                    "BIDU": {"weight": 1.2, "shares": 300},
                    "JD": {"weight": 1.0, "shares": 250}
                }
            }
            
            return {
                "asia_tech_allocation": {
                    "previous": mock_portfolio["previous_allocation"],
                    "current": mock_portfolio["current_allocation"],
                    "change": mock_portfolio["current_allocation"] - mock_portfolio["previous_allocation"]
                },
                "stock_data": stock_data,
                "earnings_surprises": earnings_surprises,
                "regional_sentiment": {
                    "label": sentiment,
                    "detail": sentiment_detail,
                    "avg_change_percent": avg_change,
                    "up_stocks": up_stocks,
                    "down_stocks": down_stocks,
                    "total_stocks": total_stocks
                },
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error calculating Asia tech exposure: {e}")
            return {"success": False, "error": str(e)}

    def get_yield_data(self) -> Dict[str, Any]:
        """Get current yield data."""
        try:
            # Treasury yield tickers
            yield_tickers = [
                "^TNX",  # 10-year Treasury yield
                "^TYX",  # 30-year Treasury yield
                "^FVX",  # 5-year Treasury yield
                "^IRX"   # 13-week Treasury bill yield
            ]
            
            yield_names = {
                "^TNX": "10-Year Treasury Yield",
                "^TYX": "30-Year Treasury Yield", 
                "^FVX": "5-Year Treasury Yield",
                "^IRX": "13-Week Treasury Bill Yield"
            }
            
            yield_data = self.get_multiple_stocks(yield_tickers, period="5d")
            
            # Process data into more readable format
            formatted_yields = {}
            for ticker, data in yield_data.items():
                if data["success"]:
                    formatted_yields[yield_names[ticker]] = {
                        "current_yield": data["latest_price"],
                        "change": data["change_percent"],
                        "ticker": ticker
                    }
            
            # Simple yield analysis
            yield_rising = sum(1 for y in formatted_yields.values() if y["change"] > 0)
            yield_falling = sum(1 for y in formatted_yields.values() if y["change"] < 0)
            
            yield_trend = "mixed"
            if yield_rising > yield_falling * 2:
                yield_trend = "strongly rising"
            elif yield_rising > yield_falling:
                yield_trend = "rising"
            elif yield_falling > yield_rising * 2:
                yield_trend = "strongly falling"
            elif yield_falling > yield_rising:
                yield_trend = "falling"
                
            ten_year = formatted_yields.get("10-Year Treasury Yield", {}).get("current_yield")
                
            return {
                "yields": formatted_yields,
                "trend": yield_trend,
                "ten_year_treasury": ten_year,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error fetching yield data: {e}")
            return {"success": False, "error": str(e)}
