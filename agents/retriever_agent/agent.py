documents[doc_idx]
                chunk = doc["chunks"][doc_chunk_idx]
                metadata = doc["chunk_metadatas"][doc_chunk_idx]
                
                # Apply filters if specified
                if filters:
                    skip = False
                    for key, value in filters.items():
                        if key not in metadata or metadata[key] != value:
                            skip = True
                            break
                    if skip:
                        continue
                
                # Check if we already have a result from this document
                if doc_idx in seen_docs:
                    continue
                seen_docs.add(doc_idx)
                
                # Add to results
                results.append({
                    "text": chunk,
                    "metadata": metadata,
                    "distance": float(distances[0][i]),
                    "document_id": doc_idx,
                    "chunk_id": doc_chunk_idx
                })
                
                if len(results) >= k:
                    break
            
            # Calculate confidence score (inverse of distance)
            for result in results:
                result["confidence"] = 1.0 / (1.0 + result["distance"])
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_chunks": self.index.ntotal,
                "confidence": results[0]["confidence"] if results else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error searching index: {e}")
            return {"success": False, "error": str(e)}
    
    def get_document(self, document_id: int) -> Dict[str, Any]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with document data
        """
        try:
            if document_id < 0 or document_id >= len(self.documents):
                return {"success": False, "error": "Invalid document ID"}
            
            doc = self.documents[document_id]
            return {
                "success": True,
                "document": {
                    "text": doc["text"],
                    "metadata": doc["metadata"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def clear_index(self) -> Dict[str, Any]:
        """
        Clear the index.
        
        Returns:
            Dictionary with result status
        """
        try:
            # Reinitialize index
            self.initialize_index()
            self.documents = []
            self.document_sources = {}
            self.company_data = {}
            
            return {"success": True, "message": "Index cleared"}
            
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            return {"success": False, "error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Dictionary with index stats
        """
        try:
            # Count documents by source
            source_counts = {source: len(docs) for source, docs in self.document_sources.items()}
            
            # Count documents by company
            company_counts = {ticker: len(docs) for ticker, docs in self.company_data.items()}
            
            return {
                "success": True,
                "total_documents": len(self.documents),
                "total_chunks": self.index.ntotal,
                "sources": source_counts,
                "companies": company_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"success": False, "error": str(e)}
            
    def search_by_company(self, 
                          ticker: str, 
                          query: str, 
                          k: int = 5) -> Dict[str, Any]:
        """
        Search for documents about a specific company.
        
        Args:
            ticker: Company ticker symbol
            query: Search query
            k: Number of results
            
        Returns:
            Dictionary with search results
        """
        try:
            if ticker not in self.company_data:
                return {"success": False, "error": f"No data for company {ticker}"}
            
            filters = {"ticker": ticker}
            return self.search(query, k, filters)
            
        except Exception as e:
            logger.error(f"Error searching for company {ticker}: {e}")
            return {"success": False, "error": str(e)}
    
    def add_financial_data(self, 
                          data: Dict[str, Any], 
                          source: str) -> Dict[str, Any]:
        """
        Add structured financial data to the index.
        
        Args:
            data: Financial data dictionary
            source: Source name (e.g., 'yahoo_finance', 'alpha_vantage')
            
        Returns:
            Dictionary with indexing results
        """
        try:
            # Convert data to text format for indexing
            text = json.dumps(data, indent=2)
            
            # Create metadata
            metadata = {
                "source": source,
                "type": "financial_data",
                "date": datetime.now().isoformat(),
            }
            
            # Add ticker if available
            if "symbol" in data:
                metadata["ticker"] = data["symbol"]
            
            # Add to index
            return self.add_document(text, metadata)
            
        except Exception as e:
            logger.error(f"Error adding financial data: {e}")
            return {"success": False, "error": str(e)}
    
    def add_filing(self, 
                  filing_data: Dict[str, Any], 
                  content: str) -> Dict[str, Any]:
        """
        Add an SEC filing to the index.
        
        Args:
            filing_data: Filing metadata
            content: Filing text content
            
        Returns:
            Dictionary with indexing results
        """
        try:
            # Create metadata
            metadata = {
                "source": "sec_filing",
                "type": "filing",
                "ticker": filing_data.get("ticker", ""),
                "filing_type": filing_data.get("form", ""),
                "filing_date": filing_data.get("filing_date", ""),
                "url": filing_data.get("url", "")
            }
            
            # Add to index
            return self.add_document(content, metadata)
            
        except Exception as e:
            logger.error(f"Error adding filing: {e}")
            return {"success": False, "error": str(e)}
    
    def add_news_article(self, 
                        article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a news article to the index.
        
        Args:
            article: News article data
            
        Returns:
            Dictionary with indexing results
        """
        try:
            # Try to extract content if not provided
            content = article.get("content", article.get("title", ""))
            
            # Create metadata
            metadata = {
                "source": "news",
                "type": "article",
                "title": article.get("title", ""),
                "date": article.get("timestamp", datetime.now().isoformat()),
                "url": article.get("url", ""),
                "publisher": article.get("source", "")
            }
            
            # Add ticker if available
            if "ticker" in article:
                metadata["ticker"] = article["ticker"]
                
            # Add to index
            return self.add_document(content, metadata, chunk_size=256)  # Smaller chunks for news
            
        except Exception as e:
            logger.error(f"Error adding news article: {e}")
            return {"success": False, "error": str(e)}
    
    def query_financial_context(self, 
                              query: str, 
                              tickers: Optional[List[str]] = None, 
                              k: int = 5) -> Dict[str, Any]:
        """
        Get financial context for a query.
        
        Args:
            query: User query
            tickers: List of ticker symbols to focus on
            k: Number of results
            
        Returns:
            Dictionary with contextualized search results
        """
        try:
            results = []
            
            # If tickers are specified, search for each one
            if tickers:
                for ticker in tickers:
                    ticker_results = self.search_by_company(ticker, query, k=2)
                    if ticker_results["success"] and ticker_results["results"]:
                        results.extend(ticker_results["results"])
            
            # Add general search results
            general_results = self.search(query, k=k)
            if general_results["success"] and general_results["results"]:
                for result in general_results["results"]:
                    # Avoid duplicates
                    if not any(r["document_id"] == result["document_id"] for r in results):
                        results.append(result)
            
            # Sort by confidence
            results.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Limit to k results
            results = results[:k]
            
            # Calculate overall confidence
            overall_confidence = sum(r["confidence"] for r in results) / len(results) if results else 0.0
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "tickers": tickers,
                "confidence": overall_confidence
            }
            
        except Exception as e:
            logger.error(f"Error getting financial context: {e}")
            return {"success": False, "error": str(e)}
