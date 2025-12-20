from unittest.mock import MagicMock

import pytest

from rice_agents.agents.base import Agent
from rice_agents.memory.vector_store import VectorStore


class MockVectorStore(VectorStore):
    def __init__(self):
        self.data = []

    def add_texts(self, texts, metadatas=None, ids=None):
        self.data.extend(texts)

    def query(self, query, n_results=5):
        # specific mock behavior
        if "color" in query:
            return ["My favorite color is blue."]
        return []


@pytest.mark.asyncio
async def test_agent_memory_interaction():
    mock_llm = MagicMock()

    # Mocking the async chat method
    async def async_chat(*args, **kwargs):
        from rice_agents.llms.base import RiceLLMResponse

        return RiceLLMResponse(content="I see.", provider="mock", model="mock")

    mock_llm.chat.side_effect = async_chat

    memory = MockVectorStore()
    memory.add_texts(["My favorite color is blue."])

    agent = Agent("TestBot", mock_llm, memory=memory)

    await agent.run("What is my favorite color?")

    # Check if history contains the context
    last_user_msg = agent.history[0]["content"]
    assert "[RELEVANT MEMORY]" in last_user_msg
    assert "My favorite color is blue." in last_user_msg
