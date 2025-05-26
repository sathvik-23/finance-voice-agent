FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    ffmpeg \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose ports for microservices
EXPOSE 8000  # FastAPI orchestrator
EXPOSE 8501  # Streamlit app
EXPOSE 8080  # API Agent
EXPOSE 8081  # Scraping Agent
EXPOSE 8082  # Retriever Agent
EXPOSE 8083  # Analysis Agent
EXPOSE 8084  # Language Agent
EXPOSE 8085  # Voice Agent

# Command to run when the container starts
CMD ["bash", "scripts/start_services.sh"]