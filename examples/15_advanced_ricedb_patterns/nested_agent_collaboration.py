#!/usr/bin/env python3
"""
RiceDB Cortex Pattern: Nested Agent Collaboration

This example demonstrates hierarchical memory management where a 'Worker' agent
operates in a child session of a 'Supervisor' agent.
"""

import os
import asyncio
from dotenv import load_dotenv
from ricedb import RiceDBClient

load_dotenv()

HOST = os.environ.get("RICEDB_HOST", "localhost")
PORT = int(os.environ.get("RICEDB_PORT", "50051"))
PASSWORD = os.environ.get("RICEDB_PASSWORD", "admin")
SSL = os.environ.get("RICEDB_SSL", "false").lower() == "true"


def main():
    print("🔹 RiceDB Cortex: Nested Agent Collaboration Demo")

    # 1. Connect
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL
    if not client.connect():
        print("❌ Failed to connect")
        return
    client.login("admin", PASSWORD)

    # 2. Base Knowledge
    print("\n1. Setup Base Knowledge...")
    project_id = 200
    client.insert(
        project_id,
        "Project Plan: Status = Draft",
        {"status": "draft", "text": "Project Plan: Status = Draft"},
        user_id=1,
    )
    print(f"   ✓ Base Status: Draft")

    # 3. Supervisor Session
    print("\n2. Supervisor starts planning session...")
    supervisor_id = client.create_session()
    print(f"   ✓ Supervisor Session: {supervisor_id}")

    # Supervisor updates status to In Review
    client.insert(
        project_id,
        "Project Plan: Status = In Review",
        {"status": "review", "text": "Project Plan: Status = In Review"},
        user_id=1,
        session_id=supervisor_id,
    )
    print("   ✓ Supervisor set status to 'In Review'")

    # 4. Worker Session (Nested)
    print("\n3. Supervisor delegates to Worker (Nested Session)...")
    try:
        worker_id = client.create_session(parent_session_id=supervisor_id)
        print(f"   ✓ Worker Session: {worker_id} (Child of Supervisor)")
    except TypeError:
        print("❌ Client does not support nested sessions yet.")
        return

    # Worker checks status (Inheritance)
    res = client.search("Project Plan", user_id=1, k=1, session_id=worker_id)
    print(f"   [Worker View]: {res[0]['metadata'].get('text')}")

    # Worker updates status to Approved
    print("   -> Worker approving plan...")
    client.insert(
        project_id,
        "Project Plan: Status = Approved",
        {
            "status": "approved",
            "approver": "worker",
            "text": "Project Plan: Status = Approved",
        },
        user_id=1,
        session_id=worker_id,
    )

    # 5. Worker Commit (Merge Up)
    print("\n4. Worker commits to Supervisor...")
    if client.commit_session(worker_id):
        print("   ✓ Worker committed.")
    else:
        print("   ❌ Worker commit failed.")

    # 6. Supervisor Verification
    print("\n5. Supervisor verifying update...")
    res_sup = client.search("Project Plan", user_id=1, k=1, session_id=supervisor_id)
    status = res_sup[0]["metadata"].get("status")
    print(f"   [Supervisor View]: Status = {status}")

    if status == "approved":
        print("   ✅ Supervisor sees Worker's approval.")

        # 7. Final Commit
        print("\n6. Supervisor commits to Base...")
        client.commit_session(supervisor_id)

        # Verify Base
        res_base = client.search("Project Plan", user_id=1, k=1)
        print(f"   [Base View]: Status = {res_base[0]['metadata'].get('status')}")
    else:
        print("   ❌ Supervisor did not see approval!")

    client.disconnect()


if __name__ == "__main__":
    main()
