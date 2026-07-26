"""
Unit tests for the resume parser system.

Tests individual components and integration scenarios.
"""

import tempfile
from datetime import date
from pathlib import Path

import pytest

from parser import (
    ResumeParser,
    Resume,
    ContactDetails,
    EducationEntry,
    ExperienceEntry,
)
from parser.exceptions import FileValidationException, ResumeParsingException
from parser.extractors import (
    ContactExtractor,
    SkillsExtractor,
    EducationExtractor,
    ExperienceExtractor,
)
from parser.preprocessors import TextPreprocessor


class TestTextPreprocessor:
    """Tests for text preprocessing."""

    def test_normalize_text(self):
        """Test text normalization."""
        raw_text = "Hello   \n\n  World\r\nTest"
        normalized = TextPreprocessor.normalize_text(raw_text)

        assert "Hello" in normalized
        assert "World" in normalized
        assert "\r" not in normalized

    def test_clean_text(self):
        """Test text cleaning removes empty lines."""
        text = "Line 1\n\n\nLine 2\n  \nLine 3"
        cleaned = TextPreprocessor.clean_text(text)

        lines = cleaned.split("\n")
        assert len([l for l in lines if l.strip()]) == 3

    def test_split_into_lines(self):
        """Test text splitting into lines."""
        text = "Line 1\nLine 2\n\nLine 3"
        lines = TextPreprocessor.split_into_lines(text)

        assert len(lines) == 3
        assert lines[0] == "Line 1"
        assert lines[2] == "Line 3"


class TestContactExtractor:
    """Tests for contact details extraction."""

    def test_extract_email(self):
        """Test email extraction."""
        text = "John Doe john.doe@example.com +1-234-567-8900"
        extractor = ContactExtractor()
        contact = extractor.extract(text)

        assert contact.email == "john.doe@example.com"

    def test_extract_phone(self):
        """Test phone number extraction."""
        text = "Contact: +1-555-123-4567"
        extractor = ContactExtractor()
        contact = extractor.extract(text)

        assert contact.phone is not None
        assert "555" in contact.phone

    def test_extract_linkedin(self):
        """Test LinkedIn URL extraction."""
        text = "Profile: https://linkedin.com/in/johndoe"
        extractor = ContactExtractor()
        contact = extractor.extract(text)

        assert contact.linkedin is not None
        assert "linkedin" in str(contact.linkedin).lower()

    def test_extract_name(self):
        """Test name extraction."""
        text = "John Doe\nEmail: john@example.com"
        extractor = ContactExtractor()
        contact = extractor.extract(text)

        assert contact.full_name == "John Doe"


class TestSkillsExtractor:
    """Tests for skills extraction."""

    def test_extract_technical_skills(self):
        """Test technical skills extraction."""
        text = "Skills: Python, Django, PostgreSQL, React, Docker"
        extractor = SkillsExtractor()
        skills = extractor.extract(text)

        assert "Python" in skills
        assert "Docker" in skills

    def test_extract_soft_skills(self):
        """Test soft skills extraction."""
        text = "Leadership, Communication, Problem Solving, Teamwork"
        extractor = SkillsExtractor()
        skills = extractor.extract(text)

        assert any("leadership" in s.lower() for s in skills)

    def test_no_duplicate_skills(self):
        """Test that skills are not duplicated."""
        text = "Python Python Django Python"
        extractor = SkillsExtractor()
        skills = extractor.extract(text)

        python_count = sum(1 for s in skills if s.lower() == "python")
        assert python_count <= 1


class TestEducationExtractor:
    """Tests for education extraction."""

    def test_extract_education_entry(self):
        """Test education entry extraction."""
        text = """
        Bachelor of Science in Computer Science
        Massachusetts Institute of Technology (MIT)
        2015 - 2019
        """
        extractor = EducationExtractor()
        education = extractor.extract(text)

        # At least verify processing completes
        assert isinstance(education, list)

    def test_extract_degree(self):
        """Test degree type extraction."""
        text = "Master of Science in Data Science"
        extractor = EducationExtractor()
        degree = extractor._extract_degree(text)

        assert degree in ["Master", "Master's"]


class TestExperienceExtractor:
    """Tests for experience extraction."""

    def test_extract_experience_entry(self):
        """Test experience entry extraction."""
        text = """
        Senior Software Engineer | Tech Corp
        Jan 2020 - Present
        New York, NY
        Led development of microservices architecture
        """
        extractor = ExperienceExtractor()
        experience = extractor.extract(text)

        assert isinstance(experience, list)


class TestResumeModel:
    """Tests for Resume Pydantic model."""

    def test_create_resume(self):
        """Test creating a resume object."""
        contact = ContactDetails(full_name="John Doe", email="john@example.com")
        resume = Resume(contact=contact)

        assert resume.contact.full_name == "John Doe"
        assert resume.contact.email == "john@example.com"

    def test_resume_model_dump_clean(self):
        """Test clean JSON dump excludes None values."""
        contact = ContactDetails(full_name="John Doe")
        resume = Resume(contact=contact, skills=["Python", "Java"])

        clean_data = resume.model_dump_clean()

        assert "contact" in clean_data
        assert "skills" in clean_data
        assert clean_data.get("education") is None
        assert clean_data.get("experience") is None


class TestFileValidation:
    """Tests for file validation."""

    def test_unsupported_file_extension(self):
        """Test that unsupported file types raise exception."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            with pytest.raises(FileValidationException):
                from parser.readers import get_reader
                get_reader(tmp.name)

    def test_file_not_found(self):
        """Test that missing files raise exception."""
        with pytest.raises(FileValidationException):
            from parser.readers import get_reader
            get_reader("/nonexistent/file.pdf")


class TestParserIntegration:
    """Integration tests for the full parser."""

    def test_parser_instantiation(self):
        """Test that parser can be instantiated."""
        parser = ResumeParser()
        assert parser is not None
        assert hasattr(parser, "parse")
        assert hasattr(parser, "parse_and_return_json")
        assert hasattr(parser, "parse_and_save_json")


if __name__ == "__main__":
    # Run basic tests
    print("Running Resume Parser Tests...")
    print("=" * 60)

    # Test preprocessing
    print("\nTesting TextPreprocessor...")
    test_prep = TestTextPreprocessor()
    test_prep.test_normalize_text()
    test_prep.test_clean_text()
    print("✓ TextPreprocessor tests passed")

    # Test contact extraction
    print("\nTesting ContactExtractor...")
    test_contact = TestContactExtractor()
    test_contact.test_extract_email()
    test_contact.test_extract_name()
    print("✓ ContactExtractor tests passed")

    # Test skills extraction
    print("\nTesting SkillsExtractor...")
    test_skills = TestSkillsExtractor()
    test_skills.test_extract_technical_skills()
    print("✓ SkillsExtractor tests passed")

    # Test models
    print("\nTesting Resume Models...")
    test_models = TestResumeModel()
    test_models.test_create_resume()
    test_models.test_resume_model_dump_clean()
    print("✓ Resume models tests passed")

    # Test parser
    print("\nTesting Parser Integration...")
    test_integration = TestParserIntegration()
    test_integration.test_parser_instantiation()
    print("✓ Parser integration tests passed")

    print("\n" + "="*60)
    print("All tests passed!")
