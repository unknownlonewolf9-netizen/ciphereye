from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
from app.runner import list_modules, enqueue_run

router = APIRouter()

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
    
    run_id = enqueue_run(req.module, req.target, req.options)
    return {"run_id": run_id, "status": "queued"}
