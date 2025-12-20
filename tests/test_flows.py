import pytest

from rice_agents.agents.base import Agent
from rice_agents.orchestration.flows import ParallelFlow, SequentialFlow


class MockAgent(Agent):
    def __init__(self, name, return_value):
        self.name = name
        self.return_value = return_value

    async def run(self, task):
        return f"{task} -> {self.return_value}"


@pytest.mark.asyncio
async def test_sequential_flow():
    a1 = MockAgent("A1", "Out1")
    a2 = MockAgent("A2", "Out2")

    flow = SequentialFlow([a1, a2])
    result = await flow.run("Input")

    # Input -> Out1 -> Out2
    # Logic: A1 receives "Input", returns "Input -> Out1"
    # A2 receives "Input -> Out1", returns "Input -> Out1 -> Out2"
    assert result == "Input -> Out1 -> Out2"


@pytest.mark.asyncio
async def test_parallel_flow():
    a1 = MockAgent("A1", "Out1")
    a2 = MockAgent("A2", "Out2")

    flow = ParallelFlow([a1, a2])
    results = await flow.run("Input")

    assert len(results) == 2
    assert results[0] == "Input -> Out1"
    assert results[1] == "Input -> Out2"
