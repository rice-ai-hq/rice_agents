import asyncio

from ..agents.base import Agent


class SequentialFlow:
    """
    Executes a list of agents in sequence.
    The output of one agent becomes the input of the next.
    """

    def __init__(self, agents: list[Agent]):
        self.agents = agents

    async def run(self, initial_task: str) -> str:
        current_input = initial_task
        for i, agent in enumerate(self.agents):
            print(
                f"--- [SequentialFlow] Step {i + 1}/{len(self.agents)}: {agent.name} ---"
            )
            # We treat the previous output as the new task for the next agent
            current_input = await agent.run(current_input)
        return current_input


class ParallelFlow:
    """
    Executes a list of agents in parallel on the same task.
    Returns a list of results.
    """

    def __init__(self, agents: list[Agent]):
        self.agents = agents

    async def run(self, task: str) -> list[str]:
        print(f"--- [ParallelFlow] Starting {len(self.agents)} agents ---")
        tasks = [agent.run(task) for agent in self.agents]
        results = await asyncio.gather(*tasks)
        print("--- [ParallelFlow] Finished ---")
        return results
