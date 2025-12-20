from abc import ABC, abstractmethod
from typing import Any


class VectorStore(ABC):
    """Abstract base class for vector storage."""

    @abstractmethod
    def add_texts(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        """Add texts to the vector store."""
        pass

    @abstractmethod
    def query(self, query: str, n_results: int = 5) -> list[str]:
        """Query the vector store for similar texts."""
        pass
