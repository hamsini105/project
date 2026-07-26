"""
Example usage of the ResumeParser.

Demonstrates how to use the parser in your own applications.
"""

import json
from pathlib import Path

from parser import ResumeParser
from parser.logging_config import setup_logging

# Configure logging (optional - logs to console)
setup_logging()


def example_basic_parsing():
    """Example 1: Basic parsing and printing results."""
    print("\n" + "="*60)
    print("Example 1: Basic Resume Parsing")
    print("="*60)

    parser = ResumeParser()

    # Parse a resume file
    resume_path = Path("sample_resume.pdf")  # Replace with actual file

    if not resume_path.exists():
        print(f"Note: {resume_path} not found. Create a sample resume to test.")
        print("\nCode example:")
        print("""
    resume = parser.parse("resume.pdf")
    print(f"Name: {resume.contact.full_name}")
    print(f"Email: {resume.contact.email}")
    print(f"Skills: {resume.skills}")
    """)
        return

    resume = parser.parse(resume_path)

    print(f"\nName: {resume.contact.full_name}")
    print(f"Email: {resume.contact.email}")
    print(f"Phone: {resume.contact.phone}")
    print(f"Location: {resume.contact.location}")

    if resume.skills:
        print(f"\nSkills ({len(resume.skills)}):")
        for skill in resume.skills[:5]:  # Show first 5
            print(f"  - {skill}")

    if resume.education:
        print(f"\nEducation ({len(resume.education)}):")
        for edu in resume.education:
            print(f"  - {edu.degree or 'Degree'} in {edu.field_of_study or 'Unknown'}")
            print(f"    {edu.institution}")

    if resume.experience:
        print(f"\nExperience ({len(resume.experience)}):")
        for exp in resume.experience[:3]:  # Show first 3
            print(f"  - {exp.position} at {exp.company}")


def example_save_json():
    """Example 2: Parse and save as JSON."""
    print("\n" + "="*60)
    print("Example 2: Parse and Save as JSON")
    print("="*60)

    parser = ResumeParser()
    resume_path = Path("sample_resume.pdf")

    if not resume_path.exists():
        print(f"Note: {resume_path} not found.")
        print("\nCode example:")
        print("""
    parser.parse_and_save_json("resume.pdf", "output.json")
    print("Resume data saved to output.json")
    """)
        return

    output_path = Path("parsed_resume.json")
    parser.parse_and_save_json(resume_path, output_path)

    # Read and display
    with open(output_path, "r") as f:
        data = json.load(f)

    print(f"\nJSON saved to: {output_path}")
    print(f"JSON Structure:")
    print(f"  - contact")
    print(f"  - summary")
    print(f"  - skills")
    print(f"  - education")
    print(f"  - experience")
    print(f"  - projects")
    print(f"  - certifications")


def example_access_data_model():
    """Example 3: Access parsed data as Pydantic model."""
    print("\n" + "="*60)
    print("Example 3: Access Pydantic Model")
    print("="*60)

    parser = ResumeParser()

    print("""
Code example:

    resume = parser.parse("resume.pdf")
    
    # Access contact details
    contact = resume.contact
    print(f"Email: {contact.email}")
    print(f"LinkedIn: {contact.linkedin}")
    
    # Access education
    for edu in resume.education or []:
        print(f"{edu.degree} from {edu.institution}")
    
    # Access experience
    for exp in resume.experience or []:
        print(f"{exp.position} at {exp.company}")
        if exp.description:
            for desc in exp.description:
                print(f"  • {desc}")
    
    # Validate and get clean JSON (no None values)
    clean_data = resume.model_dump_clean()
    """)


def example_integration():
    """Example 4: Integration with your application."""
    print("\n" + "="*60)
    print("Example 4: Application Integration")
    print("="*60)

    print("""
Code example:

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
            
            resume = parser.parse(tmp.name)
            return resume.model_dump_clean()
    """)


if __name__ == "__main__":
    print("Resume Parser Examples")
    print("=" * 60)

    example_basic_parsing()
    example_save_json()
    example_access_data_model()
    example_integration()

    print("\n" + "="*60)
    print("For more information, see the parser module documentation.")
    print("="*60)
