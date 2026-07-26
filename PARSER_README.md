# Resume Parser System - Production-Grade Implementation

A modular, type-safe, production-ready resume parsing engine supporting PDF and DOCX formats with standardized JSON output.

## Features

- **Multi-format Support**: Parse PDF (via PyMuPDF) and DOCX resume files
- **Modular Architecture**: Separate readers, preprocessors, and extractors for clean separation of concerns
- **Comprehensive Extraction**: Contact details, skills, education, experience, projects, certifications
- **Type Safety**: Full type hints and Pydantic data models for validation
- **Production Ready**: Comprehensive error handling, logging, and structured code
- **Extensible**: Easy to add new extractors or customize existing ones
- **Clean JSON Output**: Standardized, schema-validated resume data

## Architecture

### Directory Structure

```
parser/
├── __init__.py                 # Main module exports
├── config.py                   # Configuration and constants
├── exceptions.py               # Custom exception classes
├── models.py                   # Pydantic data models
├── parser.py                   # Main parser orchestrator
├── logging_config.py           # Logging setup
├── cli.py                      # Command-line interface
├── readers/
│   ├── __init__.py            # Reader factory and base class
│   ├── pdf.py                 # PDF reader (PyMuPDF)
│   └── docx.py                # DOCX reader (python-docx)
├── preprocessors/
│   └── __init__.py            # Text preprocessing module
└── extractors/
    ├── __init__.py            # Extractor exports
    ├── base.py                # Base extractor class
    ├── contact.py             # Contact details extractor
    ├── skills.py              # Skills extractor
    ├── education.py           # Education extractor
    ├── experience.py          # Experience extractor
    ├── projects.py            # Projects extractor
    └── certifications.py      # Certifications extractor
```

### Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **DRY**: No code duplication; shared utilities in base classes
3. **Extensibility**: Add new extractors by inheriting from `BaseExtractor`
4. **Type Safety**: Full type hints throughout the codebase
5. **Error Handling**: Custom exceptions and graceful degradation
6. **Logging**: Comprehensive logging at module level

## Installation

```bash
pip install -r requirements.txt
```

### Dependencies

- `PyMuPDF>=1.23.8` - PDF parsing
- `python-docx>=0.8.11` - DOCX parsing
- `pydantic>=2.0.0` - Data validation and serialization
- `streamlit>=1.40.0` - Web UI (optional)

## Usage

### Basic Usage

```python
from parser import ResumeParser

# Initialize parser
parser = ResumeParser()

# Parse a resume
resume = parser.parse("resume.pdf")

# Access extracted data
print(f"Name: {resume.contact.full_name}")
print(f"Email: {resume.contact.email}")
print(f"Skills: {resume.skills}")

# Get clean JSON (excludes None values)
json_data = resume.model_dump_clean()
```

### Save to JSON File

```python
# Parse and save as JSON
parser.parse_and_save_json("resume.pdf", "output.json")

# Or get JSON dict
json_data = parser.parse_and_return_json("resume.pdf")
```

### Command-Line Interface

```bash
# Parse and print to stdout
python -m parser.cli resume.pdf

# Parse and save to file
python -m parser.cli resume.pdf -o output.json

# With debug logging
python -m parser.cli resume.pdf -o output.json --log-level DEBUG

# Save logs to file
python -m parser.cli resume.pdf --log-file parser.log
```

## Data Models

### Resume Structure

```json
{
  "contact": {
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "location": "San Francisco, CA",
    "linkedin": "https://linkedin.com/in/johndoe",
    "github": "https://github.com/johndoe",
    "website": "https://johndoe.dev"
  },
  "summary": "Brief professional summary...",
  "skills": ["Python", "Django", "PostgreSQL", "React"],
  "education": [
    {
      "institution": "MIT",
      "degree": "Bachelor of Science",
      "field_of_study": "Computer Science",
      "start_date": "2015-01-01",
      "end_date": "2019-12-31",
      "grade": "3.8",
      "details": ["Relevant coursework", "Honors"]
    }
  ],
  "experience": [
    {
      "company": "Tech Corp",
      "position": "Senior Software Engineer",
      "location": "San Francisco, CA",
      "start_date": "2020-01-01",
      "end_date": null,
      "is_current": true,
      "description": ["Responsibility 1", "Achievement 2"]
    }
  ],
  "projects": [
    {
      "title": "Project Name",
      "description": "Project description",
      "technologies": ["Python", "Django"],
      "link": "https://github.com/johndoe/project",
      "start_date": "2022-01-01",
      "end_date": "2022-12-31"
    }
  ],
  "certifications": [
    {
      "title": "AWS Solutions Architect",
      "issuer": "Amazon",
      "issue_date": "2021-06-01",
      "expiry_date": "2024-06-01",
      "credential_id": "CERT123",
      "credential_url": "https://aws.amazon.com/verify"
    }
  ]
}
```

