from celery import Celery
from loguru import logger
import logging
from app.core.config import settings
from celery.schedules import crontab
from celery.signals import setup_logging
import sys

# Remove default Loguru handler (stdout)
logger.remove()

# Console logging
logger.add(
    sys.stdout,
    level="INFO",
)

logger.add(
    "logs/celery.log",
    level="INFO",
    rotation="20 MB",
    retention="14 days",
    enqueue=True,
    serialize=True
)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())

# Forward all stdlib logging (including Celery) to Loguru
logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)


@setup_logging.connect
def disable_celery_logging(**kwargs):
    pass


celery_app = Celery(
    "invoice_worker",
    broker=settings.redis_url,
    backend=settings.redis_backend,
    include=["app.tasks.reminder_tasks"]
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


import app.tasks.reminder_tasks
import app.tasks.signals
