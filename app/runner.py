import importlib
import pkgutil
import uuid
import json
from datetime import datetime
from sqlmodel import Session
from app.core.celery_app import celery_app
from app.modules import base as base_mod
from app.db.database import engine_sync
from app.models import Run

def list_modules():
    pkg = importlib.import_module("app.modules")
    return [name for _, name, _ in pkgutil.iter_modules(pkg.__path__) if name != "base"]

def load_module(name: str):
    mod_name = name
    if mod_name.endswith("_module"):
        mod_name = mod_name[:-7]
    mod = importlib.import_module(f"app.modules.{mod_name}_module")
    return mod.get_module()

def serialize_datetime(obj):
    """Recursively convert datetime objects to ISO format strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj

@celery_app.task(name="run_module_task")
def run_module_task(run_id: str, name: str, target: str, options: dict):
    # 1. Load module
    module = load_module(name)

    # 2. Run Module
    try:
        result_data = module.run(target, **options)
        # Serialize any datetime objects in the result
        result_data = serialize_datetime(result_data)
        status = "success" if result_data.get("success") else "failed"
    except Exception as e:
        result_data = {"error": str(e)}
        status = "failed"

    # 3. Save to DB (Synchronous)
    with Session(engine_sync) as session:
        run_obj = session.get(Run, run_id)
        if run_obj:
            run_obj.result = result_data
            run_obj.status = status
            run_obj.finished_at = datetime.utcnow()
            session.add(run_obj)
            session.commit()

    return result_data

def enqueue_run(name: str, target: str, options: dict = {}):
    run_id = uuid.uuid4()

    with Session(engine_sync) as session:
        run_obj = Run(id=run_id, module=name, target=target, status="queued")
        session.add(run_obj)
        session.commit()

    # Send to 'default' queue (matches worker configuration)
    run_module_task.apply_async(args=[str(run_id), name, target, options], task_id=str(run_id))
    return str(run_id)
