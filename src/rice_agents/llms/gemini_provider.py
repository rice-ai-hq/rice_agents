import os
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from .base import LLMProvider, RiceLLMResponse, ToolCall
from ..tools.base import RiceTool

class GeminiProvider(LLMProvider):
    """Google Gemini implementation of LLMProvider using google-genai SDK."""

    def __init__(self, model: str = "gemini-1.5-flash", api_key: Optional[str] = None, **kwargs):
        api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        super().__init__(model, api_key, **kwargs)
        self.client = genai.Client(api_key=self.api_key)

    async def chat(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[RiceTool]] = None,
        system_prompt: Optional[str] = None
    ) -> RiceLLMResponse:
        
        # 1. Prepare Tools
        gemini_tools = None
        if tools:
            tool_declarations = [t.gemini_schema for t in tools]
            gemini_tools = [types.Tool(function_declarations=tool_declarations)]

        # 2. Prepare Config
        config_args = {k: v for k, v in self.config.items() if k not in ["tools", "system_instruction"]}
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=gemini_tools,
            **config_args
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
                        # tc is dict: {'name': ..., 'args': ..., 'id': ...}
                        parts.append(types.Part(
                            function_call=types.FunctionCall(
                                name=tc['name'],
                                args=tc['args']
                            )
                        ))
                gemini_contents.append(types.Content(role="model", parts=parts))

            elif role == "tool":
                # OpenAI format: role='tool', content=result, name=name, tool_call_id=...
                # Gemini expects this in a 'function' role (or 'user' in some contexts, but 'user' with function_response is safer)
                # Google GenAI SDK v1 usually uses 'user' role for function responses in chat mode.
                
                # We need to construct a FunctionResponse
                parts.append(types.Part(
                    function_response=types.FunctionResponse(
                        name=m.get("name"),
                        response={"result": m.get("content")} # wrapper dict
                    )
                ))
                gemini_contents.append(types.Content(role="user", parts=parts))

        # 4. Generate Content
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=gemini_contents,
            config=config
        )

        # 5. Parse Response
        content_text = None
        tool_calls = []
        
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.text:
                        content_text = (content_text or "") + part.text
                    
                    if part.function_call:
                        # part.function_call has .name and .args
                        # args is usually a dict
                        tool_calls.append(ToolCall(
                            name=part.function_call.name,
                            args=part.function_call.args,
                            # Gemini doesn't always strictly use IDs like OpenAI, but we can generate one or leave None
                            id=None 
                        ))
        
        usage = {}
        if response.usage_metadata:
            # Mapping common fields
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count
            }

        return RiceLLMResponse(
            content=content_text,
            tool_calls=tool_calls,
            provider="google",
            model=self.model,
            usage=usage
        )
