from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with white background
width, height = 800, 600
image = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(image)

# Try to load a font, fallback to default if not available
try:
    font_title = ImageFont.truetype("Arial", 20)
    font_label = ImageFont.truetype("Arial", 14)
    font_small = ImageFont.truetype("Arial", 10)
except:
    # Fallback to default font
    font_title = ImageFont.load_default()
    font_label = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Colors
blue = "#4285F4"
light_blue = "#E1F5FE"
dark_blue = "#0D47A1"
lighter_blue = "#E3F2FD"

# Draw title
draw.text((width // 2, 30), "Finance Voice Agent Architecture", fill=dark_blue, font=font_title, anchor="mm")

# Draw components
def draw_box(x, y, w, h, label, sublabel=None, fill=light_blue, outline=blue):
    draw.rectangle((x, y, x + w, y + h), fill=fill, outline=outline, width=2)
    draw.text((x + w // 2, y + h // 2 - 5), label, fill=dark_blue, font=font_label, anchor="mm")
    if sublabel:
        draw.text((x + w // 2, y + h // 2 + 15), sublabel, fill=dark_blue, font=font_small, anchor="mm")

# Draw user (circle)
user_x, user_y = width // 2, 80
user_radius = 20
draw.ellipse((user_x - user_radius, user_y - user_radius, user_x + user_radius, user_y + user_radius), 
             fill=light_blue, outline=blue, width=2)
draw.text((user_x, user_y), "User", fill=dark_blue, font=font_label, anchor="mm")

# Draw components
box_width, box_height = 150, 60

# Streamlit App
app_x, app_y = width // 2 - box_width // 2, 120
draw_box(app_x, app_y, box_width, box_height, "Streamlit App", "Web UI")

# Orchestrator
orch_x, orch_y = width // 2 - box_width // 2, 220
draw_box(orch_x, orch_y, box_width, box_height, "Orchestrator", "FastAPI")

# Agent layer 1
api_x, api_y = 50, 320
draw_box(api_x, api_y, box_width, box_height, "API Agent", "AlphaVantage, Yahoo")

scraping_x, scraping_y = 225, 320
draw_box(scraping_x, scraping_y, box_width, box_height, "Scraping Agent", "SEC Filings, News")

retriever_x, retriever_y = 400, 320
draw_box(retriever_x, retriever_y, box_width, box_height, "Retriever Agent", "FAISS Vector Store")

analysis_x, analysis_y = 575, 320
draw_box(analysis_x, analysis_y, box_width, box_height, "Analysis Agent", "Financial Analysis")

# Agent layer 2
lang_x, lang_y = 125, 420
draw_box(lang_x, lang_y, box_width, box_height, "Language Agent", "Agno, LLM")

voice_x, voice_y = 475, 420
draw_box(voice_x, voice_y, box_width, box_height, "Voice Agent", "Whisper STT, TTS")

# External Services
ext_x, ext_y = 50, 520
draw_box(ext_x, ext_y, 700, 40, "External Services: AlphaVantage, Yahoo Finance, SEC EDGAR, OpenAI API", 
         fill=lighter_blue, outline=dark_blue)

# Draw connections
def draw_arrow(start_x, start_y, end_x, end_y, color=blue, width=2, dash=False):
    # Draw line
    if dash:
        # Draw dashed line (simplified)
        for i in range(0, int((end_y - start_y)), 10):
            y1 = start_y + i
            y2 = min(y1 + 5, end_y)
            draw.line((start_x, y1, start_x, y2), fill=color, width=width)
    else:
        draw.line((start_x, start_y, end_x, end_y), fill=color, width=width)
    
    # Draw arrowhead
    if end_y > start_y:  # Downward arrow
        draw.polygon([(end_x - 5, end_y - 10), (end_x, end_y), (end_x + 5, end_y - 10)], fill=color)
    elif end_y < start_y:  # Upward arrow
        draw.polygon([(end_x - 5, end_y + 10), (end_x, end_y), (end_x + 5, end_y + 10)], fill=color)
    elif end_x > start_x:  # Rightward arrow
        draw.polygon([(end_x - 10, end_y - 5), (end_x, end_y), (end_x - 10, end_y + 5)], fill=color)
    else:  # Leftward arrow
        draw.polygon([(end_x + 10, end_y - 5), (end_x, end_y), (end_x + 10, end_y + 5)], fill=color)

# Connect components
# User to Streamlit
draw_arrow(user_x, user_y + user_radius, user_x, app_y)

# Streamlit to Orchestrator
draw_arrow(app_x + box_width // 2, app_y + box_height, orch_x + box_width // 2, orch_y)

# Orchestrator to Agents
draw_arrow(orch_x + box_width // 2, orch_y + box_height, api_x + box_width // 2, api_y)
draw_arrow(orch_x + box_width // 2, orch_y + box_height, scraping_x + box_width // 2, scraping_y)
draw_arrow(orch_x + box_width // 2, orch_y + box_height, retriever_x + box_width // 2, retriever_y)
draw_arrow(orch_x + box_width // 2, orch_y + box_height, analysis_x + box_width // 2, analysis_y)
draw_arrow(orch_x + box_width // 2, orch_y + box_height, lang_x + box_width // 2, lang_y)
draw_arrow(orch_x + box_width // 2, orch_y + box_height, voice_x + box_width // 2, voice_y)

# Agents to External Services
draw_arrow(api_x + box_width // 2, api_y + box_height, api_x + box_width // 2, ext_y)
draw_arrow(scraping_x + box_width // 2, scraping_y + box_height, scraping_x + box_width // 2, ext_y)
draw_arrow(lang_x + box_width // 2, lang_y + box_height, lang_x + box_width // 2, ext_y)
draw_arrow(voice_x + box_width // 2, voice_y + box_height, voice_x + box_width // 2, ext_y)

# Data flows between agents (dashed)
draw_arrow(api_x + box_width, api_y + box_height // 2, retriever_x, retriever_y + box_height // 2, dash=True)
draw_arrow(scraping_x + box_width, scraping_y + box_height // 2, retriever_x, retriever_y + box_height // 2, dash=True)

# Save the image
image.save("/Users/sathvik/Project/finance-voice-agent/docs/architecture.png")
print("Architecture diagram saved to /Users/sathvik/Project/finance-voice-agent/docs/architecture.png")
