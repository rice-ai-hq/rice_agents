# Core Concepts

## Agent

The `Agent` is the primary unit of execution.

```python
class Agent:
    def __init__(self, name: str, llm: LLMProvider, tools: list[RiceTool] = None, container: Container = None):
        ...
```

- **Identity**: `name` defines who the agent is (e.g., "Researcher", "Reviewer").
- **Intelligence**: `llm` provides the reasoning capability (Gemini, OpenAI).
- **Capability**: `tools` extend the agent's reach (file I/O, search, custom functions).
- **Context**: `container` provides shared state, memory, and configuration.

### Lifecycle

1.  **Initialization**: Agent registers with its Container.
2.  **Run**: `await agent.run(task)` starts the loop.
3.  **Thought**: Agent constructs a prompt history and calls the LLM.
4.  **Action**: If LLM requests a tool call, Agent executes it and feeds the result back.
5.  **Completion**: Agent returns the final answer.
6.  **Hook**: `Container.on_agent_finish` is called (for auto-memory).

## Container

A `Container` represents an execution environment or a logical group of agents.

- **Resource Management**: Holds the connection to RiceDB (Memory).
- **Configuration**: Loads settings from `rice_agents.toml`.
- **Coordination**: Agents in the same container share the same `memory_store`.

## LLM Provider

An abstraction over model APIs.

- `GeminiProvider`: Supports Google's Gemini models (including `gemini-3-flash-preview`).
- `OpenAIProvider`: Supports GPT models.

## Orchestration

Rice Agents supports various orchestration patterns:

- **SequentialFlow**: Chain agents (A -> B -> C).
- **ParallelFlow**: Run agents concurrently (A + B).
- **AdaptiveOrchestrator**: Dynamic planning where an agent decides the next steps at runtime.
