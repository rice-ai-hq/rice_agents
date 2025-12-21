# RiceDB Integration in Rice Agents

Rice Agents supports [RiceDB](https://github.com/shankha98/ricedb-python) as a powerful backend for both persistent vector memory (RAG) and ephemeral agent scratchpad (shared memory).

## Overview

Integrating RiceDB enhances your agents with:

1.  **Persistent Memory (RAG)**: Store and retrieve knowledge using vector similarity search.
2.  **Agent Scratchpad**: A shared, session-based memory space for agents to log thoughts, plans, and intermediate results without polluting the long-term memory.
3.  **Performance**: RiceDB is optimized for high-performance vector and graph operations.

## Installation

RiceDB integration is optional. To use it, you must install the `ricedb` package:

```bash
pip install ricedb
# or with extra features
pip install "ricedb[grpc,embeddings]"
```

If you are installing `rice_agents` from source/git, the dependency is included in `pyproject.toml`.

## Usage

### 1. Initialize RiceDB Memory

Use the `RiceDBStore` class to connect to your RiceDB server.

```python
from rice_agents.memory.ricedb_store import RiceDBStore

# Connect to RiceDB running on localhost
memory = RiceDBStore(
    host="localhost",
    user_id=1,  # Optional: specific user ID for ACL
)
```

### 2. Use with an Agent

Pass the `RiceDBStore` instance to your `Agent`. The agent will automatically utilize both the vector store (for RAG) and the scratchpad (for logging).

```python
from rice_agents.agents.base import Agent

agent = Agent(
    name="ResearchBot",
    llm=my_llm_provider,
    memory=memory,
    system_prompt="You are a helpful researcher."
)
```

### 3. Agent Scratchpad (Shared Memory)

When an `Agent` is initialized with a `RiceDBStore`, it automatically logs key events to the RiceDB Agent Memory (Scratchpad):

- **Task Start**: Logs the initial user prompt/task.
- **Tool Calls**: Logs every tool execution and its arguments.

This creates a real-time, shared context that other agents or monitoring tools can subscribe to or query.

You can also manually interact with the scratchpad:

```python
# Add a custom thought to the scratchpad
memory.add_scratchpad(
    session_id=agent.session_id,
    agent="ResearchBot",
    content="I need to verify this source.",
    metadata={"priority": "high"}
)

# Retrieve scratchpad history for the current session
history = memory.get_scratchpad(session_id=agent.session_id)
for entry in history:
    print(f"[{entry['agent']}] {entry['content']}")
```

### 4. Vector Memory (RAG)

Standard RAG operations work as expected. You can add documents to the store, and the agent will retrieve relevant context during execution.

```python
# Add knowledge
memory.add_texts([
    "RiceDB is a vector-graph database.",
    "Rice Agents is a modular framework."
])

# The agent will retrieve this context when asked relevant questions.
response = await agent.run("What is RiceDB?")
```

## Configuration

`RiceDBStore` accepts the following parameters:

- `host` (str): Hostname of the RiceDB server (default: "localhost").
- `user_id` (int): User ID for authentication and ACL (default: 1).
- `embedding_generator` (optional): A custom embedding generator instance. If not provided, it uses `DummyEmbeddingGenerator` (if available) or expects the server to handle embeddings (if configured).

## Example

See [examples/07_ricedb_memory.py](../examples/07_ricedb_memory.py) for a complete runnable example.
