"""
PDF file reader implementation using PyMuPDF (fitz).

Provides text and metadata extraction from PDF resume files with
robust error handling.
"""

import logging
from pathlib import Path
from typing import Any

import fitz

from parser.exceptions import FileReadException

logger = logging.getLogger(__name__)


class PDFReader:
    """Reader for PDF resume files using PyMuPDF."""

    def __init__(self, file_path: str | Path) -> None:
        """
        Initialize PDF reader.

        Args:
            file_path: Path to the PDF file.
        """
        self.file_path = Path(file_path)

    def extract_text(self) -> str:
        """
        Extract text from PDF file.

        Returns:
            Concatenated text from all pages.

        Raises:
            FileReadException: If PDF reading fails.
        """
        try:
            doc = fitz.open(self.file_path)
            text_content = []

            for page_num, page in enumerate(doc, 1):
                try:
                    text = page.get_text()
                    if text.strip():
                        text_content.append(text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {e}")

            doc.close()

            extracted_text = "\n".join(text_content)
            if not extracted_text.strip():
                logger.warning(f"No text extracted from PDF: {self.file_path}")

            logger.debug(f"Extracted {len(extracted_text)} characters from PDF")
            return extracted_text

        except Exception as e:
            msg = f"Failed to read PDF file {self.file_path}: {e}"
            logger.error(msg)
            raise FileReadException(msg) from e

    def extract_metadata(self) -> dict[str, Any]:
        """
        Extract metadata from PDF file.

        Returns:
            Dictionary with file metadata including page count, author, etc.

        Raises:
            FileReadException: If metadata extraction fails.
        """
        try:
            doc = fitz.open(self.file_path)
            metadata = {
                "page_count": doc.page_count,
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
            }
            doc.close()

            logger.debug(f"Extracted metadata from PDF: {metadata}")
            return metadata

        except Exception as e:
            msg = f"Failed to extract metadata from PDF {self.file_path}: {e}"
            logger.error(msg)
            raise FileReadException(msg) from e
