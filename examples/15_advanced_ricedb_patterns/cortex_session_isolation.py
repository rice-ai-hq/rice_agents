#!/usr/bin/env python3
"""
RiceDB Cortex Pattern: Session Isolation ("Forking Reality")

This example demonstrates how an Agent can safely experiment with changes
in an isolated session (Fork) without affecting the global Base state.
"""

import os
import asyncio
from dotenv import load_dotenv
from ricedb import RiceDBClient
from rice_agents.agents.base import Agent
from rice_agents.llms.gemini_provider import GeminiProvider

load_dotenv()

HOST = os.environ.get("RICEDB_HOST", "localhost")
PORT = int(os.environ.get("RICEDB_PORT", "50051"))
PASSWORD = os.environ.get("RICEDB_PASSWORD", "admin")
SSL = os.environ.get("RICEDB_SSL", "false").lower() == "true"


def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    return GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)


async def main():
    print("🔹 RiceDB Cortex: Session Isolation Demo")

    # 1. Setup Client
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL
    if not client.connect():
        print("❌ Failed to connect to RiceDB")
        return
    client.login("admin", PASSWORD)

    # 2. Base State
    print("\n1. Initializing Base Knowledge...")
    base_id = 1000
    base_text = "Production Config: Max Threads = 4, Timeout = 30s."
    client.insert(
        base_id,
        base_text,
        {"type": "config", "env": "prod", "text": base_text},
        user_id=1,
    )
    print(f"   ✓ Base: {base_text}")

    # 3. Agent Fork
    print("\n2. Agent 'Optimizer' creating Experimental Session...")
    session_id = client.create_session()
    print(f"   ✓ Created Session: {session_id}")

    # 4. Agent Experiment (Shadowing)
    print("\n3. Agent modifying config in Session...")
    # Shadowing: Inserting same ID in session overrides it for that session
    new_text = "Production Config: Max Threads = 16, Timeout = 60s (OPTIMIZED)."
    client.insert(
        base_id,
        new_text,
        {
            "type": "config",
            "env": "prod",
            "status": "experimental",
            "text": new_text,
        },
        user_id=1,
        session_id=session_id,
    )
    print(f"   ✓ Shadowed ID {base_id} in Session.")

    # 5. Verification (Isolation)
    print("\n4. Verifying Isolation...")

    # Search in Base
    res_base = client.search("Max Threads", user_id=1, k=1)
    print(
        f"   [Base View]    : {res_base[0]['metadata'].get('text') if res_base else '?'}"
    )

    # Search in Session
    res_session = client.search("Max Threads", user_id=1, k=1, session_id=session_id)
    print(
        f"   [Session View] : {res_session[0]['metadata'].get('text') if res_session else '?'}"
    )

    if "16" in res_session[0]["metadata"]["text"] and "4" in res_base[0][
        "metadata"
    ].get("text", base_text):
        print("   ✅ Isolation Verified: Base is untouched, Session is updated.")
    else:
        print("   ❌ Isolation Failed!")

    # 6. Commit
    print("\n5. Committing Experiment to Base...")
    # Simulate LLM decision
    agent = Agent("Approver", get_llm(), system_prompt="You approve valid configs.")
    decision = await agent.run(f"Should we commit this config change? '{new_text}'")
    print(f"   [Agent Decision] {decision}")

    if client.commit_session(session_id):
        print("   ✓ Session Committed.")
    else:
        print("   ❌ Commit Failed.")

    # 7. Final Check
    print("\n6. Final Base State...")
    res_final = client.search("Max Threads", user_id=1, k=1)
    print(f"   [Base View]    : {res_final[0]['metadata'].get('text')}")

    client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
