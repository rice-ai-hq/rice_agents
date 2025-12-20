import asyncio
import os

from dotenv import load_dotenv

from rice_agents.agents.base import Agent
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.tools.base import tool

# Load environment variables
load_dotenv()


# 1. Define a tool
@tool("get_stock_price")
def get_stock_price(ticker: str) -> str:
    """Mock function to get stock price."""
    print(f"\n[Tool] Fetching stock price for {ticker}...")
    prices = {"AAPL": "150.00", "GOOGL": "2800.00", "MSFT": "300.00"}
    return prices.get(ticker.upper(), "Unknown ticker")


async def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in .env")
        return

    # 2. Initialize Provider
    llm = GeminiProvider(model="gemini-1.5-flash", api_key=api_key)

    # 3. Create Agent
    agent = Agent(
        name="FinanceBot",
        llm=llm,
        tools=[get_stock_price],
        system_prompt="You are a helpful financial assistant. Use tools to find data.",
    )

    # 4. Run
    print("User: What is the price of Apple stock?")
    response = await agent.run("What is the price of Apple stock?")
    print(f"Agent: {response}")


if __name__ == "__main__":
    asyncio.run(main())
