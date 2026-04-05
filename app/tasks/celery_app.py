from celery import Celery
from loguru import logger
import logging
from app.core.config import settings
from celery.schedules import crontab
from celery.signals import setup_logging
from sentry_sdk.integrations.celery import CeleryIntegration
import sentry_sdk
from app.core.logging import setup_logger
from loguru import logger as base_logger


sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[CeleryIntegration()],
    traces_sample_rate=1.0
)

setup_logger()
logger = base_logger.bind(process="celery", request_id="-")

class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(exception=record.exc_info, depth=6)
        level = record.levelname if hasattr(record, "levelname") else "INFO"
        logger_opt.log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)


@setup_logging.connect
def disable_celery_logging(**kwargs):
    pass


celery_app = Celery(
    "invoice_worker",
    broker=settings.redis_url,
    backend=settings.redis_backend,
    include=[
        "app.tasks.reminder_tasks",
        "app.tasks.invoice_sync_tasks",
        "app.tasks.invoice_webhooks_tasks",
    ],
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
import app.tasks.invoice_sync_tasks
import app.tasks.invoice_webhooks_tasks
import app.tasks.signals
