"""
Certifications extractor from resume text.

Extracts certification and credential information including title, issuer,
dates, and credential details.
"""

import logging
import re
from datetime import date
from typing import List, Optional

from parser.config import YEAR_PATTERN
from parser.extractors.base import BaseExtractor
from parser.models import CertificationEntry

logger = logging.getLogger(__name__)

# Common certification issuers
COMMON_ISSUERS = {
    "aws",
    "amazon",
    "microsoft",
    "azure",
    "google",
    "gcp",
    "ibm",
    "cisco",
    "comptia",
    "oracle",
    "salesforce",
    "coursera",
    "edx",
    "udemy",
    "linux academy",
    "pmp",
    "scrum alliance",
}


class CertificationsExtractor(BaseExtractor):
    """Extracts certification entries from resume text."""

    def extract(self, text: str) -> List[CertificationEntry]:
        """
        Extract certification entries from text.

        Args:
            text: Resume text section containing certifications.

        Returns:
            List of CertificationEntry objects.
        """
        try:
            certifications = []
            lines = text.split("\n")

            current_cert = None
            cert_lines = []

            for line in lines:
                cleaned = self.clean_line(line)
                if not cleaned:
                    continue

                # Check if this looks like a certification header
                if self._is_certification_header(cleaned):
                    # Save previous certification
                    if current_cert:
                        certifications.append(current_cert)

                    # Parse new certification
                    current_cert = self._parse_certification(cleaned, cert_lines)
                    cert_lines = []
                else:
                    cert_lines.append(cleaned)

            # Save last certification
            if current_cert:
                certifications.append(current_cert)

            logger.debug(f"Extracted {len(certifications)} certifications")
            return certifications

        except Exception as e:
            logger.error(f"Failed to extract certifications: {e}")
            return []

    def _is_certification_header(self, line: str) -> bool:
        """Check if line looks like a certification title."""
        # Certifications are typically shorter lines
        if len(line) > 150:
            return False

        # Check for common issuer names or cert indicators
        line_lower = line.lower()

        has_cert_keyword = any(
            keyword in line_lower
            for keyword in ["certification", "certificate", "certified", "credential"]
        )

        has_issuer = any(issuer in line_lower for issuer in COMMON_ISSUERS)

        return has_cert_keyword or has_issuer or (5 < len(line) < 100)

    def _parse_certification(self, header: str, detail_lines: List[str]) -> CertificationEntry:
        """Parse certification from header and detail lines."""
        title = None
        issuer = None
        issue_date = None
        expiry_date = None
        credential_id = None
        credential_url = None

        # Extract title and issuer from header
        if "|" in header:
            parts = header.split("|")
            title = parts[0].strip()
            issuer = parts[1].strip() if len(parts) > 1 else None
        else:
            title = header
            # Try to extract issuer from title
            issuer = self._extract_issuer(title)

        # Process detail lines
        combined_details = " ".join(detail_lines)

        # Extract dates
        issue_date, expiry_date = self._extract_dates(combined_details)

        # Extract credential ID
        credential_id = self._extract_credential_id(combined_details)

        # Extract credential URL
        credential_url = self.find_pattern(
            re.compile(
                r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b"
            ),
            combined_details,
        )

        return CertificationEntry(
            title=title or "Unknown Certification",
            issuer=issuer,
            issue_date=issue_date,
            expiry_date=expiry_date,
            credential_id=credential_id,
            credential_url=credential_url,
        )

    def _extract_issuer(self, text: str) -> Optional[str]:
        """Extract issuer from text."""
        text_lower = text.lower()

        # Check for known issuers
        for issuer in COMMON_ISSUERS:
            if issuer in text_lower:
                return issuer.title()

        # Try to find organization name pattern
        # Usually "Certified by [Organization]" or "[Certification] from [Organization]"
        org_pattern = r"(?:by|from)\s+([A-Z][a-zA-Z\s]+)"
        match = re.search(org_pattern, text)
        if match:
            return match.group(1).strip()

        return None

    def _extract_dates(self, text: str) -> tuple[Optional[date], Optional[date]]:
        """Extract issue and expiry dates."""
        years = YEAR_PATTERN.findall(text)
        issue_date = None
        expiry_date = None

        if len(years) >= 2:
            try:
                issue_date = date(int(years[0]), 1, 1)
                if "valid" not in text.lower() and "lifetime" not in text.lower():
                    expiry_date = date(int(years[1]), 12, 31)
            except ValueError:
                pass
        elif len(years) == 1:
            try:
                # If only one year, assume it's the issue date
                if "expires" not in text.lower() and "valid until" not in text.lower():
                    issue_date = date(int(years[0]), 1, 1)
            except ValueError:
                pass

        return issue_date, expiry_date

    def _extract_credential_id(self, text: str) -> Optional[str]:
        """Extract credential ID from text."""
        # Look for patterns like "Credential ID: ABC123" or "License #: XYZ789"
        id_pattern = r"(?:credential\s+id|license\s+#?|cert\s+#?)[:\s]+([A-Z0-9\-]+)"
        match = re.search(id_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

        return None
