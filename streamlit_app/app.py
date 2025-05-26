"""
Streamlit app for the Finance Voice Agent.
"""
import os
import json
import base64
import asyncio
from datetime import datetime
import streamlit as st
import requests
import httpx
from dotenv import load_dotenv
from io import BytesIO
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

# Load environment variables
load_dotenv()

# Service URLs
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
API_AGENT_URL = os.getenv("API_AGENT_URL", "http://localhost:8080")
VOICE_AGENT_URL = os.getenv("VOICE_AGENT_URL", "http://localhost:8085")

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

if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

if "market_data" not in st.session_state:
    st.session_state.market_data = None

if "last_update" not in st.session_state:
    st.session_state.last_update = None

# Sidebar
with st.sidebar:
    st.header("Options")
    
    # Voice options
    st.subheader("Voice Settings")
    voice_option = st.selectbox(
        "Select voice type",
        options=["default", "male", "female", "alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        index=0
    )
    
    # Market data options
    st.subheader("Market Data")
    update_data = st.button("Refresh Market Data")
    
    # Show last update time if available
    if st.session_state.last_update:
        st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # About section
    st.subheader("About")
    st.markdown("""
    This app provides spoken market briefs using multiple AI agents:
    - API Agent: Real-time market data
    - Scraping Agent: News and filings
    - Retriever Agent: Contextual information
    - Analysis Agent: Financial insights
    - Language Agent: Natural responses
    - Voice Agent: Speech I/O
    """)

# Function to get market brief
def get_market_brief():
    try:
        response = requests.post(f"{ORCHESTRATOR_URL}/market-brief")
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                st.session_state.market_data = result["data"]
                st.session_state.last_update = datetime.now()
                return result["data"]
        return None
    except Exception as e:
        st.error(f"Error getting market brief: {e}")
        return None

# Function to process text query
def process_text_query(query):
    try:
        response = requests.post(
            f"{ORCHESTRATOR_URL}/query",
            json={"query": query}
        )
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                return result["data"]
        return None
    except Exception as e:
        st.error(f"Error processing query: {e}")
        return None

# Function to process voice query
def process_voice_query(audio_data):
    try:
        # Convert audio data to base64
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        
        response = requests.post(
            f"{ORCHESTRATOR_URL}/voice-query",
            json={"audio_data": audio_base64}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                return result["data"]
        return None
    except Exception as e:
        st.error(f"Error processing voice query: {e}")
        return None

# Function to play audio
def autoplay_audio(audio_base64):
    audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# Refresh market data if button clicked
if update_data:
    with st.spinner("Fetching latest market data..."):
        market_brief = get_market_brief()
        if market_brief:
            st.success("Market data refreshed!")
            
            # Play the voice response if available
            if "voice_response" in market_brief and "audio_data" in market_brief["voice_response"]:
                autoplay_audio(market_brief["voice_response"]["audio_data"])
            
            # Add to conversation
            st.session_state.messages.append({"role": "assistant", "content": market_brief["text_response"]})

# Chat interface
chat_container = st.container()

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Audio recorder for voice input
st.subheader("Speak your question")
audio_bytes = st.audio_recorder(
    pause_threshold=2.0,
    sample_rate=16000,
    energy_threshold=0.01
)

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
            st.session_state.messages.append({"role": "assistant", "content": response["text_response"]})
            
            # Display assistant message
            with st.chat_message("assistant"):
                st.write(response["text_response"])
            
            # Play the voice response if available
            if "voice_response" in response and "audio_data" in response["voice_response"]:
                autoplay_audio(response["voice_response"]["audio_data"])

# Process audio input
if audio_bytes:
    # Store the audio data
    st.session_state.audio_data = audio_bytes
    
    # Process the voice query
    with st.spinner("Processing voice query..."):
        response = process_voice_query(audio_bytes)
        
        if response and "query" in response:
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": response["query"]})
            
            # Display user message
            with st.chat_message("user"):
                st.write(response["query"])
            
            # Add assistant message to chat
            st.session_state.messages.append({"role": "assistant", "content": response["text_response"]})
            
            # Display assistant message
            with st.chat_message("assistant"):
                st.write(response["text_response"])
            
            # Play the voice response if available
            if "voice_response" in response and "audio_data" in response["voice_response"]:
                autoplay_audio(response["voice_response"]["audio_data"])

# Dashboard for market data
st.header("Market Dashboard")

# Check if we have market data
if st.session_state.market_data and "data" in st.session_state.market_data:
    market_data = st.session_state.market_data["data"]
    
    # Create tabs for different data categories
    tab1, tab2, tab3, tab4 = st.tabs(["Asia Tech", "Earnings", "Sentiment", "Yields"])
    
    with tab1:
        st.subheader("Asia Tech Allocation")
        
        if "asia_tech" in market_data:
            asia_tech = market_data["asia_tech"]
            
            # Display allocation change
            if "allocation" in asia_tech:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Current Allocation", 
                        f"{asia_tech['allocation']['current']}%",
                        f"{asia_tech['allocation']['change']}%"
                    )
                
                with col2:
                    st.metric(
                        "Previous Allocation", 
                        f"{asia_tech['allocation']['previous']}%"
                    )
                
                with col3:
                    st.metric(
                        "Direction", 
                        asia_tech['allocation']['direction']
                    )
            
            # Display stock performance if available
            if "stock_performance" in asia_tech and "top_performers" in asia_tech["stock_performance"]:
                st.subheader("Stock Performance")
                
                # Create DataFrame for top performers
                top_performers = asia_tech["stock_performance"]["top_performers"]
                if top_performers:
                    df_top = pd.DataFrame(top_performers)
                    
                    # Display as a bar chart
                    fig = px.bar(
                        df_top,
                        x="symbol",
                        y="change_percent",
                        title="Top Performing Stocks",
                        color="change_percent",
                        color_continuous_scale=["red", "yellow", "green"],
                        range_color=[-5, 5]
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Earnings Surprises")
        
        if "earnings" in market_data and "earnings_surprises" in market_data["earnings"]:
            earnings = market_data["earnings"]
            
            # Display positive surprises
            if "positive" in earnings["earnings_surprises"] and earnings["earnings_surprises"]["positive"]:
                st.subheader("Positive Surprises")
                df_positive = pd.DataFrame(earnings["earnings_surprises"]["positive"])
                if not df_positive.empty and "surprise_percent" in df_positive.columns:
                    st.dataframe(df_positive)
            
            # Display negative surprises
            if "negative" in earnings["earnings_surprises"] and earnings["earnings_surprises"]["negative"]:
                st.subheader("Negative Surprises")
                df_negative = pd.DataFrame(earnings["earnings_surprises"]["negative"])
                if not df_negative.empty and "surprise_percent" in df_negative.columns:
                    st.dataframe(df_negative)
    
    with tab3:
        st.subheader("Market Sentiment")
        
        if "sentiment" in market_data:
            sentiment = market_data["sentiment"]
            
            # Display sentiment score
            if "sentiment_score" in sentiment:
                # Create a gauge chart for sentiment
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=sentiment["sentiment_score"],
                    title={"text": f"Sentiment: {sentiment.get('sentiment_label', 'neutral')}"},
                    gauge={
                        "axis": {"range": [-1, 1]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [-1, -0.6], "color": "red"},
                            {"range": [-0.6, -0.2], "color": "orange"},
                            {"range": [-0.2, 0.2], "color": "yellow"},
                            {"range": [0.2, 0.6], "color": "lightgreen"},
                            {"range": [0.6, 1], "color": "green"}
                        ]
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
            
            # Display factors
            if "top_positive_factors" in sentiment:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Positive Factors")
                    for factor in sentiment["top_positive_factors"]:
                        st.write(f"• {factor.get('factor', '')}")
                
                with col2:
                    st.subheader("Negative Factors")
                    for factor in sentiment.get("top_negative_factors", []):
                        st.write(f"• {factor.get('factor', '')}")
    
    with tab4:
        st.subheader("Yield Environment")
        
        if "yields" in market_data:
            yields_data = market_data["yields"]
            
            # Display yield curve information
            if "yield_curve" in yields_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "10-Year Treasury", 
                        f"{yields_data.get('ten_year_treasury', 'N/A')}%"
                    )
                
                with col2:
                    st.metric(
                        "Yield Curve Shape", 
                        yields_data["yield_curve"].get("shape", "N/A")
                    )
            
            # Display equity market impact
            if "equity_market_impact" in yields_data:
                st.info(f"Yield Environment Impact on Equities: {yields_data['equity_market_impact']}")
            
            # Display key yields if available
            if "key_yields" in yields_data:
                # Convert to DataFrame
                yields_list = []
                for name, data in yields_data["key_yields"].items():
                    yields_list.append({
                        "name": name,
                        "yield": data.get("current"),
                        "change": data.get("change")
                    })
                
                if yields_list:
                    df_yields = pd.DataFrame(yields_list)
                    
                    # Create bar chart
                    fig = px.bar(
                        df_yields,
                        x="name",
                        y="yield",
                        title="Key Treasury Yields",
                        text="yield"
                    )
                    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No market data available. Click 'Refresh Market Data' in the sidebar to fetch the latest information.")

# Footer
st.markdown("---")
st.caption("Finance Voice Agent - Built with multiple AI agents, FastAPI, and Streamlit")
