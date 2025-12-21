import asyncio
import os

from dotenv import load_dotenv

from rice_agents.agents.base import Agent
from rice_agents.containers.base import Container
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.orchestration.flows import ParallelFlow, SequentialFlow

load_dotenv()


async def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in .env")
        return

    llm = GeminiProvider(model="gemini-1.5-flash", api_key=api_key)

    # --- Sequential Flow Example ---
    print("\n=== Sequential Flow: Joke -> Explanation ===")

    # Create a container for sequential agents
    seq_container = Container("ComedyClub")

    comedian = Agent(
        name="Comedian",
        llm=llm,
        system_prompt="Tell a short, obscure joke.",
        container=seq_container,
    )
    explainer = Agent(
        name="Explainer",
        llm=llm,
        system_prompt="Explain why the input joke is funny.",
        container=seq_container,
    )

    seq_flow = SequentialFlow([comedian, explainer])
    result = await seq_flow.run("Tell me a joke about programming.")
    print(f"Final Output:\n{result}")

    # --- Parallel Flow Example ---
    print("\n=== Parallel Flow: Haiku vs Limerick ===")

    # Create a container for parallel agents
    poet_container = Container("PoetryCorner")

    poet1 = Agent(
        name="HaikuBot",
        llm=llm,
        system_prompt="Write a haiku about the topic.",
        container=poet_container,
    )
    poet2 = Agent(
        name="LimerickBot",
        llm=llm,
        system_prompt="Write a limerick about the topic.",
        container=poet_container,
    )

    par_flow = ParallelFlow([poet1, poet2])
    results = await par_flow.run("Coffee")

    print("\nResults:")
    for res in results:
        print(f"--- Poem ---\n{res}")


if __name__ == "__main__":
    asyncio.run(main())
