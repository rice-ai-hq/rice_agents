# Rice Agents Documentation

Welcome to **Rice Agents**, a modular, provider-agnostic framework for building and orchestrating AI agents. Rice Agents is designed to scale from simple scripts to massive multi-agent swarms, with native support for state persistence, vector memory, and containerized execution contexts.

## Key Features

- **🧩 Modular Architecture**: Decoupled Agents, Tools, LLM Providers, and Memory.
- **📦 Container System**: Define execution environments, configuration, and shared resources in `rice_agents.toml`.
- **🧠 RiceDB Integration**: First-class support for **RiceDB** (Vector-Graph Database) for persistent RAG memory and ephemeral Agent Scratchpads.
- **🌊 Flows & Swarms**: Patterns for Sequential, Parallel, Hierarchical, and Adaptive multi-agent orchestration.
- **🛠️ Tooling**: Type-safe tool definitions with Pydantic support.

## Documentation Structure

1.  [Getting Started](getting_started.md): Installation and your first agent.
2.  [Core Concepts](concepts.md): Agents, Tools, LLMs, and Orchestration.
3.  [Containers & Configuration](containers.md): Managing environments with `rice_agents.toml` and the `Container` class.
4.  [RiceDB Integration](ricedb_integration.md): RAG, Memory, and Shared Scratchpad.
5.  [Complex Patterns](complex_patterns.md): Building Swarms, Event-Driven Systems, and Adaptive Architectures.

## Quick Example

```python
from rice_agents.agents import Agent
from rice_agents.llms import GeminiProvider
from rice_agents.containers import Container

# 1. Setup
llm = GeminiProvider(model="gemini-3-flash-preview")
container = Container("MyFirstApp")

# 2. Define Agent
agent = Agent(
    name="Greeter",
    llm=llm,
    system_prompt="You are a friendly AI.",
    container=container
)

# 3. Run
response = await agent.run("Hello!")
print(response)
```
