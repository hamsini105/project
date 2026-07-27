"""
ATS Analysis Examples

Demonstrates usage of the ATS analyzer with various scenarios.
"""

import json
from pathlib import Path

from parser import ResumeParser
from ats import ATSAnalyzer
from ats.logging_config import setup_logging


def example_basic_ats_analysis():
    """Example 1: Basic ATS analysis of a parsed resume."""
    print("\n" + "="*60)
    print("Example 1: Basic ATS Analysis")
    print("="*60)

    # Parse a resume
    parser = ResumeParser()
    resume_path = Path("sample_resume.pdf")

    if not resume_path.exists():
        print(f"Note: {resume_path} not found. Create a sample resume to test.")
        print("\nCode example:")
        print("""
    parser = ResumeParser()
    resume = parser.parse("resume.pdf")
    
    analyzer = ATSAnalyzer()
    report = analyzer.analyze(resume)
    
    print(f"ATS Score: {report.overall_score}/100")
    print(f"Rating: {report.score_rating}")
    print(f"Completeness: {report.completeness_percentage:.1f}%")
    print(f"Experience: {report.experience_years} years ({report.experience_level})")
        """)
        return

    try:
        resume = parser.parse(resume_path)
        analyzer = ATSAnalyzer()
        report = analyzer.analyze(resume)

        print(f"\n✓ Resume parsed and analyzed successfully")
        print(f"\nOverall ATS Score: {report.overall_score}/100 ({report.score_rating})")
        print(f"Completeness: {report.completeness_percentage:.1f}%")
        print(f"Experience: {report.experience_years} years ({report.experience_level})")

        print("\n--- Score Breakdown ---")
        breakdown = report.score_breakdown.model_dump()
        for category, score in breakdown.items():
            print(f"  {category.replace('_', ' ').title()}: {score:.1f}")

        print(f"\n--- Strengths ({len(report.strengths)}) ---")
        for strength in report.strengths[:3]:
            print(f"  • [{strength.impact}] {strength.description}")

        print(f"\n--- Weaknesses ({len(report.weaknesses)}) ---")
        for weakness in report.weaknesses[:3]:
            print(f"  • [{weakness.severity}] {weakness.description}")

        print(f"\n--- Top Recommendations ---")
        for rec in report.recommendations[:3]:
            print(f"  • [{rec.priority}] {rec.action}")
            if rec.estimated_score_improvement:
                print(f"    (Est. improvement: +{rec.estimated_score_improvement}%)")

    except Exception as e:
        print(f"Error: {e}")


def example_ats_json_output():
    """Example 2: Get ATS report as JSON."""
    print("\n" + "="*60)
    print("Example 2: ATS Report as JSON")
    print("="*60)

    print("""
Code example:

    analyzer = ATSAnalyzer()
    
    # Get JSON dictionary
    json_report = analyzer.analyze_and_return_json(resume)
    print(json.dumps(json_report, indent=2, default=str))
    
    # Or save to file
    analyzer.analyze_and_save_json(resume, "ats_report.json")
    """)


def example_score_components():
    """Example 3: Understand score components."""
    print("\n" + "="*60)
    print("Example 3: Understanding ATS Score Components")
    print("="*60)

    print("""
ATS Score Breakdown (Total 100 points):

1. Contact Details (10%) - Email, phone, name, location
2. Professional Summary (8%) - Objective or career summary
3. Skills (15%) - Relevant technical and soft skills
4. Education (12%) - Degrees, institutions, field of study
5. Work Experience (25%) - Job history and accomplishments ⭐ HIGHEST WEIGHT
6. Projects (10%) - Portfolio projects and contributions
7. Certifications (8%) - Professional credentials
8. Formatting (7%) - Clean, ATS-friendly layout
9. Keywords (5%) - Achievement words and metrics

Example Scores:
- 80-100: Excellent - Strong candidate profile
- 70-79: Good - Solid profile with minor improvements
- 60-69: Fair - Multiple areas for improvement
- 0-59: Poor - Significant gaps to address
    """)


def example_recommendations_system():
    """Example 4: Recommendations system."""
    print("\n" + "="*60)
    print("Example 4: Recommendations System")
    print("="*60)

    print("""
Recommendations are prioritized by impact:

Critical (⭐⭐⭐):
  - Must fix for good ATS score
  - Examples: Missing contact info, no experience

High (⭐⭐):
  - Strongly recommended
  - Examples: Add skills, quantify achievements

Medium (⭐):
  - Recommended for improvement
  - Examples: Add LinkedIn, fix gaps

Low:
  - Nice to have enhancements
  - Examples: Add certifications, more projects

Each recommendation includes:
  - Specific action to take
  - Why it matters
  - Estimated score improvement (e.g., +4%)
    """)


def example_integration():
    """Example 5: Integration with your application."""
    print("\n" + "="*60)
    print("Example 5: Application Integration")
    print("="*60)

    print("""
FastAPI Integration:

    from fastapi import FastAPI, UploadFile, File
    from parser import ResumeParser
    from ats import ATSAnalyzer
    import tempfile
    
    app = FastAPI()
    parser = ResumeParser()
    ats_analyzer = ATSAnalyzer()
    
    @app.post("/analyze-resume/")
    async def analyze_resume(file: UploadFile = File(...)):
        try:
            with tempfile.NamedTemporaryFile(suffix=file.filename) as tmp:
                tmp.write(await file.read())
                tmp.flush()
                
                # Parse resume
                resume = parser.parse(tmp.name)
                
                # Analyze with ATS
                report = ats_analyzer.analyze(resume)
                
                # Return JSON report
                return report.model_dump_clean()
        except Exception as e:
            return {"error": str(e)}, 400

    # Usage:
    # POST /analyze-resume/ with resume file
    # Response:
    # {
    #     "overall_score": 75,
    #     "score_rating": "Good",
    #     "completeness_percentage": 85,
    #     "strengths": [...],
    #     "weaknesses": [...],
    #     "recommendations": [...]
    # }
    """)


if __name__ == "__main__":
    print("ATS Analysis Engine - Examples")
    print("=" * 60)

    # Setup logging
    setup_logging()

    example_basic_ats_analysis()
    example_ats_json_output()
    example_score_components()
    example_recommendations_system()
    example_integration()

    print("\n" + "="*60)
    print("For more information, see ATS_README.md and ATS_ARCHITECTURE.md")
    print("="*60)
