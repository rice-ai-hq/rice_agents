from rice_agents.tools.base import RiceTool, tool


# --- Test Tools ---
def simple_func(x: int, y: int) -> int:
    """Adds two numbers."""
    return x + y


@tool("custom_adder")
def decorated_func(a: str, b: str = "default") -> str:
    """Concatenates strings."""
    return a + b


def test_tool_initialization():
    t = RiceTool(simple_func)
    assert t.name == "simple_func"
    assert t.description == "Adds two numbers."
    assert t(1, 2) == 3


def test_tool_decorator():
    assert isinstance(decorated_func, RiceTool)
    assert decorated_func.name == "custom_adder"
    assert decorated_func("hello", "world") == "helloworld"


def test_openai_schema_generation():
    t = RiceTool(simple_func)
    schema = t.openai_schema

    assert schema["type"] == "function"
    assert schema["function"]["name"] == "simple_func"
    assert "x" in schema["function"]["parameters"]["properties"]
    assert "y" in schema["function"]["parameters"]["properties"]
    assert schema["function"]["parameters"]["properties"]["x"]["type"] == "integer"
    assert "x" in schema["function"]["parameters"]["required"]


def test_gemini_schema_generation():
    # decorated_func is already a RiceTool instance
    t = decorated_func
    schema = t.gemini_schema

    assert schema["name"] == "custom_adder"
    assert schema["parameters"]["properties"]["a"]["type"] == "string"
    # 'b' has a default, so it shouldn't be required
    assert "b" not in schema["parameters"]["required"]
