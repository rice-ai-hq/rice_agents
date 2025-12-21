import asyncio
import os

from agents import (
    AdaptiveOrchestrator,
    DynamicWorker,
    IngestionAgent,
    SynthesizerWrapper,
)
from db_handler import SwarmRiceDBHandler
from dotenv import load_dotenv

load_dotenv()

TARGET_DIR = "dummy_codebase"


async def ingest_codebase(db):
    ingest_agent = IngestionAgent()
    print(f"Starting ingestion of {TARGET_DIR}...")
    project_root = os.path.abspath(TARGET_DIR)

    for root, dirs, files in os.walk(project_root):
        for file in files:
            file_path = os.path.join(root, file)
            if not file.endswith((".py", ".js", ".ts", ".html")):
                continue

            with open(file_path, "r") as f:
                content = f.read()

            print(f"Analyzing {file}...")
            analysis = await ingest_agent.process_file(file_path, content)
            indexed_text = f"--- AI ANALYSIS ---\n{analysis}\n\n--- CODE ---\n{content}"
            db.insert_code_file(file_path, indexed_text, project_root)
            print(f"Ingested: {file}")


async def run_swarm():
    # 1. Setup
    try:
        db = SwarmRiceDBHandler()
    except Exception as e:
        return print(f"DB Error: {e}")

    await ingest_codebase(db)

    # 2. Adaptive Planning
    orchestrator = AdaptiveOrchestrator(db)
    plan = await orchestrator.analyze_and_plan()

    if not plan:
        print("No plan generated.")
        return

    print("\n=== Adaptive Plan ===")
    workers = []
    for step in plan:
        role = step.get("role", "Worker")
        instr = step.get("instruction", "")
        query = step.get("query", "")
        print(f" - Role: {role}, Task: {instr}")

        # Post task
        orchestrator.post_task(role, instr, query)

        # Spawn Worker (if not already spawned for this role, or we can have 1 per role)
        # We will create a worker for each planned item
        worker = DynamicWorker(role, db)
        workers.append(worker)

    # 3. Execution Loop
    active = True
    iteration = 0
    max_iterations = 5

    while active and iteration < max_iterations:
        iteration += 1
        print(f"\n--- Cycle {iteration} ---")
        work_done = False

        for worker in workers:
            if await worker.poll_and_work():
                work_done = True

        # Monitor (Adaptive might add more tasks in real implementation, here we just check pending)
        if not orchestrator.monitor() and not work_done:
            print("All tasks completed.")
            active = False

    # 4. Synthesize
    print("\n--- Synthesis Phase ---")
    synth = SynthesizerWrapper(db)
    await synth.run()


if __name__ == "__main__":
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    # Ensure dummy files exist
    if not os.path.exists(f"{TARGET_DIR}/auth.py"):
        with open(f"{TARGET_DIR}/auth.py", "w") as f:
            f.write(
                "def login(u, p):\n    # TODO: remove hardcoded secret\n    secret = 'my_secret'\n    if p == secret: return True"
            )
    if not os.path.exists(f"{TARGET_DIR}/heavy.py"):
        with open(f"{TARGET_DIR}/heavy.py", "w") as f:
            f.write("def process():\n    for i in range(1000000):\n        print(i)")

    asyncio.run(run_swarm())
