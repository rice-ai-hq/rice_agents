import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Mock ricedb modules to avoid import errors and connection attempts
mock_ricedb = MagicMock()
mock_ricedb_client = MagicMock()
mock_ricedb.RiceDBClient = mock_ricedb_client
sys.modules["ricedb"] = mock_ricedb
sys.modules["ricedb.utils"] = MagicMock()

from rice_agents.containers.base import Container, get_default_container
from rice_agents.config import Config
from rice_agents.agents.base import Agent
from rice_agents.llms.base import RiceLLMResponse


@pytest.fixture
def mock_config():
    with patch("rice_agents.containers.base.global_config") as mock_conf:
        yield mock_conf


@pytest.fixture
def mock_llm():
    llm = MagicMock()

    async def mock_chat(*args, **kwargs):
        return RiceLLMResponse(content="Test Response", provider="mock", model="mock")

    llm.chat.side_effect = mock_chat
    return llm


def test_container_initialization(mock_config):
    mock_config.get_container_config.return_value = {
        "memory": "ricedb",
        "memory_config": {"host": "localhost"},
    }

    container = Container("test_container")
    assert container.name == "test_container"
    assert (
        container.memory_store is not None
    )  # Should be initialized because we mocked ricedb
    assert container.config["memory"] == "ricedb"


def test_agent_registration(mock_config, mock_llm):
    mock_config.get_container_config.return_value = {}
    container = Container("test_container")

    agent = Agent("TestBot", mock_llm)

    # Manually register
    container.register_agent(agent)

    assert agent.name in container.agents
    assert agent.container == container


def test_agent_auto_container_assignment(mock_config, mock_llm):
    # Reset default container
    import rice_agents.containers.base

    rice_agents.containers.base._default_container = None

    agent = Agent("TestBot", mock_llm)
    assert agent.container is not None
    assert agent.container.name == "default"


@pytest.mark.asyncio
async def test_auto_memory_hook(mock_config, mock_llm):
    # Setup container with auto_memory = True
    mock_config.get_container_config.return_value = {
        "memory": "ricedb",
        "auto_memory": True,
    }

    container = Container("memory_container")
    # Verify memory store mock is set up
    assert container.memory_store is not None

    # We need to ensure the memory_store has the add_texts method mocked properly
    # RiceDBStore uses self.client.insert_text, but add_texts is what we call
    # Let's mock add_texts directly on the instance to be sure
    container.memory_store.add_texts = MagicMock()

    agent = Agent("MemoryBot", mock_llm, container=container)

    # Run agent
    await agent.run("Hello")

    # Check if add_texts was called
    container.memory_store.add_texts.assert_called_once()
    args, kwargs = container.memory_store.add_texts.call_args
    assert args[0] == ["Test Response"]  # The content from mock_llm
    assert kwargs["metadatas"][0]["agent"] == "MemoryBot"
    assert kwargs["metadatas"][0]["source"] == "agent_output"
