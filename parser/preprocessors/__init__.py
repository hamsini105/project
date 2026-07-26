"""
Text preprocessing module for resume parsing.

Handles text normalization, cleaning, and section detection to prepare
raw extracted text for further processing.
"""

import logging
import re
from typing import List

from parser.config import (
    EDUCATION_KEYWORDS,
    EXPERIENCE_KEYWORDS,
    EXTRA_WHITESPACE_PATTERN,
    MIN_LINE_LENGTH,
    SKILLS_KEYWORDS,
)
from parser.exceptions import PreprocessingException

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Handles text normalization and cleaning."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text by removing special characters and extra whitespace.

        Args:
            text: Raw text to normalize.

        Returns:
            Normalized text.

        Raises:
            PreprocessingException: If preprocessing fails.
        """
        try:
            if not isinstance(text, str):
                msg = "Input must be a string"
                logger.error(msg)
                raise TypeError(msg)

            # Remove form feeds and other special characters
            text = re.sub(r"[\f\v\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)

            # Normalize line breaks
            text = re.sub(r"\r\n", "\n", text)
            text = re.sub(r"\r", "\n", text)

            # Remove extra whitespace while preserving structure
            text = re.sub(EXTRA_WHITESPACE_PATTERN, " ", text)

            # Remove excessive line breaks
            text = re.sub(r"\n{3,}", "\n\n", text)

            return text.strip()

        except Exception as e:
            msg = f"Text normalization failed: {e}"
            logger.error(msg)
            raise PreprocessingException(msg) from e

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean text by removing empty lines and normalizing spacing.

        Args:
            text: Text to clean.

        Returns:
            Cleaned text.
        """
        try:
            lines = text.split("\n")
            cleaned_lines = [
                line.strip() for line in lines if len(line.strip()) > MIN_LINE_LENGTH
            ]
            return "\n".join(cleaned_lines)
        except Exception as e:
            msg = f"Text cleaning failed: {e}"
            logger.error(msg)
            raise PreprocessingException(msg) from e

    @staticmethod
    def split_into_lines(text: str) -> List[str]:
        """
        Split text into lines and filter empty lines.

        Args:
            text: Text to split.

        Returns:
            List of non-empty lines.
        """
        lines = text.split("\n")
        return [line.strip() for line in lines if line.strip()]

    @staticmethod
    def extract_sections(text: str) -> dict[str, str]:
        """
        Detect and extract major resume sections.

        Args:
            text: Full resume text.

        Returns:
            Dictionary with section names as keys and section text as values.
        """
        try:
            sections = {}
            current_section = "summary"
            current_content = []

            lines = TextPreprocessor.split_into_lines(text)

            for line in lines:
                line_lower = line.lower()

                # Check if line is a section header
                detected_section = None
                if any(kw in line_lower for kw in EDUCATION_KEYWORDS):
                    detected_section = "education"
                elif any(kw in line_lower for kw in EXPERIENCE_KEYWORDS):
                    detected_section = "experience"
                elif any(kw in line_lower for kw in SKILLS_KEYWORDS):
                    detected_section = "skills"

                if detected_section:
                    # Save previous section
                    if current_content:
                        sections[current_section] = "\n".join(current_content)
                    current_section = detected_section
                    current_content = []
                else:
                    current_content.append(line)

            # Save last section
            if current_content:
                sections[current_section] = "\n".join(current_content)

            logger.debug(f"Detected sections: {list(sections.keys())}")
            return sections

        except Exception as e:
            msg = f"Section extraction failed: {e}"
            logger.error(msg)
            raise PreprocessingException(msg) from e
