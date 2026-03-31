"""
PhishNet - Multimodal Phishing Detection API
FastAPI backend with async agent orchestration
"""
import asyncio
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
import uvicorn

from agents.orchestrator import OrchestratorAgent
from database import init_db, log_analysis
from utils.url_validator import normalize_url


# ── Lifespan (startup / shutdown) ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all agents and database on startup."""
    print("🚀 PhishNet starting up...")
    await init_db()
    app.state.orchestrator = OrchestratorAgent()
    await app.state.orchestrator.initialize()
    print("✅ All agents initialized and ready.")
    yield
    print("👋 PhishNet shutting down.")


# ── App setup ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="PhishNet API",
    description="Multimodal Phishing Detection — URL + Text + Image",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response schemas ───────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = "http://" + v
        return v


class AgentResult(BaseModel):
    score: Optional[float]          # 0.0 = legit, 1.0 = phishing
    confidence: float               # how sure the agent is
    explanation: str                # plain-English reason
    features: dict                  # raw signals for the UI


class AnalyzeResponse(BaseModel):
    url: str
    verdict: str                    # "phishing" | "suspicious" | "safe"
    phishing_probability: float     # 0–100
    processing_time_ms: float
    url_agent: AgentResult
    text_agent: AgentResult
    image_agent: AgentResult
    fusion_weights: dict
    screenshot_base64: Optional[str]
    gradcam_base64: Optional[str]


# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "PhishNet API"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    start = time.time()
    url = normalize_url(req.url)

    try:
        result = await app.state.orchestrator.analyze(url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    elapsed = (time.time() - start) * 1000

    response = AnalyzeResponse(
        url=url,
        verdict=result["verdict"],
        phishing_probability=round(result["phishing_probability"], 2),
        processing_time_ms=round(elapsed, 1),
        url_agent=AgentResult(**result["url_agent"]),
        text_agent=AgentResult(**result["text_agent"]),
        image_agent=AgentResult(**result["image_agent"]),
        fusion_weights=result["fusion_weights"],
        screenshot_base64=result.get("screenshot_base64"),
        gradcam_base64=result.get("gradcam_base64"),
    )

    background_tasks.add_task(log_analysis, url, response.model_dump())
    return response


@app.get("/history")
async def get_history(limit: int = 20):
    from database import get_recent_analyses
    return await get_recent_analyses(limit)


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)