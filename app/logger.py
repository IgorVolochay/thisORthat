"""
Centralized logging configuration using Loguru.

Outputs structured JSON to stdout (INFO/WARNING) and stderr (ERROR/CRITICAL).
Designed for Docker + Grafana Loki / Promtail.

Usage:
    from logger import logger, setup_logging

    setup_logging()          # call once at application entry point
    logger.info("message")
"""

from __future__ import annotations
import os
import sys
import logging
from types import FrameType
from typing import TYPE_CHECKING
from dotenv import load_dotenv
from loguru import logger

if TYPE_CHECKING:
    from loguru import Record


def get_log_level() -> str:
    """Reads LOG_LEVEL or log_level from .env or environment, defaults to 'INFO'."""
    load_dotenv()
    level = os.getenv("LOG_LEVEL") or os.getenv("log_level") or "INFO"
    return level.strip().upper()


# ── Stdout / stderr filters ───────────────────────────────────────────────────

def _stdout_filter(record: Record) -> bool:
    """Pass DEBUG / INFO / WARNING to stdout."""
    return record["level"].no < logging.ERROR


def _stderr_filter(record: Record) -> bool:
    """Pass ERROR / CRITICAL to stderr."""
    return record["level"].no >= logging.ERROR


# ── Stdlib → Loguru bridge ────────────────────────────────────────────────────

class InterceptHandler(logging.Handler):
    """Redirect all stdlib logging calls into Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: FrameType | None = sys._getframe(6)
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# ── Public setup function ─────────────────────────────────────────────────────

def setup_logging(level: str | None = None) -> None:
    """
    Configure Loguru sinks and intercept all stdlib loggers.
    Call once at the very start of the application entry point.
    """
    if not level:
        level = get_log_level()
    else:
        level = level.strip().upper()

    logger.remove()  # remove default sink

    common: dict = {
        "level": level,
        "serialize": True,   # JSON output
        "backtrace": False,
        "diagnose": False,
    }

    # stdout — DEBUG / INFO / WARNING
    logger.add(sys.stdout, filter=_stdout_filter, **common)

    # stderr — ERROR / CRITICAL
    logger.add(sys.stderr, filter=_stderr_filter, **{**common, "level": "ERROR"})

    # Redirect all stdlib loggers (uvicorn, motor, aiogram, aio_pika …)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Suppress noisy third-party loggers — we handle HTTP access via middleware
    _quiet = {
        "uvicorn.access": logging.WARNING,  # replaced by our middleware
        "motor":          logging.WARNING,
        "aio_pika":       logging.WARNING,
        "aiormq":         logging.WARNING,
    }
    for name, lvl in _quiet.items():
        _lib_logger = logging.getLogger(name)
        _lib_logger.handlers = [InterceptHandler()]
        _lib_logger.setLevel(lvl)
        _lib_logger.propagate = False
