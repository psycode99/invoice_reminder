import logging
from logging.config import dictConfig
import os

os.makedirs("logs", exist_ok=True)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": (
                "[%(asctime)s] " "%(levelname)s " "%(name)s:%(lineno)d - " "%(message)s"
            ),
        },
        "access": {
            "format": (
                "%(asctime)s "
                "%(levelname)s "
                "%(client_addr)s "
                "%(request_line)s "
                "%(status_code)s"
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}
