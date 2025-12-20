import asyncio
import os
import shutil
from dotenv import load_dotenv
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.agents.base import Agent
from rice_agents.memory.vector_store import ChromaDBStore

load_dotenv()

async def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in .env")
        return

    # Clean up previous db for this example
    if os.path.exists("./example_memory_db"):
        shutil.rmtree("./example_memory_db")

    # 1. Setup Memory
    print("Initializing Memory...")
    memory = ChromaDBStore(path="./example_memory_db")
    
    # Add some facts to memory
    facts = [
        "My favorite food is sushi.",
        "I have a pet cat named Luna.",
        "I live in a yellow house on Elm Street."
    ]
    memory.add_texts(facts)
    print("Memory populated.")

    # 2. Create Agent with Memory
    llm = GeminiProvider(model="gemini-1.5-flash", api_key=api_key)
    
    agent = Agent(
        name="PersonalBot",
        llm=llm,
        memory=memory,
        system_prompt="You are a personal assistant. Use your memory to answer questions about the user."
    )

    # 3. Run - The agent should auto-retrieve relevant facts
    questions = [
        "What is my pet's name?",
        "Where do I live?"
    ]

    for q in questions:
        print(f"\nUser: {q}")
        response = await agent.run(q)
        print(f"Agent: {response}")

if __name__ == "__main__":
    asyncio.run(main())
