import contextlib
import os

from dotenv import load_dotenv
from ricedb import RiceDBClient

load_dotenv()


class RiceDBHandler:
    def __init__(self):
        # Remote connection settings from environment
        HOST = os.environ.get("RICEDB_HOST", "localhost")
        PORT = int(os.environ.get("RICEDB_PORT", "80"))
        PASSWORD = os.environ.get("RICEDB_PASSWORD", "password123")
        SSL = os.environ.get("RICEDB_SSL", "false").lower() == "true"

        # Initialize client (auto-detects transport)
        self.client = RiceDBClient(HOST, port=PORT)
        self.client.ssl = SSL

        try:
            self.client.connect()
        except Exception as e:
            raise Exception(f"RiceDB connection failed: {e}") from e

        with contextlib.suppress(Exception):
            self.client.login("admin", PASSWORD)

        self.user_id = 15

    def ingest_kb(self, text):
        print("Ingesting Knowledge Base...")
        chunks = [line for line in text.split("\n") if line.strip()]
        for i, chunk in enumerate(chunks):
            self.client.insert(
                node_id=20000 + i,
                text=chunk,
                metadata={"type": "kb", "text": chunk},
                user_id=self.user_id,
            )

    def get_context(self, query):
        results = self.client.search(query=query, k=3, user_id=self.user_id)
        return "\n".join(
            [
                r["metadata"].get("text", "")
                for r in results
                if r.get("metadata", {}).get("type") == "kb"
            ]
        )

    def log_interaction(self, lead_id, content):
        self.client.insert(
            node_id=abs(hash(content)) % 10000000,
            text=content,
            metadata={"type": "interaction", "lead_id": lead_id, "text": content},
            user_id=self.user_id,
        )
