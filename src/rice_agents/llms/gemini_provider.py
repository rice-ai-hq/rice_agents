import os
from typing import Any

from google import genai
from google.genai import types

from ..tools.base import RiceTool
from .base import LLMProvider, RiceLLMResponse, ToolCall


class GeminiProvider(LLMProvider):
    """Google Gemini implementation of LLMProvider using google-genai SDK."""

    def __init__(
        self, model: str = "gemini-1.5-flash", api_key: str | None = None, **kwargs
    ):
        api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        super().__init__(model, api_key, **kwargs)  # ty:ignore[invalid-argument-type]
        self.client = genai.Client(api_key=self.api_key)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[RiceTool] | None = None,
        system_prompt: str | None = None,
    ) -> RiceLLMResponse:
        # 1. Prepare Tools
        gemini_tools = None
        if tools:
            tool_declarations = [t.gemini_schema for t in tools]
            gemini_tools = [types.Tool(function_declarations=tool_declarations)]  # ty:ignore[invalid-argument-type]

        # 2. Prepare Config
        config_args = {
            k: v
            for k, v in self.config.items()
            if k not in ["tools", "system_instruction"]
        }
        config = types.GenerateContentConfig(
            system_instruction=system_prompt, tools=gemini_tools, **config_args
        )

        # 3. Prepare Contents
        gemini_contents = []
        for m in messages:
            role = m["role"]
            content = m.get("content")
            tool_calls = m.get("tool_calls", [])

            parts = []

            if role == "user":
                if content:
                    parts.append(types.Part(text=str(content)))
                gemini_contents.append(types.Content(role="user", parts=parts))

            elif role == "assistant":
                # If there's text content
                if content:
                    parts.append(types.Part(text=str(content)))

                # If there were tool calls in this assistant turn
                if tool_calls:
                    for tc in tool_calls:
                        # tc is dict: {'name': ..., 'args': ..., 'id': ..., 'extra': ...}
                        extra = tc.get("extra", {})
                        # Extract thought_signature from extra if present
                        part_kwargs = {}
                        if "thought_signature" in extra:
                            part_kwargs["thought_signature"] = extra[
                                "thought_signature"
                            ]

                        # Remove thought_signature from extra to avoid passing it to FunctionCall
                        # (assuming FunctionCall doesn't take it, but Part does)
                        fc_extra = {
                            k: v for k, v in extra.items() if k != "thought_signature"
                        }

                        parts.append(
                            types.Part(
                                function_call=types.FunctionCall(
                                    name=tc["name"], args=tc["args"], **fc_extra
                                ),
                                **part_kwargs,
                            )
                        )
                gemini_contents.append(types.Content(role="model", parts=parts))

            elif role == "tool":
                # OpenAI format: role='tool', content=result, name=name, tool_call_id=...
                # Gemini expects this in a 'function' role (or 'user' in some contexts, but 'user' with function_response is safer)
                # Google GenAI SDK v1 usually uses 'user' role for function responses in chat mode.

                # We need to construct a FunctionResponse
                parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=m.get("name"),
                            response={"result": m.get("content")},  # wrapper dict
                        )
                    )
                )
                gemini_contents.append(types.Content(role="tool", parts=parts))

        # 4. Generate Content
        response = await self.client.aio.models.generate_content(
            model=self.model, contents=gemini_contents, config=config
        )

        # 5. Parse Response
        content_text = None
        tool_calls = []

        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    # Debug: Inspect part attributes
                    # print(f"DEBUG: Part attributes: {dir(part)}")

                    if part.text:
                        content_text = (content_text or "") + part.text

                    if part.function_call:
                        # part.function_call has .name and .args
                        # args is usually a dict

                        # Extract extra fields (like thought_signature for Gemini 2/3)
                        extra = {}

                        # Capture thought_signature from the Part itself (per Gemini 3 docs)
                        if (
                            hasattr(part, "thought_signature")
                            and part.thought_signature
                        ):
                            extra["thought_signature"] = part.thought_signature
                        elif hasattr(part, "extra_content") and part.extra_content:  # noqa: SIM102
                            # Fallback to extra_content (seen in OpenAI compat docs)
                            # It might be nested like extra_content.google.thought_signature
                            if (
                                "google" in part.extra_content
                                and "thought_signature" in part.extra_content["google"]
                            ):
                                extra["thought_signature"] = part.extra_content[
                                    "google"
                                ]["thought_signature"]

                        # Check specific fields or dump model from function_call
                        if hasattr(part.function_call, "model_dump"):
                            fc_dict = part.function_call.model_dump()
                            for k, v in fc_dict.items():
                                if k not in ["name", "args"]:
                                    extra[k] = v

                        tool_calls.append(
                            ToolCall(
                                name=part.function_call.name,
                                args=part.function_call.args,
                                # Gemini doesn't always strictly use IDs like OpenAI, but we can generate one or leave None
                                id=None,
                                extra=extra,
                            )
                        )

        usage = {}
        if response.usage_metadata:
            # Mapping common fields, handle potential None values
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count or 0,
                "completion_tokens": response.usage_metadata.candidates_token_count
                or 0,
                "total_tokens": response.usage_metadata.total_token_count or 0,
            }

        return RiceLLMResponse(
            content=content_text,
            tool_calls=tool_calls,
            provider="google",
            model=self.model,
            usage=usage,  # ty:ignore[invalid-argument-type]
        )
