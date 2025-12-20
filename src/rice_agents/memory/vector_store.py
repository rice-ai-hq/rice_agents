import uuid
import chromadb
from typing import List, Dict, Any, Optional
from .base import VectorStore

class ChromaDBStore(VectorStore):
    def __init__(self, collection_name: str = "rice_agents_memory", path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=path)
        # Using default embedding function (all-MiniLM-L6-v2) implicitly
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> None:
        if not ids:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query: str, n_results: int = 5) -> List[str]:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        if results and results['documents']:
            return results['documents'][0]
        return []
