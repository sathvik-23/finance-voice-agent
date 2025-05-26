"""
Mock Finance Voice Agent - Simulates voice assistant functionality without API calls.
"""
import os
import json
import base64
import io
from datetime import datetime
import streamlit as st
import random
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np
import queue
import threading
import time

# App title and configuration
st.set_page_config(
    page_title="Finance Voice Agent (Mock)",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("Finance Voice Assistant")
st.subheader("Your AI-powered market brief companion (Mock Version)")

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
    
    # Mock mode explanation
    st.info("Mock Mode: No actual API calls are made to OpenAI. Responses are simulated.")
    
    # About section
    st.subheader("About")
    st.markdown("""
    This mock app simulates:
    - Text generation (without OpenAI GPT)
    - Speech-to-text (without OpenAI Whisper)
    - Text-to-speech (without OpenAI TTS)
    
    Ask financial questions by voice or text, and get simulated insights on your portfolio.
    """)

# Financial data for generating mock responses
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

# Mock responses for different query types
mock_responses = {
    "market_brief": "Today, your Asia tech allocation is 22% of AUM, up from 18% yesterday. TSMC beat estimates by 4%, Samsung missed by 2%. Regional sentiment is neutral with a cautionary tilt due to rising yields.",
    
    "risk_exposure": "Your current risk exposure in Asia tech stocks is 22% of your total portfolio, which is higher than your target allocation of 20%. This increase is primarily due to TSMC's strong performance which beat earnings estimates by 4%. Consider rebalancing to reduce exposure if you're concerned about regional volatility.",
    
    "earnings": "Recent earnings reports show mixed results. TSMC exceeded expectations with a 4% positive surprise, driven by strong demand for advanced chips. However, Samsung missed projections by 2%, citing weakened consumer electronics demand and inventory adjustments.",
    
    "portfolio": "Your current portfolio allocation is: 22% Asia tech (up from 18%), 35% US equities, 15% European markets, 18% fixed income, and 10% cash reserves. Total AUM stands at $1.25 billion USD.",
    
    "default": "Based on the current market data, Asian tech stocks show mixed performance. TSMC continues to outperform while Samsung faces challenges. Market sentiment remains cautious due to rising treasury yields, suggesting potential volatility ahead. Consider reviewing your current 22% allocation to this sector based on your risk tolerance."
}

# Function to simulate audio playback (just displays a message)
def autoplay_audio(audio_data=None):
    st.info("🔊 Mock audio would play here in a real implementation.")
# Function to generate mock text response based on query
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

# Function to process text query with mock response
def process_text_query(query):
    try:
        # Generate mock response based on query
        text_response = generate_mock_response(query)
        
        # Simulate a delay for realism
        with st.spinner("Processing query..."):
            time.sleep(1.5)  # Simulate API call delay
        
        return {
            "text_response": text_response
        }
    except Exception as e:
        st.error(f"Error processing query: {str(e)}")
        return {"text_response": f"Error processing query: {str(e)}"}

# Function to get mock market brief
def get_market_brief():
    try:
        # Use predefined market brief
        text_response = mock_responses["market_brief"]
        
        # Simulate a delay for realism
        with st.spinner("Fetching market data..."):
            time.sleep(1.5)  # Simulate API call delay
        
        return {
            "text_response": text_response
        }
    except Exception as e:
        st.error(f"Error generating market brief: {str(e)}")
        return {"text_response": f"Error generating market brief: {str(e)}"}

# Function to simulate voice query processing
def process_voice_query(audio_bytes=None):
    try:
        # Predefined mock transcriptions
        mock_transcriptions = [
            "What's our risk exposure in Asia tech stocks today?",
            "How are tech stocks performing?",
            "Tell me about recent earnings surprises",
            "What's our current portfolio allocation?",
            "Give me a market brief"
        ]
        
        # Randomly select a transcription
        transcribed_text = random.choice(mock_transcriptions)
        
        # Simulate a delay for realism
        with st.spinner("Transcribing audio..."):
            time.sleep(1.5)  # Simulate transcription delay
        
        st.success(f"Transcribed text: {transcribed_text}")
        
        # Process the transcribed text
        query_response = process_text_query(transcribed_text)
        
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
# Voice Input Section
st.subheader("Voice Input")
st.markdown("""
Speak your financial question into the microphone below. The system will simulate
transcribing your speech, analyzing your query, and responding both in text and voice.
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
    
    # Process the audio (mock processing)
    with st.spinner("Processing voice query..."):
        time.sleep(1)  # Simulate processing delay
        transcribed_text, response = process_voice_query()
        
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
                
                # Simulate audio playback
                autoplay_audio()

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
        
        # Simulate audio playback
        autoplay_audio()

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
    response = process_text_query(user_input)
    
    if response:
        # Add assistant message to chat
        st.session_state.messages.append({"role": "assistant", "content": response.get("text_response", "")})
        
        # Display assistant message
        with st.chat_message("assistant"):
            st.write(response.get("text_response", ""))
        
        # Simulate audio playback
        autoplay_audio()

# Footer
st.markdown("---")
st.caption("Finance Voice Agent - Mock Version (No API Calls)")

if __name__ == "__main__":
    # This will run the Streamlit app
    pass
