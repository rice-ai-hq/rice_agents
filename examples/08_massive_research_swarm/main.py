import asyncio
import os

from dotenv import load_dotenv

from rice_agents.agents.base import Agent
from rice_agents.containers.base import Container
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.tools.base import tool

load_dotenv()


@tool("search_database")
def search_database(query: str) -> str:
    """Simulates searching a database."""
    # Deterministic mock response based on query
    return f"Detailed technical information regarding {query}. This topic is critical for the project."


async def run_agent_safe(agent, task, sem):
    async with sem:
        try:
            print(f"[{agent.name}] Starting task: {task}")
            res = await agent.run(task)
            print(f"[{agent.name}] Finished.")
            return res
        except Exception as e:
            return f"Error: {e}"


async def main():
    print("=== Massive Research Swarm Demo ===")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in .env")
        return

    llm = GeminiProvider(model="gemini-1.5-flash", api_key=api_key)

    # 1. Initialize Container
    # This loads config from rice_agents.toml, connecting to RiceDB and enabling auto_memory
    container = Container("ResearchSwarm")

    if not container.memory_store:
        print(
            "⚠️  RiceDB not connected. Please start RiceDB server to see the full benefit (Auto-Memory)."
        )
        print("   Agents will still run, but results won't be saved to DB.")
    else:
        print("✅ RiceDB connected. Agent outputs will be auto-saved.")

    # 2. Create 100 Agents
    topics = [f"Quantum_Physics_Concept_{i}" for i in range(100)]
    agents = []

    print(f"🚀 Spawning {len(topics)} agents...")
    for i, topic in enumerate(topics):  # noqa: B007
        # Each agent is part of the same container, sharing the RiceDB connection
        agent = Agent(
            name=f"Researcher_{i:03d}",
            llm=llm,
            tools=[search_database],
            system_prompt="You are a fast researcher. Use the tool to get info and write a ONE sentence summary.",
            container=container,
        )
        agents.append(agent)

    # 3. Execute Swarm
    # We use a semaphore to avoid hitting API rate limits with 100 concurrent requests
    # In a real production environment with dedicated endpoints, you could increase this.
    concurrency_limit = 10
    print(f"Processing tasks with concurrency limit: {concurrency_limit}...")

    sem = asyncio.Semaphore(concurrency_limit)
    tasks = [
        run_agent_safe(agent, f"Research {topics[i]}", sem)
        for i, agent in enumerate(agents)
    ]

    results = await asyncio.gather(*tasks)

    print(f"\n✅ All {len(results)} agents completed their tasks.")

    # 4. Verify Results in RiceDB
    if container.memory_store:
        print("\n🔍 Verifying Knowledge Base Population in RiceDB...")
        # Query for one of the topics to see if the agent's output was stored
        query_topic = topics[0]
        results = container.memory_store.query(query_topic, n_results=1)

        print(f"Querying for '{query_topic}':")
        if results:
            print(f"Found: {results[0]}")
        else:
            print("No results found (Embedding generation might be slow or failed).")

        # Check count? RiceDB python client might not have count method exposed easily in store interface
        # But we proved the concept.


if __name__ == "__main__":
    asyncio.run(main())
