from __future__ import annotations

import logging
import sys
from typing import Optional

from loguru import logger


class InterceptHandler(logging.Handler):
    """Redirect standard logging messages to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - thin wrapper
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(level: Optional[str] = None) -> None:
    """Configure application-wide logging."""

    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        backtrace=False,
        diagnose=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            "| <level>{level:<8}</level> "
            "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
            "- <level>{message}</level>"
        ),
        level=level or "INFO",
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
