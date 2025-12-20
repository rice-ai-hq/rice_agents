import json
import re
from typing import Any

from ..agents.base import Agent
from ..llms.base import LLMProvider


class AdaptiveOrchestrator:
    """
    Dynamically plans and executes tasks using a Manager LLM and a swarm of agents.
    """

    def __init__(self, manager_llm: LLMProvider, agents: dict[str, Agent]):
        self.manager_llm = manager_llm
        self.agents = agents
        self.agent_names = list(agents.keys())

    async def run(self, goal: str) -> str:
        """
        Main entry point: Plans the workflow and executes it.
        """
        # 1. Plan
        print(f"--- [Adaptive] Analyzing goal: '{goal}' ---")
        plan = await self._create_plan(goal)

        if not plan:
            return "Error: Failed to generate a valid plan."

        print(f"--- [Adaptive] Plan Created: {len(plan)} steps ---")
        for s in plan:
            print(f"  - {s['id']}: {s['description']} -> {s['assigned_agent_name']}")

        context_accumulator = []
        final_result = ""

        # 2. Execute
        for step in plan:
            agent_name = step.get("assigned_agent_name")
            description = step.get("description")
            step_id = step.get("id")

            print(
                f"\n--- [Adaptive] Executing Step {step_id}: {description} (Agent: {agent_name}) ---"
            )

            agent = self.agents.get(agent_name)
            if not agent:
                print(
                    f"Error: Agent '{agent_name}' not found in registry. using first available or skipping."
                )
                # Fallback logic: use the first agent if specific one not found, or skip
                if self.agents:
                    agent = list(self.agents.values())[0]
                    print(f"  -> Fallback to agent '{agent.name}'")
                else:
                    continue

            # Construct task with context
            # We provide the original goal + specific step + accumulated context
            step_task = (
                f"Overall Goal: {goal}\n"
                f"Your Task: {description}\n"
                "Context from previous steps:\n"
                + "\n---\
".join(context_accumulator)
            )

            result = await agent.run(step_task)

            context_accumulator.append(f"Step {step_id} Output:\n{result}")
            final_result = result

        return final_result

    async def _create_plan(self, goal: str) -> list[dict[str, Any]]:
        system_prompt = (
            "You are an expert project manager and orchestrator. "
            "Your job is to break down the user's high-level goal into a logical sequence of execution steps. "
            f"You have the following team of agents available: {', '.join(self.agent_names)}. "
            "Assign each step to the most appropriate agent from this list. "
            "Return the plan strictly as a valid JSON object. Do not include any conversational text. "
            "The JSON structure must be:\n"
            '{ "steps": [ { "id": 1, "description": "Detailed description of what needs to be done", "assigned_agent_name": "exact_agent_name_from_list" } ] }'
        )

        messages = [{"role": "user", "content": goal}]

        try:
            response = await self.manager_llm.chat(
                messages, system_prompt=system_prompt
            )
            text = response.content
            if not text:
                return []

            # Robust JSON parsing
            # Remove markdown fences
            clean_text = re.sub(r"```json\s*", "", text).replace("```", "").strip()
            # Sometimes models add text before/after json
            json_match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            if json_match:
                clean_text = json_match.group(0)

            data = json.loads(clean_text)
            return data.get("steps", [])
        except Exception as e:
            print(f"Error generating plan: {e}")
            return []
