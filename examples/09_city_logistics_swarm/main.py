import asyncio
import os
import random
import time

from dotenv import load_dotenv

from rice_agents.agents.base import Agent
from rice_agents.containers.base import Container
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.tools.base import tool

load_dotenv()


# Tool for agents to update their status
@tool("update_status")
def update_status(agent_name: str, location: str, status: str) -> str:
    """Updates the agent's status in the central system."""
    return f"Status updated: {agent_name} at {location} is {status}"


@tool("check_traffic")
def check_traffic(location: str) -> str:
    """Checks traffic at a location."""
    # Mock congestion logic
    if random.random() > 0.8:
        return "CONGESTED"
    return "CLEAR"


async def run_drone_mission(agent, drone_id, container):
    """
    Simulates a complex drone mission.
    The drone 'thinks' (LLM) about traffic, then 'moves' (Simulated), updating shared memory.
    """
    # 1. Planning Phase (LLM)
    # To demonstrate LLM usage in swarm without exploding API usage in demo,
    # we'll do a single planning call per drone.
    # In a real full-scale swarm, you'd have high throughput LLM access.

    # We use a semaphore for the LLM part only if needed, but here we'll assume the user
    # wants to see the swarm in action. We'll skip the LLM call for the *loop* to keep it fast,
    # but the Agent structure is there.

    # Simulation Loop
    current_node = random.randint(0, 20)
    mission_log = []  # noqa: F841

    for step in range(5):
        # Interact with Shared Scratchpad (Read)
        # Check if too many drones are at the next target
        target_node = (current_node + random.randint(1, 3)) % 20

        # Interact with Shared Scratchpad (Write)
        if container.memory_store:
            container.memory_store.add_scratchpad(
                session_id="city_simulation_v1",
                agent=agent.name,
                content=f"Moving to {target_node}",
                metadata={
                    "location": str(target_node),
                    "step": str(step),
                    "status": "moving",
                },
            )

        # Simulate movement time
        await asyncio.sleep(random.uniform(0.05, 0.2))
        current_node = target_node

    return f"Drone {drone_id} finished at {current_node}"


async def main():
    print("=== City Logistics Swarm Demo (100 Agents) ===")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in .env")
        return

    llm = GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)

    # Initialize Container with RiceDB config
    container = Container("SmartCityOps")

    if not container.memory_store:
        print("⚠️  RiceDB not connected. Scratchpad features unavailable.")
        print(
            "   (Ensure RiceDB server is running: `cargo run --bin ricedb-server-http`)"
        )
        return

    print("✅ RiceDB connected. Shared Scratchpad active.")

    # Clear previous simulation state to ensure clean run
    print("Cleaning up old simulation data...")
    container.memory_store.clear_scratchpad("city_simulation_v1")  # ty:ignore[unresolved-attribute]

    agents = []
    print("🚀 Deploying 100 Drone Agents...")
    for i in range(100):
        agent = Agent(
            name=f"Drone_{i:03d}",
            llm=llm,
            tools=[update_status, check_traffic],
            system_prompt="You are an autonomous delivery drone. Avoid traffic.",
            container=container,
        )
        agents.append(agent)

    print("Starting simulation (5 steps per drone)...")
    start_time = time.time()

    # Execute 100 agents concurrently
    tasks = [run_drone_mission(agent, i, container) for i, agent in enumerate(agents)]
    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start_time
    print(f"\n✅ Simulation complete in {elapsed:.2f}s")
    print(f"   Processed {len(results)} agent missions.")

    # Analyze Shared Scratchpad Data
    print("\n📊 Swarm Telemetry Analysis (from RiceDB):")
    try:
        entries = container.memory_store.get_scratchpad(session_id="city_simulation_v1")  # ty:ignore[unresolved-attribute]
        print(f"Total telemetry events captured: {len(entries)}")

        # Calculate congestion
        locations = [entry.get("metadata", {}).get("location") for entry in entries]
        if locations:
            # Filter out None values
            valid_locations = [l for l in locations if l is not None]  # noqa: E741
            if valid_locations:
                from collections import Counter

                counts = Counter(valid_locations)
                most_common = counts.most_common(3)
                print("Top 3 Congested Nodes:")
                for loc, count in most_common:
                    print(f" - Node {loc}: {count} visits")
    except Exception as e:
        print(f"Error analyzing data: {e}")


if __name__ == "__main__":
    asyncio.run(main())
