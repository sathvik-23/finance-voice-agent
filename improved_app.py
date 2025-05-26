"""
Production Streamlit app for the Finance Voice Agent with OpenAI integration.
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
    
    # Show last update time if available
    if "last_update" in st.session_state:
        st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # About section
    st.subheader("About")
    st.markdown("""
    This app uses:
    - OpenAI's GPT models for text generation
    - OpenAI's Whisper for speech-to-text
    - OpenAI's TTS for text-to-speech
    
    Ask financial questions by voice or text, and get real-time insights on your portfolio.
    """)

# Function to play audio
def autoplay_audio(audio_base64):
    audio_html = f"""
        <audio autoplay controls>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# Function to process text query
def process_text_query(query):
    try:
        response = requests.post(
            "http://localhost:8001/query",
            json={"query": query},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result.get("data")
            else:
                st.error(f"Error from orchestrator: {result.get('error')}")
        else:
            st.error(f"Error status code: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Error processing query: {e}")
        return None

# Function to get market brief
def get_market_brief():
    try:
        response = requests.post(
            "http://localhost:8001/market-brief",
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result.get("data")
            else:
                st.error(f"Error from orchestrator: {result.get('error')}")
        else:
            st.error(f"Error status code: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Error getting market brief: {e}")
        return None

# Function to process voice query (using direct REST API)
def process_voice_query(audio_bytes):
    try:
        # Convert audio to base64
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        # Send to the transcription endpoint
        response = requests.post(
            "http://localhost:8001/transcribe",
            json=audio_base64,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                transcribed_text = result.get("data", {}).get("text", "")
                st.success(f"Transcribed text: {transcribed_text}")
                
                # Now, process this text query
                query_response = process_text_query(transcribed_text)
                
                return transcribed_text, query_response
            else:
                st.error(f"Error from transcription: {result.get('error')}")
        else:
            st.error(f"Error status code from transcription: {response.status_code}")
        
        return None, None
    
    except Exception as e:
        st.error(f"Error processing voice query: {e}")
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
                    
                    # Play the voice response if available
                    if "voice_response" in response and "audio_data" in response.get("voice_response", {}):
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
            
            # Play the voice response if available
            if "voice_response" in market_brief and "audio_data" in market_brief.get("voice_response", {}):
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
            
            # Play the voice response if available
            if "voice_response" in response and "audio_data" in response.get("voice_response", {}):
                st.success("Playing audio response...")
                autoplay_audio(response["voice_response"]["audio_data"])

# Footer
st.markdown("---")
st.caption("Finance Voice Agent - Powered by OpenAI's GPT, Whisper, and TTS APIs")

if __name__ == "__main__":
    # This will run the Streamlit app
    pass
