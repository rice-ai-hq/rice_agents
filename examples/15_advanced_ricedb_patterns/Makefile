.PHONY: run setup run-isolation run-nested run-branching

setup:
	uv sync

run: run-isolation run-nested run-branching

run-isolation:
	uv run cortex_session_isolation.py

run-nested:
	uv run nested_agent_collaboration.py

run-branching:
	uv run multi_agent_branching.py
