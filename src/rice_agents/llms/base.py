from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Standardized representation of a tool call."""

    name: str
    args: dict[str, Any]
    id: str | None = None


class RiceLLMResponse(BaseModel):
    """Standardized response from any LLM provider."""

    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    raw_response: Any = Field(default=None, exclude=True)
    provider: str
    model: str
    usage: dict[str, int] = Field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: str, api_key: str, **kwargs):
        self.model = model
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        system_prompt: str | None = None,
    ) -> RiceLLMResponse:
        """
        Send messages to the LLM and get a response.

        Args:
            messages: List of message dicts (role, content).
            tools: List of RiceTool objects (or provider-specific tool schemas).
            system_prompt: Optional system instruction.

        Returns:
            RiceLLMResponse: Standardized response object.
        """
        pass
