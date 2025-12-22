import os
import json
from rice_agents.agents.base import Agent
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.tools.base import tool


def get_llm():
    return GeminiProvider(
        model="gemini-3-flash-preview", api_key=os.getenv("GOOGLE_API_KEY")
    )


@tool("search_news")
def search_news(company: str) -> str:
    """Searches for recent news about a company."""
    return f"Recent news for {company}: They recently announced a digital transformation initiative and are hiring aggressively in engineering. Revenue up 20%."


class Researcher:
    def __init__(self, db):
        self.agent = Agent(
            "Researcher",
            get_llm(),
            tools=[search_news],
            system_prompt="You are an SDR Researcher.",
        )
        self.db = db

    async def research(self, lead):
        print(f"[Researcher] Analyzing {lead['company']}...")
        news = await self.agent.run(
            f"Find news about {lead['company']} to help with sales outreach."
        )
        self.db.log_interaction(lead["id"], f"Research: {news}")
        return news


class Strategist:
    def __init__(self, db):
        self.agent = Agent(
            "Strategist", get_llm(), system_prompt="You are a Sales Strategist."
        )
        self.db = db

    async def plan(self, lead, research):
        print(f"[Strategist] Planning approach for {lead['name']}...")
        query = f"{lead['industry']} {lead['role']} {lead.get('interests', '')}"
        context = self.db.get_context(query)

        prompt = f"""
        Lead: {lead["name"]}, {lead["role"]} at {lead["company"]}.
        Industry: {lead["industry"]}
        Interests: {lead.get("interests")}
        Research: {research}
        
        Relevant Product Knowledge:
        {context}
        
        Develop a sales angle. Output JSON: {{ "angle": "...", "key_value_props": [...] }}
        """
        response = await self.agent.run(prompt)
        self.db.log_interaction(lead["id"], f"Strategy: {response}")
        return response, context


class OutreachSpecialist:
    def __init__(self, db):
        self.agent = Agent(
            "Outreach", get_llm(), system_prompt="You are an SDR Copywriter."
        )
        self.db = db

    async def draft(self, lead, strategy, context):
        print(f"[Outreach] Drafting email to {lead['name']}...")
        prompt = f"""
        Draft a cold email to {lead["name"]}.
        Strategy: {strategy}
        Context: {context}
        Keep it under 150 words.
        """
        email = await self.agent.run(prompt)
        self.db.log_interaction(lead["id"], f"Draft: {email}")
        return email


class ObjectionHandler:
    def __init__(self, db):
        self.agent = Agent(
            "ObjectionHandler", get_llm(), system_prompt="You handle sales objections."
        )
        self.db = db

    async def handle(self, lead, objection):
        print(f"[ObjectionHandler] Handling: '{objection}'...")
        kb_answer = self.db.get_context(objection)
        prompt = f"""
        Lead Objected: "{objection}"
        Our Playbook says: "{kb_answer}"
        
        Draft a polite, persuasive response.
        """
        response = await self.agent.run(prompt)
        self.db.log_interaction(lead["id"], f"Objection Response: {response}")
        return response
