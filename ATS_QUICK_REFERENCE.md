# ATS Analysis Module - Quick Reference Guide

## Import Everything

```python
from ats import (
    ATSAnalyzer,
    ATSReport,
    Strength,
    Weakness,
    Recommendation,
    ATSException,
)
```

## Analyze a Resume (3 Lines)

```python
analyzer = ATSAnalyzer()
report = analyzer.analyze(resume)
print(f"ATS Score: {report.overall_score}/100 ({report.score_rating})")
```

## Get JSON Output

```python
# As Python dict
json_data = analyzer.analyze_and_return_json(resume)

# Save to file
analyzer.analyze_and_save_json(resume, "report.json")

# Access specific fields
print(json_data["overall_score"])
print(json_data["strengths"])
```

## Score Breakdown

```python
report = analyzer.analyze(resume)

# All categories
breakdown = report.score_breakdown.model_dump()
for category, score in breakdown.items():
    print(f"{category}: {score}")
```

## Strengths & Weaknesses

```python
# Strengths
for strength in report.strengths:
    print(f"[{strength.impact}] {strength.description}")

# Weaknesses
for weakness in report.weaknesses:
    print(f"[{weakness.severity}] {weakness.description}")
```

## Recommendations

```python
# All recommendations
for rec in report.recommendations:
    print(f"[{rec.priority}] {rec.action}")
    print(f"  Why: {rec.reason}")
    print(f"  Est. improvement: +{rec.estimated_score_improvement}%")

# Filter by priority
critical = [r for r in report.recommendations if r.priority == "Critical"]
```

## Experience Info

```python
print(f"Years: {report.experience_years}")
print(f"Level: {report.experience_level}")
print(f"Completeness: {report.completeness_percentage:.1f}%")
```

## Common Checks

```python
# Score rating
if report.overall_score >= 80:
    print("Excellent profile!")
elif report.overall_score >= 70:
    print("Good profile")
else:
    print("Needs improvement")

# Missing sections
if report.missing_sections:
    print(f"Add: {', '.join(report.missing_sections)}")

# Experience level
if report.experience_level in ["Junior", "Entry"]:
    print("Entry-level candidate")
```

## Validation

```python
from ats.validators import ResumeValidator

validator = ResumeValidator(resume)

try:
    if validator.validate():
        print("Resume is valid")
except ValidationException as e:
    print(f"Invalid: {e}")
```

## Configuration

```python
from ats.config import SCORING_WEIGHTS, SCORE_RANGES

# View weights
print(SCORING_WEIGHTS)

# Modify for your use case
my_weights = {
    "skills": 20,          # Increase
    "contact_details": 5,  # Decrease
    # ... other categories
}
```

## Logging

```python
from ats.logging_config import setup_logging
import logging

# Enable debug logging
setup_logging(level=logging.DEBUG, log_file="ats.log")

# Analyze (logs will be written)
report = analyzer.analyze(resume)
```

## Error Handling

```python
from ats.exceptions import ValidationException, ScoringException

try:
    report = analyzer.analyze(resume)
except ValidationException:
    print("Resume validation failed")
except ScoringException:
    print("Scoring calculation failed")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Batch Processing

```python
from parser import ResumeParser
from ats import ATSAnalyzer
import json

parser = ResumeParser()
analyzer = ATSAnalyzer()

resumes = ["resume1.pdf", "resume2.pdf", "resume3.pdf"]
reports = []

for file in resumes:
    try:
        resume = parser.parse(file)
        report = analyzer.analyze(resume)
        reports.append(report.model_dump_clean())
    except Exception as e:
        print(f"Error processing {file}: {e}")

# Save batch results
with open("batch_results.json", "w") as f:
    json.dump(reports, f, indent=2, default=str)
```

## FastAPI Integration

```python
from fastapi import FastAPI, UploadFile, File
from parser import ResumeParser
from ats import ATSAnalyzer
import tempfile

app = FastAPI()
parser = ResumeParser()
ats = ATSAnalyzer()

@app.post("/analyze-resume")
async def analyze(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(await file.read())
        tmp.flush()
        
        resume = parser.parse(tmp.name)
        report = ats.analyze(resume)
        
        return report.model_dump_clean()
```

## Score Interpretation

| Score | Rating | Meaning |
|-------|--------|---------|
| 90-100 | Excellent | Strong candidate, ready to submit |
| 80-89 | Excellent | Very good, minor improvements possible |
| 70-79 | Good | Solid profile, some improvements needed |
| 60-69 | Fair | Multiple areas for improvement |
| <60 | Poor | Significant gaps, major revisions needed |

## Category Weights (Default)

| Category | Weight | Notes |
|----------|--------|-------|
| Contact Details | 10% | Required fields |
| Professional Summary | 8% | Career objective |
| Skills | 15% | Technical skills |
| Education | 12% | Degrees |
| **Experience** | **25%** | **Most important** |
| Projects | 10% | Portfolio |
| Certifications | 8% | Credentials |
| Formatting | 7% | Document quality |
| Keywords | 5% | Metrics/numbers |

## Experience Levels

| Level | Years | Description |
|-------|-------|-------------|
| Entry | 0-2 | Fresh graduate or new field |
| Junior | 2-5 | Early career |
| Mid | 5-10 | Experienced contributor |
| Senior | 10-15 | Leadership experience |
| Lead | 15-20 | Strategic leadership |
| Executive | 20+ | C-suite/Director level |

## Common Recommendations

### Critical (Must Fix)
- Missing contact information
- No work experience
- Typos/formatting issues
- Incomplete contact details

### High (Strongly Recommended)
- Add professional summary
- Expand work experience details
- Include relevant skills
- Quantify achievements

### Medium (Recommended)
- Add projects/portfolio
- Include certifications
- Add metrics/numbers
- Improve formatting

### Low (Nice to Have)
- Add LinkedIn URL
- Expand certifications
- Add cover letter tips
- Style improvements

## Debug Info

```python
# Check what's missing
print("Missing sections:", report.missing_sections)

# View all strengths
print(f"Strengths: {len(report.strengths)}")
for s in report.strengths:
    print(f"  • {s.description} ({s.impact})")

# View all weaknesses
print(f"Weaknesses: {len(report.weaknesses)}")
for w in report.weaknesses:
    print(f"  • {w.description} ({w.severity})")

# Recommendations count
print(f"Recommendations: {len(report.recommendations)}")
```

## Performance Tips

1. **Cache results**: Store analysis results for frequently analyzed resumes
2. **Batch processing**: Process multiple resumes together
3. **Async operations**: Use async/await for API integration
4. **Streaming**: For large batch jobs, process one at a time

## Common Issues

### ValidationException
- Solution: Check that resume has contact details (name, email required)

### ScoringException
- Solution: Check resume data format, ensure dates are valid

### Low Score
- Solution: Check recommendations - they provide specific fixes

### Missing Recommendations
- Solution: Recommendations are based on actual issues - if few, resume is good!

## Debug Mode

```python
import logging
from ats.logging_config import setup_logging

# Enable all debug logging
setup_logging(level=logging.DEBUG)

# Now analysis will log detailed information
analyzer = ATSAnalyzer()
report = analyzer.analyze(resume)
```

---

For full documentation, see [ATS_README.md](ATS_README.md)  
For architecture details, see [ATS_ARCHITECTURE.md](ATS_ARCHITECTURE.md)
