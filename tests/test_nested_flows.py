import pytest

from rice_agents.orchestration.flows import ParallelFlow, SequentialFlow


class MockAgent:
    def __init__(self, name, return_val):
        self.name = name
        self.return_val = return_val

    async def run(self, task):
        return self.return_val


@pytest.mark.asyncio
async def test_nested_flows():
    # Setup
    agent1 = MockAgent("A1", "Out1")
    agent2 = MockAgent("A2", "Out2")

    # Nesting: Parallel inside Sequential
    # This caused the AttributeError before because ParallelFlow lacked .name
    parallel_step = ParallelFlow([agent1, agent2], name="MyParallelStep")

    pipeline = SequentialFlow([parallel_step], name="MainPipeline")

    # Execution
    # ParallelFlow returns a list ["Out1", "Out2"]
    # SequentialFlow will receive this list as the result of the first step
    result = await pipeline.run("Start")

    assert isinstance(result, list)
    assert "Out1" in result
    assert "Out2" in result
    assert parallel_step.name == "MyParallelStep"
