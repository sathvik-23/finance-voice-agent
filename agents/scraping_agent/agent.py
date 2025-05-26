"""
Scraping Agent for crawling financial filings and news.
"""
import os
import re
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingAgent:
    """Agent for scraping financial filings and news."""
    
    def __init__(self):
        """Initialize the Scraping Agent."""
        self.session = requests.Session()
        # Set user-agent to avoid being blocked
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        # Base URLs for different sources
        self.sec_base_url = "https://www.sec.gov"
        self.sec_edgar_url = "https://www.sec.gov/edgar/searchedgar/companysearch"
        self.yahoo_finance_url = "https://finance.yahoo.com"
        self.ft_url = "https://www.ft.com"
        self.reuters_url = "https://www.reuters.com"
        
    def search_sec_filings(self, ticker: str, filing_type: str = "10-K,10-Q,8-K", 
                           limit: int = 5) -> Dict[str, Any]:
        """
        Search SEC EDGAR database for company filings.
        
        Args:
            ticker: Company ticker symbol
            filing_type: Type of filing to search for (comma separated)
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with filing results
        """
        try:
            # SEC filings can be accessed via the EDGAR API
            url = f"https://data.sec.gov/submissions/CIK{ticker.upper().zfill(10)}.json"
            
            response = self.session.get(url)
            if response.status_code != 200:
                logger.error(f"Error fetching SEC data: {response.status_code}")
                return {"success": False, "error": f"HTTP Error: {response.status_code}"}
            
            data = response.json()
            
            # Filter filings by type
            filing_types = filing_type.split(",")
            recent_filings = []
            
            if "filings" in data and "recent" in data["filings"]:
                filings_data = data["filings"]["recent"]
                
                if "form" in filings_data and "filingDate" in filings_data:
                    forms = filings_data["form"]
                    dates = filings_data["filingDate"]
                    accession_numbers = filings_data.get("accessionNumber", [])
                    primary_docs = filings_data.get("primaryDocument", [])
                    
                    for i in range(min(len(forms), len(dates))):
                        if forms[i] in filing_types:
                            filing_info = {
                                "form": forms[i],
                                "filing_date": dates[i],
                                "url": None
                            }
                            
                            # Construct URL if we have accession number and primary doc
                            if i < len(accession_numbers) and i < len(primary_docs):
                                accession = accession_numbers[i].replace("-", "")
                                doc = primary_docs[i]
                                filing_info["url"] = f"{self.sec_base_url}/Archives/edgar/data/{data['cik']}/{accession}/{doc}"
                            
                            recent_filings.append(filing_info)
                            
                            if len(recent_filings) >= limit:
                                break
            
            return {
                "ticker": ticker,
                "company_name": data.get("name", ""),
                "cik": data.get("cik", ""),
                "filings": recent_filings,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error searching SEC filings for {ticker}: {e}")
            return {"ticker": ticker, "success": False, "error": str(e)}
    
    def scrape_filing_content(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from an SEC filing URL.
        
        Args:
            url: URL of the SEC filing
            
        Returns:
            Dictionary with filing content
        """
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                logger.error(f"Error fetching filing: {response.status_code}")
                return {"success": False, "error": f"HTTP Error: {response.status_code}"}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content, removing scripts and styles
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text and clean it up
            text = soup.get_text(separator=' ')
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            content = '\n'.join(lines)
            
            # Try to extract filing date and type
            filing_date = None
            filing_type = None
            
            # Look for common date patterns in the content
            date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\w+ \d{1,2}, \d{4}\b'
            date_matches = re.findall(date_pattern, content[:1000])
            if date_matches:
                filing_date = date_matches[0]
            
            # Try to find filing type (10-K, 10-Q, 8-K, etc.)
            type_pattern = r'\b(10-K|10-Q|8-K|20-F|6-K|13F)\b'
            type_matches = re.findall(type_pattern, content[:1000])
            if type_matches:
                filing_type = type_matches[0]
            
            return {
                "url": url,
                "filing_type": filing_type,
                "filing_date": filing_date,
                "content": content,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error scraping filing from {url}: {e}")
            return {"url": url, "success": False, "error": str(e)}
    
    def extract_filing_sections(self, content: str, filing_type: str) -> Dict[str, str]:
        """
        Extract sections from filing content based on filing type.
        
        Args:
            content: The full text content of the filing
            filing_type: Type of filing (10-K, 10-Q, 8-K)
            
        Returns:
            Dictionary with section titles and content
        """
        sections = {}
        
        if filing_type in ["10-K", "10-Q"]:
            # Common section titles in 10-K and 10-Q filings
            section_patterns = [
                (r'Item\s+1A\.?\s+Risk\s+Factors', "Risk Factors"),
                (r'Item\s+7\.?\s+Management\'s\s+Discussion\s+and\s+Analysis', "MD&A"),
                (r'Item\s+3\.?\s+Quantitative\s+and\s+Qualitative\s+Disclosures\s+About\s+Market\s+Risk', "Market Risk"),
                (r'Item\s+1\.?\s+Business', "Business"),
                (r'Item\s+2\.?\s+Properties', "Properties"),
                (r'Item\s+7A\.?\s+Quantitative\s+and\s+Qualitative\s+Disclosures\s+About\s+Market\s+Risk', "Market Risk"),
                (r'Item\s+8\.?\s+Financial\s+Statements', "Financial Statements")
            ]
            
            # Find the starting positions of each section
            section_positions = []
            for pattern, name in section_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    section_positions.append((match.start(), name))
            
            # Sort by position
            section_positions.sort()
            
            # Extract each section's content
            for i in range(len(section_positions)):
                start_pos = section_positions[i][0]
                section_name = section_positions[i][1]
                
                # End position is either the start of next section or end of content
                end_pos = content.find("Item", start_pos + 100) if i < len(section_positions) - 1 else None
                if end_pos == -1:
                    end_pos = None
                
                section_content = content[start_pos:end_pos]
                sections[section_name] = section_content
        
        elif filing_type == "8-K":
            # For 8-K, try to extract the main event and details
            event_pattern = r'Item\s+[0-9\.]+\s+(.*?)(?=Item\s+[0-9\.]+|$)'
            events = re.findall(event_pattern, content)
            
            for i, event in enumerate(events):
                sections[f"Event {i+1}"] = event.strip()
        
        return sections
    
    def search_financial_news(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Search for financial news related to a query.
        
        Args:
            query: Search query (e.g., company name, ticker)
            limit: Maximum number of results
            
        Returns:
            Dictionary with news results
        """
        try:
            # Try Yahoo Finance news search
            url = f"{self.yahoo_finance_url}/quote/{query}/news"
            response = self.session.get(url)
            
            if response.status_code != 200:
                logger.error(f"Error fetching news: {response.status_code}")
                return {"success": False, "error": f"HTTP Error: {response.status_code}"}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []
            
            # Extract news items
            articles = soup.select('li[class*="js-stream-content"]')
            
            for article in articles[:limit]:
                title_elem = article.select_one('h3, a[class*="headline"]')
                link_elem = article.select_one('a[href^="https://"]')
                time_elem = article.select_one('span[class*="timing"]')
                source_elem = article.select_one('div[class*="source"]')
                
                if title_elem and link_elem:
                    news_item = {
                        "title": title_elem.get_text().strip(),
                        "url": link_elem['href'],
                        "timestamp": time_elem.get_text().strip() if time_elem else None,
                        "source": source_elem.get_text().strip() if source_elem else "Yahoo Finance"
                    }
                    news_items.append(news_item)
            
            return {
                "query": query,
                "news": news_items,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error searching news for {query}: {e}")
            return {"query": query, "success": False, "error": str(e)}
    
    def scrape_earnings_calendar(self, days: int = 7) -> Dict[str, Any]:
        """
        Scrape upcoming earnings calendar.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            Dictionary with earnings calendar data
        """
        try:
            # Get today's date and format it
            today = datetime.now()
            end_date = today + timedelta(days=days)
            
            # Format dates for Yahoo Finance
            today_str = today.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Yahoo Finance earnings calendar URL
            url = f"{self.yahoo_finance_url}/calendar/earnings?from={today_str}&to={end_str}&day=alldays"
            
            response = self.session.get(url)
            if response.status_code != 200:
                logger.error(f"Error fetching earnings calendar: {response.status_code}")
                return {"success": False, "error": f"HTTP Error: {response.status_code}"}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse the earnings table
            earnings_data = []
            tables = soup.select('table[class*="W(100%)"]')
            
            for table in tables:
                rows = table.select('tbody tr')
                
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 5:  # Make sure we have enough cells
                        try:
                            symbol = cells[0].get_text().strip()
                            company = cells[1].get_text().strip()
                            
                            # Extract date from the page or table header
                            date_header = soup.select_one('h3[class*="Py(10px)"]')
                            earnings_date = date_header.get_text().strip() if date_header else "Unknown Date"
                            
                            call_time = cells[2].get_text().strip()
                            eps_estimate = cells[3].get_text().strip()
                            
                            earnings_data.append({
                                "symbol": symbol,
                                "company": company,
                                "date": earnings_date,
                                "call_time": call_time,
                                "eps_estimate": eps_estimate
                            })
                        except Exception as e:
                            logger.error(f"Error parsing earnings row: {e}")
                            continue
            
            return {
                "start_date": today_str,
                "end_date": end_str,
                "earnings": earnings_data,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error scraping earnings calendar: {e}")
            return {"success": False, "error": str(e)}
    
    def get_asia_tech_news(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get news specifically focused on Asian tech companies.
        
        Args:
            limit: Maximum number of news items to return
            
        Returns:
            Dictionary with Asia tech news
        """
        try:
            # Combine news from multiple sources for better coverage
            asia_tech_queries = [
                "Asia tech",
                "TSMC",
                "Taiwan Semiconductor",
                "Samsung Electronics",
                "Alibaba",
                "Tencent",
                "Baidu"
            ]
            
            all_news = []
            
            for query in asia_tech_queries:
                news_results = self.search_financial_news(query, limit=3)
                if news_results["success"] and "news" in news_results:
                    all_news.extend(news_results["news"])
            
            # Remove duplicates based on title
            unique_news = []
            seen_titles = set()
            
            for item in all_news:
                if item["title"] not in seen_titles:
                    seen_titles.add(item["title"])
                    unique_news.append(item)
            
            # Sort by timestamp if available, otherwise keep original order
            # For simplicity in this implementation, we'll skip complex timestamp parsing
            
            return {
                "category": "Asia Tech News",
                "news": unique_news[:limit],
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error fetching Asia tech news: {e}")
            return {"success": False, "error": str(e)}
