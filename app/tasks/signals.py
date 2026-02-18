from loguru import logger
from celery.signals import task_failure, task_prerun, task_postrun

@task_prerun.connect
def log_task_start(sender=None, task_id=None, task=None, args=None, kwargs=None, **extras):
    logger.info(f"Starting task {sender.name} with id {task_id}, args={args}, kwargs={kwargs}")

@task_postrun.connect
def log_task_success(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extras):
    logger.info(f"Task {sender.name} completed with state={state}, return={retval}")

@task_failure.connect
def log_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extras):
    logger.error(f"Task {sender.name} failed with exception={exception}")

