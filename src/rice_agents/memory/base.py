from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStore(ABC):
    """Abstract base class for vector storage."""
    
    @abstractmethod
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> None:
        """Add texts to the vector store."""
        pass

    @abstractmethod
    def query(self, query: str, n_results: int = 5) -> List[str]:
        """Query the vector store for similar texts."""
        pass
