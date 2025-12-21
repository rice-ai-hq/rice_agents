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

    llm = GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)

    # Create a container for the development team
    dev_container = Container("ProductTeam")

    # --- 1. Define the Agents ---

    # The Product Manager breaks down the idea into requirements
    pm = Agent(
        name="ProductManager",
        llm=llm,
        system_prompt="""You are a strict Product Manager. 
        Given a feature idea, output a clear, concise text specification. 
        Focus on what needs to be built for Backend (API) and Frontend (UI).""",
        container=dev_container,
    )

    # Backend Developer
    backend_dev = Agent(
        name="BackendDev",
        llm=llm,
        system_prompt="""You are a Python Backend Developer. 
        Given a spec, write a Python Flask route that implements the logic. 
        Return ONLY code.""",
        container=dev_container,
    )

    # Frontend Developer
    frontend_dev = Agent(
        name="FrontendDev",
        llm=llm,
        system_prompt="""You are a React Frontend Developer. 
        Given a spec, write a React component that implements the UI. 
        Return ONLY code.""",
        container=dev_container,
    )

    # QA Engineer (The Merger)
    # This agent is special: it will receive a list of outputs from the parallel step
    qa_engineer = Agent(
        name="QA_Engineer",
        llm=llm,
        system_prompt="""You are a QA Lead. 
        You will receive input that contains both Backend and Frontend code (as a list string).
        Your job is to:
        1. Review if they match the implied requirements.
        2. Combine them into a single final report titled 'Deployment Package'.
        """,
        container=dev_container,
    )

    # --- 2. Build the Hierarchy ---

    # Step 2: The Dev Team runs in parallel
    dev_team = ParallelFlow([backend_dev, frontend_dev], name="DevTeamSwarm")

    # Overall Pipeline: PM -> [Backend, Frontend] -> QA
    pipeline = SequentialFlow([pm, dev_team, qa_engineer], name="ProductPipeline")

    # --- 3. Run the Simulation ---
    feature_request = "A simple 'Quote of the Day' app where users click a button to get a random inspiring quote."

    print(f"\n🚀 Starting Development Pipeline for: '{feature_request}'\n")
    final_result = await pipeline.run(feature_request)

    print("\n\n✅ === Final Output from QA === ✅\n")
    print(final_result)


if __name__ == "__main__":
    asyncio.run(main())
