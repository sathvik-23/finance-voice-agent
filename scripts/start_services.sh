#!/bin/bash

# Start the FastAPI orchestrator
python -m uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000 &

# Start agent microservices
python -m uvicorn agents.api_agent.service:app --host 0.0.0.0 --port 8080 &
python -m uvicorn agents.scraping_agent.service:app --host 0.0.0.0 --port 8081 &
python -m uvicorn agents.retriever_agent.service:app --host 0.0.0.0 --port 8082 &
python -m uvicorn agents.analysis_agent.service:app --host 0.0.0.0 --port 8083 &
python -m uvicorn agents.language_agent.service:app --host 0.0.0.0 --port 8084 &
python -m uvicorn agents.voice_agent.service:app --host 0.0.0.0 --port 8085 &

# Start the Streamlit app
streamlit run streamlit_app/app.py --server.port 8501 --server.address 0.0.0.0
