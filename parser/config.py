"""
Configuration settings for the resume parsing engine.

Centralizes all constants, patterns, and configuration values to avoid
hardcoding values throughout the codebase.
"""

import re
from typing import List, Pattern

# File handling
MAX_FILE_SIZE_MB = 10
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}

# Text preprocessing
MIN_LINE_LENGTH = 2
EXTRA_WHITESPACE_PATTERN = r"\s+"

# Email and phone patterns
EMAIL_PATTERN: Pattern[str] = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)
PHONE_PATTERN: Pattern[str] = re.compile(
    r"(?:\+?1[-.\s]?)?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})"
)

# LinkedIn and GitHub patterns
LINKEDIN_PATTERN: Pattern[str] = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+", re.IGNORECASE
)
GITHUB_PATTERN: Pattern[str] = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", re.IGNORECASE
)

# Education keywords for section detection
EDUCATION_KEYWORDS = {
    "education",
    "academic",
    "degree",
    "university",
    "college",
    "school",
    "institute",
    "qualification",
}

# Experience keywords for section detection
EXPERIENCE_KEYWORDS = {
    "experience",
    "employment",
    "professional",
    "work",
    "career",
    "position",
    "role",
}

# Skills keywords for section detection
SKILLS_KEYWORDS = {
    "skills",
    "technical skills",
    "core competencies",
    "expertise",
    "proficiencies",
    "competencies",
}

# Certification keywords
CERTIFICATION_KEYWORDS = {
    "certification",
    "certifications",
    "credentials",
    "license",
    "licenses",
    "accreditation",
    "certificate",
    "certificates",
}

# Project keywords
PROJECT_KEYWORDS = {
    "project",
    "projects",
    "portfolio",
}

# Common degree keywords
DEGREE_KEYWORDS = {
    "bachelor",
    "master",
    "phd",
    "diploma",
    "associate",
    "b.s.",
    "b.a.",
    "m.s.",
    "m.a.",
    "b.tech",
    "m.tech",
}

# Common university names (subset - for validation)
COMMON_UNIVERSITIES: List[str] = [
    "university",
    "institute",
    "college",
    "academy",
    "polytechnic",
    "technical",
]

# Programming languages and tools (subset)
PROGRAMMING_LANGUAGES = {
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "go",
    "rust",
    "ruby",
    "php",
    "swift",
    "kotlin",
    "scala",
    "r",
    "matlab",
}

# Frameworks and libraries
FRAMEWORKS_AND_TOOLS = {
    "django",
    "flask",
    "fastapi",
    "react",
    "angular",
    "vue",
    "node.js",
    "express",
    "spring",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "git",
    "ci/cd",
}

# All technical skills (combined)
ALL_TECHNICAL_SKILLS = PROGRAMMING_LANGUAGES | FRAMEWORKS_AND_TOOLS

# Month patterns
MONTH_PATTERN: Pattern[str] = re.compile(
    r"\b(january|february|march|april|may|june|"
    r"july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b",
    re.IGNORECASE,
)

# Year pattern
YEAR_PATTERN: Pattern[str] = re.compile(r"\b(19|20)\d{2}\b")
