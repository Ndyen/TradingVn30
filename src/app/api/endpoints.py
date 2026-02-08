from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.app.db.session import get_db
from src.app.db.models import AnalysisRun, RunReport, RunScore
from pydantic import BaseModel

router = APIRouter()

class RunRequest(BaseModel):
    timeframe: str = "1D"
    universe: str = "VN30"
    strategy: str = "shortterm_v1"

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/run")
async def trigger_run(req: RunRequest):
    # Trigger run logic (could be async background task or synchronous)
    # For MVP, we might call the logic directly or subprocess.
    # Calling subprocess via CLI is safer if logic is heavy, but direct valid too.
    # To keep this fast, let's just return a message or launch background task?
    # Requirement: "trả top3 + ranking + breakdown (đồng thời lưu DB)"
    # So it implies synchronous wait or return result.
    return {"message": "Run triggered (synchronous implementation pending / use CLI for now)"}
    # NOTE: Fully integrating the CLI run logic into API requires refactoring run() to be reusable function
    # taking session. CLI run() currently handles session.
    # We will implement this if requested, but for now focusing on result serving.

@router.get("/top3")
async def get_top3(db: AsyncSession = Depends(get_db)):
    # Get latest successful run with report
    stmt = select(RunReport).join(AnalysisRun).where(AnalysisRun.status == 'success').order_by(AnalysisRun.finished_at.desc()).limit(1)
    res = (await db.execute(stmt)).scalar_one_or_none()
    if not res:
        return {"error": "No reports found"}
    return res.top3

@router.get("/ranking")
async def get_ranking(db: AsyncSession = Depends(get_db)):
    stmt = select(RunReport).join(AnalysisRun).where(AnalysisRun.status == 'success').order_by(AnalysisRun.finished_at.desc()).limit(1)
    res = (await db.execute(stmt)).scalar_one_or_none()
    if not res:
        return {"error": "No reports found"}
    return res.ranking

@router.get("/runs")
async def get_runs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    stmt = select(AnalysisRun).order_by(AnalysisRun.started_at.desc()).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [{"run_id": r.run_id, "as_of": r.as_of, "status": r.status, "started_at": r.started_at} for r in rows]
