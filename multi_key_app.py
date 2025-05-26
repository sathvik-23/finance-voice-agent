"""
Finance Voice Agent with API Key Rotation - Uses multiple API keys for redundancy.
"""
import os
import json
import base64
import io
from datetime import datetime
import streamlit as st
import requests
from dotenv import load_dotenv
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np
import queue
import threading
import time
import random
from openai import OpenAI, APIError, RateLimitError

# Load environment variables
load_dotenv()

# App title and configuration
st.set_page_config(
    page_title="Finance Voice Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("Finance Voice Assistant")
st.subheader("Your AI-powered market brief companion")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "audio_frames" not in st.session_state:
    st.session_state.audio_frames = []
    
if "recording" not in st.session_state:
    st.session_state.recording = False
    
if "recorded_audio" not in st.session_state:
    st.session_state.recorded_audio = None
    
if "api_key_index" not in st.session_state:
    st.session_state.api_key_index = 0
    
if "failed_keys" not in st.session_state:
    st.session_state.failed_keys = set()

# API Key Management
# In a production app, you'd store these securely, not in the code
API_KEYS = [
    # Primary key from .env file
    os.getenv("OPENAI_API_KEY", ""),
    
    # Add your additional API keys here
    # "sk-abc123...",
    # "sk-def456...",
    # etc.
]

# Mock financial data for when all API keys fail
financial_data = {
    "portfolio": {
        "asia_tech_allocation": 22,
        "previous_allocation": 18,
        "total_aum": 1250000000,
        "currency": "USD"
    },
    "market_data": {
        "tsmc": {
            "ticker": "TSM",
            "earnings_surprise": 4.0,
            "direction": "positive"
        },
        "samsung": {
            "ticker": "005930.KS",
            "earnings_surprise": -2.0,
            "direction": "negative"
        },
        "market_sentiment": "neutral with caution",
        "yields": {
            "10y_treasury": 4.2,
            "trend": "rising"
        }
    }
}

# Mock responses for when all API keys fail
mock_responses = {
    "market_brief": "Today, your Asia tech allocation is 22% of AUM, up from 18% yesterday. TSMC beat estimates by 4%, Samsung missed by 2%. Regional sentiment is neutral with a cautionary tilt due to rising yields.",
    "risk_exposure": "Your current risk exposure in Asia tech stocks is 22% of your total portfolio, which is higher than your target allocation of 20%. This increase is primarily due to TSMC's strong performance which beat earnings estimates by 4%. Consider rebalancing to reduce exposure if you're concerned about regional volatility.",
    "earnings": "Recent earnings reports show mixed results. TSMC exceeded expectations with a 4% positive surprise, driven by strong demand for advanced chips. However, Samsung missed projections by 2%, citing weakened consumer electronics demand and inventory adjustments.",
    "portfolio": "Your current portfolio allocation is: 22% Asia tech (up from 18%), 35% US equities, 15% European markets, 18% fixed income, and 10% cash reserves. Total AUM stands at $1.25 billion USD.",
    "default": "Based on the current market data, Asian tech stocks show mixed performance. TSMC continues to outperform while Samsung faces challenges. Market sentiment remains cautious due to rising treasury yields, suggesting potential volatility ahead. Consider reviewing your current 22% allocation to this sector based on your risk tolerance."
}
# Function to get next working API key
def get_next_api_key():
    """Rotate through API keys until finding one that works or exhausting all options."""
    # Reset failed keys if we've tried all keys
    if len(st.session_state.failed_keys) >= len(API_KEYS):
        st.session_state.failed_keys = set()
        st.warning("All API keys have failed. Using mock responses.")
        return None
    
    # Try keys in order, skipping known failed ones
    original_index = st.session_state.api_key_index
    
    while True:
        # Get current key
        current_key = API_KEYS[st.session_state.api_key_index]
        
        # Skip if this key is known to have failed
        if current_key in st.session_state.failed_keys:
            # Move to next key
            st.session_state.api_key_index = (st.session_state.api_key_index + 1) % len(API_KEYS)
            
            # If we've tried all keys, break
            if st.session_state.api_key_index == original_index:
                return None
            continue
        
        # Return the current key and increment the index for next time
        next_key = current_key
        st.session_state.api_key_index = (st.session_state.api_key_index + 1) % len(API_KEYS)
        return next_key

def mark_key_as_failed(api_key):
    """Mark an API key as failed."""
    if api_key:
        st.session_state.failed_keys.add(api_key)
        st.warning(f"API key failed. {len(API_KEYS) - len(st.session_state.failed_keys)} keys remaining.")

# Function to play audio
def autoplay_audio(audio_base64):
    audio_html = f"""
        <audio autoplay controls>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# Function to generate mock response based on query
def generate_mock_response(query):
    query = query.lower()
    
    if "market brief" in query:
        return mock_responses["market_brief"]
    elif "risk" in query and "exposure" in query:
        return mock_responses["risk_exposure"]
    elif "earning" in query or "surprise" in query:
        return mock_responses["earnings"]
    elif "portfolio" in query or "allocation" in query:
        return mock_responses["portfolio"]
    else:
        return mock_responses["default"]

# Function to process text query with API key rotation
def process_text_query(query):
    try:
        # Get next available API key
        api_key = get_next_api_key()
        
        if api_key:
            try:
                # Use OpenAI API with the current key
                client = OpenAI(api_key=api_key)
                
                # Use GPT-3.5-Turbo (cheaper model)
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Lower cost model
                    messages=[
                        {"role": "system", "content": """You are a financial assistant AI. 
                        Analyze the query to understand what financial information is being requested.
                        Respond with concise, professional financial insights."""},
                        {"role": "user", "content": f"Query: {query}\n\nCurrent portfolio data: {json.dumps(financial_data)}"}
                    ]
                )
                
                # Get the response text
                text_response = completion.choices[0].message.content
                
                # Generate voice response
                voice_response = generate_voice_response(text_response, api_key)
                
                return {
                    "text_response": text_response,
                    "voice_response": voice_response,
                    "mock": False
                }
            
            except (APIError, RateLimitError, Exception) as e:
                # Mark this key as failed
                mark_key_as_failed(api_key)
                
                # Try again with a different key
                return process_text_query(query)
        
        # If no working keys, use mock response
        text_response = generate_mock_response(query)
        return {
            "text_response": text_response,
            "mock": True
        }
    
    except Exception as e:
        st.error(f"Error processing query: {str(e)}")
        return {"text_response": f"Error processing query: {str(e)}", "mock": True}
# Function to generate voice response with API key rotation
def generate_voice_response(text, api_key=None):
    try:
        if not api_key:
            api_key = get_next_api_key()
            
        if api_key:
            try:
                import tempfile
                client = OpenAI(api_key=api_key)
                
                # Create a temporary file
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as temp_file:
                    # Use OpenAI's TTS-1 (lower cost)
                    response = client.audio.speech.create(
                        model="tts-1",  # Lower cost model
                        voice=st.session_state.get("voice_option", "alloy"),
                        input=text
                    )
                    
                    # Save to temporary file
                    response.stream_to_file(temp_file.name)
                    
                    # Read the file back
                    with open(temp_file.name, "rb") as audio_file:
                        audio_data = audio_file.read()
                    
                    # Convert to base64 for web playback
                    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                    
                    return {
                        "audio_data": audio_base64,
                        "format": "mp3"
                    }
            
            except (APIError, RateLimitError, Exception) as e:
                # Mark this key as failed
                mark_key_as_failed(api_key)
                
                # Try again with a different key
                return generate_voice_response(text)
        
        # If no working keys, return None (no voice response)
        return None
    
    except Exception as e:
        st.error(f"Error generating voice response: {str(e)}")
        return None

# Function to get market brief with API key rotation
def get_market_brief():
    try:
        # Get next available API key
        api_key = get_next_api_key()
        
        if api_key:
            try:
                # Use OpenAI API with the current key
                client = OpenAI(api_key=api_key)
                
                # Use GPT-3.5-Turbo (cheaper model)
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Lower cost model
                    messages=[
                        {"role": "system", "content": """You are a financial assistant AI.
                        Generate a concise market brief focusing on Asia tech exposure and recent earnings surprises.
                        Use the provided financial data to inform your response."""},
                        {"role": "user", "content": f"Generate a market brief. Financial data: {json.dumps(financial_data)}"}
                    ]
                )
                
                # Get the response text
                text_response = completion.choices[0].message.content
                
                # Generate voice response
                voice_response = generate_voice_response(text_response, api_key)
                
                return {
                    "text_response": text_response,
                    "voice_response": voice_response,
                    "mock": False
                }
            
            except (APIError, RateLimitError, Exception) as e:
                # Mark this key as failed
                mark_key_as_failed(api_key)
                
                # Try again with a different key
                return get_market_brief()
        
        # If no working keys, use mock response
        text_response = mock_responses["market_brief"]
        return {
            "text_response": text_response,
            "mock": True
        }
    
    except Exception as e:
        st.error(f"Error generating market brief: {str(e)}")
        return {"text_response": f"Error generating market brief: {str(e)}", "mock": True}
# Function to process voice query with API key rotation
def process_voice_query(audio_bytes):
    try:
        # Get next available API key
        api_key = get_next_api_key()
        
        if api_key:
            try:
                import tempfile
                client = OpenAI(api_key=api_key)
                
                # Create a temporary file for the audio
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                    temp_file.write(audio_bytes)
                    temp_file.flush()
                    
                    # Use OpenAI's Whisper API for transcription
                    with open(temp_file.name, "rb") as audio_file:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )
                    
                    transcribed_text = transcript.text
                    st.success(f"Transcribed text: {transcribed_text}")
                    
                    # Process the transcribed text
                    query_response = process_text_query(transcribed_text)
                    
                    return transcribed_text, query_response
            
            except (APIError, RateLimitError, Exception) as e:
                # Mark this key as failed
                mark_key_as_failed(api_key)
                
                # Try again with a different key
                return process_voice_query(audio_bytes)
        
        # If no working keys, use mock transcription
        mock_transcriptions = [
            "What's our risk exposure in Asia tech stocks today?",
            "How are tech stocks performing?",
            "Tell me about recent earnings surprises",
            "What's our current portfolio allocation?",
            "Give me a market brief"
        ]
        
        # Randomly select a transcription
        transcribed_text = random.choice(mock_transcriptions)
        st.success(f"Transcribed text (mock): {transcribed_text}")
        
        # Process with mock response
        text_response = generate_mock_response(transcribed_text)
        query_response = {"text_response": text_response, "mock": True}
        
        return transcribed_text, query_response
    
    except Exception as e:
        st.error(f"Error processing voice query: {str(e)}")
        return None, None

# Audio recording using WebRTC
class AudioProcessor:
    def __init__(self):
        self.audio_buffer = queue.Queue()
        self.audio_frames = []
        self.recording = False
        
    def start_recording(self):
        self.recording = True
        self.audio_frames = []
        
    def stop_recording(self):
        self.recording = False
        return self.audio_frames
        
    def process_audio(self, frame):
        if self.recording:
            sound = frame.to_ndarray()
            self.audio_frames.append(sound)
        return frame

audio_processor = AudioProcessor()

# Sidebar
with st.sidebar:
    st.header("Options")
    
    # Show a simple get market brief button
    update_data = st.button("Get Market Brief")
    
    # Voice selection
    voice_option = st.selectbox(
        "Voice",
        ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        index=0
    )
    st.session_state.voice_option = voice_option
    
    # API key status
    st.subheader("API Key Status")
    if API_KEYS and API_KEYS[0]:
        total_keys = len(API_KEYS)
        failed_keys = len(st.session_state.failed_keys)
        working_keys = total_keys - failed_keys
        
        st.write(f"Total API Keys: {total_keys}")
        st.write(f"Working Keys: {working_keys}")
        st.write(f"Failed Keys: {failed_keys}")
        
        if failed_keys > 0:
            if st.button("Reset Failed Keys"):
                st.session_state.failed_keys = set()
                st.success("All keys reset!")
    else:
        st.error("No API keys configured. Using mock mode only.")
    
    # About section
    st.subheader("About")
    st.markdown("""
    This app uses:
    - Multiple OpenAI API keys for redundancy
    - Falls back to mock mode when all keys fail
    - GPT-3.5-Turbo for text generation
    - Whisper-1 for speech-to-text
    - TTS-1 for text-to-speech
    
    Ask financial questions by voice or text, and get insights on your portfolio.
    """)
# Voice Input Section
st.subheader("Voice Input")
st.markdown("""
Speak your financial question into the microphone below. The system will transcribe
your speech, analyze your query, and respond both in text and voice.
""")

# Recording controls
col1, col2 = st.columns(2)
start_button = col1.button("Start Recording")
stop_button = col2.button("Stop Recording")

# Handle recording logic
if start_button:
    st.session_state.recording = True
    audio_processor.start_recording()
    st.info("Recording started... Speak your question")
    
if stop_button and st.session_state.recording:
    st.session_state.recording = False
    audio_frames = audio_processor.stop_recording()
    
    # Convert audio frames to bytes
    if audio_frames:
        # Convert audio frames to a single audio file
        import io
        import wave
        import numpy as np
        
        # Concatenate all frames
        all_audio = np.concatenate(audio_frames, axis=0)
        
        # Create an in-memory WAV file
        audio_buffer = io.BytesIO()
        with wave.open(audio_buffer, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(48000)  # Sample rate
            wf.writeframes((all_audio * 32767).astype(np.int16).tobytes())
        
        audio_bytes = audio_buffer.getvalue()
        
        # Process the audio
        with st.spinner("Processing voice query..."):
            transcribed_text, response = process_voice_query(audio_bytes)
            
            if transcribed_text:
                # Add user message to chat
                st.session_state.messages.append({"role": "user", "content": transcribed_text})
                
                # Display user message
                with st.chat_message("user"):
                    st.write(transcribed_text)
                
                if response:
                    # Add assistant message to chat
                    st.session_state.messages.append({"role": "assistant", "content": response.get("text_response", "")})
                    
                    # Display assistant message
                    with st.chat_message("assistant"):
                        st.write(response.get("text_response", ""))
                        
                        # Indicate if this was a mock response
                        if response.get("mock", False):
                            st.caption("(Mock response - no API keys available)")
                    
                    # Play the voice response if available
                    if not response.get("mock", False) and "voice_response" in response and "audio_data" in response.get("voice_response", {}):
                        st.success("Playing audio response...")
                        autoplay_audio(response["voice_response"]["audio_data"])
    else:
        st.warning("No audio recorded. Please try again.")

# WebRTC streamer (only processes audio)
webrtc_ctx = webrtc_streamer(
    key="finance-voice-agent",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=lambda: audio_processor,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"video": False, "audio": True},
)

# Get market brief if button clicked
if update_data:
    with st.spinner("Fetching latest market data..."):
        market_brief = get_market_brief()
        if market_brief:
            st.session_state.last_update = datetime.now()
            
            # Add to conversation
            st.session_state.messages.append({
                "role": "assistant", 
                "content": market_brief.get("text_response", "")
            })
            
            # Display the response
            with st.chat_message("assistant"):
                st.write(market_brief.get("text_response", ""))
                
                # Indicate if this was a mock response
                if market_brief.get("mock", False):
                    st.caption("(Mock response - no API keys available)")
            
            # Play the voice response if available
            if not market_brief.get("mock", False) and "voice_response" in market_brief and "audio_data" in market_brief.get("voice_response", {}):
                st.success("Playing audio response...")
                autoplay_audio(market_brief["voice_response"]["audio_data"])
# Chat interface
st.subheader("Chat History")
chat_container = st.container()

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Text input for manual queries
user_input = st.chat_input("Type your financial question here...")

# Process text input
if user_input:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Process query
    with st.spinner("Processing..."):
        response = process_text_query(user_input)
        
        if response:
            # Add assistant message to chat
            st.session_state.messages.append({"role": "assistant", "content": response.get("text_response", "")})
            
            # Display assistant message
            with st.chat_message("assistant"):
                st.write(response.get("text_response", ""))
                
                # Indicate if this was a mock response
                if response.get("mock", False):
                    st.caption("(Mock response - no API keys available)")
            
            # Play the voice response if available
            if not response.get("mock", False) and "voice_response" in response and "audio_data" in response.get("voice_response", {}):
                st.success("Playing audio response...")
                autoplay_audio(response["voice_response"]["audio_data"])

# Instructions for adding API keys
if not API_KEYS or not API_KEYS[0]:
    st.warning("""
    ### How to Add API Keys
    
    To use this app with real OpenAI functionality, add your API keys to the `API_KEYS` list at the top of the code:
    
    ```python
    API_KEYS = [
        # Primary key from .env file
        os.getenv("OPENAI_API_KEY", ""),
        
        # Add your additional API keys here
        "sk-abc123...",
        "sk-def456...",
        # etc.
    ]
    ```
    
    The app will automatically rotate through these keys if one fails or exceeds its quota.
    """)

# Footer
st.markdown("---")
st.caption("Finance Voice Agent - With API Key Rotation")

if __name__ == "__main__":
    # This will run the Streamlit app
    pass
