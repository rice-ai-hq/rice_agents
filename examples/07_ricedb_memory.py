import asyncio
import os

from dotenv import load_dotenv

from rice_agents.agents.base import Agent
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.memory.ricedb_store import RiceDBStore

load_dotenv()


async def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in .env")
        # return

    # Check if RiceDB is available
    try:
        from ricedb import RiceDBClient  # noqa: F401
    except ImportError:
        print(
            "RiceDB is not installed. Please install it with `pip install ricedb` to run this example."
        )
        return

    print("Initializing RiceDB Memory...")
    try:
        # Assumes RiceDB server is running on localhost
        # We use default admin/password123 for demonstration
        memory = RiceDBStore(
            host="localhost",
            user_id=1,
            username="admin",
            password="password123",
        )
    except Exception as e:
        print(f"Failed to connect to RiceDB: {e}")
        print(
            "Make sure RiceDB server is running (e.g. `cargo run --bin ricedb-server-http`)"
        )
        return

    # 1. Add some facts to memory (Main Graph/Vector Store)
    facts = [
        "Project Alpha deadline is next Friday.",
        "Team standup is at 10 AM daily.",
        "Use Python 3.11 for all new microservices.",
    ]
    print(f"Adding {len(facts)} facts to main memory...")
    memory.add_texts(facts)

    # 2. Create Agent with Memory
    # Using a dummy LLM provider if API key is missing for demo purposes, or handle gracefully
    if api_key:
        llm = GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)
    else:
        raise ValueError("GOOGLE_API_KEY is required to run this example.")

    agent = Agent(
        name="ProjectBot",
        llm=llm,
        memory=memory,
        system_prompt="You are a project assistant. Use memory to answer questions.",
    )

    # 3. Run Agent (RAG + Scratchpad)
    # The Agent will automatically log task start to scratchpad

    question = "When is the project deadline?"
    print(f"\nUser: {question}")
    response = await agent.run(question)
    print(f"Agent: {response}")

    # 4. Verify Scratchpad usage
    print("\n[Verification] Checking Agent Scratchpad in RiceDB...")
    try:
        # Retrieve scratchpad entries for this session
        scratchpad_entries = memory.get_scratchpad(session_id=agent.session_id)
        print(
            f"Found {len(scratchpad_entries)} entries in scratchpad for session {agent.session_id}:"
        )
        for entry in scratchpad_entries:
            print(
                f" - [{entry.get('agent_id')}] {entry.get('content')} (Meta: {entry.get('metadata')})"
            )

    except Exception as e:
        print(f"Error reading scratchpad: {e}")


if __name__ == "__main__":
    asyncio.run(main())
