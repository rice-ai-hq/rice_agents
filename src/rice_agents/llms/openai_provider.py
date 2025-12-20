import json
import os
from typing import Any

from openai import AsyncOpenAI

from ..tools.base import RiceTool
from .base import LLMProvider, RiceLLMResponse, ToolCall


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLMProvider."""

    def __init__(self, model: str = "gpt-4o", api_key: str | None = None, **kwargs):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        super().__init__(model, api_key, **kwargs)
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[RiceTool] | None = None,
        system_prompt: str | None = None,
    ) -> RiceLLMResponse:
        final_messages = []
        if system_prompt:
            final_messages.append({"role": "system", "content": system_prompt})
        final_messages.extend(messages)

        openai_tools = [t.openai_schema for t in tools] if tools else None

        # Only pass tools param if tools are provided
        kwargs = self.config.copy()
        if openai_tools:
            kwargs["tools"] = openai_tools

        response = await self.client.chat.completions.create(
            model=self.model, messages=final_messages, **kwargs
        )

        message = response.choices[0].message

        rice_tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                rice_tool_calls.append(
                    ToolCall(
                        name=tc.function.name,
                        args=json.loads(tc.function.arguments),
                        id=tc.id,
                    )
                )

        return RiceLLMResponse(
            content=message.content,
            tool_calls=rice_tool_calls,
            provider="openai",
            model=self.model,
            usage=response.usage.model_dump() if response.usage else {},
        )
