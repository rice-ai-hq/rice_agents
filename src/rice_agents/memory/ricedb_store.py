import logging
import uuid
from typing import Any

from .base import VectorStore

logger = logging.getLogger(__name__)

try:
    from ricedb import RiceDBClient
    from ricedb.utils import DummyEmbeddingGenerator
except ImportError:
    RiceDBClient: Any = None
    DummyEmbeddingGenerator: Any = None


class RiceDBStore(VectorStore):
    """
    RiceDB implementation of the VectorStore interface.
    Also provides access to RiceDB's Agent Memory (Scratchpad) features.
    """

    def __init__(
        self,
        host: str = "localhost",
        user_id: int = 1,
        embedding_generator: Any = None,
    ):
        if RiceDBClient is None:
            raise ImportError(
                "RiceDB is not installed. Please install it with `pip install ricedb`."
            )

        self.client = RiceDBClient(host)
        if not self.client.connect():
            # In a real scenario we might want to retry or fail hard
            logger.warning(f"Failed to connect to RiceDB at {host}")

        self.user_id = user_id

        # Use provided generator or dummy one
        if embedding_generator:
            self.embedding_generator = embedding_generator
        elif DummyEmbeddingGenerator:
            self.embedding_generator = DummyEmbeddingGenerator()
        else:
            self.embedding_generator = None

    def add_texts(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        """
        Add texts to RiceDB.
        Note: RiceDB typically uses integer node_ids.
        We will attempt to hash string IDs to integers if provided,
        or generate new integer IDs.
        """
        if not ids:
            ids = [str(uuid.uuid4()) for _ in texts]

        if metadatas is None:
            metadatas = [{} for _ in texts]

        for i, text in enumerate(texts):
            # RiceDB expects integer node_id.
            # We try to convert the ID to int if possible, otherwise hash it.
            try:
                node_id = int(ids[i])
            except ValueError:
                # Simple hash to get a positive integer
                node_id = abs(hash(ids[i])) % (10**9)

            try:
                self.client.insert_text(
                    node_id=node_id,
                    text=text,
                    metadata=metadatas[i],
                    embedding_generator=self.embedding_generator,
                    user_id=self.user_id,
                )
            except Exception as e:
                logger.error(f"Failed to insert text into RiceDB: {e}")

    def query(self, query: str, n_results: int = 5) -> list[str]:
        """
        Query RiceDB for similar texts.
        """
        try:
            results = self.client.search_text(
                query=query,
                embedding_generator=self.embedding_generator,
                user_id=self.user_id,
                k=n_results,
            )

            # Extract text from results
            # RiceDB results usually contain 'metadata' with 'text' if inserted via insert_text
            texts = []
            for res in results:
                metadata = res.get("metadata", {})
                if "text" in metadata:
                    texts.append(metadata["text"])

            return texts

        except Exception as e:
            logger.error(f"Failed to query RiceDB: {e}")
            return []

    # --- Agent Memory (Scratchpad) Features ---

    def add_scratchpad(
        self,
        session_id: str,
        agent: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        ttl: int | None = None,
    ) -> None:
        """
        Add an entry to the agent scratchpad memory.
        """
        if hasattr(self.client, "memory"):
            try:
                self.client.memory.add(
                    session_id=session_id,
                    agent=agent,
                    content=content,
                    metadata=metadata,
                    ttl=ttl,
                )
            except Exception as e:
                logger.error(f"Failed to add to scratchpad: {e}")
        else:
            logger.warning("RiceDB client does not support memory/scratchpad features.")

    def get_scratchpad(
        self, session_id: str, filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve entries from the agent scratchpad memory.
        """
        if hasattr(self.client, "memory"):
            try:
                return self.client.memory.get(session_id=session_id, filter=filter)
            except Exception as e:
                logger.error(f"Failed to get from scratchpad: {e}")
                return []
        else:
            logger.warning("RiceDB client does not support memory/scratchpad features.")
            return []

    def clear_scratchpad(self, session_id: str) -> None:
        """
        Clear scratchpad memory for a session.
        """
        if hasattr(self.client, "memory"):
            try:
                self.client.memory.clear(session_id=session_id)
            except Exception as e:
                logger.error(f"Failed to clear scratchpad: {e}")
        else:
            logger.warning("RiceDB client does not support memory/scratchpad features.")
