import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock ricedb before importing the store module
mock_ricedb = MagicMock()
sys.modules["ricedb"] = mock_ricedb
sys.modules["ricedb.utils"] = MagicMock()

# Now we can import
from rice_agents.agents.base import Agent  # noqa: E402
from rice_agents.memory.ricedb_store import RiceDBStore  # noqa: E402


@pytest.fixture
def mock_ricedb_client():
    # We need to patch the RiceDBClient that was imported/assigned in ricedb_store
    # Since we mocked the module 'ricedb' before import, RiceDBStore should have imported RiceDBClient from the mock
    # So RiceDBStore.RiceDBClient should be our mock class.

    # However, ricedb_store.py does: `from ricedb import RiceDBClient`
    # So `RiceDBClient` in `ricedb_store` is `mock_ricedb.RiceDBClient`.

    with patch("rice_agents.memory.ricedb_store.RiceDBClient") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        mock_instance.connect.return_value = True
        yield mock_instance


def test_ricedb_store_init(mock_ricedb_client):
    # Ensure RiceDBClient is not None (it shouldn't be if our mock worked)
    assert RiceDBStore is not None

    store = RiceDBStore(host="localhost")
    store.client.connect.assert_called_once()  # type: ignore


def test_ricedb_store_add_texts(mock_ricedb_client):
    store = RiceDBStore()
    # Mock uuid to return a known value so we can predict the int hash?
    # Or just pass explicit IDs that are parseable as ints
    store.add_texts(["hello"], metadatas=[{"a": 1}], ids=["100"])

    store.client.insert_text.assert_called_with(  # type: ignore
        node_id=100,
        text="hello",
        metadata={"a": 1},
        embedding_generator=store.embedding_generator,
        user_id=1,
    )


def test_ricedb_store_query(mock_ricedb_client):
    store = RiceDBStore()
    store.client.search_text.return_value = [  # type: ignore
        {"metadata": {"text": "hello", "a": 1}}
    ]
    results = store.query("hi")
    assert results == ["hello"]
    store.client.search_text.assert_called()  # type: ignore


def test_ricedb_scratchpad(mock_ricedb_client):
    store = RiceDBStore()
    mock_memory = MagicMock()
    store.client.memory = mock_memory

    store.add_scratchpad("sess1", "agent1", "content")
    mock_memory.add.assert_called_with(
        session_id="sess1", agent="agent1", content="content", metadata=None, ttl=None
    )


@pytest.mark.asyncio
async def test_agent_with_ricedb_scratchpad(mock_ricedb_client):
    store = RiceDBStore()
    mock_memory = MagicMock()
    store.client.memory = mock_memory  # type: ignore
    store.client.search_text.return_value = []  # type: ignore

    mock_llm = MagicMock()

    async def mock_chat(*args, **kwargs):
        from rice_agents.llms.base import RiceLLMResponse

        return RiceLLMResponse(content="Response", provider="mock", model="mock")

    mock_llm.chat.side_effect = mock_chat

    agent = Agent("TestAgent", mock_llm, memory=store)

    await agent.run("Task")

    # Verify scratchpad was called for task start
    assert mock_memory.add.called
    # Check that it was called with "Started task"
    calls = mock_memory.add.call_args_list
    start_task_call = next(
        (call for call in calls if "Started task" in call.kwargs.get("content", "")),
        None,
    )
    assert start_task_call is not None
    assert start_task_call.kwargs["agent"] == "TestAgent"
