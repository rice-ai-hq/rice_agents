# RiceDB Integration

Rice Agents is built to leverage **RiceDB**, a high-performance database optimized for AI agents.

## Connection

Rice Agents connects to RiceDB via `RiceDBStore`.

- **Host**: Can be `localhost` or a remote IP (e.g., `34.39.89.94`).
- **Protocol**: gRPC (default, port 50051) or HTTP.
- **Authentication**: Supports username/password (e.g., `admin`/`password123`).

## Capabilities

### 1. Vector Memory (RAG)

Agents can automatically retrieve relevant context from RiceDB before answering.

- **Ingestion**: You can pre-load massive datasets (`client.batch_insert`).
- **Retrieval**: `Agent.run` automatically queries the store using the task as the query.

### 2. Ephemeral Scratchpad

A shared, time-to-live (TTL) memory space for agent coordination.

- **Usage**: Agents post updates ("I finished step 1") to the scratchpad.
- **Coordination**: Other agents poll the scratchpad to react to events.
- **Isolation**: Scratchpad entries are separated by `session_id`.

### 3. Knowledge Graph

RiceDB supports linking nodes.

- **Example**: Link a `code_file` node to another `code_file` with an `IMPORTS` relation.
- **Traversal**: Agents can traverse these links to understand dependencies.

## Benchmarks

RiceDB is highly performant. In our benchmarks (Example 14), RiceDB remote ingestion was faster than Pinecone Serverless (0.56s vs 5.35s for 1k items) and query latency was significantly lower (1ms vs 125ms).
