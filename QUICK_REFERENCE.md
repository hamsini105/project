# Resume Parser - Quick Reference Guide

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Basic Parsing (3 lines of code)
```python
from parser import ResumeParser

parser = ResumeParser()
resume = parser.parse("resume.pdf")
print(resume.contact.full_name)
```

### 2. Get JSON Output
```python
# As dictionary
json_data = parser.parse_and_return_json("resume.pdf")

# Save to file
parser.parse_and_save_json("resume.pdf", "output.json")
```

### 3. Command Line
```bash
python -m parser.cli resume.pdf -o output.json
```

## Common Tasks

### Access Extracted Data
```python
resume = parser.parse("resume.pdf")

# Contact information
print(resume.contact.full_name)
print(resume.contact.email)
print(resume.contact.phone)
print(resume.contact.location)
print(resume.contact.linkedin)
print(resume.contact.github)

# Skills
for skill in resume.skills or []:
    print(f"- {skill}")

# Education
for edu in resume.education or []:
    print(f"{edu.degree} from {edu.institution}")
    print(f"  Field: {edu.field_of_study}")
    print(f"  Dates: {edu.start_date} to {edu.end_date}")

# Experience
for exp in resume.experience or []:
    print(f"{exp.position} at {exp.company}")
    print(f"  {exp.start_date} to {exp.end_date}")
    if exp.description:
        for desc in exp.description:
            print(f"    • {desc}")

# Projects
for proj in resume.projects or []:
    print(f"Project: {proj.title}")
    print(f"  Technologies: {', '.join(proj.technologies or [])}")

# Certifications
for cert in resume.certifications or []:
    print(f"Certification: {cert.title}")
    print(f"  Issuer: {cert.issuer}")
    print(f"  Issue Date: {cert.issue_date}")
```

### Handle Errors
```python
from parser import ResumeParser
from parser.exceptions import ResumeParsingException

parser = ResumeParser()

try:
    resume = parser.parse("resume.pdf")
except ResumeParsingException as e:
    print(f"Parsing failed: {e}")
```

### Configure Logging
```python
from parser.logging_config import setup_logging
import logging

setup_logging(
    level=logging.DEBUG,
    log_file="parser.log"
)

resume = parser.parse("resume.pdf")  # Will log details
```

### Use in FastAPI
```python
from fastapi import FastAPI, UploadFile
from parser import ResumeParser
import tempfile

app = FastAPI()
parser = ResumeParser()

@app.post("/parse-resume/")
async def parse_resume(file: UploadFile):
    with tempfile.NamedTemporaryFile(suffix=file.filename) as tmp:
        tmp.write(await file.read())
        tmp.flush()
        
        try:
            resume = parser.parse(tmp.name)
            return resume.model_dump_clean()
        except Exception as e:
            return {"error": str(e)}
```

### Use in Flask
```python
from flask import Flask, request, jsonify
from parser import ResumeParser
import tempfile

app = Flask(__name__)
parser = ResumeParser()

@app.route("/parse", methods=["POST"])
def parse_resume():
    file = request.files["file"]
    
    with tempfile.NamedTemporaryFile(suffix=file.filename) as tmp:
        file.save(tmp.name)
        
        try:
            resume = parser.parse(tmp.name)
            return jsonify(resume.model_dump_clean())
        except Exception as e:
            return jsonify({"error": str(e)}), 400
```

### Batch Processing
```python
from pathlib import Path
from parser import ResumeParser

parser = ResumeParser()
resume_dir = Path("resumes/")

results = []
for resume_file in resume_dir.glob("*.pdf"):
    try:
        resume = parser.parse(resume_file)
        results.append({
            "file": resume_file.name,
            "name": resume.contact.full_name,
            "email": resume.contact.email,
        })
    except Exception as e:
        print(f"Failed to parse {resume_file}: {e}")

for result in results:
    print(f"{result['name']} - {result['email']}")
```

## Data Types

### Resume Object
```python
class Resume:
    contact: ContactDetails
    summary: Optional[str]
    skills: Optional[List[str]]
    education: Optional[List[EducationEntry]]
    experience: Optional[List[ExperienceEntry]]
    projects: Optional[List[ProjectEntry]]
    certifications: Optional[List[CertificationEntry]]
    languages: Optional[List[str]]
```

