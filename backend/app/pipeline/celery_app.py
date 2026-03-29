# app/pipeline/celery_app.py
from celery import Celery
from app.config.settings import settings

celery_app = Celery(
    "content_ops",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.pipeline.tasks"]
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_max_retries=3,
)