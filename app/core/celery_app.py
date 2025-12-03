from celery import Celery
from .config import settings

celery_app = Celery(
    "ciphereye",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.runner"]
)

# Configure Celery to use the default queue
celery_app.conf.update(
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
)
