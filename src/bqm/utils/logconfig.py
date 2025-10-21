from logging import INFO, Formatter, Logger, StreamHandler, config, getLogger
from typing import Any


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


def init_logging(conf: dict[str, Any]):
    config.dictConfig(conf)
