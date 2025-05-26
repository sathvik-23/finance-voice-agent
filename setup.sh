#!/bin/bash

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example. Please update with your API keys."
fi

# Initialize vector database (creates local FAISS index if not using Pinecone)
python data_ingestion/init_vector_db.py

# Run tests to ensure everything is set up correctly
pytest tests/

echo "Setup complete! You can now run the application using:"
echo "- Development mode: bash scripts/start_services.sh"
echo "- Docker: docker-compose up"
