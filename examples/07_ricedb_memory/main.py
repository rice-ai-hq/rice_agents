import asyncio
import os

from dotenv import load_dotenv

from rice_agents.agents.base import Agent
from rice_agents.containers.base import Container
from rice_agents.llms.gemini_provider import GeminiProvider

load_dotenv()


async def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in .env")
        # return

    # Check if RiceDB is available
    try:
        import ricedb  # noqa: F401
    except ImportError:
        print(
            "RiceDB is not installed. Please install it with `pip install ricedb` to run this example."
        )
        return

    print("Initializing Container with RiceDB Memory (from rice_agents.toml)...")

    # Create container - Configuration is loaded from rice_agents.toml
    # This will attempt to connect to RiceDB using settings from the config file.
    container = Container("ProjectContainer")

    if not container.memory_store:
        print(
            "Failed to initialize RiceDB memory in container. Make sure RiceDB server is running."
        )
        return

    # 1. Add some facts to memory (Main Graph/Vector Store)
    facts = [
        "Project Alpha deadline is next Friday.",
        "Team standup is at 10 AM daily.",
        "Use Python 3.11 for all new microservices.",
    ]
    print(f"Adding {len(facts)} facts to main memory via container...")
    container.memory_store.add_texts(facts)

    # 2. Create Agent with Container
    # Using a dummy LLM provider if API key is missing for demo purposes, or handle gracefully
    if api_key:
        llm = GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)
    else:
        raise ValueError("GOOGLE_API_KEY is required to run this example.")

    # Agent will automatically inherit memory from the container
    agent = Agent(
        name="ProjectBot",
        llm=llm,
        system_prompt="You are a project assistant. Use memory to answer questions.",
        container=container,
    )

    # 3. Run Agent (RAG + Scratchpad + Auto-Memory)
    question = "When is the project deadline?"
    print(f"\nUser: {question}")
    response = await agent.run(question)
    print(f"Agent: {response}")

    # 4. Verify Scratchpad usage and Auto-Memory
    print("\n[Verification] Checking Agent Scratchpad in RiceDB...")
    try:
        # Retrieve scratchpad entries for this session
        scratchpad_entries = container.memory_store.get_scratchpad(
            session_id=agent.session_id
        )
        print(
            f"Found {len(scratchpad_entries)} entries in scratchpad for session {agent.session_id}:"
        )
        for entry in scratchpad_entries:
            print(
                f" - [{entry.get('agent_id')}] {entry.get('content')} (Meta: {entry.get('metadata')})"
            )

    except Exception as e:
        print(f"Error reading scratchpad: {e}")

    print("\n[Verification] Checking Auto-Memory (Agent Output)...")
    # In a real scenario, we would search for the text the agent just generated.
    # Since we enabled `auto_memory=True`, the response should be in the store.


if __name__ == "__main__":
    asyncio.run(main())
