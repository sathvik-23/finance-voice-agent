# Finance Voice Agent

A production-ready financial voice assistant that uses OpenAI's APIs for speech-to-text and text-to-speech functionality.

## Features

- 🎙️ **Voice Input**: Ask financial questions by speaking into the microphone
- 🔊 **Voice Output**: Receive answers in natural, human-like speech
- 💬 **Text Chat**: Interact with the assistant through a chat interface
- 📊 **Market Brief**: Get a daily overview of your portfolio and market conditions
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Architecture

The system consists of three main components:

1. **Streamlit App**: Web interface for user interaction
2. **Orchestrator**: Central service that processes queries and coordinates responses
3. **Voice Agent Service**: Handles speech-to-text and text-to-speech operations

## Technologies Used

- [OpenAI Whisper API](https://platform.openai.com/docs/api-reference/audio/createTranscription) for speech-to-text
- [OpenAI GPT-4o mini TTS API](https://platform.openai.com/docs/api-reference/audio/createSpeech) for text-to-speech
- [OpenAI GPT-4o mini](https://platform.openai.com/docs/models/gpt-4o-mini) for natural language understanding
- [FastAPI](https://fastapi.tiangolo.com/) for backend services
- [Streamlit](https://streamlit.io/) for the web interface

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your environment variables in `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```
4. Run the system:
   ```
   ./run_production.sh
   ```
5. Open the web interface at [http://localhost:8501](http://localhost:8501)

## Usage

1. Click the microphone button and ask a financial question
2. The system will transcribe your speech, process your query, and respond with both text and speech
3. Alternatively, type your question in the chat input
4. Click "Get Market Brief" to receive a summary of your portfolio and market conditions

## Example Queries

- "What's our risk exposure in Asia tech stocks today?"
- "How are tech stocks performing?"
- "What's our portfolio allocation?"
- "Any significant news in the financial markets?"
- "Highlight any earnings surprises in our portfolio"

## Production Deployment

For production deployment, consider:

1. Setting up proper authentication
2. Securing API keys
3. Using HTTPS
4. Implementing rate limiting
5. Setting up monitoring and logging

## License

This project is licensed under the MIT License - see the LICENSE file for details.
