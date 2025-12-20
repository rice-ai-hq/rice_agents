import asyncio
import os
import shutil

from dotenv import load_dotenv

from rice_agents.agents.base import Agent
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.tools.base import tool

load_dotenv()

# --- Setup Sandboxed Environment ---
SANDBOX_DIR = "./sandbox_example"


def setup_sandbox():
    if os.path.exists(SANDBOX_DIR):
        shutil.rmtree(SANDBOX_DIR)
    os.makedirs(SANDBOX_DIR)
    print(f"[System] Sandbox created at {SANDBOX_DIR}")


# --- Define Tools ---


@tool("list_files")
def list_files() -> str:
    """Lists all files in the current sandbox directory."""
    files = os.listdir(SANDBOX_DIR)
    return f"Files in directory: {files}" if files else "Directory is empty."


@tool("write_file")
def write_file(filename: str, content: str) -> str:
    """Writes content to a file in the sandbox. Overwrites if exists."""
    filepath = os.path.join(SANDBOX_DIR, filename)
    try:
        with open(filepath, "w") as f:
            f.write(content)
        return f"Successfully wrote to {filename}."
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool("read_file")
def read_file(filename: str) -> str:
    """Reads content from a file in the sandbox."""
    filepath = os.path.join(SANDBOX_DIR, filename)
    if not os.path.exists(filepath):
        return f"Error: File {filename} does not exist."
    try:
        with open(filepath) as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


async def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in .env")
        return

    setup_sandbox()

    llm = GeminiProvider(model="gemini-1.5-flash", api_key=api_key)

    # --- Create the SysAdmin Agent ---
    sys_admin = Agent(
        name="SysAdmin",
        llm=llm,
        tools=[list_files, write_file, read_file],
        system_prompt="""You are a System Administrator agent capable of managing files.
        You are working in a persistent sandbox environment.
        Always verify your actions by listing files or reading them back after writing.
        """,
    )

    # --- Complex Multi-Step Task ---
    # The agent needs to:
    # 1. Check if empty.
    # 2. Create a file.
    # 3. Create another file.
    # 4. Verify they exist.
    # 5. Read one back.
    task = """
    Please perform the following operations:
    1. Create a file named 'notes.txt' with a grocery list.
    2. Create a python script 'hello.py' that prints 'Hello World'.
    3. List the files to confirm they were created.
    4. Read the content of 'hello.py' to verify it.
    """

    print(f"\n🖥️  SysAdmin Agent started with task:\n{task}\n")
    response = await sys_admin.run(task)

    print("\n🤖 === Agent Final Response === 🤖\n")
    print(response)

    # Verification from outside
    print("\n[System] Verifying sandbox content manually:")
    if os.path.exists(os.path.join(SANDBOX_DIR, "hello.py")):
        print(" - hello.py exists ✅")
    else:
        print(" - hello.py MISSING ❌")


if __name__ == "__main__":
    asyncio.run(main())
