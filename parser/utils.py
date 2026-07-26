"""
Utility functions for the resume parser system.

Helper functions and utilities used across the parsing pipeline.
"""

import re
from datetime import datetime, date
from typing import List, Optional, Tuple


def parse_date_string(date_str: str) -> Optional[date]:
    """
    Parse common date formats found in resumes.

    Supports formats like:
    - "2020-01-15"
    - "Jan 2020"
    - "January 2020"
    - "01/15/2020"
    - "2020"

    Args:
        date_str: String containing date information.

    Returns:
        Parsed date object or None if parsing fails.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()

    # Try ISO format (YYYY-MM-DD)
    try:
        return datetime.fromisoformat(date_str).date()
    except (ValueError, AttributeError):
        pass

    # Try US format (MM/DD/YYYY)
    try:
        parts = date_str.split("/")
        if len(parts) == 3:
            month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
            return date(year, month, day)
    except (ValueError, IndexError):
        pass

    # Try month-year format (Jan 2020, January 2020)
    try:
        month_patterns = {
            "january": 1, "jan": 1,
            "february": 2, "feb": 2,
            "march": 3, "mar": 3,
            "april": 4, "apr": 4,
            "may": 5,
            "june": 6, "jun": 6,
            "july": 7, "jul": 7,
            "august": 8, "aug": 8,
            "september": 9, "sep": 9, "sept": 9,
            "october": 10, "oct": 10,
            "november": 11, "nov": 11,
            "december": 12, "dec": 12,
        }

        date_lower = date_str.lower()
        for month_name, month_num in month_patterns.items():
            if month_name in date_lower:
                # Extract year (4 digits)
                year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
                if year_match:
                    year = int(year_match.group(0))
                    return date(year, month_num, 1)
    except (ValueError, IndexError):
        pass

    # Try year only (YYYY)
    try:
        year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
        if year_match:
            year = int(year_match.group(0))
            return date(year, 1, 1)
    except (ValueError, IndexError):
        pass

    return None


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.

    Args:
        text: Text to normalize.

    Returns:
        Text with normalized whitespace.
    """
    # Replace multiple spaces with single space
    text = re.sub(r" +", " ", text)
    # Replace multiple newlines with double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_phone_parts(phone: str) -> Optional[Tuple[str, str, str]]:
    """
    Extract phone number parts (area code, exchange, number).

    Args:
        phone: Phone number string.

    Returns:
        Tuple of (area_code, exchange, number) or None.
    """
    # Remove non-digits
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 10:
        return digits[:3], digits[3:6], digits[6:]
    elif len(digits) == 11 and digits[0] == "1":
        return digits[1:4], digits[4:7], digits[7:]

    return None


def is_valid_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate.

    Returns:
        True if email format is valid.
    """
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, email))


def is_valid_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate.

    Returns:
        True if URL format is valid.
    """
    url_pattern = r"^https?://[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)$"
    return bool(re.match(url_pattern, url))


def calculate_date_range(start_date: Optional[date], end_date: Optional[date]) -> Optional[str]:
    """
    Calculate human-readable date range.

    Args:
        start_date: Start date.
        end_date: End date.

    Returns:
        Formatted date range string or None.
    """
    if not start_date:
        return None

    start_str = start_date.strftime("%b %Y")

    if not end_date:
        return f"{start_str} - Present"

    end_str = end_date.strftime("%b %Y")
    return f"{start_str} - {end_str}"


def deduplicate_list(items: List[str], case_sensitive: bool = False) -> List[str]:
    """
    Remove duplicates from list while preserving order.

    Args:
        items: List of items.
        case_sensitive: Whether comparison is case-sensitive.

    Returns:
        List with duplicates removed.
    """
    seen = set()
    result = []

    for item in items:
        compare_item = item if case_sensitive else item.lower()

        if compare_item not in seen:
            seen.add(compare_item)
            result.append(item)

    return result


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate.
        max_length: Maximum length.
        suffix: Suffix to add if truncated.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def merge_consecutive_entries(items: List[str], max_gap: int = 1) -> List[str]:
    """
    Merge consecutive similar items (e.g., consecutive description lines).

    Args:
        items: List of items to process.
        max_gap: Maximum gap in sequence (not used for merging).

    Returns:
        Processed list.
    """
    if not items:
        return []

    # Remove very short items and duplicates
    filtered = []
    for item in items:
        if len(item.strip()) > 5 and item not in filtered:
            filtered.append(item)

    return filtered
