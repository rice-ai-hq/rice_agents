# Containers & Configuration

The **Container** system is the backbone of Rice Agents' scalability. It provides dependency injection, configuration management, and shared state for agents.

## Project Configuration

Rice Agents looks for `rice_agents.toml` in your project root.

### Example Configuration

```toml
[default_container]
llm_provider = "gemini"
model = "gemini-3-flash-preview"
memory = "ricedb"
auto_memory = true

[default_container.memory_config]
host = "34.39.89.94"
user_id = 1
username = "admin"
password = "password123"

[containers.ResearchTeam]
description = "Specialized container for researchers"
model = "gemini-ultra-preview" # Override model
```

## Using Containers

### Automatic Assignment

If you don't specify a container, agents are assigned to the `default` container (loaded from `[default_container]`).

```python
agent = Agent(name="Bot", llm=llm)
# agent.container is set to Default Container automatically
```

### Explicit Assignment

You can create specific containers defined in your config.

```python
from rice_agents.containers import Container

team_container = Container("ResearchTeam")
agent = Agent(name="Researcher", llm=llm, container=team_container)
```

## Features

### 1. Auto-Memory

If `auto_memory = true` in config:

- The container automatically initializes a `RiceDBStore`.
- Every time an agent in this container finishes a task, the result is automatically indexed into RiceDB.
- This builds a knowledge base effortlessly as agents work.

### 2. Shared Scratchpad

All agents in a container share the same `RiceDBStore` instance. This allows them to read/write to a shared **Scratchpad** for coordination.

```python
# Agent A writes
container.memory_store.add_scratchpad(..., content="I found X")

# Agent B reads
entries = container.memory_store.get_scratchpad(...)
```
