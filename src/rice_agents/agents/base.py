import inspect
import uuid
from typing import Any, Optional, TYPE_CHECKING

from ..llms.base import LLMProvider, ToolCall
from ..memory.base import VectorStore
from ..tools.base import RiceTool

if TYPE_CHECKING:
    from ..containers.base import Container


class Agent:
    """
    Base Agent class that manages LLM interaction, history, and tool execution.
    """

    def __init__(
        self,
        name: str,
        llm: LLMProvider,
        tools: list[RiceTool] | None = None,
        memory: VectorStore | None = None,
        system_prompt: str = "You are a helpful assistant.",
        session_id: str | None = None,
        container: Optional["Container"] = None,
    ):
        self.name = name
        self.llm = llm
        self.tools = tools or []
        self.memory = memory
        self.system_prompt = system_prompt
        self.history: list[dict[str, Any]] = []
        self.tool_map = {t.name: t for t in self.tools}
        self.session_id = session_id or str(uuid.uuid4())
        self.container = container
        if self.container is None:
            try:
                from ..containers import get_default_container

                self.container = get_default_container()
            except ImportError:
                pass

        if self.container:
            self.container.register_agent(self)

    async def run(self, task: str) -> str:
        """
        Executes the agent on a given task.
        """
        # RAG Retrieval
        context = ""
        if self.memory:
            # Scratchpad: Log task start
            add_scratchpad = getattr(self.memory, "add_scratchpad", None)
            if add_scratchpad:
                add_scratchpad(
                    session_id=self.session_id,
                    agent=self.name,
                    content=f"Started task: {task}",
                    metadata={"type": "task_start"},
                )

            try:
                results = self.memory.query(task, n_results=3)
                if results:
                    context = (
                        "\n[RELEVANT MEMORY]\n"
                        + "\n".join(results)
                        + "\n[END MEMORY]\n\n"
                    )
            except Exception as e:
                print(f"Warning: Memory query failed: {e}")

        # Add user message with context
        full_message = context + task if context else task
        self.history.append({"role": "user", "content": full_message})

        max_turns = 15
        current_turn = 0

        while current_turn < max_turns:
            current_turn += 1

            response = await self.llm.chat(
                messages=self.history,
                tools=self.tools,
                system_prompt=self.system_prompt,
            )

            # Handle tool calls
            if response.tool_calls:
                # Add assistant message with tool calls
                assistant_msg = {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": [
                        {"name": t.name, "args": t.args, "id": t.id}
                        for t in response.tool_calls
                    ],
                }
                self.history.append(assistant_msg)

                # Execute tools
                for tool_call in response.tool_calls:
                    print(f"[{self.name}] Calling tool: {tool_call.name}")

                    # Scratchpad: Log tool call
                    add_scratchpad = getattr(self.memory, "add_scratchpad", None)
                    if self.memory and add_scratchpad:
                        add_scratchpad(
                            session_id=self.session_id,
                            agent=self.name,
                            content=f"Calling tool: {tool_call.name}",
                            metadata={
                                "type": "tool_call",
                                "tool": tool_call.name,
                                "args": str(tool_call.args),
                            },
                        )

                    result = await self._execute_tool(tool_call)

                    self.history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,  # Important for OpenAI
                            "name": tool_call.name,  # Important for Gemini
                            "content": str(result),
                        }
                    )

                continue

            else:
                # No tools, final response
                final_content = "Error: Empty response from LLM."
                if response.content:
                    self.history.append(
                        {"role": "assistant", "content": response.content}
                    )
                    final_content = response.content

                if self.container:
                    self.container.on_agent_finish(self, task, final_content)

                return final_content

        msg = "Max turns reached."
        if self.container:
            self.container.on_agent_finish(self, task, msg)
        return msg

    async def _execute_tool(self, tool_call: ToolCall) -> Any:
        tool = self.tool_map.get(tool_call.name)
        if not tool:
            return f"Error: Tool {tool_call.name} not found."

        try:
            if inspect.iscoroutinefunction(tool.func):
                return await tool(**tool_call.args)
            else:
                return tool(**tool_call.args)
        except Exception as e:
            return f"Error executing {tool_call.name}: {str(e)}"
