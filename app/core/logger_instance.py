from loguru import logger

fastapi_logger = logger.bind(process="fastapi")
celery_logger = logger.bind(process="celery")