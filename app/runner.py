import importlib
import pkgutil
import uuid
from app.core.celery_app import celery_app
from app.modules import base as base_mod

def list_modules():
    pkg = importlib.import_module("app.modules")
    return [name for _, name, _ in pkgutil.iter_modules(pkg.__path__) if name != "base"]

def load_module(name: str):
    mod_name = name
    if mod_name.endswith("_module"):
        mod_name = mod_name[:-7]
    mod = importlib.import_module(f"app.modules.{mod_name}_module")
    return mod.get_module()

@celery_app.task(name="run_module_task")
def run_module_task(name: str, target: str, options: dict):
    module = load_module(name)
    return module.run(target, **options)

def enqueue_run(name: str, target: str, options: dict = {}):
    run_id = str(uuid.uuid4())
    run_module_task.apply_async(args=[name, target, options], task_id=run_id)
    return run_id
