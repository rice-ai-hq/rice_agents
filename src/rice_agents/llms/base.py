from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    """Standardized representation of a tool call."""
    name: str
    args: Dict[str, Any]
    id: Optional[str] = None

class RiceLLMResponse(BaseModel):
    """Standardized response from any LLM provider."""
    content: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    raw_response: Any = Field(default=None, exclude=True)
    provider: str
    model: str
    usage: Dict[str, int] = Field(default_factory=dict)

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, model: str, api_key: str, **kwargs):
        self.model = model
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def chat(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Any]] = None,
        system_prompt: Optional[str] = None
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
