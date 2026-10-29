import inspect
import logging
import sys

from loguru import logger

from .config import settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:

        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    logger.remove()

    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line: >4}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        level=settings.app.log_level,
        serialize=settings.app.log_json,
        format=fmt,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = True

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    # Every Qdrant and Groq call is an httpx request; INFO would log each of them.
    logging.getLogger("httpx").setLevel(logging.WARNING)
