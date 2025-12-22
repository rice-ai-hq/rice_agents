# Getting Started

## Installation

Rice Agents requires Python 3.11 or later. We recommend using `uv` for package management.

```bash
# Install package
pip install rice-agents

# Or with uv
uv pip install rice-agents
```

### Dependencies

To use certain features, you may need extra dependencies:

- **RiceDB Integration**: `pip install "rice-agents[ricedb]"`
- **Gemini**: `pip install google-genai`
- **OpenAI**: `pip install openai`

## Your First Agent

Create a file `main.py`:

```python
import asyncio
import os
from rice_agents.agents import Agent
from rice_agents.containers import Container
from rice_agents.llms import GeminiProvider

# 1. Configure Provider
api_key = os.getenv("GOOGLE_API_KEY")
llm = GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)

# 2. Setup Container (Recommended)
# Containers manage shared state and configuration
container = Container("GettingStarted")

# 3. Create Agent
agent = Agent(
    name="Assistant",
    llm=llm,
    system_prompt="You are a helpful assistant.",
    container=container
)

# 4. Run
async def main():
    response = await agent.run("Tell me a joke.")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
export GOOGLE_API_KEY="your_key"
python main.py
```

## Adding Tools

Agents become powerful when they can interact with the world.

```python
from rice_agents.tools import tool

@tool("get_weather")
def get_weather(location: str) -> str:
    """Gets the current weather for a location."""
    return f"The weather in {location} is Sunny."

agent = Agent(
    name="WeatherBot",
    llm=llm,
    tools=[get_weather], # Register the tool
    container=container
)

await agent.run("What is the weather in London?")
# Agent calls tool -> Tool returns "Sunny" -> Agent responds "It's Sunny in London."
```
