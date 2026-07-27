"""
Core package — application-wide infrastructure.

Exports the three primary entry points that callers need:
  - get_settings()    : typed, cached settings singleton
  - configure_logging(): root-logger setup (call once at startup)
"""

from core.logging_setup import configure_logging
from core.settings import Settings, get_settings

__all__ = ["Settings", "get_settings", "configure_logging"]
