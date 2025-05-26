# Finance Voice Agent

A voice-enabled financial assistant that uses OpenAI's speech-to-text, natural language processing, and text-to-speech APIs to provide real-time financial insights.

## Features

- 🎙️ **Voice Input**: Ask financial questions by speaking into the microphone
- 🔊 **Voice Output**: Receive answers in natural, human-like speech
- 💬 **Text Chat**: Interact with the assistant through a chat interface
- 📊 **Market Brief**: Get a daily overview of your portfolio and market conditions
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🔄 **API Key Rotation**: Automatically rotates through multiple API keys for reliability

## Architecture

The system consists of three main components:

1. **Streamlit App**: Web interface for user interaction
2. **Voice Processing**: Handles speech-to-text and text-to-speech operations
3. **Financial Assistant**: Processes queries and generates responses

## App Versions

This repository includes multiple versions of the application:

- **production_app.py**: Full version using OpenAI's GPT-4 models
- **economical_app.py**: Uses lower-cost OpenAI models (GPT-3.5, Whisper-1, TTS-1)
- **mock_app.py**: Completely offline version with simulated responses (no API calls)
- **multi_key_app.py**: Advanced version with API key rotation system

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
4. Run one of the app versions:
   ```
   streamlit run mock_app.py  # For offline demo
   # OR
   streamlit run multi_key_app.py  # For API key rotation
   # OR
   streamlit run economical_app.py  # For lower-cost models
   ```
5. Open the web interface at the URL provided in the terminal

## API Key Rotation

The multi_key_app.py version supports using multiple OpenAI API keys for increased reliability:

1. Open multi_key_app.py
2. Add your API keys to the API_KEYS list
3. The app will automatically rotate through these keys if one fails

See [API_KEY_ROTATION_GUIDE.md](API_KEY_ROTATION_GUIDE.md) for detailed instructions.

## Example Queries

- "What's our risk exposure in Asia tech stocks today?"
- "How are tech stocks performing?"
- "What's our portfolio allocation?"
- "Any significant news in the financial markets?"
- "Highlight any earnings surprises in our portfolio"

## Technologies Used

- [OpenAI Whisper API](https://platform.openai.com/docs/api-reference/audio/createTranscription) for speech-to-text
- [OpenAI GPT-4/3.5 API](https://platform.openai.com/docs/models/gpt-4) for natural language understanding
- [OpenAI TTS API](https://platform.openai.com/docs/api-reference/audio/createSpeech) for text-to-speech
- [FastAPI](https://fastapi.tiangolo.com/) for backend services
- [Streamlit](https://streamlit.io/) for the web interface
- [Streamlit WebRTC](https://github.com/whitphx/streamlit-webrtc) for audio recording

## License

This project is licensed under the MIT License - see the LICENSE file for details.
