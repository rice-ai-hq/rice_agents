import asyncio
import os
import random
import time
from typing import List

from dotenv import load_dotenv

from rice_agents.agents.base import Agent
from rice_agents.containers.base import Container
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.tools.base import tool

load_dotenv()


@tool("search_database")
def search_database(query: str) -> str:
    """Simulates searching a database for external/new information."""
    # Deterministic mock response based on query
    return f"Latest external findings regarding {query}: [Data from external DB]"


async def run_agent_safe(agent, task, sem):
    async with sem:
        try:
            # print(f"[{agent.name}] Starting task: {task}")
            res = await agent.run(task)
            # print(f"[{agent.name}] Finished.")
            return res
        except Exception as e:
            return f"Error: {e}"


def generate_massive_dataset(size: int = 2000) -> List[str]:
    """Generates a large synthetic dataset for RiceDB."""
    print(f"Generating {size} knowledge entries...")
    data = []
    concepts = [
        "Entanglement",
        "Superposition",
        "Tunneling",
        "Decoherence",
        "Spin",
        "Quark",
        "Lepton",
        "Boson",
    ]
    adjectives = [
        "Critical",
        "Theoretical",
        "Applied",
        "Experimental",
        "Hypothetical",
        "Verified",
    ]

    for i in range(size):
        concept = random.choice(concepts)
        adj = random.choice(adjectives)
        # Create a fact that links a specific ID (like Topic_X) to a concept
        # This ensures when Agent researches "Topic_X", it finds this specific fact.
        fact = f"Quantum_Physics_Concept_{i} is a {adj} instance of {concept} observed in Sector {random.randint(1, 99)}."
        data.append(fact)
    return data


async def main():
    print("=== Massive Research Swarm Demo (with RiceDB Pre-loading) ===")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in .env")
        return

    llm = GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)

    # 1. Initialize Container
    container = Container("ResearchSwarm")

    if not container.memory_store:
        print("⚠️  RiceDB not connected. Cannot pre-load data.")
        return
    else:
        print("✅ RiceDB connected.")

    # 2. Pre-provision Data (Ingestion Phase)
    # Generate massive dataset
    dataset_size = 2000  # "Massive" for a demo script
    facts = generate_massive_dataset(dataset_size)

    print(f"📥 Ingesting {dataset_size} records into RiceDB (RAG Context)...")
    start_ingest = time.time()

    # Optimization: Use RiceDBClient directly for batch_insert
    # This demonstrates accessing the underlying client for high-performance operations
    store = container.memory_store
    client = store.client
    embed_gen = store.embedding_generator

    batch_size = 500
    for i in range(0, len(facts), batch_size):
        batch_texts = facts[i : i + batch_size]
        print(
            f"   - Ingesting batch {i // batch_size + 1} ({len(batch_texts)} items)..."
        )

        # Prepare batch with vectors
        batch_data = []
        for j, text in enumerate(batch_texts):
            # Deterministic ID for demo
            node_id = 100000 + i + j

            # Generate embedding (Dummy or Real depending on environment)
            vector = embed_gen.generate_embedding(text) if embed_gen else []

            batch_data.append(
                {"id": node_id, "vector": vector, "metadata": {"text": text}}
            )

        # Perform bulk insert
        client.batch_insert(batch_data, user_id=store.user_id)

    ingest_time = time.time() - start_ingest
    print(f"✅ Ingestion complete in {ingest_time:.2f}s")

    # 3. Create 100 Agents
    # We create agents to research a SUBSET of the topics we just ingested.
    # e.g. Agents 0-99 will research Concepts 0-99.
    topics = [f"Quantum_Physics_Concept_{i}" for i in range(100)]
    agents = []

    print(f"🚀 Spawning {len(topics)} agents...")
    for i, topic in enumerate(topics):  # noqa: B007
        agent = Agent(
            name=f"Researcher_{i:03d}",
            llm=llm,
            tools=[search_database],
            # Prompt instructs to use Memory (RAG) and Tool
            system_prompt="""You are a researcher. 
            1. CHECK YOUR MEMORY FIRST for existing definitions of the topic.
            2. Use the tool if needed for extra info.
            3. Write a summary combining memory context and tool output.""",
            container=container,
        )
        agents.append(agent)

    # 4. Execute Swarm
    concurrency_limit = 20
    print(f"Processing tasks with concurrency limit: {concurrency_limit}...")

    sem = asyncio.Semaphore(concurrency_limit)
    tasks = [
        run_agent_safe(agent, f"Research {topics[i]}", sem)
        for i, agent in enumerate(agents)
    ]

    results = await asyncio.gather(*tasks)

    print(f"\n✅ All {len(results)} agents completed their tasks.")

    # 5. Verify Output (Auto-Memory)
    # The agents' outputs should now be saved in RiceDB (via auto_memory=True in config)
    # We can query for one of them.
    if container.memory_store:
        print("\n🔍 Verifying Agent Output in RiceDB...")
        # We query for the RESULT of the research on Concept_0
        # Since agent output is text, we search for something likely in it.
        query_text = f"Research Quantum_Physics_Concept_0"
        # Note: The agent output itself is what is stored.
        # We search using the TOPIC to find the AGENT'S REPORT.

        results = container.memory_store.query(query_text, n_results=1)

        print(f"Querying for agent output related to '{query_text}':")
        if results:
            print(f"Found: {results[0]}")
        else:
            print("No results found.")


if __name__ == "__main__":
    asyncio.run(main())
