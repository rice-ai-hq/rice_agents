import time
import uuid
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class TaskPayload(BaseModel):
    focus_query: str
    file_context: Optional[List[str]] = None
    instruction: str


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # e.g., "review_code", "synthesis"
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    assigned_to: Optional[str] = None  # Agent Role or Specific ID
    priority: Literal["high", "medium", "low"] = "medium"
    payload: TaskPayload
    round: int = 1
    created_at: float = Field(default_factory=time.time)


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    type: Literal["vulnerability", "bug", "optimization", "style", "info"]
    severity: Literal["critical", "high", "medium", "low"]
    description: str
    file: Optional[str] = None
    line: Optional[str] = None
    recommendation: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
