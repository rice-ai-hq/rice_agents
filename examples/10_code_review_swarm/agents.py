import json
import os
from typing import List

from db_handler import SwarmRiceDBHandler
from schema import Finding, Task, TaskPayload

from rice_agents.agents.base import Agent
from rice_agents.llms.gemini_provider import GeminiProvider


# Initialize Provider globally for this example or per agent
def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    return GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)


class Orchestrator:
    def __init__(self, db: SwarmRiceDBHandler):
        self.name = "Orchestrator"
        self.db = db
        self.round = 1
        self.max_rounds = 2

    def log(self, msg):
        print(f"[{self.name}] {msg}")

    def initialize_job_board(self):
        self.log("Initializing Job Board with Round 1 tasks...")
        initial_tasks = [
            (
                "SecurityAgent",
                "password secret auth token injection",
                "Scan for security vulnerabilities.",
            ),
            (
                "PerformanceAgent",
                "loop heavy database query optimization",
                "Identify performance bottlenecks.",
            ),
            (
                "StyleAgent",
                "naming indent format readable",
                "Check code style and conventions.",
            ),
            (
                "ArchitectureAgent",
                "class interface component dependency",
                "Analyze system architecture.",
            ),
        ]

        for role, query, instr in initial_tasks:
            task = Task(
                type="review_code",
                assigned_to=role,
                payload=TaskPayload(focus_query=query, instruction=instr),
                round=1,
            )
            self.post_task(task)

    def post_task(self, task: Task):
        self.db.write_scratchpad_entry(
            agent_name=self.name,
            content=task.model_dump_json(),
            related_file="job_board",
            ttl=3600 * 24,
        )

    def monitor(self) -> bool:
        entries = self.db.get_scratchpad_entries()
        tasks = {}
        findings = []

        for entry in entries:
            try:
                content = entry.get("content", "")
                data = json.loads(content)
                if "payload" in data:
                    t = Task(**data)
                    tasks[t.id] = t
                elif "severity" in data:
                    findings.append(Finding(**data))
            except:
                continue

        pending = [t for t in tasks.values() if t.status in ("pending", "in_progress")]

        if not pending and self.round < self.max_rounds:
            self.log("Round finished. Analyzing findings for follow-up...")
            if self.analyze_findings_and_retask(findings) > 0:
                self.round += 1
                return True
            return False
        elif not pending:
            return False

        return True

    def analyze_findings_and_retask(self, findings: List[Finding]) -> int:
        count = 0
        for f in findings:
            if f.severity == "critical" and "auth" in f.description.lower():
                task = Task(
                    type="review_code",
                    assigned_to="SecurityAgent",
                    priority="high",
                    payload=TaskPayload(
                        focus_query="auth0 config session",
                        instruction=f"Deep dive based on finding: {f.description}",
                    ),
                    round=self.round + 1,
                )
                self.post_task(task)
                self.log(f"Created follow-up for finding: {f.id}")
                count += 1
        return count


class WorkerWrapper:
    def __init__(self, role: str, db: SwarmRiceDBHandler):
        self.role = role
        self.name = role
        self.db = db
        # Internal Rice Agent for intelligence
        self.agent = Agent(
            name=role,
            llm=get_llm(),
            system_prompt=f"You are a {role} expert. Output strictly JSON findings.",
        )

    def log(self, msg):
        print(f"[{self.name}] {msg}")

    async def poll_and_work(self) -> bool:
        entries = self.db.get_scratchpad_entries()
        tasks = {}
        for entry in entries:
            try:
                data = json.loads(entry.get("content", ""))
                if "payload" in data:
                    t = Task(**data)
                    tasks[t.id] = t
            except:
                pass

        my_tasks = [
            t
            for t in tasks.values()
            if t.status == "pending"
            and (t.assigned_to == self.role or t.assigned_to is None)
        ]
        if not my_tasks:
            return False

        task = my_tasks[0]
        self.claim_task(task)
        await self.execute_task_async(task)
        return True

    def claim_task(self, task: Task):
        task.status = "in_progress"
        self.db.write_scratchpad_entry(
            self.name, task.model_dump_json(), "job_board_update"
        )

    async def execute_task_async(self, task: Task):
        # We need async here because Agent.run is async
        self.log(f"Executing task {task.id}")

        # 1. Search Code
        results = self.db.get_code_files(query=task.payload.focus_query, limit=5)
        context_str = "\n".join(
            [
                f"File: {r.get('metadata', {}).get('file_path')}\n{r.get('metadata', {}).get('text', '')[:2000]}"
                for r in results
            ]
        )

        # 2. LLM Analysis via Rice Agent
        prompt = f"""
        Task: {task.payload.instruction}
        Code Context:
        {context_str}
        
        Identify issues. Return ONLY a JSON list of objects with keys: severity (critical/high/medium/low), description, file, line (int or string), recommendation.
        Example: [{{"severity": "high", "description": "Auth bypass", "file": "auth.ts", "line": "10", "recommendation": "Fix check"}}]
        """

        try:
            response = await self.agent.run(prompt)
            # Cleanup json
            json_str = response.replace("```json", "").replace("```", "").strip()
            # Handle possible intro text if model chats
            if "[" in json_str:
                json_str = json_str[json_str.find("[") : json_str.rfind("]") + 1]

            findings_data = json.loads(json_str)

            if isinstance(findings_data, list):
                for item in findings_data:
                    f = Finding(
                        task_id=task.id,
                        type="vulnerability"
                        if "security" in self.role.lower()
                        else "bug",
                        severity=item.get("severity", "medium"),
                        description=item.get("description", "No desc"),
                        file=item.get("file"),
                        line=str(item.get("line")),
                        recommendation=item.get("recommendation"),
                    )
                    self.db.write_scratchpad_entry(
                        self.name, f.model_dump_json(), "finding"
                    )
                    self.log(f"Reported finding: {f.description[:50]}...")
        except Exception as e:
            self.log(f"Error: {e}")

        task.status = "completed"
        self.db.write_scratchpad_entry(
            self.name, task.model_dump_json(), "job_board_update"
        )

    # Sync wrapper removed, use execute_task_async


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


class SynthesizerWrapper:
    def __init__(self, db: SwarmRiceDBHandler):
        self.name = "Synthesizer"
        self.db = db
        self.agent = Agent(name="Synthesizer", llm=get_llm())

    async def run(self):
        print(f"[{self.name}] Gathering reports...")
        entries = self.db.get_scratchpad_entries()
        if not entries:
            return

        reports = ""
        for entry in entries:
            content = entry.get("content", "")
            # Filter for Findings
            if "severity" in content:
                reports += f"\nFinding: {content}\n"

        if not reports:
            print("No findings to synthesize.")
            return

        prompt = f"""
        Synthesize these code review findings into a Markdown report.
        Findings:
        {reports}
        """

        response = await self.agent.run(prompt)
        with open("FINAL_CODE_REVIEW.md", "w") as f:
            f.write(response)
        print(f"[{self.name}] Report written.")
