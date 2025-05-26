from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.yfinance import YFinanceTools
from dotenv import load_dotenv
from agno.tools.googlesearch import GoogleSearchTools

load_dotenv()
# Initialize the financial API agent
api_agent = Agent(
    model=Gemini(id="gemini-2.0-flash"),
    tools=[
        YFinanceTools(
            stock_price=True,
            company_info=True,
            stock_fundamentals=True,
            income_statements=True,
            key_financial_ratios=True,
            analyst_recommendations=True,
            company_news=True,
            technical_indicators=True,
            historical_prices=True
        ),
        GoogleSearchTools()
    ],
    instructions=[
    "Step 1: Use GoogleSearchTools to find the top 5 Asia tech stocks by market cap or trading volume. Ensure the data is recent (2024 or later).",
    "Step 2: For each of the companies identified, use YFinanceTools to get the following:",
    "- Current stock price and % change from previous close",
    "- Latest earnings data: actual vs expected EPS, revenue, surprise if any",
    "- Recent analyst recommendations (upgrades/downgrades, sentiment)",
    "- Any notable recent company news (1-line summary)",
    "Step 3: Format your response in markdown using bullet points or tables.",
    "Step 4: Clearly label sections by company name or ticker symbol.",
    "Step 5: Use proper units for numbers (e.g., %, $, B for billion, M for million) and readable date formats (e.g., May 26, 2025).",
    "Step 6: Do not fabricate any data. If information is missing, clearly say: 'No recent data available'."
],

    markdown=True,
    show_tool_calls=True,
    debug_mode=True,
    add_datetime_to_instructions=True,

)

# Example usage
api_agent.print_response("Give me today’s market update for the top Asia tech stocks. Include price movement, earnings results, analyst views, and any key news.")
