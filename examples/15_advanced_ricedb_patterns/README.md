# Advanced RiceDB Patterns

This example demonstrates advanced workflow patterns enabled by RiceDB's Vector-Graph architecture, Cortex (Scratchpad/Sessions), and Holographic Merge.

## Patterns

1.  **Cortex Session Isolation** (`cortex_session_isolation.py`):

    - Demonstrates "Forking Reality" where an agent can test hypotheses or make risky changes in an isolated session.
    - Shows shadowing (overriding base facts) and commitment (merging back to base).

2.  **Nested Agent Collaboration** (`nested_agent_collaboration.py`):

    - Demonstrates hierarchical session management (Supervisor -> Worker).
    - Worker inherits Supervisor's context, makes changes, and commits back to Supervisor without affecting Global Base.

3.  **Multi-Agent Branching** (`multi_agent_branching.py`):
    - Demonstrates parallel execution where multiple agents (Architect vs Feature Dev) work in separate, isolated realities.
    - Shows how one branch can be committed while another is dropped or rebased.

## Usage

Run all examples:

```bash
make run
```

Or individually:

```bash
make run-isolation
make run-nested
make run-branching
```
