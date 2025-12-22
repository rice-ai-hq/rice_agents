# Complex Patterns

Rice Agents shines in complex, multi-agent scenarios.

## 1. Massive Swarms (100+ Agents)

**Example 08: Research Swarm** shows how to run 100 concurrent agents.

- **Pattern**: Single Container, Shared RAG Memory.
- **Workflow**:
  1.  Ingest vast dataset into RiceDB.
  2.  Spawn 100 agents.
  3.  Use `asyncio.gather` and `Semaphore` to execute them.
  4.  Each agent queries shared memory for its specific topic.
  5.  Results are auto-saved.

## 2. Event-Driven Architecture

**Example 10: Code Review Swarm** demonstrates a decentralized system.

- **Pattern**: Job Board (Scratchpad).
- **Workflow**:
  - **Orchestrator**: Posts tasks to RiceDB.
  - **Workers**: Poll RiceDB for pending tasks matching their role.
  - **Execution**: Workers execute and write findings back to RiceDB.
  - **Synthesis**: A final agent reads all findings to create a report.

## 3. Adaptive Environments

**Example 11: Adaptive Code Review** shows dynamic planning.

- **Pattern**: Observe -> Plan -> Spawn.
- **Workflow**:
  1.  Orchestrator analyzes the environment (codebase structure).
  2.  LLM generates a _plan_ (list of required agents).
  3.  System dynamically instantiates those agents.

## 4. Multi-Modal Pipelines

**Example 12: Music Processing** shows handling non-text data.

- **Pattern**: Tool-Centric Pipeline.
- **Workflow**:
  - Agent A (Separator) calls DSP tool.
  - Agent B (Analyzer) processes audio file.
  - Agent C (Producer) uses RiceDB Knowledge Base to classify the result.
