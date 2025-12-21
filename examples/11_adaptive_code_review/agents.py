import json
import time
import os
from typing import List, Dict, Optional, Any
from db_handler import SwarmRiceDBHandler
from schema import Task, Finding, TaskPayload
from rice_agents.agents.base import Agent
from rice_agents.llms.gemini_provider import GeminiProvider


def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    return GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)


class IngestionAgent:
    def __init__(self):
        self.agent = Agent(name="Ingestion", llm=get_llm())

    async def process_file(self, file_path: str, content: str) -> str:
        prompt = f"""
        Analyze code file: {file_path}
        Content: {content[:4000]}
        Output: 1-sentence summary, Key symbols, Tech stack.
        Format: Text.
        """
        return await self.agent.run(prompt)


class AdaptiveOrchestrator:
    def __init__(self, db: SwarmRiceDBHandler):
        self.name = "AdaptiveOrchestrator"
        self.db = db
        self.agent = Agent(name="Orchestrator", llm=get_llm())

    async def analyze_and_plan(self) -> List[Dict]:
        print(f"[{self.name}] Analyzing codebase to form a dynamic plan...")

        # Get overview of files
        files = self.db.get_code_files(query="code", limit=50)
        # Filter for code files only
        files = [f for f in files if f.get("metadata", {}).get("type") == "code_file"]

        file_summary = "\n".join(
            [f"- {f.get('metadata', {}).get('file_path')}" for f in files]
        )

        prompt = f"""
        You are a Lead Software Architect.
        Analyze the following file list from a codebase:
        {file_summary}
        
        Determine the necessary specialized review agents based on the tech stack and file types.
        For example:
        - If python files: PythonExpert
        - If database files: DatabaseExpert
        - If UI files: UIExpert
        - Always include SecurityExpert
        
        Output strictly a JSON list of objects:
        [{{ "role": "RoleName", "instruction": "Specific instruction for this agent", "query": "Search query for this agent" }}]
        """

        try:
            response = await self.agent.run(prompt)
            json_str = response.replace("```json", "").replace("```", "").strip()
            if "[" in json_str:
                json_str = json_str[json_str.find("[") : json_str.rfind("]") + 1]
            plan = json.loads(json_str)
            return plan
        except Exception as e:
            print(f"[{self.name}] Plan generation failed: {e}")
            # Fallback plan
            return [
                {
                    "role": "GeneralReviewer",
                    "instruction": "Review code",
                    "query": "code",
                }
            ]

    def post_task(self, role: str, instruction: str, query: str):
        task = Task(
            type="adaptive_review",
            assigned_to=role,
            payload=TaskPayload(focus_query=query, instruction=instruction),
        )
        self.db.write_scratchpad_entry(self.name, task.model_dump_json(), "job_board")
        print(f"[{self.name}] Posted task for {role}: {instruction}")

    def monitor(self) -> bool:
        entries = self.db.get_scratchpad_entries()
        for entry in entries:
            try:
                data = json.loads(entry.get("content", ""))
                if "payload" in data:
                    t = Task(**data)
                    if t.status in ("pending", "in_progress"):
                        return True
            except:
                continue
        return False


class DynamicWorker:
    def __init__(self, role: str, db: SwarmRiceDBHandler):
        self.role = role
        self.name = role
        self.db = db
        self.agent = Agent(
            name=role,
            llm=get_llm(),
            system_prompt=f"You are a {role}. Review code context provided and output findings in strictly JSON format.",
        )

    async def poll_and_work(self) -> bool:
        entries = self.db.get_scratchpad_entries()
        tasks = []
        for entry in entries:
            try:
                data = json.loads(entry.get("content", ""))
                if "payload" in data:
                    t = Task(**data)
                    if t.status == "pending" and t.assigned_to == self.role:
                        tasks.append(t)
            except:
                pass

        if not tasks:
            return False

        task = tasks[0]
        self.claim_task(task)
        await self.execute_task(task)
        return True

    def claim_task(self, task):
        task.status = "in_progress"
        self.db.write_scratchpad_entry(
            self.name, task.model_dump_json(), "job_board_update"
        )

    async def execute_task(self, task):
        print(f"[{self.name}] Executing task...")
        results = self.db.get_code_files(query=task.payload.focus_query, limit=5)
        results = [
            r for r in results if r.get("metadata", {}).get("type") == "code_file"
        ]

        context = "\n".join(
            [
                f"File: {r.get('metadata', {}).get('file_path')}\n{r.get('metadata', {}).get('text', '')[:2000]}"
                for r in results
            ]
        )

        prompt = f"""
        Instruction: {task.payload.instruction}
        Code Context:
        {context}
        
        Identify issues. Return ONLY a JSON list of objects with keys: severity, description, file, line, recommendation.
        Example: [{{"severity": "high", "description": "Issue", "file": "file.py", "line": "1", "recommendation": "Fix"}}]
        """

        try:
            response = await self.agent.run(prompt)
            json_str = response.replace("```json", "").replace("```", "").strip()
            if "[" in json_str:
                json_str = json_str[json_str.find("[") : json_str.rfind("]") + 1]

            findings = json.loads(json_str)
            if isinstance(findings, list):
                for item in findings:
                    f = Finding(
                        task_id=task.id,
                        type="bug",
                        severity=item.get("severity", "medium"),
                        description=item.get("description", "No desc"),
                        file=item.get("file"),
                        line=str(item.get("line")),
                        recommendation=item.get("recommendation"),
                    )
                    self.db.write_scratchpad_entry(
                        self.name, f.model_dump_json(), "finding"
                    )
                    print(f"[{self.name}] Found: {f.description[:50]}...")
        except Exception as e:
            print(f"[{self.name}] Error: {e}")

        task.status = "completed"
        self.db.write_scratchpad_entry(
            self.name, task.model_dump_json(), "job_board_update"
        )


class SynthesizerWrapper:
    def __init__(self, db: SwarmRiceDBHandler):
        self.name = "Synthesizer"
        self.db = db
        self.agent = Agent(name="Synthesizer", llm=get_llm())

    async def run(self):
        print(f"[{self.name}] Synthesizing report...")
        entries = self.db.get_scratchpad_entries()
        reports = ""
        for entry in entries:
            content = entry.get("content", "")
            if "severity" in content:
                reports += f"\nFinding: {content}\n"

        if not reports:
            print("No findings to synthesize.")
            return

        prompt = f"""
        Create a Final Code Review Report based on:
        {reports}
        """

        response = await self.agent.run(prompt)
        with open("FINAL_ADAPTIVE_REPORT.md", "w") as f:
            f.write(response)
        print(f"[{self.name}] Report written.")
