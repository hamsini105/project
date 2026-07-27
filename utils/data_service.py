"""
Candidate data service.

Provides a thin data-access layer over the candidate DataFrame.
Mock data is generated deterministically and cached for the session lifetime.

In a production deployment, replace _build_mock_dataframe() with real
database calls — the service interface stays the same.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from utils.logger import get_logger

logger = get_logger(__name__)

# ── Mock data constants ───────────────────────────────────────────────────────

_FIRST_NAMES = [
    "Alice", "Bob", "Carol", "David", "Elena", "Frank", "Grace", "Henry",
    "Isabel", "James", "Karen", "Liam", "Maya", "Noah", "Olivia", "Peter",
    "Quinn", "Rachel", "Samuel", "Tara", "Uma", "Victor", "Wendy", "Xavier",
    "Yara", "Zoe", "Aaron", "Bella", "Carlos", "Diana", "Ethan", "Fiona",
    "George", "Hannah", "Ivan", "Julia", "Kevin", "Laura", "Marcus", "Nina",
    "Oscar", "Paula", "Ryan", "Sara", "Tom", "Ursula", "Vince", "Willa",
]

_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Martinez",
    "Anderson", "Taylor", "Thomas", "Hernandez", "Moore", "Martin", "Jackson",
    "Thompson", "White", "Lopez", "Lee", "Gonzalez", "Harris", "Clark",
    "Lewis", "Robinson", "Walker", "Perez", "Hall", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Adams", "Nelson", "Hill", "Ramirez", "Patel",
    "Kim", "Chen", "Singh", "Kumar", "Wang", "Li", "Zhang", "Liu", "Ahmed",
]

_ROLES = [
    "Senior Python Engineer",
    "Machine Learning Engineer",
    "Data Scientist",
    "Frontend Engineer",
    "DevOps / Platform Engineer",
    "Backend Engineer",
    "Data Analyst",
    "Product Manager",
]

_STATUSES = [
    "Screening",
    "Phone Screen",
    "Technical Round",
    "Final Round",
    "Hired",
    "Rejected",
]

_LOCATIONS = [
    "San Francisco, CA",
    "New York, NY",
    "Austin, TX",
    "Seattle, WA",
    "Chicago, IL",
    "Boston, MA",
    "Remote",
    "Denver, CO",
]

_EDUCATION_LEVELS = ["Bachelor", "Master", "PhD"]

_SKILLS_POOL = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "Scala",
    "React", "Vue", "Angular", "Node.js", "Django", "FastAPI", "Flask",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "Docker", "Kubernetes", "Terraform", "AWS", "GCP", "Azure",
    "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "scikit-learn",
    "Pandas", "Spark", "Kafka", "Airflow", "dbt",
    "CI/CD", "Git", "Linux", "REST API", "GraphQL",
]

_STATUS_WEIGHTS = [0.25, 0.20, 0.18, 0.12, 0.10, 0.15]  # must sum to 1.0

_EDUCATION_WEIGHTS = [0.55, 0.35, 0.10]


# ── Data generation ────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _build_mock_dataframe() -> pd.DataFrame:
    """
    Generate a deterministic mock candidate DataFrame.

    Cached for the full Streamlit session.  The Random seed ensures
    repeated runs produce identical data, avoiding confusing layout shifts.
    """
    rng = random.Random(42)
    today = date.today()
    records: List[Dict[str, Any]] = []

    for i in range(150):
        name = f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}"
        first, last = name.split(" ", 1)
        email = f"{first.lower()}.{last.lower().replace(' ', '')}{rng.randint(1, 99)}@example.com"

        role = rng.choices(_ROLES, weights=[0.18, 0.15, 0.14, 0.13, 0.10, 0.12, 0.10, 0.08])[0]
        status = rng.choices(_STATUSES, weights=_STATUS_WEIGHTS)[0]
        education = rng.choices(_EDUCATION_LEVELS, weights=_EDUCATION_WEIGHTS)[0]
        location = rng.choice(_LOCATIONS)

        experience_years = round(rng.uniform(0.5, 15.0), 1)
        ats_score = round(
            min(98, max(30, rng.gauss(67, 15))), 1
        )

        num_skills = rng.randint(3, 10)
        skills = rng.sample(_SKILLS_POOL, num_skills)

        days_ago = rng.randint(1, 180)
        applied_date = today - timedelta(days=days_ago)

        records.append({
            "id":               str(i + 1).zfill(4),
            "name":             name,
            "email":            email,
            "role":             role,
            "status":           status,
            "ats_score":        ats_score,
            "experience_years": experience_years,
            "education":        education,
            "location":         location,
            "skills":           skills,
            "applied_date":     applied_date,
            "phone":            f"+1-{rng.randint(200,999)}-{rng.randint(100,999)}-{rng.randint(1000,9999)}",
            "linkedin":         f"https://linkedin.com/in/{first.lower()}-{last.lower().replace(' ','-')}-{rng.randint(10,99)}",
            "notes":            "",
        })

    df = pd.DataFrame(records)
    df["applied_date"] = pd.to_datetime(df["applied_date"])
    logger.debug("Built mock candidate DataFrame: %d rows", len(df))
    return df


# ── Service class ──────────────────────────────────────────────────────────────

class CandidateService:
    """
    Read-focused data access layer over the candidate dataset.

    All mutation methods update a copy stored in ``st.session_state``
    so changes persist within a single browser session without affecting
    the cached baseline data.
    """

    _SESSION_KEY = "candidate_overrides"

    # ── Retrieval ──────────────────────────────────────────────────────────────

    def get_all(self) -> pd.DataFrame:
        """Return all candidates with any session-level overrides applied."""
        base = _build_mock_dataframe().copy()
        overrides: Dict[str, Dict] = st.session_state.get(self._SESSION_KEY, {})
        if overrides:
            for cid, fields in overrides.items():
                mask = base["id"] == cid
                for col, val in fields.items():
                    base.loc[mask, col] = val
        return base

    def get_by_id(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Return a single candidate as a dict, or None if not found."""
        df = self.get_all()
        row = df[df["id"] == candidate_id]
        if row.empty:
            return None
        record = row.iloc[0].to_dict()
        # Convert skills back to list if it was stored as a string
        if isinstance(record.get("skills"), str):
            record["skills"] = [s.strip() for s in record["skills"].split(",")]
        return record

    # ── Search & filter ────────────────────────────────────────────────────────

    @staticmethod
    def search(query: str, df: pd.DataFrame) -> pd.DataFrame:
        """Full-text search across name, email, role, and location columns."""
        if not query or not query.strip():
            return df
        q = query.strip().lower()
        mask = (
            df["name"].str.lower().str.contains(q, na=False)
            | df["email"].str.lower().str.contains(q, na=False)
            | df["role"].str.lower().str.contains(q, na=False)
            | df["location"].str.lower().str.contains(q, na=False)
        )
        return df[mask]

    @staticmethod
    def apply_filters(
        df: pd.DataFrame,
        *,
        statuses: Optional[List[str]] = None,
        roles:    Optional[List[str]] = None,
        min_score: float = 0.0,
        max_score: float = 100.0,
        min_exp: float = 0.0,
        max_exp: float = 20.0,
        education: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Apply structured filters to a candidate DataFrame."""
        out = df.copy()
        if statuses:
            out = out[out["status"].isin(statuses)]
        if roles:
            out = out[out["role"].isin(roles)]
        out = out[out["ats_score"].between(min_score, max_score)]
        out = out[out["experience_years"].between(min_exp, max_exp)]
        if education:
            out = out[out["education"].isin(education)]
        return out

    # ── Aggregates ─────────────────────────────────────────────────────────────

    def get_kpi_summary(self) -> Dict[str, Any]:
        """Return top-level dashboard KPI values."""
        df = self.get_all()
        hired_cutoff = pd.Timestamp(date.today() - timedelta(days=30))
        hired_this_month = int(
            ((df["status"] == "Hired") & (df["applied_date"] >= hired_cutoff)).sum()
        )
        return {
            "total_candidates": len(df),
            "active_roles":     df["role"].nunique(),
            "avg_ats_score":    round(float(df["ats_score"].mean()), 1),
            "hired_this_month": hired_this_month,
            "pending_review":   int((df["status"] == "Screening").sum()),
            "rejection_rate":   round(float((df["status"] == "Rejected").mean()) * 100, 1),
        }

    def get_pipeline_stages(self) -> pd.DataFrame:
        """Return candidate counts per pipeline status, in funnel order."""
        order = ["Screening", "Phone Screen", "Technical Round", "Final Round", "Hired"]
        df = self.get_all()
        counts = df[df["status"].isin(order)]["status"].value_counts()
        result = pd.DataFrame({"stage": order, "count": [int(counts.get(s, 0)) for s in order]})
        return result

    def get_status_distribution(self) -> pd.DataFrame:
        """Return candidate counts per status for donut/pie charts."""
        df = self.get_all()
        return df["status"].value_counts().reset_index().rename(
            columns={"index": "status", "count": "count"}
        )

    def get_skills_frequency(self, top_n: int = 15) -> pd.DataFrame:
        """Return the most-frequent skills across all candidates."""
        df = self.get_all()
        skill_lists = df["skills"].tolist()
        all_skills: List[str] = []
        for skills in skill_lists:
            if isinstance(skills, list):
                all_skills.extend(skills)
            elif isinstance(skills, str):
                all_skills.extend(s.strip() for s in skills.split(","))
        series = pd.Series(all_skills)
        top = series.value_counts().head(top_n).reset_index()
        top.columns = ["skill", "count"]
        return top

    def get_score_by_role(self) -> pd.DataFrame:
        """Return avg ATS score grouped by role for comparison charts."""
        df = self.get_all()
        return (
            df.groupby("role")["ats_score"]
            .agg(["mean", "min", "max", "count"])
            .reset_index()
            .rename(columns={"mean": "avg_score", "count": "num_candidates"})
            .sort_values("avg_score", ascending=False)
        )

    def get_applications_over_time(self) -> pd.DataFrame:
        """Return weekly application counts for trend charts."""
        df = self.get_all()
        weekly = (
            df.set_index("applied_date")
            .resample("W")["id"]
            .count()
            .reset_index()
            .rename(columns={"applied_date": "week", "id": "applications"})
        )
        weekly["week"] = weekly["week"].dt.date
        return weekly

    def get_education_distribution(self) -> pd.DataFrame:
        """Return candidate counts by education level."""
        df = self.get_all()
        return df["education"].value_counts().reset_index().rename(
            columns={"index": "education", "count": "count"}
        )

    # ── Mutations ──────────────────────────────────────────────────────────────

    def update_status(self, candidate_id: str, new_status: str) -> None:
        """Persist a status change for the current session."""
        overrides = st.session_state.setdefault(self._SESSION_KEY, {})
        overrides.setdefault(candidate_id, {})["status"] = new_status
        logger.info("Status updated: candidate=%s status=%s", candidate_id, new_status)

    def update_notes(self, candidate_id: str, notes: str) -> None:
        """Persist recruiter notes for the current session."""
        overrides = st.session_state.setdefault(self._SESSION_KEY, {})
        overrides.setdefault(candidate_id, {})["notes"] = notes
        logger.info("Notes updated: candidate=%s", candidate_id)
