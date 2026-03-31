"""
PhishNet Database — SQLite via SQLAlchemy async
Stores analysis logs for history view and model retraining.
"""
import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./phishnet.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False)
    verdict = Column(String(20), nullable=False)
    phishing_probability = Column(Float, nullable=False)
    url_score = Column(Float)
    text_score = Column(Float)
    image_score = Column(Float)
    processing_time_ms = Column(Float)
    full_result = Column(Text)                  # JSON blob
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def log_analysis(url: str, result: dict):
    async with AsyncSessionLocal() as session:
        entry = AnalysisLog(
            url=url,
            verdict=result["verdict"],
            phishing_probability=result["phishing_probability"],
            url_score=result["url_agent"].get("score"),
            text_score=result["text_agent"].get("score"),
            image_score=result["image_agent"].get("score"),
            processing_time_ms=result.get("processing_time_ms"),
            full_result=json.dumps(result, default=str),
        )
        session.add(entry)
        await session.commit()


async def get_recent_analyses(limit: int = 20):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(AnalysisLog)
            .order_by(AnalysisLog.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "url": r.url,
                "verdict": r.verdict,
                "phishing_probability": r.phishing_probability,
                "url_score": r.url_score,
                "text_score": r.text_score,
                "image_score": r.image_score,
                "processing_time_ms": r.processing_time_ms,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]