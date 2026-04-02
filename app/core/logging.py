from loguru import logger
import sys

def setup_logger():
    logger.remove()

    def patcher(record):
        record["extra"].setdefault("process", "unknown")
        record["extra"].setdefault("request_id", "-")

    logger.configure(patcher=patcher)

    logger.add(
        sys.stdout,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level:<7}</level> | "
               "<cyan>{extra[process]}</cyan> | "
               "<cyan>{extra[request_id]}</cyan> | "
               "<level>{message}</level>",
        enqueue=True,
    )

    logger.add(
        "logs/app.log",
        filter=lambda r: r["extra"]["process"] == "fastapi",
        serialize=True,
        enqueue=True,
    )

    logger.add(
        "logs/celery.log",
        filter=lambda r: r["extra"]["process"] == "celery",
        serialize=True,
        enqueue=True,
    )

    return logger