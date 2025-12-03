from celery import Celery
from .config import settings

celery_app = Celery(
    "ciphereye",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
