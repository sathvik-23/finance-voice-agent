"""
Fallback Streamlit app for the Finance Voice Agent with lower-cost OpenAI models.
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
    
    # Model selection (lower cost models)
    model_option = st.selectbox(
        "Model",
        ["gpt-3.5-turbo", "whisper-1", "tts-1"],
        index=0
    )
    
    # Show last update time if available
    if "last_update" in st.session_state:
        st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # About section
    st.subheader("About")
    st.markdown("""
    This app uses:
    - OpenAI's GPT-3.5-Turbo for text generation (lower cost)
    - OpenAI's Whisper-1 for speech-to-text
    - OpenAI's TTS-1 for text-to-speech
    
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
# Function to process text query with lower-cost model
def process_text_query(query):
    try:
        # Use direct OpenAI API call instead of our expensive orchestrator
        import openai
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Financial data for context (hardcoded to avoid additional API calls)
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
        
        # Use GPT-3.5-Turbo instead of GPT-4
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
        
        # Generate voice response with lower-cost TTS model
        voice_response = generate_voice_response(text_response, voice_option)
        
        return {
            "text_response": text_response,
            "voice_response": voice_response
        }
    except Exception as e:
        st.error(f"Error processing query: {str(e)}")
        return {"text_response": f"Error processing query: {str(e)}"}

# Function to get market brief with lower-cost model
def get_market_brief():
    try:
        # Use direct OpenAI API call with GPT-3.5
        import openai
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Financial data for context (hardcoded to avoid additional API calls)
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
        
        # Use GPT-3.5-Turbo instead of GPT-4
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
        
        # Generate voice response with lower-cost TTS model
        voice_response = generate_voice_response(text_response, voice_option)
        
        return {
            "text_response": text_response,
            "voice_response": voice_response
        }
    except Exception as e:
        st.error(f"Error generating market brief: {str(e)}")
        return {"text_response": f"Error generating market brief: {str(e)}"}
# Function to generate voice response with lower-cost TTS model
def generate_voice_response(text, voice="alloy"):
    try:
        import openai
        from openai import OpenAI
        import tempfile
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as temp_file:
            # Use OpenAI's TTS-1 (lower cost) instead of TTS-1-HD
            response = client.audio.speech.create(
                model="tts-1",  # Lower cost model
                voice=voice,
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
    
    except Exception as e:
        st.error(f"Error generating voice response: {str(e)}")
        return None

# Function to process voice query with direct OpenAI API
def process_voice_query(audio_bytes):
    try:
        import openai
        from openai import OpenAI
        import tempfile
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
            temp_file.write(audio_bytes)
            temp_file.flush()
            
            # Use OpenAI's Whisper API for transcription
            with open(temp_file.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",  # This is already the lowest cost model
                    file=audio_file
                )
            
            transcribed_text = transcript.text
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
st.caption("Finance Voice Agent - Using economical OpenAI models (GPT-3.5, Whisper-1, TTS-1)")

if __name__ == "__main__":
    # This will run the Streamlit app
    pass
