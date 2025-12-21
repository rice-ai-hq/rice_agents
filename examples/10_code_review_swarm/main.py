import asyncio
import os

from agents import IngestionAgent, Orchestrator, SynthesizerWrapper, WorkerWrapper
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
            # Skip non-code
            if not file.endswith((".py", ".js", ".ts", ".html")):
                continue

            with open(file_path, "r") as f:
                content = f.read()

            # Pre-process
            print(f"Analyzing {file}...")
            analysis = await ingest_agent.process_file(file_path, content)
            indexed_text = f"--- AI ANALYSIS ---\n{analysis}\n\n--- CODE ---\n{content}"

            db.insert_code_file(file_path, indexed_text, project_root)
            print(f"Ingested: {file}")


async def run_swarm():
    # 1. Setup DB
    print("Initializing DB Handler...")
    try:
        db = SwarmRiceDBHandler()
    except Exception as e:
        print(f"DB Error: {e}")
        return

    # 2. Ingest
    await ingest_codebase(db)

    # 3. Orchestrator
    print("Initializing Orchestrator...")
    orchestrator = Orchestrator(db)
    orchestrator.initialize_job_board()

    workers = [
        WorkerWrapper("SecurityAgent", db),
        WorkerWrapper("PerformanceAgent", db),
        WorkerWrapper("StyleAgent", db),
        WorkerWrapper("ArchitectureAgent", db),
    ]

    # 4. Loop
    active = True
    iteration = 0
    max_iterations = 5

    while active and iteration < max_iterations:
        iteration += 1
        print(f"\n--- Cycle {iteration} ---")
        work_done = False

        # Workers poll
        for worker in workers:
            if await worker.poll_and_work():
                work_done = True

        # Orchestrator
        if not orchestrator.monitor() and not work_done:
            print("Orchestrator signals completion.")
            active = False

    # 5. Synthesize
    print("\n--- Synthesis Phase ---")
    synth = SynthesizerWrapper(db)
    await synth.run()


if __name__ == "__main__":
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        # Create a security vulnerability
        with open(f"{TARGET_DIR}/auth.py", "w") as f:
            f.write(
                "def login(u, p):\n    # TODO: remove hardcoded secret\n    secret = 'my_secret'\n    if p == secret: return True"
            )
        # Create a performance issue
        with open(f"{TARGET_DIR}/heavy.py", "w") as f:
            f.write("def process():\n    for i in range(1000000):\n        print(i)")

    asyncio.run(run_swarm())
