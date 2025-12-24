# Rice Agents

A modular, provider-agnostic framework for building and orchestrating AI agents. Rice Agents scales from simple scripts to massive multi-agent swarms, with native support for state persistence, vector memory, and containerized execution contexts.

## Key Features

- **Modular Architecture** - Decoupled Agents, Tools, LLM Providers, and Memory
- **Container System** - Define execution environments, configuration, and shared resources via `rice_agents.toml`
- **RiceDB Integration** - First-class support for RiceDB
- **Flows & Swarms** - Patterns for Sequential, Parallel, Hierarchical, and Adaptive multi-agent orchestration
- **Type-Safe Tooling** - Tool definitions with Pydantic support and automatic schema generation
- **Multi-Provider Support** - Works with Gemini, OpenAI, and Anthropic

## Installation

Rice Agents requires Python 3.11 or later. We recommend using [uv](https://docs.astral.sh/uv/) for package management.

> **Note:** Rice Agents is not yet published to PyPI. Install directly from GitHub.

### Using uv (Recommended)

Add to your `pyproject.toml`:

```toml
[project]
name = "my-agent-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "rice-agents @ git+https://github.com/shankha98/rice_agents.git",
]
```

Then run:

```bash
uv sync
```

### Using pip

```bash
pip install git+https://github.com/shankha98/rice_agents.git
```

### Optional Dependencies

Rice Agents includes all core dependencies. For additional features:

```bash
# RiceDB with gRPC support (recommended for performance)
uv add "ricedb[grpc]"

# RiceDB with embedding generators
uv add "ricedb[embeddings]"  # Sentence Transformers
uv add "ricedb[openai]"      # OpenAI embeddings
uv add "ricedb[all]"         # All features

# Additional LLM providers (if needed)
uv add google-genai  # Gemini
uv add openai        # OpenAI
uv add anthropic     # Anthropic
```

## Quick Start

```python
import asyncio
import os
from rice_agents.agents import Agent
from rice_agents.containers import Container
from rice_agents.llms import GeminiProvider

# 1. Configure Provider
api_key = os.getenv("GOOGLE_API_KEY")
llm = GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)

# 2. Setup Container
container = Container("MyApp")

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

## Adding Tools

Agents become powerful when they can interact with the world:

```python
from rice_agents.tools import tool

@tool("get_weather")
def get_weather(location: str) -> str:
    """Gets the current weather for a location."""
    return f"The weather in {location} is Sunny."

agent = Agent(
    name="WeatherBot",
    llm=llm,
    tools=[get_weather],
    container=container
)

await agent.run("What is the weather in London?")
```

## Orchestration Patterns

### Sequential Flow

Chain agents where output flows from one to the next:

```python
from rice_agents.orchestration.flows import SequentialFlow

flow = SequentialFlow([researcher, writer, editor])
result = await flow.run("Write an article about AI")
```

### Parallel Flow

Run multiple agents concurrently on the same task:

```python
from rice_agents.orchestration.flows import ParallelFlow

flow = ParallelFlow([analyst1, analyst2, analyst3])
results = await flow.run("Analyze market trends")
```

### Adaptive Orchestrator

Dynamic planning where a manager LLM decides the workflow at runtime:

```python
from rice_agents.orchestration.adaptive import AdaptiveOrchestrator

orchestrator = AdaptiveOrchestrator(
    manager_llm=llm,
    agents={"Researcher": researcher, "Writer": writer, "Reviewer": reviewer}
)
result = await orchestrator.run("Create a technical blog post about quantum computing")
```

## Configuration

Rice Agents uses `rice_agents.toml` for project configuration:

```toml
[default_container]
llm_provider = "gemini"
model = "gemini-3-flash-preview"
memory = "ricedb"
auto_memory = true

[default_container.memory_config]
host = "localhost"
user_id = 1

[containers.ResearchTeam]
description = "Specialized container for researchers"
model = "gemini-ultra-preview"
```

## RiceDB Agent Memory (Scratchpad)

RiceDB provides a native **Agent Memory** (scratchpad) system for multi-agent coordination. Unlike the main vector index, the scratchpad is optimized for high-frequency, ephemeral updates between agents.

### Writing to Scratchpad

Agents write their findings, status updates, or tasks to the shared scratchpad:

```python
from ricedb import RiceDBClient

client = RiceDBClient("localhost")
client.connect()
client.login("admin", "admin")

# Agent writes a finding to the scratchpad
client.memory.add(
    session_id="code-review-session-001",
    agent="SecurityAgent",
    content='{"severity": "critical", "description": "Hardcoded secret found", "file": "auth.py"}',
    metadata={"type": "finding", "related_file": "auth.py"},
    ttl=3600  # Auto-expire after 1 hour
)
```

### Reading from Scratchpad

Other agents poll the scratchpad to react to events or pick up tasks:

```python
# Get all entries for this session
entries = client.memory.get(session_id="code-review-session-001", limit=100)

for entry in entries:
    print(f"[{entry['agent_id']}] {entry['content']}")

# Poll for new messages since last check
new_entries = client.memory.get(
    session_id="code-review-session-001",
    after=last_timestamp
)
```

### Multi-Agent Coordination Pattern

Here's how multiple agents coordinate using the scratchpad (from `examples/10_code_review_swarm`):

```python
class Orchestrator:
    def post_task(self, task: Task):
        """Post a task to the job board (scratchpad)"""
        self.db.write_scratchpad_entry(
            agent_name="Orchestrator",
            content=task.model_dump_json(),
            related_file="job_board",
            ttl=3600 * 24
        )

class Worker:
    async def poll_and_work(self):
        """Poll scratchpad for pending tasks"""
        entries = self.db.get_scratchpad_entries()

        # Find tasks assigned to this worker
        my_tasks = [t for t in parse_tasks(entries)
                    if t.status == "pending" and t.assigned_to == self.role]

        if my_tasks:
            task = my_tasks[0]
            await self.execute_task(task)

            # Write findings back to scratchpad
            self.db.write_scratchpad_entry(
                agent_name=self.role,
                content=finding.model_dump_json(),
                related_file="finding"
            )
```

### Container Integration

When using containers with `auto_memory = true`, scratchpad entries are automatically created:

```python
from rice_agents.containers import Container
from rice_agents.agents import Agent

container = Container("ReviewTeam")  # Loads RiceDB config from rice_agents.toml

agent = Agent(
    name="SecurityAgent",
    llm=llm,
    container=container  # Shares memory with other agents in container
)

# Agent automatically logs to scratchpad during execution
response = await agent.run("Scan auth.py for vulnerabilities")

# Retrieve scratchpad entries for this agent's session
scratchpad_entries = container.memory_store.get_scratchpad(
    session_id=agent.session_id
)
```

## Examples

The `examples/` directory contains 14 comprehensive examples:

| Example                     | Description                    |
| --------------------------- | ------------------------------ |
| `01_basic_tool`             | Simple agent with tool calling |
| `02_memory_rag`             | RAG with vector memory         |
| `03_flows`                  | Sequential and parallel flows  |
| `04_adaptive_swarm`         | Dynamic agent orchestration    |
| `05_hierarchical_dev_team`  | Multi-level agent hierarchy    |
| `06_interactive_filesystem` | File system interaction        |
| `07_ricedb_memory`          | RiceDB integration             |
| `08_massive_research_swarm` | 100+ concurrent agents         |
| `09_city_logistics_swarm`   | Complex coordination patterns  |
| `10_code_review_swarm`      | Event-driven code review       |
| `11_adaptive_code_review`   | Dynamic planning for reviews   |
| `12_retrieval_benchmark`    | Memory retrieval testing       |
| `13_adaptive_sdr`           | Sales development agents       |
| `14_complex_config`         | Advanced configuration         |

## Development

This project uses `uv` for development:

```bash
# Install dependencies
make install

# Run tests
make test

# Lint code
make lint

# Format code
make format

# Run all checks
make check

# Build package
make build
```

## Documentation

See the [Documentation](docs/rice_agents/index.md) for detailed guides:

- [Getting Started](docs/rice_agents/getting_started.md)
- [Core Concepts](docs/rice_agents/concepts.md)
- [Containers & Configuration](docs/rice_agents/containers.md)
- [RiceDB Integration](docs/rice_agents/ricedb_integration.md)
- [Complex Patterns](docs/rice_agents/complex_patterns.md)

## License

Copyright (C) 2025 Reliable AI, Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
