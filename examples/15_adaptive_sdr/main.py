import os
import json
import asyncio
from dotenv import load_dotenv
from db import RiceDBHandler
from agents import Researcher, Strategist, OutreachSpecialist, ObjectionHandler

load_dotenv()


async def run_sdr_campaign():
    # 1. Initialize
    print("=== Adaptive SDR Campaign ===")
    try:
        db = RiceDBHandler()
    except Exception as e:
        print(f"RiceDB Error: {e}")
        return

    # 2. Ingest Product KB
    if os.path.exists("product_kb.txt"):
        with open("product_kb.txt", "r") as f:
            kb_text = f.read()
        db.ingest_kb(kb_text)
    else:
        print("Warning: product_kb.txt not found.")

    # 3. Load Leads
    if os.path.exists("leads.json"):
        with open("leads.json", "r") as f:
            leads = json.load(f)
    else:
        print("Warning: leads.json not found.")
        leads = []

    # 4. Agents
    researcher = Researcher(db)
    strategist = Strategist(db)
    outreach = OutreachSpecialist(db)
    handler = ObjectionHandler(db)

    # 5. Process Leads
    for lead in leads:
        print(f"\n--- Processing Lead: {lead['name']} ---")

        # Step A: Research
        # Uses tool to find news
        news = await researcher.research(lead)
        print(f"   > Research Found: {news[:60]}...")

        # Step B: Strategy
        # Uses RAG (product info) + Research to decide angle
        strategy, context = await strategist.plan(lead, news)
        print(f"   > Strategy Formulated.")

        # Step C: Outreach
        # Drafts email
        email = await outreach.draft(lead, strategy, context)
        print(f"   > Email Draft:\n{email}\n")

        # Step D: Simulation - Objection
        # Simulates a common objection to see how agent uses KB to handle it
        objection = "It sounds expensive."
        print(f"   [Simulation] Lead replies: '{objection}'")
        reply = await handler.handle(lead, objection)
        print(f"   > Handling Response:\n{reply}\n")


if __name__ == "__main__":
    asyncio.run(run_sdr_campaign())
