import os
import json
from ricedb import RiceDBClient
from ricedb.utils import SentenceTransformersEmbeddingGenerator


class RiceDBHandler:
    def __init__(self):
        self.client = RiceDBClient("localhost")
        if not self.client.connect():
            raise Exception("RiceDB connection failed")

        try:
            self.client.login("admin", "password123")
        except:
            pass

        self.user_id = 15
        self.embed = SentenceTransformersEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2"
        )

    def ingest_kb(self, text):
        print("Ingesting Knowledge Base...")
        chunks = [line for line in text.split("\n") if line.strip()]
        for i, chunk in enumerate(chunks):
            self.client.insert_text(
                node_id=20000 + i,
                text=chunk,
                metadata={"type": "kb"},
                embedding_generator=self.embed,
                user_id=self.user_id,
            )

    def get_context(self, query):
        results = self.client.search_text(
            query=query, k=3, embedding_generator=self.embed, user_id=self.user_id
        )
        return "\n".join(
            [
                r["metadata"]["text"]
                for r in results
                if r["metadata"].get("type") == "kb"
            ]
        )

    def log_interaction(self, lead_id, content):
        self.client.insert_text(
            node_id=abs(hash(content)) % 10000000,
            text=content,
            metadata={"type": "interaction", "lead_id": lead_id},
            embedding_generator=self.embed,
            user_id=self.user_id,
        )
