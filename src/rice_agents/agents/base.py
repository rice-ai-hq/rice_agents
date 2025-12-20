import uuid
import inspect
from typing import List, Optional, Any, Dict
from ..llms.base import LLMProvider, ToolCall
from ..tools.base import RiceTool

from ..memory.base import VectorStore

class Agent:
    """
    Base Agent class that manages LLM interaction, history, and tool execution.
    """
    def __init__(
        self, 
        name: str, 
        llm: LLMProvider, 
        tools: Optional[List[RiceTool]] = None, 
        memory: Optional[VectorStore] = None,
        system_prompt: str = "You are a helpful assistant."
    ):
        self.name = name
        self.llm = llm
        self.tools = tools or []
        self.memory = memory
        self.system_prompt = system_prompt
        self.history: List[Dict[str, Any]] = []
        self.tool_map = {t.name: t for t in self.tools}

    async def run(self, task: str) -> str:
        """
        Executes the agent on a given task. 
        """
        # RAG Retrieval
        context = ""
        if self.memory:
            try:
                results = self.memory.query(task, n_results=3)
                if results:
                    context = "\n[RELEVANT MEMORY]\n" + "\n".join(results) + "\n[END MEMORY]\n\n"
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
                system_prompt=self.system_prompt
            )
            
            # Handle tool calls
            if response.tool_calls:
                # Add assistant message with tool calls
                assistant_msg = {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": [
                        {
                            "name": t.name, 
                            "args": t.args, 
                            "id": t.id
                        } for t in response.tool_calls
                    ]
                }
                self.history.append(assistant_msg)
                
                # Execute tools
                for tool_call in response.tool_calls:
                    print(f"[{self.name}] Calling tool: {tool_call.name}")
                    result = await self._execute_tool(tool_call)
                    
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id, # Important for OpenAI
                        "name": tool_call.name, # Important for Gemini
                        "content": str(result)
                    })
                
                continue
            
            else:
                # No tools, final response
                if response.content:
                    self.history.append({"role": "assistant", "content": response.content})
                    return response.content
                else:
                    return "Error: Empty response from LLM."
        
        return "Max turns reached."

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
