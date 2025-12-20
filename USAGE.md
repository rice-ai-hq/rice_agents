# Rice Agents Framework - Usage Guide

Rice Agents is a modular, provider-agnostic framework for building and orchestrating AI agents in Python. It supports multiple LLM providers (Gemini, OpenAI), tool usage, long-term memory (RAG), and complex orchestration patterns like sequential chains, parallel swarms, and adaptive planning.

## Installation

Install the package via pip (or uv):

```bash
pip install rice-agents
# or
uv add rice-agents
```

## Configuration

Set up your environment variables in a `.env` file or export them directly:

```env
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-...
```

## 1. Creating a Basic Agent

The `Agent` is the core unit. It wraps an LLM provider and handles conversation history.

```python
import asyncio
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.agents.base import Agent

async def main():
    # Initialize Provider (Gemini or OpenAI)
    llm = GeminiProvider(model="gemini-1.5-flash")
    
    agent = Agent(
        name="Assistant",
        llm=llm,
        system_prompt="You are a helpful assistant."
    )
    
    response = await agent.run("Hello, who are you?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

## 2. Defining Tools

Use the `@tool` decorator to register any Python function as a tool. The framework automatically generates schemas for the specific LLM provider.

```python
from rice_agents.tools.base import tool

@tool("get_weather")
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    return f"The weather in {location} is Sunny, 25°C."

# Attach tools to the agent
agent = Agent(name="Bot", llm=llm, tools=[get_weather])
```

## 3. Adding Memory (RAG)

Give agents long-term memory using vector stores. The agent automatically retrieves relevant context before answering.

```python
from rice_agents.memory.vector_store import ChromaDBStore

# Initialize persistent memory
memory = ChromaDBStore(path="./agent_memory")
memory.add_texts(["User loves sci-fi movies.", "User lives in New York."])

agent = Agent(name="MemoryBot", llm=llm, memory=memory)
```

## 4. Orchestration Flows

Combine agents into powerful, composable workflows.

### Sequential & Parallel

*   **SequentialFlow**: Chains agents together (Output of Agent A -> Input of Agent B).
*   **ParallelFlow**: Runs agents concurrently.

```python
from rice_agents.orchestration.flows import SequentialFlow, ParallelFlow

# Define Agents
pm = Agent(name="PM", llm=llm, system_prompt="Create specs.")
backend = Agent(name="Backend", llm=llm, system_prompt="Write API code.")
frontend = Agent(name="Frontend", llm=llm, system_prompt="Write UI code.")
qa = Agent(name="QA", llm=llm, system_prompt="Review the code.")

# Hierarchical Flow:
# 1. PM creates specs -> 
# 2. (Backend & Frontend work in parallel) -> 
# 3. QA reviews everything
dev_team = ParallelFlow([backend, frontend])
pipeline = SequentialFlow([pm, dev_team, qa])

result = await pipeline.run("Build a To-Do App")
```

### Adaptive Swarm

Let a "Manager" agent dynamically plan the task and delegate steps to specialized agents.

```python
from rice_agents.orchestration.adaptive import AdaptiveOrchestrator

specialists = {
    "coder": Agent(name="Coder", llm=llm),
    "tester": Agent(name="Tester", llm=llm)
}

orchestrator = AdaptiveOrchestrator(manager_llm=llm, agents=specialists)
await orchestrator.run("Build a calculator app and test it.")
```

## Examples

Check the `examples/` directory for complete, runnable scripts:

*   `01_basic_tool.py`: Simple tool usage.
*   `02_memory_rag.py`: Persistent memory with ChromaDB.
*   `03_flows.py`: Basic Sequential and Parallel flows.
*   `04_adaptive_swarm.py`: Dynamic planning with a manager agent.
*   `05_hierarchical_dev_team.py`: Complex nested flows (PM -> Devs -> QA).
*   `06_interactive_filesystem.py`: Stateful agent interacting with the OS via tools.