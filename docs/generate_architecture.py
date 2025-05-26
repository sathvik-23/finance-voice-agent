"""
Generate a simple architecture diagram for the Finance Voice Agent.
"""
import os
import plotly.graph_objects as go
from PIL import Image
import numpy as np

# Create a figure
fig = go.Figure()

# Add nodes for each component
components = [
    {"name": "User", "x": 0.5, "y": 0.9, "type": "user"},
    {"name": "Streamlit App", "x": 0.5, "y": 0.8, "type": "ui"},
    {"name": "Orchestrator", "x": 0.5, "y": 0.7, "type": "service"},
    {"name": "API Agent", "x": 0.2, "y": 0.6, "type": "agent"},
    {"name": "Scraping Agent", "x": 0.4, "y": 0.6, "type": "agent"},
    {"name": "Retriever Agent", "x": 0.6, "y": 0.6, "type": "agent"},
    {"name": "Analysis Agent", "x": 0.8, "y": 0.6, "type": "agent"},
    {"name": "Language Agent", "x": 0.3, "y": 0.5, "type": "agent"},
    {"name": "Voice Agent", "x": 0.7, "y": 0.5, "type": "agent"},
    {"name": "External Services", "x": 0.5, "y": 0.3, "type": "external"}
]

# Add edges for connections
edges = [
    {"from": "User", "to": "Streamlit App"},
    {"from": "Streamlit App", "to": "Orchestrator"},
    {"from": "Orchestrator", "to": "API Agent"},
    {"from": "Orchestrator", "to": "Scraping Agent"},
    {"from": "Orchestrator", "to": "Retriever Agent"},
    {"from": "Orchestrator", "to": "Analysis Agent"},
    {"from": "Orchestrator", "to": "Language Agent"},
    {"from": "Orchestrator", "to": "Voice Agent"},
    {"from": "API Agent", "to": "External Services"},
    {"from": "Scraping Agent", "to": "External Services"},
    {"from": "Language Agent", "to": "External Services"},
    {"from": "Voice Agent", "to": "External Services"},
    # Data flows for indexing (dashed)
    {"from": "API Agent", "to": "Retriever Agent", "dash": "dash"},
    {"from": "Scraping Agent", "to": "Retriever Agent", "dash": "dash"}
]

# Add nodes
for component in components:
    if component["type"] == "user":
        marker_symbol = "circle"
        marker_size = 15
        marker_color = "#E1F5FE"
        marker_line_color = "#4285F4"
        marker_line_width = 2
    elif component["type"] == "ui":
        marker_symbol = "square"
        marker_size = 20
        marker_color = "#E1F5FE"
        marker_line_color = "#4285F4"
        marker_line_width = 2
    elif component["type"] == "service":
        marker_symbol = "square"
        marker_size = 20
        marker_color = "#E1F5FE"
        marker_line_color = "#4285F4"
        marker_line_width = 2
    elif component["type"] == "agent":
        marker_symbol = "square"
        marker_size = 20
        marker_color = "#E1F5FE"
        marker_line_color = "#4285F4"
        marker_line_width = 2
    elif component["type"] == "external":
        marker_symbol = "square"
        marker_size = 30
        marker_color = "#E3F2FD"
        marker_line_color = "#0D47A1"
        marker_line_width = 2
    
    fig.add_trace(go.Scatter(
        x=[component["x"]],
        y=[component["y"]],
        mode="markers+text",
        marker=dict(
            symbol=marker_symbol,
            size=marker_size,
            color=marker_color,
            line=dict(color=marker_line_color, width=marker_line_width)
        ),
        text=component["name"],
        textposition="bottom center",
        name=component["name"]
    ))

# Add edges
for edge in edges:
    # Find the source and target nodes
    source = next(c for c in components if c["name"] == edge["from"])
    target = next(c for c in components if c["name"] == edge["to"])
    
    # Determine line style
    line_dash = edge.get("dash", "solid")
    
    fig.add_trace(go.Scatter(
        x=[source["x"], target["x"]],
        y=[source["y"], target["y"]],
        mode="lines",
        line=dict(color="#4285F4", width=2, dash=line_dash),
        showlegend=False
    ))

# Configure layout
fig.update_layout(
    title="Finance Voice Agent Architecture",
    showlegend=False,
    plot_bgcolor="white",
    width=800,
    height=600,
    margin=dict(l=20, r=20, t=50, b=20),
    xaxis=dict(
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        range=[0, 1]
    ),
    yaxis=dict(
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        range=[0, 1]
    )
)

# Save as PNG
fig.write_image("architecture.png")
print("Architecture diagram saved as architecture.png")
