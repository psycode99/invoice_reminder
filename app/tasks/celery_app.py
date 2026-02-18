from celery import Celery
from app.core.config import settings

from celery.schedules import crontab

celery_app = Celery(
    "invoice_worker",
    broker=settings.redis_url,
    backend=settings.redis_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
)

celery_app.conf.beat_schedule = {
    "process-invoice-reminders": {
        "task": "app.tasks.reminder_tasks.process_due_reminders",
        "schedule": 300.0,  # every 5 minutes
    },
}