### ContactDetails
```python
class ContactDetails:
    full_name: str
    email: Optional[EmailStr]
    phone: Optional[str]
    location: Optional[str]
    linkedin: Optional[HttpUrl]
    github: Optional[HttpUrl]
    website: Optional[HttpUrl]
```

### EducationEntry
```python
class EducationEntry:
    institution: str
    degree: Optional[str]
    field_of_study: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    grade: Optional[str]
    details: Optional[List[str]]
```

### ExperienceEntry
```python
class ExperienceEntry:
    company: str
    position: str
    start_date: Optional[date]
    end_date: Optional[date]
    is_current: Optional[bool]
    description: Optional[List[str]]
    location: Optional[str]
```

### ProjectEntry
```python
class ProjectEntry:
    title: str
    description: Optional[str]
    technologies: Optional[List[str]]
    link: Optional[HttpUrl]
    start_date: Optional[date]
    end_date: Optional[date]
```

### CertificationEntry
```python
class CertificationEntry:
    title: str
    issuer: Optional[str]
    issue_date: Optional[date]
    expiry_date: Optional[date]
    credential_id: Optional[str]
    credential_url: Optional[HttpUrl]
```

## Exceptions

```python
from parser.exceptions import (
    ResumeParsingException,      # Base exception
    FileValidationException,      # File issues
    FileReadException,            # Read errors
    PreprocessingException,       # Text processing errors
    ExtractionException,          # Extraction errors
    InvalidResumeDataException,   # Validation errors
)
```

## Customization

### Create Custom Extractor
```python
from parser.extractors.base import BaseExtractor

class CustomExtractor(BaseExtractor):
    def extract(self, text: str):
        # Your extraction logic
        return extracted_data
```

### Modify Extraction Keywords
Edit `parser/config.py`:
```python
EDUCATION_KEYWORDS = {"education", "academic", "degree", ...}
EXPERIENCE_KEYWORDS = {"work", "employment", "career", ...}
SKILLS_KEYWORDS = {"skills", "technical", ...}
```

### Use Custom Parser
```python
class MyParser(ResumeParser):
    def parse(self, file_path):
        # Custom parsing logic
        return super().parse(file_path)
```

## CLI Usage

```bash
# Parse and print JSON
python -m parser.cli resume.pdf

# Parse and save to file
python -m parser.cli resume.pdf -o output.json

# Debug with verbose logging
python -m parser.cli resume.pdf -o output.json --log-level DEBUG

# Save logs to file
python -m parser.cli resume.pdf --log-file parser.log
```

## Testing

```bash
# Run all tests
python tests.py

# Run specific test class
python -m pytest tests.py::TestContactExtractor -v

# Run with coverage
pytest tests.py --cov=parser --cov-report=html
```

## Performance Tips

1. **Batch Processing**: Process multiple files sequentially
2. **Reuse Parser**: Create one ResumeParser instance, reuse it
3. **Check File Size**: Validate file size before parsing
4. **Error Handling**: Use try-except to handle failures gracefully
5. **Logging**: Use appropriate log levels (INFO for production)

## Supported File Formats

- ✅ PDF (via PyMuPDF) - text-based PDFs
- ✅ DOCX (via python-docx)
- ❌ DOC (legacy Word format)
- ❌ Scanned PDFs (requires OCR)
- ❌ Images
- ❌ RTF, ODP, etc.

## Limits

- Maximum file size: 10MB (configurable)
- Maximum contact.summary length: 1000 chars
- Maximum additional_info length: 1000 chars

## Getting Help

1. Check docstrings in source code
2. Review `PARSER_README.md` for comprehensive docs
3. See `IMPLEMENTATION_SUMMARY.md` for architecture
4. Run `examples.py` for usage examples
5. Check `tests.py` for test patterns

## File Structure

```
parser/
├── Core modules
│   ├── __init__.py
│   ├── parser.py         # Main class
│   ├── models.py         # Data models
│   ├── config.py         # Configuration
│   ├── exceptions.py     # Exceptions
│   ├── logging_config.py # Logging
│   ├── utils.py          # Utilities
│   └── cli.py            # Command-line
├── readers/              # File readers
├── preprocessors/        # Text preprocessing
└── extractors/           # Data extractors
```

---

For more details, see `PARSER_README.md` and `IMPLEMENTATION_SUMMARY.md`.
