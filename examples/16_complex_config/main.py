from rice_agents.containers.base import Container
from rice_agents.config import config as global_config


def main():
    print("=== Complex Config Loading Demo ===")

    # List of expected containers
    container_names = [
        "FrontendTeam",
        "BackendTeam",
        "DevOps",
        "DataScience",
        "MarketResearch",
        "RedTeam",
        "Legal",
        "LegacySystem",
        "Experimental",
    ]

    for name in container_names:
        print(f"\n--- Loading Container: {name} ---")
        try:
            container = Container(name)
            print(f"✅ Successfully initialized '{container.name}'")
            print(f"   Description: {container.config.get('description')}")
            print(f"   Model: {container.config.get('model', 'Default')}")
            print(f"   Memory Type: {container.config.get('memory', 'None')}")
            print(f"   Auto-Memory: {container.config.get('auto_memory', 'Default')}")

            # Show specific config parts
            if "env" in container.config:
                print(f"   Env Vars: {container.config['env']}")
            if "tools" in container.config:
                print(f"   Tool Policy: {container.config['tools']}")
            if "memory_config" in container.config:
                print(f"   Memory Config: {container.config['memory_config']}")

        except Exception as e:
            print(f"❌ Failed to load '{name}': {e}")


if __name__ == "__main__":
    main()
