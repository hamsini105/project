"""
Centralized logging setup.

Call ``configure_logging()`` once at application startup — before any
other module imports that call ``logging.getLogger()``.  All subsequent
loggers inherit the handlers and level established here.

Supports two output formats:
  - ``"text"``  Human-readable, suitable for local development and stderr.
  - ``"json"``  Machine-readable, suitable for log aggregators (Datadog,
                CloudWatch, Loki).  Requires ``python-json-logger``.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

# Guard prevents duplicate handler registration on Streamlit reruns.
_logging_configured: bool = False

_TEXT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
_TEXT_DATE   = "%Y-%m-%d %H:%M:%S"

# Third-party loggers that are excessively noisy at default levels
_SUPPRESS = (
    "urllib3",
    "requests",
    "httpx",
    "sentence_transformers",
    "transformers",
    "huggingface_hub",
    "filelock",
    "PIL",
)


def configure_logging(
    level:        str = "INFO",
    format_type:  str = "text",
    log_file:     Optional[str] = None,
    max_bytes:    int = 10_485_760,
    backup_count: int = 5,
) -> None:
    """
    Configure the root logger for the application.

    Idempotent: subsequent calls with the same arguments are no-ops.
    Call with different arguments to reconfigure (e.g., in tests).

    Args:
        level:        Root log level string.  Case-insensitive.
        format_type:  ``"text"`` or ``"json"``.
        log_file:     Optional path for a rotating log file.  Parent
                      directories are created automatically.
        max_bytes:    Rotating file handler maximum size.
        backup_count: Number of backup files retained by the file handler.
    """
    global _logging_configured

    root = logging.getLogger()
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(numeric_level)

    # Remove any handlers set by earlier calls or basicConfig
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    formatter = _build_formatter(format_type)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_file:
        _attach_file_handler(root, log_file, formatter, max_bytes, backup_count)

    _suppress_noisy_loggers(numeric_level)

    _logging_configured = True
    logging.getLogger(__name__).debug(
        "Logging configured | level=%s format=%s file=%s",
        level.upper(), format_type, log_file or "none",
    )


def reconfigure(
    level:       str = "INFO",
    format_type: str = "text",
    log_file:    Optional[str] = None,
) -> None:
    """Force-reconfigure logging, ignoring the idempotency guard."""
    global _logging_configured
    _logging_configured = False
    configure_logging(level=level, format_type=format_type, log_file=log_file)


# ── Private helpers ───────────────────────────────────────────────────────────

def _build_formatter(format_type: str) -> logging.Formatter:
    """Return a text or JSON formatter."""
    if format_type == "json":
        try:
            from pythonjsonlogger import jsonlogger  # type: ignore[import-untyped]

            return jsonlogger.JsonFormatter(
                "%(asctime)s %(levelname)s %(name)s %(lineno)d %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
                rename_fields={"levelname": "level", "asctime": "timestamp"},
            )
        except ImportError:
            logging.getLogger(__name__).warning(
                "python-json-logger not installed; falling back to text format. "
                "Install with: pip install python-json-logger"
            )

    return logging.Formatter(fmt=_TEXT_FORMAT, datefmt=_TEXT_DATE)


def _attach_file_handler(
    root:         logging.Logger,
    log_file:     str,
    formatter:    logging.Formatter,
    max_bytes:    int,
    backup_count: int,
) -> None:
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


def _suppress_noisy_loggers(root_level: int) -> None:
    """
    Raise the log level of chatty third-party libraries to WARNING
    unless the application itself is configured at DEBUG level.
    """
    if root_level <= logging.DEBUG:
        return
    for name in _SUPPRESS:
        logging.getLogger(name).setLevel(logging.WARNING)
