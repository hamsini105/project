"""
Experience calculation and analysis for ATS.

Calculates total years of experience and experience level categorization.
"""

import logging
from datetime import date, datetime

from parser.models import Resume

from ats.config import EXPERIENCE_RANGES

logger = logging.getLogger(__name__)


class ExperienceCalculator:
    """Calculates experience metrics from resume data."""

    def __init__(self, resume: Resume) -> None:
        """
        Initialize calculator with resume data.

        Args:
            resume: Resume object to analyze.
        """
        self.resume = resume

    def calculate_total_experience(self) -> float:
        """
        Calculate total years of work experience.

        Returns:
            Total years of experience (fractional).
        """
        if not self.resume.experience or len(self.resume.experience) == 0:
            logger.debug("No experience data found")
            return 0.0

        total_years = 0.0
        today = date.today()

        for exp in self.resume.experience:
            if not exp.start_date:
                continue

            # Determine end date
            if exp.is_current or exp.end_date is None:
                end_date = today
            else:
                end_date = exp.end_date

            # Calculate duration
            days_worked = (end_date - exp.start_date).days
            years = days_worked / 365.25

            total_years += years
            logger.debug(
                f"Experience: {exp.company} - {exp.position} ({years:.2f} years)"
            )

        # Round to 1 decimal place
        total_years = round(total_years, 1)
        logger.debug(f"Total experience: {total_years} years")
        return total_years

    def get_experience_level(self, years: float) -> str:
        """
        Determine experience level based on years.

        Args:
            years: Years of experience.

        Returns:
            Experience level category (Entry, Junior, Mid, Senior, Lead, Executive).
        """
        for level, (min_years, max_years) in EXPERIENCE_RANGES.items():
            if min_years <= years < max_years:
                level_display = level.replace("_", " ").title()
                logger.debug(f"Experience level for {years} years: {level_display}")
                return level_display

        # Default to Executive for 20+ years
        logger.debug(f"Experience level for {years} years: Executive")
        return "Executive"

    def get_recency_score(self) -> float:
        """
        Score based on recency of recent experience (0-100).

        Returns:
            Recency score.
        """
        if not self.resume.experience or len(self.resume.experience) == 0:
            return 0.0

        # Find most recent role
        today = date.today()
        most_recent = None
        max_end_date = None

        for exp in self.resume.experience:
            if exp.is_current:
                # Current role gets maximum score
                logger.debug("Currently employed - maximum recency score")
                return 100.0

            if exp.end_date:
                if max_end_date is None or exp.end_date > max_end_date:
                    max_end_date = exp.end_date
                    most_recent = exp

        if most_recent and most_recent.end_date:
            months_ago = (today - most_recent.end_date).days / 30.44
            logger.debug(f"Most recent experience ended {months_ago:.1f} months ago")

            # Score decreases with time: 100% if <6 months, 0% if >5 years
            if months_ago < 6:
                return 100.0
            elif months_ago > 60:  # 5 years
                return 0.0
            else:
                # Linear decay from 100 to 0 over 5 years
                score = max(0, 100 - (months_ago / 60) * 100)
                logger.debug(f"Recency score: {score:.1f}%")
                return score

        return 50.0  # Default if no end dates found

    def get_role_diversity(self) -> float:
        """
        Calculate diversity of roles held (0-100).

        Returns:
            Role diversity score based on number of different positions.
        """
        if not self.resume.experience or len(self.resume.experience) == 0:
            return 0.0

        # Get unique positions (lower case for comparison)
        unique_positions = set()
        for exp in self.resume.experience:
            if exp.position:
                unique_positions.add(exp.position.lower())

        role_count = len(unique_positions)
        # 5+ unique roles = 100%, 1 role = 20%
        diversity_score = min(100, (role_count / 5) * 100)
        logger.debug(f"Role diversity: {role_count} unique roles, score: {diversity_score:.1f}%")
        return diversity_score

    def get_company_diversity(self) -> float:
        """
        Calculate diversity of companies worked for (0-100).

        Returns:
            Company diversity score based on number of different employers.
        """
        if not self.resume.experience or len(self.resume.experience) == 0:
            return 0.0

        # Get unique companies
        unique_companies = set()
        for exp in self.resume.experience:
            if exp.company:
                unique_companies.add(exp.company.lower())

        company_count = len(unique_companies)
        # 4+ companies = 100%, 1 company = 25%
        diversity_score = min(100, (company_count / 4) * 100)
        logger.debug(
            f"Company diversity: {company_count} unique companies, score: {diversity_score:.1f}%"
        )
        return diversity_score

    def has_employment_gaps(self) -> bool:
        """
        Check if resume has significant employment gaps (>6 months).

        Returns:
            True if gaps found, False otherwise.
        """
        if not self.resume.experience or len(self.resume.experience) < 2:
            return False

        # Sort by end date
        sorted_exp = sorted(
            self.resume.experience,
            key=lambda x: x.end_date or date.today(),
            reverse=True,
        )

        for i in range(len(sorted_exp) - 1):
            current = sorted_exp[i]
            next_exp = sorted_exp[i + 1]

            if current.start_date and next_exp.end_date:
                gap_days = (current.start_date - next_exp.end_date).days
                if gap_days > 180:  # 6 months
                    logger.debug(f"Employment gap detected: {gap_days} days")
                    return True

        logger.debug("No significant employment gaps found")
        return False

    def get_employment_stability(self) -> float:
        """
        Calculate employment stability score (0-100).

        Based on average tenure at each position.

        Returns:
            Stability score.
        """
        if not self.resume.experience or len(self.resume.experience) == 0:
            return 50.0  # Default unknown

        tenures = []
        today = date.today()

        for exp in self.resume.experience:
            if not exp.start_date:
                continue

            if exp.is_current or exp.end_date is None:
                end_date = today
            else:
                end_date = exp.end_date

            days = (end_date - exp.start_date).days
            years = days / 365.25
            tenures.append(years)

        if not tenures:
            return 50.0

        avg_tenure = sum(tenures) / len(tenures)
        # 3+ years average = 100%, <1 year = 0%
        stability = min(100, max(0, (avg_tenure / 3) * 100))
        logger.debug(f"Employment stability: {stability:.1f}%")
        return stability
