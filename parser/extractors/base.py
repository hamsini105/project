"""
Base extractor class and utilities for section-specific data extraction.

Provides common functionality for all extractors including regex pattern matching
and text preprocessing utilities.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from parser.config import (
    EMAIL_PATTERN,
    GITHUB_PATTERN,
    LINKEDIN_PATTERN,
    PHONE_PATTERN,
)
from parser.exceptions import ExtractionException

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Abstract base class for section extractors."""

    def __init__(self) -> None:
        """Initialize extractor."""
        pass

    @abstractmethod
    def extract(self, text: str) -> Any:
        """
        Extract data from text.

        Args:
            text: Text section to extract from.

        Returns:
            Extracted data in appropriate format.

        Raises:
            ExtractionException: If extraction fails.
        """
        pass

    @staticmethod
    def find_pattern(pattern: re.Pattern[str], text: str) -> Optional[str]:
        """
        Find first match of regex pattern in text.

        Args:
            pattern: Compiled regex pattern.
            text: Text to search in.

        Returns:
            Matched string or None.
        """
        match = pattern.search(text)
        return match.group(0) if match else None

    @staticmethod
    def find_all_patterns(pattern: re.Pattern[str], text: str) -> List[str]:
        """
        Find all matches of regex pattern in text.

        Args:
            pattern: Compiled regex pattern.
            text: Text to search in.

        Returns:
            List of matched strings.
        """
        return pattern.findall(text)

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from text."""
        emails = BaseExtractor.find_all_patterns(EMAIL_PATTERN, text)
        return [email.lower() for email in emails if email]

    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract phone numbers from text."""
        return BaseExtractor.find_all_patterns(PHONE_PATTERN, text)

    @staticmethod
    def extract_linkedin(text: str) -> Optional[str]:
        """Extract LinkedIn URL from text."""
        return BaseExtractor.find_pattern(LINKEDIN_PATTERN, text)

    @staticmethod
    def extract_github(text: str) -> Optional[str]:
        """Extract GitHub URL from text."""
        return BaseExtractor.find_pattern(GITHUB_PATTERN, text)

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract all URLs from text."""
        url_pattern = re.compile(
            r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)"
        )
        return url_pattern.findall(text)

    @staticmethod
    def clean_line(line: str) -> str:
        """Clean and normalize a single line of text."""
        return " ".join(line.split())
