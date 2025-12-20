from unittest.mock import MagicMock

import pytest

from rice_agents.agents.base import Agent
from rice_agents.llms.base import RiceLLMResponse, ToolCall
from rice_agents.tools.base import tool


@tool("get_test_value")
def get_test_value() -> str:
    return "tested"


@pytest.mark.asyncio
async def test_agent_run_basic():
    mock_llm = MagicMock()

    async def mock_chat(*args, **kwargs):
        return RiceLLMResponse(content="Hello World", provider="mock", model="mock")

    mock_llm.chat.side_effect = mock_chat

    agent = Agent("TestBot", mock_llm)
    response = await agent.run("Hi")

    assert response == "Hello World"
    assert len(agent.history) == 2  # User + Assistant


@pytest.mark.asyncio
async def test_agent_tool_calling():
    mock_llm = MagicMock()

    # Sequence of responses: Tool Call -> Final Answer
    async def mock_chat_sequence(messages, **kwargs):
        if len(messages) == 1:  # User message only
            return RiceLLMResponse(
                provider="mock",
                model="mock",
                tool_calls=[ToolCall(name="get_test_value", args={}, id="call_1")],
            )
        else:  # After tool execution
            return RiceLLMResponse(
                content="The value is tested", provider="mock", model="mock"
            )

    mock_llm.chat.side_effect = mock_chat_sequence

    agent = Agent("ToolBot", mock_llm, tools=[get_test_value])
    response = await agent.run("Get the value")

    assert response == "The value is tested"
    # Verify history structure: User -> Assistant(ToolCall) -> Tool(Result) -> Assistant(Final)
    assert len(agent.history) == 4
    assert agent.history[2]["role"] == "tool"
    assert agent.history[2]["content"] == "tested"
