"""
Main resume parser orchestrator.

Coordinates the complete parsing pipeline: file reading, preprocessing,
and section-specific data extraction.
"""

import json
import logging
from pathlib import Path
from typing import Any

from parser.exceptions import ResumeParsingException
from parser.extractors import (
    CertificationsExtractor,
    ContactExtractor,
    EducationExtractor,
    ExperienceExtractor,
    ProjectsExtractor,
    SkillsExtractor,
)
from parser.models import Resume
from parser.preprocessors import TextPreprocessor
from parser.readers import get_reader

logger = logging.getLogger(__name__)


class ResumeParser:
    """
    Production-grade resume parser.

    Orchestrates the complete parsing pipeline including file reading,
    text preprocessing, and section-specific data extraction.
    """

    def __init__(self) -> None:
        """Initialize parser with all required extractors."""
        self.text_preprocessor = TextPreprocessor()
        self.contact_extractor = ContactExtractor()
        self.skills_extractor = SkillsExtractor()
        self.education_extractor = EducationExtractor()
        self.experience_extractor = ExperienceExtractor()
        self.projects_extractor = ProjectsExtractor()
        self.certifications_extractor = CertificationsExtractor()

    def parse(self, file_path: str | Path) -> Resume:
        """
        Parse a resume file and extract all information.

        Args:
            file_path: Path to the resume file (PDF or DOCX).

        Returns:
            Resume object containing all extracted data.

        Raises:
            ResumeParsingException: If parsing fails at any stage.
        """
        try:
            file_path = Path(file_path)
            logger.info(f"Starting resume parsing for: {file_path}")

            # Step 1: Read file
            reader = get_reader(file_path)
            raw_text = reader.extract_text()
            logger.debug(f"Raw text extracted: {len(raw_text)} characters")

            # Step 2: Preprocess text
            normalized_text = self.text_preprocessor.normalize_text(raw_text)
            cleaned_text = self.text_preprocessor.clean_text(normalized_text)
            logger.debug(f"Text preprocessed: {len(cleaned_text)} characters")

            # Step 3: Extract sections
            sections = self.text_preprocessor.extract_sections(cleaned_text)
            logger.debug(f"Sections detected: {list(sections.keys())}")

            # Step 4: Extract contact details (from full text)
            contact = self.contact_extractor.extract(cleaned_text)
            logger.debug(f"Contact extracted: {contact.full_name}")

            # Step 5: Extract summary (if present)
            summary = sections.get("summary", "").strip()
            if summary and len(summary) > 500:
                summary = summary[:500]  # Cap at 500 chars

            # Step 6: Extract skills
            skills_text = sections.get("skills", cleaned_text)
            skills = self.skills_extractor.extract(skills_text)
            logger.debug(f"Skills extracted: {len(skills)}")

            # Step 7: Extract education
            education_text = sections.get("education", cleaned_text)
            education = self.education_extractor.extract(education_text)
            logger.debug(f"Education entries extracted: {len(education)}")

            # Step 8: Extract experience
            experience_text = sections.get("experience", cleaned_text)
            experience = self.experience_extractor.extract(experience_text)
            logger.debug(f"Experience entries extracted: {len(experience)}")

            # Step 9: Extract projects (from full text or experience section)
            projects = self.projects_extractor.extract(cleaned_text)
            logger.debug(f"Projects extracted: {len(projects)}")

            # Step 10: Extract certifications
            certifications = self.certifications_extractor.extract(cleaned_text)
            logger.debug(f"Certifications extracted: {len(certifications)}")

            # Step 11: Build resume object
            resume = Resume(
                contact=contact,
                summary=summary if summary else None,
                skills=skills if skills else None,
                education=education if education else None,
                experience=experience if experience else None,
                projects=projects if projects else None,
                certifications=certifications if certifications else None,
            )

            logger.info(f"Resume parsing completed successfully for: {contact.full_name}")
            return resume

        except ResumeParsingException:
            raise
        except Exception as e:
            msg = f"Unexpected error during resume parsing: {e}"
            logger.error(msg, exc_info=True)
            raise ResumeParsingException(msg) from e

    def parse_and_return_json(self, file_path: str | Path) -> dict[str, Any]:
        """
        Parse resume and return as JSON-serializable dictionary.

        Args:
            file_path: Path to the resume file.

        Returns:
            Dictionary representation of the resume.
        """
        resume = self.parse(file_path)
        return resume.model_dump_clean()

    def parse_and_save_json(self, file_path: str | Path, output_path: str | Path) -> None:
        """
        Parse resume and save extracted data as JSON file.

        Args:
            file_path: Path to the resume file.
            output_path: Path where JSON output should be saved.
        """
        resume_data = self.parse_and_return_json(file_path)
        output_path = Path(output_path)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(resume_data, f, indent=2, default=str)

        logger.info(f"Resume data saved to: {output_path}")
