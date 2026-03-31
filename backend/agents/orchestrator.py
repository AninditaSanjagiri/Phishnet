"""
OrchestratorAgent
Dispatches URL, Text, and Image agents in parallel via asyncio.gather(),
then passes results to the FusionAgent for the final verdict.
"""
import asyncio
from typing import Optional

from agents.url_agent import URLAgent
from agents.text_agent import TextAgent

from agents.fusion_agent import FusionAgent


class OrchestratorAgent:
    def __init__(self):
        self.url_agent = URLAgent()
        self.text_agent = TextAgent()
        self.fusion_agent = FusionAgent()

    async def initialize(self):
        """Load models for all agents (called once at startup)."""
        print("  ⏳ Loading URL agent...")
        await self.url_agent.load()
        print("  ⏳ Loading Text agent (DistilBERT)...")
        await self.text_agent.load()
        
        #await self.image_agent.load()
        print("  ⏳ Loading Fusion agent...")
        await self.fusion_agent.load()

    async def analyze(self, url: str) -> dict:
        """
        Run all three agents in parallel, then fuse results.
        Gracefully handles agent failures — missing scores are
        redistributed in the fusion layer.
        """
        url_task = asyncio.create_task(self._safe_run(self.url_agent, url))
        text_task = asyncio.create_task(self._safe_run(self.text_agent, url))

        url_result, text_result = await asyncio.gather(
        url_task, text_task
        )

        image_result = {
            "score": None,
            "confidence": 0.0,
            "explanation": "Image agent disabled (development mode).",
            "features": {},
        }
        fusion_result = self.fusion_agent.fuse(url_result, text_result, image_result)

        return {
            **fusion_result,
            "url_agent": url_result,
            "text_agent": text_result,
            "image_agent": image_result,
            "screenshot_base64": image_result.get("screenshot_base64"),
            "gradcam_base64": image_result.get("gradcam_base64"),
        }

    async def _safe_run(self, agent, url: str) -> dict:
        """Wrap agent.analyze() to catch exceptions without crashing the pipeline."""
        try:
            return await agent.analyze(url)
        except Exception as exc:
            agent_name = type(agent).__name__
            print(f"  ⚠️  {agent_name} failed for {url}: {exc}")
            return {
                "score": None,
                "confidence": 0.0,
                "explanation": f"{agent_name} unavailable: {str(exc)[:100]}",
                "features": {},
            }