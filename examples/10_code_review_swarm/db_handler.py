import os
import time
import uuid
import json
from typing import List, Dict, Optional, Any
import logging
from dotenv import load_dotenv

load_dotenv()

try:
    from ricedb import RiceDBClient
except ImportError:
    RiceDBClient = None

logger = logging.getLogger(__name__)


class SwarmRiceDBHandler:
    def __init__(
        self,
        host: str = "localhost",
        user_id: int = 101,
        username: str = "admin",
        password: str = "password123",
    ):
        if RiceDBClient is None:
            raise ImportError("RiceDB not installed")

        # Remote connection settings from environment
        HOST = os.environ.get("RICEDB_HOST", host)
        PORT = int(os.environ.get("RICEDB_PORT", "80"))
        PASSWORD = os.environ.get("RICEDB_PASSWORD", password)
        SSL = os.environ.get("RICEDB_SSL", "false").lower() == "true"

        # Initialize client (auto-detects transport)
        self.client = RiceDBClient(HOST, port=PORT)
        self.client.ssl = SSL

        try:
            self.client.connect()
        except Exception as e:
            logger.warning(f"Failed to connect to RiceDB at {HOST}:{PORT}: {e}")

        # Auth
        try:
            self.client.login(username, PASSWORD)
        except Exception as e:
            logger.warning(f"Login failed: {e}")

        self.user_id = user_id
        self.session_id = f"review-session-{uuid.uuid4().hex[:8]}"

    def insert_code_file(self, file_path: str, content: str, project_root: str):
        rel_path = os.path.relpath(file_path, project_root)
        # Deterministic node ID from path hash
        node_id = abs(hash(rel_path)) % 10000000

        metadata = {
            "type": "code_file",
            "file_path": rel_path,
            "extension": os.path.splitext(rel_path)[1],
            "timestamp": time.time(),
            "text": content,
        }

        self.client.insert(
            node_id=node_id,
            text=content,
            metadata=metadata,
            user_id=self.user_id,
        )

    def write_scratchpad_entry(
        self,
        agent_name: str,
        content: str,
        related_file: Optional[str] = None,
        ttl: Optional[int] = None,
    ):
        """
        Agents use this to write their findings/thoughts using the native Agent Memory.
        """
        meta = {"type": "scratchpad_entry"}
        if related_file:
            meta["related_file"] = related_file

        # Use native memory if available
        if hasattr(self.client, "memory"):
            self.client.memory.add(
                session_id=self.session_id,
                agent=agent_name,
                content=content,
                metadata=meta,
                ttl=ttl,
            )
        else:
            # Fallback
            node_id = abs(hash(f"{agent_name}_{time.time()}")) % 10000000
            meta["agent"] = agent_name
            meta["timestamp"] = time.time()
            meta["text"] = content

            self.client.insert(
                node_id=node_id,
                text=content,
                metadata=meta,
                user_id=self.user_id,
            )

    def get_scratchpad_entries(self, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Retrieve scratchpad entries from native memory.
        """
        if hasattr(self.client, "memory"):
            return self.client.memory.get(
                session_id=self.session_id, limit=100, filter=filter_dict
            )
        return []

    def link_files(
        self, source_path: str, relation: str, target_path: str, project_root: str
    ):
        rel_source = os.path.relpath(source_path, project_root)
        rel_target = os.path.relpath(target_path, project_root)

        source_id = abs(hash(rel_source)) % 10000000
        target_id = abs(hash(rel_target)) % 10000000

        try:
            self.client.link(source_id, relation, target_id)
        except Exception as e:
            logger.warning(f"Failed to link {rel_source} -> {rel_target}: {e}")

    def get_code_files(self, query: str = "", limit: int = 10) -> List[Dict]:
        if not query:
            query = "code"

        results = self.client.search(
            query=query,
            k=limit * 5,
            user_id=self.user_id,
        )
        # Client-side filtering to ensure we only get code files
        # This avoids finding unrelated data from other examples (like Quantum Physics facts)
        filtered = [
            r for r in results if r.get("metadata", {}).get("type") == "code_file"
        ]
        return filtered[:limit]
