"""
Base reader interface and file utilities for resume parsing.

Defines the abstract base class for file readers and provides common utilities
for file validation and text extraction.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from parser.config import MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS
from parser.exceptions import FileValidationException

logger = logging.getLogger(__name__)


class BaseReader(ABC):
    """Abstract base class for file readers."""

    def __init__(self, file_path: str | Path) -> None:
        """
        Initialize reader with file path.

        Args:
            file_path: Path to the resume file.

        Raises:
            FileValidationException: If file validation fails.
        """
        self.file_path = Path(file_path)
        self._validate_file()

    def _validate_file(self) -> None:
        """
        Validate file existence, extension, and size.

        Raises:
            FileValidationException: If validation fails.
        """
        if not self.file_path.exists():
            msg = f"File not found: {self.file_path}"
            logger.error(msg)
            raise FileValidationException(msg)

        if self.file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            msg = f"Unsupported file extension: {self.file_path.suffix}"
            logger.error(msg)
            raise FileValidationException(msg)

        file_size_mb = self.file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            msg = f"File size exceeds maximum ({file_size_mb:.2f}MB > {MAX_FILE_SIZE_MB}MB)"
            logger.error(msg)
            raise FileValidationException(msg)

        logger.debug(f"File validation passed: {self.file_path}")

    @abstractmethod
    def extract_text(self) -> str:
        """
        Extract text from the resume file.

        Returns:
            Extracted text content.

        Raises:
            FileReadException: If text extraction fails.
        """
        pass

    @abstractmethod
    def extract_metadata(self) -> dict:
        """
        Extract metadata from the resume file.

        Returns:
            Dictionary containing file metadata.

        Raises:
            FileReadException: If metadata extraction fails.
        """
        pass


def get_reader(file_path: str | Path) -> BaseReader:
    """
    Factory function to get appropriate reader for file type.

    Args:
        file_path: Path to the resume file.

    Returns:
        Appropriate reader instance (PDFReader or DocxReader).

    Raises:
        FileValidationException: If file type is not supported.
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        from parser.readers.pdf import PDFReader

        return PDFReader(file_path)
    elif extension in {".docx", ".doc"}:
        from parser.readers.docx import DocxReader

        return DocxReader(file_path)
    else:
        msg = f"Unsupported file type: {extension}"
        logger.error(msg)
        raise FileValidationException(msg)
