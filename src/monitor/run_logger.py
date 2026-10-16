"""Structured logging with run_id tracking for RetailSync pipeline."""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import settings


class RunIdFilter(logging.Filter):
    """Injects a run_id attribute into every log record if not present."""

    def __init__(self, run_id: Optional[str] = None):
        super().__init__()
        self.run_id = run_id or "NO_RUN_ID"

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id") or not record.run_id:
            record.run_id = self.run_id
        return True


def setup_logger(
    name: str = "retailsync",
    run_id: Optional[str] = None,
    log_to_file: bool = True,
) -> logging.Logger:
    """Configures and returns a structured logger with run_id propagation.

    Args:
        name: Name of the logger.
        run_id: Unique pipeline run identifier.
        log_to_file: Whether to attach a file handler in the logs directory.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        for handler in logger.handlers:
            # Update filter run_id if reconfigured with new run_id
            for f in handler.filters:
                if isinstance(f, RunIdFilter):
                    f.run_id = run_id or f.run_id
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | [%(run_id)s] | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    run_filter = RunIdFilter(run_id=run_id)

    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(run_filter)
    logger.addHandler(console_handler)

    # File Handler
    if log_to_file:
        settings.logs_dir.mkdir(parents=True, exist_ok=True)
        file_path = settings.logs_dir / "retailsync.log"
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(run_filter)
        logger.addHandler(file_handler)

    return logger
