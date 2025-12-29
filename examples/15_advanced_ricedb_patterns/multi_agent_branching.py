#!/usr/bin/env python3
"""
RiceDB Cortex Pattern: Multi-Agent Branching

This example demonstrates parallel reality simulation where multiple agents work
in isolated sessions, and how changes propagate upon commitment.
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
    print("🔹 RiceDB Cortex: Multi-Agent Branching Demo")

    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL
    if not client.connect():
        print("❌ Failed to connect")
        return
    client.login("admin", PASSWORD)

    # 1. Base State
    print("\n1. Initializing Legacy Codebase...")
    # ID 500: Main App
    client.insert(
        500, "MainApp: Uses LegacyAuth", {"module": "main", "auth": "legacy"}, user_id=1
    )
    # ID 501: Legacy Auth
    client.insert(
        501, "LegacyAuth Module", {"module": "auth", "type": "legacy"}, user_id=1
    )
    print("   ✓ Base: MainApp uses LegacyAuth")

    # 2. Architect (Session A)
    print("\n2. Architect refactoring in Session A...")
    session_a = client.create_session()

    # Architect switches MainApp to OAuth (Shadowing ID 500)
    client.insert(
        500,
        "MainApp: Uses OAuth",
        {"module": "main", "auth": "oauth"},
        user_id=1,
        session_id=session_a,
    )
    # Architect deletes LegacyAuth (Tombstone ID 501)
    client.delete(501, session_id=session_a)
    # Architect adds OAuth (New ID 600)
    client.insert(
        600,
        "OAuth Module",
        {"module": "oauth", "type": "modern"},
        user_id=1,
        session_id=session_a,
    )
    print("   ✓ Architect: Switched to OAuth, deleted LegacyAuth.")

    # 3. Feature Dev (Session B)
    print("\n3. Feature Dev adding features in Session B...")
    session_b = client.create_session()

    # Feature Dev modifies UserProfile (ID 502 - New)
    client.insert(
        502,
        "UserProfile with Avatar",
        {"module": "user", "feature": "avatar"},
        user_id=1,
        session_id=session_b,
    )
    print("   ✓ Feature Dev: Added UserProfile.")

    # 4. Isolation Check
    print("\n4. Verifying Isolation...")
    # Base
    res_base = client.search("MainApp", k=1, user_id=1)
    print(f"   [Base] MainApp Auth: {res_base[0]['metadata'].get('auth')}")

    # Architect
    res_a = client.search("MainApp", k=1, user_id=1, session_id=session_a)
    print(f"   [Architect] MainApp Auth: {res_a[0]['metadata'].get('auth')}")

    # Feature Dev
    res_b = client.search("MainApp", k=1, user_id=1, session_id=session_b)
    print(f"   [Feature Dev] MainApp Auth: {res_b[0]['metadata'].get('auth')}")

    if (
        res_base[0]["metadata"]["auth"] == "legacy"
        and res_a[0]["metadata"]["auth"] == "oauth"
        and res_b[0]["metadata"]["auth"] == "legacy"
    ):
        print("   ✅ Isolation Verified.")
    else:
        print("   ❌ Isolation Failed.")

    # 5. Architect Commits
    print("\n5. Committing Architect's Refactor...")
    client.commit_session(session_a)
    print("   ✓ Architect Committed.")

    # 6. Live Update Check (Feature Dev)
    print("\n6. Checking Feature Dev's View (Live Rebase)...")
    # Feature Dev did NOT shadow ID 500. So they should now see the committed version from Base.
    res_b_new = client.search("MainApp", k=1, user_id=1, session_id=session_b)
    auth_type = res_b_new[0]["metadata"].get("auth")
    print(f"   [Feature Dev] MainApp Auth: {auth_type}")

    if auth_type == "oauth":
        print("   ✅ Feature Dev automatically sees updated Base (Live Rebase).")
    else:
        print("   ⚠️  Feature Dev sees stale data (or isolation behavior differs).")

    # 7. Cleanup
    print("\n7. Cleanup...")
    client.drop_session(session_b)
    client.disconnect()


if __name__ == "__main__":
    main()
