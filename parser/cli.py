"""
Command-line interface for the resume parser.

Provides a CLI tool for parsing resume files and saving results as JSON.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from parser import ResumeParser
from parser.exceptions import ResumeParsingException
from parser.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Resume Parser - Extract data from PDF and DOCX resumes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m parser.cli input.pdf
  python -m parser.cli input.pdf -o output.json
  python -m parser.cli input.docx --log-level DEBUG
        """,
    )

    parser.add_argument("input", help="Path to resume file (PDF or DOCX)")
    parser.add_argument(
        "-o",
        "--output",
        help="Output JSON file path (optional, prints to stdout if not provided)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--log-file",
        help="Log file path (optional)",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(level=log_level, log_file=args.log_file)

    try:
        input_path = Path(args.input)

        if not input_path.exists():
            logger.error(f"File not found: {input_path}")
            return 1

        logger.info(f"Parsing resume: {input_path}")

        # Parse resume
        resume_parser = ResumeParser()
        resume = resume_parser.parse(input_path)

        # Get output data
        output_data = resume.model_dump_clean()

        # Save or print
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, default=str)

            logger.info(f"Resume data saved to: {output_path}")
            print(f"✓ Resume successfully parsed and saved to {output_path}")
        else:
            # Print to stdout
            print(json.dumps(output_data, indent=2, default=str))

        return 0

    except ResumeParsingException as e:
        logger.error(f"Parsing failed: {e}")
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
