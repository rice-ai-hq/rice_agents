from typing import Any, Optional, TYPE_CHECKING
import logging

from ..config import config as global_config
from ..memory.ricedb_store import RiceDBStore
from ..memory.base import VectorStore

if TYPE_CHECKING:
    from ..agents.base import Agent

logger = logging.getLogger(__name__)


class Container:
    """
    A container for agents that provides shared configuration and resources.
    """

    def __init__(self, name: str = "default", config: dict[str, Any] | None = None):
        self.name = name
        self.config = global_config.get_container_config(name)
        if config:
            self.config.update(config)

        self.agents: dict[str, "Agent"] = {}
        self.memory_store: Optional[VectorStore] = None

        self._setup_resources()

    def _setup_resources(self):
        # Setup Memory if configured
        mem_config = self.config.get("memory_config", {})
        memory_type = self.config.get("memory")

        # If memory_type is specifically "ricedb", we try to initialize it.
        if memory_type == "ricedb":
            host = mem_config.get("host", "localhost")
            user_id = mem_config.get("user_id", 1)
            username = mem_config.get("username")
            password = mem_config.get("password")

            try:
                self.memory_store = RiceDBStore(
                    host=host, user_id=user_id, username=username, password=password
                )
                logger.info(f"Container '{self.name}': RiceDB initialized.")
            except Exception as e:
                logger.error(
                    f"Container '{self.name}': Failed to initialize RiceDB: {e}"
                )

    def register_agent(self, agent: "Agent"):
        """
        Registers an agent with this container.
        Injects container resources into the agent if they are missing in the agent.
        """
        self.agents[agent.name] = agent
        # Only set if not already set or different to avoid recursion if agent sets it
        if agent.container != self:
            agent.container = self

        # Inject Memory if agent doesn't have one and container does
        if not agent.memory and self.memory_store:
            agent.memory = self.memory_store

    async def run_agent(self, agent_name: str, task: str) -> str:
        """
        Runs an agent within the container context.
        """
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found in container {self.name}")

        # Run the agent
        return await agent.run(task)

    def on_agent_finish(self, agent: "Agent", task: str, response: str):
        """
        Hook called by Agent when it finishes a task.
        """
        if self.config.get("auto_memory", False) and self.memory_store:
            try:
                logger.info(
                    f"Container '{self.name}': Auto-adding memory for agent '{agent.name}'"
                )
                self.memory_store.add_texts(
                    [response],
                    metadatas=[
                        {
                            "source": "agent_output",
                            "agent": agent.name,
                            "task": task,
                            "container": self.name,
                        }
                    ],
                )
            except Exception as e:
                logger.error(f"Container '{self.name}': Error auto-adding memory: {e}")


_default_container: Optional[Container] = None


def get_default_container() -> Container:
    global _default_container
    if _default_container is None:
        _default_container = Container(name="default")
    return _default_container
