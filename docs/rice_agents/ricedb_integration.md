# RiceDB Integration

Rice Agents is built to leverage **RiceDB**, a high-performance, ACID-compliant database designed specifically for **Multi-Agent AI Systems**. It combines vector search, graph traversal, and agent memory in a unified engine.

## Why RiceDB?

| Challenge                         | RiceDB Solution                                        |
| --------------------------------- | ------------------------------------------------------ |
| Agents need semantic search       | HNSW-based vector index with SIMD optimizations        |
| Multiple agents need coordination | Native Agent Memory (scratchpad) for real-time sharing |
| Knowledge has relationships       | Integrated Graph Database for semantic linking         |
| Multi-tenant environments         | Bitmap-based ACL for zero-latency permission checks    |
| High-frequency updates            | LSM-tree storage with Write-Ahead Log (WAL)            |
| Real-time notifications           | Pub/Sub with semantic subscriptions                    |

## Installation

```bash
# With gRPC support (recommended for performance)
uv add "ricedb[grpc]"

# With embedding support
uv add "ricedb[embeddings]"

# With all features
uv add "ricedb[all]"
```

## Connection

Rice Agents connects to RiceDB via `RiceDBStore`.

```python
from rice_agents.memory.ricedb_store import RiceDBStore

# Connect to RiceDB
store = RiceDBStore(
    host="localhost",           # or remote IP like "34.39.89.94"
    user_id=1,
    username="admin",
    password="password123"
)
```

### Transport Options

| Feature           | HTTP | gRPC           |
| ----------------- | ---- | -------------- |
| Basic CRUD        | ✅   | ✅             |
| Vector Search     | ✅   | ✅             |
| Batch Insert      | ✅   | ✅ (Streaming) |
| Stream Search     | ❌   | ✅             |
| Agent Memory      | ✅   | ✅             |
| Memory Watch      | ❌   | ✅             |
| Graph Operations  | ✅   | ✅             |
| Pub/Sub Subscribe | ❌   | ✅             |

## Capabilities

### 1. Vector Memory (RAG)

Agents automatically retrieve relevant context from RiceDB before answering.

```python
# Ingestion: Pre-load datasets
store.add_texts(
    texts=["Financial report Q4 2023", "Sales projections 2024"],
    metadatas=[{"dept": "finance"}, {"dept": "sales"}]
)

# Retrieval: Agent.run() automatically queries the store
results = store.query("quarterly financial data", n_results=5)
```

### 2. Agent Memory (Scratchpad)

A lightweight, time-ordered shared memory for multi-agent coordination. Avoids polluting the main vector index with intermediate thoughts.

```python
# Agent A writes to scratchpad
store.add_scratchpad(
    session_id="task-123",
    agent="ReviewerAgent",
    content="Found a critical bug in auth.py",
    metadata={"severity": "high"},
    ttl=3600  # Auto-expire after 1 hour
)

# Agent B reads from scratchpad
history = store.get_scratchpad(session_id="task-123", limit=10)
for entry in history:
    print(f"[{entry['agent_id']}] {entry['content']}")

# Poll for new messages
new_msgs = store.get_scratchpad(session_id="task-123", after=last_timestamp)

# Clear session when done
store.clear_scratchpad("task-123")
```

### 3. Knowledge Graph (Graph-RAG)

RiceDB includes an integrated graph database for representing relationships between entities.

```python
from ricedb import RiceDBClient

client = RiceDBClient("localhost")
client.connect()
client.login("admin", "admin")

# Add edges between nodes
client.add_edge(
    from_node=101,
    to_node=102,
    relation="IMPORTS",
    weight=0.9
)

# Query neighbors
neighbors = client.get_neighbors(node_id=101)
related = client.get_neighbors(node_id=101, relation="IMPORTS")

# BFS traversal for dependency analysis
visited = client.traverse(start_node=101, max_depth=3)
```

### 4. User Access Control

RiceDB provides bitmap-based ACL for multi-tenant environments:

```python
# Insert as user 100
client.insert_text(1, "Secret document", user_id=100)

# Search as user 200 won't find user 100's documents
results = client.search_text("secret", user_id=200)  # Returns []

# Search as user 100 finds their own documents
results = client.search_text("secret", user_id=100)  # Returns documents

# Grant permissions to another user
client.grant_permission(
    node_id=1,
    user_id=200,
    permissions={"read": True, "write": False}
)
```

## Embedding Generators

RiceDB supports multiple embedding providers:

```python
# Sentence Transformers (local)
from ricedb.utils import SentenceTransformersEmbeddingGenerator
embed_gen = SentenceTransformersEmbeddingGenerator(model_name="all-MiniLM-L6-v2")

# OpenAI
from ricedb.utils import OpenAIEmbeddingGenerator
embed_gen = OpenAIEmbeddingGenerator(model="text-embedding-ada-002", api_key="...")

# Hugging Face
from ricedb.utils import HuggingFaceEmbeddingGenerator
embed_gen = HuggingFaceEmbeddingGenerator(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Dummy (for testing)
from ricedb.utils import DummyEmbeddingGenerator
embed_gen = DummyEmbeddingGenerator(dimensions=384)
```

## Auto-Memory with Containers

When `auto_memory = true` in your container config, agent outputs are automatically indexed:

```toml
# rice_agents.toml
[default_container]
memory = "ricedb"
auto_memory = true

[default_container.memory_config]
host = "localhost"
user_id = 1
username = "admin"
password = "password123"
```

```python
from rice_agents.containers import Container
from rice_agents.agents import Agent

# Container auto-initializes RiceDBStore
container = Container("ResearchTeam")

agent = Agent(
    name="Researcher",
    llm=llm,
    container=container  # Memory is automatically shared
)

# Every agent.run() result is auto-indexed into RiceDB
result = await agent.run("Research quantum computing")
# Result is now searchable by other agents in the same container
```

## Benchmarks

RiceDB is highly performant. In our benchmarks:

| Metric               | RiceDB | Pinecone Serverless |
| -------------------- | ------ | ------------------- |
| Ingestion (1k items) | 0.56s  | 5.35s               |
| Query Latency        | ~1ms   | ~125ms              |

## Real-time Pub/Sub (gRPC only)

Subscribe to database events with semantic filtering:

```python
# Subscribe to all events
for event in client.subscribe(filter_type="all"):
    print(f"Event: {event['type']}, Node: {event['node_id']}")

# Semantic subscription (wake on similar vectors)
for event in client.subscribe(
    filter_type="semantic",
    vector=query_vector,
    threshold=0.85
):
    print(f"Similar content inserted: {event['node']}")
```
