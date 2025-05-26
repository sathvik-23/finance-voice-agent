"""
Improved Streamlit app for the Finance Voice Agent with Enhanced Fallback Mode.
"""
import os
import json
import base64
import io
from datetime import datetime
import streamlit as st
import requests
from dotenv import load_dotenv

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

# Sidebar
with st.sidebar:
    st.header("Options")
    
    # Show a simple get market brief button
    update_data = st.button("Get Market Brief")
    
    # Show last update time if available
    if "last_update" in st.session_state:
        st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # About section
    st.subheader("About")
    st.markdown("""
    This app is running in demo mode due to API quota limitations.
    
    In a production environment, it would use:
    - OpenAI's GPT models for text generation
    - OpenAI's Whisper for speech-to-text
    - OpenAI's TTS for text-to-speech
    
    Currently, it uses simulated responses but still demonstrates the core functionality.
    """)

# Function to play audio (not used in fallback mode, but kept for future use)
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
        st.info(f"Sending query to orchestrator: {query}")
        response = requests.post(
            "http://localhost:8001/query",
            json={"query": query},
            timeout=10  # Shorter timeout for fallback mode
        )
        st.info(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            st.info(f"Response success: {result.get('success')}")
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
            timeout=10  # Shorter timeout for fallback mode
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

# Function to process voice query in fallback mode
def process_voice_query(audio_bytes):
    try:
        # Convert audio to base64
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        # Send to the fallback transcription endpoint
        response = requests.post(
            "http://localhost:8001/transcribe",
            json=audio_base64,
            timeout=10  # Shorter timeout for fallback mode
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

# Add a voice input feature
st.subheader("Voice Input")
st.markdown("""
Speak your question into the microphone below. In demo mode, the transcription is simulated
based on the length of your recording.
""")
audio_bytes = st.audio_recorder(key="audio_recorder")

# Process voice input
if audio_bytes:
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
                
                # Play the voice response if available (not in fallback mode)
                if "voice_response" in response and "audio_data" in response.get("voice_response", {}):
                    st.success("Playing audio response...")
                    autoplay_audio(response["voice_response"]["audio_data"])
                elif response.get("fallback_mode"):
                    st.info("Audio response not available in demo mode")

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
            
            # Note about audio in demo mode
            st.info("Audio response not available in demo mode")

# Chat interface
st.subheader("Chat History")
chat_container = st.container()

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Text input for manual queries
user_input = st.chat_input("Type your question here...")

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
            
            # Note about audio in demo mode
            if response.get("fallback_mode"):
                st.info("Audio response not available in demo mode")

# Footer
st.markdown("---")
st.caption("Finance Voice Agent - Demo Mode with Voice Input Simulation")
