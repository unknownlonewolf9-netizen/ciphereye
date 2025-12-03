from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.runner import list_modules, enqueue_run
from app.db.database import AsyncSessionLocal
from app.models import Run

router = APIRouter()

# Dependency to get async DB session
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

class RunRequest(BaseModel):
    module: str
    target: str
    options: Dict = {}

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/modules")
async def modules():
    return {"modules": list_modules()}

@router.post("/run")
async def run(req: RunRequest):
    modules = list_modules()
    if req.module not in modules:
        raise HTTPException(status_code=400, detail=f"Module '{req.module}' not found")
    
    # Enqueue (creates DB row synchronously in runner for safety)
    run_id = enqueue_run(req.module, req.target, req.options)
    return {"run_id": run_id, "status": "queued"}

@router.get("/run/{run_id}")
async def get_run(run_id: str, session: AsyncSession = Depends(get_session)):
    run_obj = await session.get(Run, run_id)
    if not run_obj:
        raise HTTPException(status_code=404, detail="Run not found")
    return run_obj
