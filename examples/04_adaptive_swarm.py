import asyncio
import os

from dotenv import load_dotenv

from rice_agents.agents.base import Agent
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.orchestration.adaptive import AdaptiveOrchestrator

load_dotenv()


async def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in .env")
        return

    llm = GeminiProvider(model="gemini-1.5-flash", api_key=api_key)

    # 1. Define Specialist Agents
    agents = {
        "python_expert": Agent(
            name="PythonExpert",
            llm=llm,
            system_prompt="You are a senior Python developer. Write clean, efficient code.",
        ),
        "security_auditor": Agent(
            name="SecurityAuditor",
            llm=llm,
            system_prompt="You are a security expert. Review code for vulnerabilities.",
        ),
        "tech_writer": Agent(
            name="TechWriter",
            llm=llm,
            system_prompt="You are a technical writer. Write clear documentation.",
        ),
    }

    # 2. Initialize Adaptive Orchestrator
    orchestrator = AdaptiveOrchestrator(manager_llm=llm, agents=agents)

    # 3. Run Complex Task
    goal = "Write a Python function to validate email addresses, audit it for ReDoS attacks, and write usage docs."

    print(f"Goal: {goal}\n")
    final_output = await orchestrator.run(goal)

    print("\n\n=== Final Result ===\n")
    print(final_output)


if __name__ == "__main__":
    asyncio.run(main())
