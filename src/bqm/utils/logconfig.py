from logging import INFO, Formatter, Logger, StreamHandler, config, getLogger
from typing import Any


class LogFuzz:
    @staticmethod
    def make_logger(
        name: str,
        level: int = INFO,
        pattern: str = "%(asctime)s - %(levelname)s - %(message)s",
    ) -> Logger:
        logger = getLogger(name)
        logger.setLevel(level)
        if not logger.handlers:
            handler = StreamHandler()
            handler.setLevel(level)
            formatter = Formatter(pattern)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.propagate = False

        return logger

    @staticmethod
    def init_logging(conf: dict[str, Any]):
        config.dictConfig(conf)

    @staticmethod
    def init_logging_default():
        config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "🕐 %(asctime)s - %(levelname)s - %(message)s",
                    },
                    "app-formatter": {
                        "format": "custom-logger %(name)s %(asctime)s - %(levelname)s - %(message)s",
                    },
                },
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "formatter": "default",
                        "stream": "ext://sys.stdout",
                    },
                    "app-handler": {
                        "class": "logging.StreamHandler",
                        "formatter": "app-formatter",
                        "stream": "ext://sys.stdout",
                    },
                },
                "loggers": {
                    "myapp": {
                        "level": "INFO",
                        "handlers": ["app-handler"],
                        "propagate": False,
                    },
                    "root": {
                        "level": "INFO",
                        "handlers": ["console"],
                    },
                },
            }
        )
