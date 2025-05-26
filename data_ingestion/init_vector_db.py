"""
Initialize the vector database for the Finance Voice Agent.
"""
import os
import logging
import json
from typing import Dict, List, Any
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def initialize_vector_db():
    """Initialize the vector database."""
    logger.info("Initializing vector database...")
    
    # Check if Pinecone API key is available
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
    vector_index_name = os.getenv("VECTOR_INDEX_NAME", "finance_vector_index")
    
    if pinecone_api_key and pinecone_environment:
        logger.info("Pinecone API key found. Initializing Pinecone index...")
        try:
            import pinecone
            
            # Initialize Pinecone
            pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)
            
            # Check if index exists, create if it doesn't
            if vector_index_name not in pinecone.list_indexes():
                logger.info(f"Creating Pinecone index: {vector_index_name}")
                
                # Get embedding dimension
                embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                dummy_embedding = embedding_model.encode(["test"])[0]
                dimension = len(dummy_embedding)
                
                # Create index
                pinecone.create_index(
                    name=vector_index_name,
                    dimension=dimension,
                    metric="cosine"
                )
                logger.info(f"Pinecone index {vector_index_name} created with dimension {dimension}")
            else:
                logger.info(f"Pinecone index {vector_index_name} already exists")
                
            return {"success": True, "db_type": "pinecone", "index_name": vector_index_name}
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {e}")
            logger.info("Falling back to local FAISS index")
    else:
        logger.info("No Pinecone API key found. Using local FAISS index...")
    
    # Fallback to local FAISS index
    try:
        # Create directory for FAISS index if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Get embedding dimension
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        dummy_embedding = embedding_model.encode(["test"])[0]
        dimension = len(dummy_embedding)
        
        # Create FAISS index
        index = faiss.IndexFlatL2(dimension)
        
        # Save empty index
        faiss.write_index(index, "data/finance_vector_index.faiss")
        
        # Save metadata
        with open("data/finance_vector_metadata.json", "w") as f:
            json.dump({
                "dimension": dimension,
                "model": "all-MiniLM-L6-v2",
                "documents": [],
                "created_at": pd.Timestamp.now().isoformat()
            }, f)
        
        logger.info(f"Local FAISS index created with dimension {dimension}")
        return {"success": True, "db_type": "faiss", "index_path": "data/finance_vector_index.faiss"}
        
    except Exception as e:
        logger.error(f"Error initializing local FAISS index: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = initialize_vector_db()
    if result["success"]:
        logger.info(f"Vector database initialized: {result['db_type']}")
    else:
        logger.error(f"Vector database initialization failed: {result.get('error', 'Unknown error')}")
