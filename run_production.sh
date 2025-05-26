#!/bin/bash

# Start the Production Finance Voice Agent

# Check if the environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    
    # Check which virtual environment exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "venv311" ]; then
        source venv311/bin/activate
    elif [ -d "myenv" ]; then
        source myenv/bin/activate
    else
        echo "No virtual environment found. Creating one..."
        python3 -m venv venv
        source venv/bin/activate
        
        # Install requirements
        pip install -r requirements.txt
    fi
fi

# Check if the required API keys are set
if [ -z "$OPENAI_API_KEY" ]; then
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
        echo "Loaded environment variables from .env file"
    else
        echo "Error: OPENAI_API_KEY not set and .env file not found"
        exit 1
    fi
fi

# Start the voice agent service
echo "Starting Voice Agent service..."
python -m agents.voice_agent.production_service &
VOICE_PID=$!
echo "Voice Agent running with PID: $VOICE_PID"

# Start the orchestrator
echo "Starting Orchestrator service..."
python production_orchestrator.py &
ORCHESTRATOR_PID=$!
echo "Orchestrator running with PID: $ORCHESTRATOR_PID"

# Start the Streamlit app
echo "Starting Streamlit app..."
streamlit run production_app.py &
STREAMLIT_PID=$!
echo "Streamlit app running with PID: $STREAMLIT_PID"

echo "All services are running!"
echo "Access the Finance Voice Agent at: http://localhost:8501"

# Define a function to handle cleanup
cleanup() {
    echo "Shutting down services..."
    kill $VOICE_PID $ORCHESTRATOR_PID $STREAMLIT_PID
    exit 0
}

# Trap for Ctrl+C to properly clean up
trap cleanup SIGINT

# Wait for user to press Ctrl+C
echo "Press Ctrl+C to stop all services"
wait
