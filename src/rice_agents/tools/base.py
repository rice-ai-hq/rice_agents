import inspect
import typing
from typing import Any, Callable, Dict, List, Optional, get_type_hints
from pydantic import BaseModel

class RiceTool:
    """
    A wrapper around a Python function that provides metadata and schema generation
    for various LLM providers.
    """
    def __init__(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        self.signature = inspect.signature(func)
        self.type_hints = get_type_hints(func)

    def __call__(self, *args, **kwargs):
        """Execute the wrapped function."""
        return self.func(*args, **kwargs)

    @property
    def openai_schema(self) -> Dict[str, Any]:
        """Generates OpenAI-compatible function schema."""
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in self.signature.parameters.items():
            if param_name == 'self':
                continue
            
            param_type = self.type_hints.get(param_name, Any)
            json_type = self._get_json_type(param_type)
            
            parameters["properties"][param_name] = {
                "type": json_type,
                # In a real impl, we'd parse docstrings for param descriptions
            }
            
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters
            }
        }

    @property
    def gemini_schema(self) -> Dict[str, Any]:
        """
        Generates Google Gemini compatible function declaration.
        Note: The google-genai SDK 1.x often takes a dict or a specific object.
        We will return the dict representation that matches the API.
        """
        # Gemini uses a similar OpenAPI-ish schema but structure is slightly different
        # usually passed in 'tools' list as function_declarations
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.openai_schema["function"]["parameters"]
        }

    @property
    def anthropic_schema(self) -> Dict[str, Any]:
        """Generates Anthropic-compatible tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.openai_schema["function"]["parameters"]
        }

    def _get_json_type(self, py_type: Any) -> str:
        """Helper to map python types to JSON types."""
        if py_type == str:
            return "string"
        if py_type == int:
            return "integer"
        if py_type == float:
            return "number"
        if py_type == bool:
            return "boolean"
        if py_type == list or typing.get_origin(py_type) == list:
            return "array"
        if py_type == dict or typing.get_origin(py_type) == dict:
            return "object"
        return "string" # Default fallback

def tool(name: Optional[str] = None, description: Optional[str] = None):
    """Decorator to register a function as a RiceTool."""
    def decorator(func):
        return RiceTool(func, name, description)
    return decorator
