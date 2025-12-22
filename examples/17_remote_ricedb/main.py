import asyncio
from rice_agents.containers.base import Container


async def main():
    print("=== Remote RiceDB Connectivity Test ===")

    # 1. Init
    container = Container()  # Uses default_container from toml
    if not container.memory_store:
        print("❌ Failed to initialize RiceDB connection logic.")
        return

    print(f"Connecting to RiceDB at {container.config['memory_config']['host']}...")

    # 2. Check Connection
    client = container.memory_store.client

    try:
        transport = client.get_transport_info()
        print(f"✅ Connected! Transport: {transport}")

        # Register if needed (User suggestion)
        print("Attempting registration...")
        try:
            user_id = client.register("admin", "password123")
            print(f"Registered user 'admin' with ID: {user_id}")
            # Re-login to ensure token is set
            client.login("admin", "password123")
        except Exception as e:
            print(f"Registration note: {e}")
            # Try login anyway
            try:
                client.login("admin", "password123")
                print("Logged in.")
            except:
                pass

        # 3. Insert
        print("Testing Insert...")
        text = "RiceDB Remote Connection Test - Success"
        # Using specific ID to avoid pollution if running multiple times
        container.memory_store.add_texts(
            [text], metadatas=[{"type": "test_ping"}], ids=["remote_test_1"]
        )
        print("✅ Insert successful.")

        # 4. Search
        print("Testing Search...")
        results = container.memory_store.query("Connection Test")
        print(f"✅ Search successful. Found {len(results)} results.")
        if results:
            print(f"   Top result: {results[0]}")

    except Exception as e:
        print(f"❌ Operation failed: {e}")
        print(
            "Please ensure the remote server is accessible and credentials are correct."
        )


if __name__ == "__main__":
    asyncio.run(main())
