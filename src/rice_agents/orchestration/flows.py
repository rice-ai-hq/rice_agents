import asyncio
from typing import Any


class SequentialFlow:
    """
    Executes a list of agents (or other flows) in sequence.
    The output of one agent becomes the input of the next.
    """

    def __init__(self, agents: list[Any], name: str = "SequentialFlow"):
        self.agents = agents
        self.name = name

    async def run(self, initial_task: str) -> str:
        current_input = initial_task
        for i, agent in enumerate(self.agents):
            agent_name = getattr(agent, "name", f"Step-{i + 1}")
            print(
                f"--- [{self.name}] Step {i + 1}/{len(self.agents)}: {agent_name} ---"
            )
            # We treat the previous output as the new task for the next agent
            current_input = await agent.run(current_input)
        return current_input


class ParallelFlow:
    """
    Executes a list of agents (or other flows) in parallel on the same task.
    Returns a list of results.
    """

    def __init__(self, agents: list[Any], name: str = "ParallelFlow"):
        self.agents = agents
        self.name = name

    async def run(self, task: str) -> list[str]:
        print(f"--- [{self.name}] Starting {len(self.agents)} agents ---")
        tasks = [agent.run(task) for agent in self.agents]
        results = await asyncio.gather(*tasks)
        print(f"--- [{self.name}] Finished ---")
        return results
