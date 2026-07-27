"""
Logging configuration for the ATS analysis engine.

Sets up structured logging for ATS operations.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

try:
    import colorlog

    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str | Path] = None,
    use_color: bool = True,
) -> None:
    """
    Configure logging for ATS analysis.

    Args:
        level: Logging level (default: logging.INFO).
        log_file: Path to log file. If provided, logs will also be written to file.
        use_color: Whether to use colored output (requires colorlog).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Formatter
    if use_color and HAS_COLORLOG:
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s[%(levelname)-8s]%(reset)s %(asctime)s - %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    else:
        formatter = logging.Formatter(
            "[%(levelname)-8s] %(asctime)s - %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log_file is provided)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level)

        file_formatter = logging.Formatter(
            "[%(levelname)-8s] %(asctime)s - %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        logging.info(f"Logging to file: {log_file}")

    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


# Default setup on import
setup_logging(level=logging.INFO)
