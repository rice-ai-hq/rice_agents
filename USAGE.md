# Rice Agents Framework - Usage Guide

## Setup

Ensure dependencies are installed and `.env` is configured with keys.

```bash
uv sync
```

`.env`:
```env
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-...
```

## 1. Defining Tools

Use the `@tool` decorator to turn any Python function into an agent-ready tool.

```python
from rice_agents.tools.base import tool

@tool("get_weather")
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    return f"The weather in {location} is Sunny, 25°C."
```

## 2. Creating an Agent (with Gemini)

```python
import asyncio
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.agents.base import Agent

async def main():
    # Initialize LLM
    llm = GeminiProvider(model="gemini-1.5-flash")
    
    # Create Agent
    agent = Agent(
        name="WeatherBot",
        llm=llm,
        tools=[get_weather], # Pass the tool instance or decorated function
        system_prompt="You are a helpful weather assistant."
    )
    
    # Run
    response = await agent.run("What is the weather in Tokyo?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

## 3. Using Memory (RAG)

Attach a vector store to an agent to give it long-term memory.

```python
from rice_agents.memory.vector_store import ChromaDBStore

# Initialize Memory
memory = ChromaDBStore(path="./my_memory")
memory.add_texts(["My favorite color is blue.", "I live in San Francisco."])

# Create Agent with Memory
agent = Agent(name="MemoryBot", llm=llm, memory=memory)

# The agent will automatically query memory before answering
await agent.run("What is my favorite color?") 
```

## 4. Orchestration: Sequential Flow

Chain agents together.

```python
from rice_agents.orchestration.flows import SequentialFlow

researcher = Agent(name="Researcher", llm=llm, system_prompt="Research the topic.")
writer = Agent(name="Writer", llm=llm, system_prompt="Write a blog post based on the research.")

flow = SequentialFlow([researcher, writer])
final_blog = await flow.run("Quantum Computing")
```

## 5. Orchestration: Adaptive Swarm

Let a "Manager" agent plan and delegate tasks dynamically.

```python
from rice_agents.orchestration.adaptive import AdaptiveOrchestrator

# Registry of available specialists
agents = {
    "coder": Agent(name="Coder", llm=llm, system_prompt="Write Python code."),
    "reviewer": Agent(name="Reviewer", llm=llm, system_prompt="Review code for bugs."),
    "writer": Agent(name="Writer", llm=llm, system_prompt="Write documentation.")
}

orchestrator = AdaptiveOrchestrator(manager_llm=llm, agents=agents)

# The orchestrator will create a plan (e.g., Code -> Review -> Write Docs) and execute it
result = await orchestrator.run("Create a snake game in Python and document it.")
```
