"""
Contact details extractor from resume text.

Extracts contact information including name, email, phone, location,
and social media profiles.
"""

import logging
import re
from typing import Optional

from parser.extractors.base import BaseExtractor
from parser.models import ContactDetails

logger = logging.getLogger(__name__)


class ContactExtractor(BaseExtractor):
    """Extracts contact details from resume text."""

    def extract(self, text: str) -> ContactDetails:
        """
        Extract contact details from text.

        Args:
            text: Resume text to extract from.

        Returns:
            ContactDetails object with extracted information.
        """
        try:
            name = self._extract_name(text)
            email = self._extract_email(text)
            phone = self._extract_phone(text)
            location = self._extract_location(text)
            linkedin = self._extract_linkedin(text)
            github = self._extract_github(text)
            website = self._extract_website(text)

            contact = ContactDetails(
                full_name=name or "Unknown",
                email=email,
                phone=phone,
                location=location,
                linkedin=linkedin,
                github=github,
                website=website,
            )

            logger.debug(f"Extracted contact: {contact.full_name}, email: {contact.email}")
            return contact

        except Exception as e:
            logger.error(f"Failed to extract contact details: {e}")
            # Return minimal contact with just name if extraction fails
            return ContactDetails(full_name="Unknown")

    def _extract_name(self, text: str) -> Optional[str]:
        """
        Extract full name from resume.

        Assumes the first meaningful line or specially formatted text is the name.
        """
        lines = text.split("\n")
        for line in lines:
            cleaned = self.clean_line(line)
            # Skip lines that look like emails, URLs, or are too short
            if (
                len(cleaned) > 3
                and len(cleaned) < 100
                and "@" not in cleaned
                and "http" not in cleaned.lower()
                and not cleaned.startswith(("•", "-", "*"))
            ):
                return cleaned

        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract primary email address."""
        emails = self.extract_emails(text)
        return emails[0] if emails else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract primary phone number."""
        phones = self.extract_phone_numbers(text)
        if phones:
            # Format phone number
            if isinstance(phones[0], tuple):
                return "-".join(phones[0])
            return phones[0]
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """
        Extract location (city, state/country).

        Looks for patterns like "City, State" or "City, Country".
        """
        # Pattern for location: "City, State/Country"
        location_pattern = re.compile(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)")

        match = location_pattern.search(text)
        if match:
            return f"{match.group(1)}, {match.group(2)}"

        return None

    def _extract_linkedin(self, text: str) -> Optional[str]:
        """Extract LinkedIn profile URL."""
        linkedin_url = self.extract_linkedin(text)
        if linkedin_url:
            # Ensure it has proper scheme
            if not linkedin_url.startswith("http"):
                linkedin_url = "https://" + linkedin_url
        return linkedin_url

    def _extract_github(self, text: str) -> Optional[str]:
        """Extract GitHub profile URL."""
        github_url = self.extract_github(text)
        if github_url:
            # Ensure it has proper scheme
            if not github_url.startswith("http"):
                github_url = "https://" + github_url
        return github_url

    def _extract_website(self, text: str) -> Optional[str]:
        """Extract personal website URL."""
        urls = self.extract_urls(text)
        # Filter out LinkedIn and GitHub URLs
        for url in urls:
            if "linkedin" not in url.lower() and "github" not in url.lower():
                return url
        return None
