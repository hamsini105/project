"""Shared logging configuration for the frontend project."""

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger with consistent formatting."""
    logger = logging.getLogger(name)

    if logging.getLogger().handlers:
        return logger

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logger
