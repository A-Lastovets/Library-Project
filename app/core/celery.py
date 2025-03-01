from celery import Celery
from app.core.config import settings

celery_app = Celery("tasks")

# 🔹 Конфігурація Celery
celery_app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND if hasattr(settings, "CELERY_RESULT_BACKEND") else None,
    task_routes={"app.tasks.*": {"queue": "default"}},
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["app.services"])