## Extractors

Each extractor is a specialized class inheriting from `BaseExtractor`:

### ContactExtractor
Extracts name, email, phone, location, and social media profiles.

### SkillsExtractor
Identifies technical skills (programming languages, frameworks, tools) and soft skills using keyword matching.

### EducationExtractor
Extracts degree, institution, field of study, dates, and GPA.

### ExperienceExtractor
Parses company, position, dates, location, and job responsibilities.

### ProjectsExtractor
Extracts project titles, descriptions, technologies, and links.

### CertificationsExtractor
Identifies certifications, issuers, dates, and credential details.

## Extending the Parser

### Adding a New Extractor

```python
from parser.extractors.base import BaseExtractor
from parser.models import YourDataModel

class CustomExtractor(BaseExtractor):
    """Extract custom data from resume text."""
    
    def extract(self, text: str) -> YourDataModel:
        """
        Extract custom data.
        
        Args:
            text: Resume text to extract from.
            
        Returns:
            Extracted data object.
        """
        # Implementation here
        pass
```

### Customizing Extraction Logic

You can subclass and override the main parser:

```python
from parser import ResumeParser

class CustomResumeParser(ResumeParser):
    """Custom parser with modified extraction logic."""
    
    def __init__(self):
        super().__init__()
        # Add custom extractors or modify existing ones
```

## Error Handling

The parser uses custom exceptions for different failure scenarios:

```python
from parser.exceptions import (
    ResumeParsingException,
    FileReadException,
    FileValidationException,
    ExtractionException,
    PreprocessingException,
)

try:
    resume = parser.parse("resume.pdf")
except FileValidationException:
    # Handle file validation errors
    pass
except ExtractionException:
    # Handle extraction errors
    pass
except ResumeParsingException:
    # Handle other parsing errors
    pass
```

## Logging

Logging is configured automatically on import. Customize it as needed:

```python
from parser.logging_config import setup_logging

# Setup with custom level and file
setup_logging(
    level=logging.DEBUG,
    log_file="parser.log",
    use_color=True
)
```

## Testing

Run the included test suite:

```bash
python tests.py
```

Or use pytest:

```bash
pip install pytest
pytest tests.py -v
```

## Examples

See `examples.py` for comprehensive usage examples:

```bash
python examples.py
```

## Performance Considerations

- **Large Files**: Parser handles up to 10MB resume files (configurable in `config.py`)
- **Text Extraction**: PDF text extraction varies based on PDF structure; OCR is not implemented
- **Memory**: Entire file is loaded into memory during processing
- **Processing Time**: Typically <1 second for standard resumes

## Limitations and Future Improvements

- OCR support for scanned PDFs (future enhancement)
- Support for additional languages
- Machine learning-based field extraction
- Confidence scores for extracted data
- Batch processing of multiple resumes

## Code Quality

- **Type Hints**: 100% type coverage
- **Docstrings**: Comprehensive module, class, and function documentation
- **Error Handling**: Graceful error handling with informative messages
- **Logging**: Production-grade logging throughout
- **Testing**: Unit tests for all major components

## License

This implementation is part of the Resume Parser System.

## Contributing

To add new features:

1. Create a new extractor in `parser/extractors/`
2. Add corresponding data model in `parser/models.py`
3. Update `ResumeParser.parse()` method
4. Add tests in `tests.py`
5. Update documentation

## Support

For issues or questions, refer to the docstrings in the source code or examine the test cases for usage patterns.
