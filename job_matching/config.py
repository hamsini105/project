"""
Centralized configuration for the Job Matching module.

All tunable thresholds, model settings, and scoring parameters live here.
No hardcoded values exist in core logic — every parameter is sourced from
this module to ensure testability and operator configurability.
"""

from typing import Dict, List, Tuple

# ── Embedding Model ────────────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE: int = 32
EMBEDDING_MAX_SEQ_LENGTH: int = 256
# LRU cache capacity for in-process embedding memoisation
EMBEDDING_CACHE_SIZE: int = 1024

# ── Scoring Weights (must sum to 1.0) ─────────────────────────────────────────
SCORING_WEIGHTS: Dict[str, float] = {
    "skills_match":        0.40,
    "semantic_similarity": 0.35,
    "experience_match":    0.15,
    "education_match":     0.10,
}

# ── Similarity Thresholds ─────────────────────────────────────────────────────
# Cosine similarity floor to accept a semantic skill match
SEMANTIC_SKILL_MATCH_THRESHOLD: float = 0.65
# Above this, report as a "strong" semantic match (vs. just "semantic")
STRONG_SKILL_MATCH_THRESHOLD: float = 0.85

# ── Match Rating Bands ────────────────────────────────────────────────────────
SCORE_RANGES: Dict[str, Tuple[float, float]] = {
    "excellent": (85.0, 100.0),
    "good":      (70.0, 84.9),
    "fair":      (50.0, 69.9),
    "poor":      (0.0,  49.9),
}

# ── JD Section Detection ──────────────────────────────────────────────────────
# Maps canonical section names to the surface-text patterns that trigger them.
# Matching is case-insensitive substring search on stripped lines.
JD_SECTION_HEADERS: Dict[str, List[str]] = {
    "requirements": [
        "requirements", "required qualifications", "required skills",
        "must have", "must-have", "qualifications", "what we require",
        "minimum qualifications", "basic qualifications",
    ],
    "preferred": [
        "preferred", "preferred qualifications", "nice to have",
        "nice-to-have", "bonus", "desired", "plus",
        "would be a plus", "additional qualifications",
    ],
    "responsibilities": [
        "responsibilities", "key responsibilities", "duties",
        "what you'll do", "what you will do", "your role",
        "day-to-day", "day to day",
    ],
    "about": [
        "about the role", "about the job", "about this role",
        "overview", "position summary", "job summary", "role summary",
    ],
}

# ── Experience Extraction Patterns ───────────────────────────────────────────
# Ordered from most-specific to least-specific.
EXPERIENCE_REGEX_PATTERNS: List[str] = [
    r"(\d+)\s*[-\u2013]\s*(\d+)\s*years?\s+(?:of\s+)?experience",  # Range: "3-5 years"
    r"(\d+)\+\s*years?",                                           # Minimum: "5+ years" (flexible)
    r"minimum\s+(?:of\s+)?(\d+)\s+years?",                        # Explicit minimum
    r"at\s+least\s+(\d+)\s+years?",                               # At least
    r"(\d+)\s*years?\s+(?:of\s+)?(?:relevant\s+)?experience",     # Generic "X years of experience"
]

# ── Education ─────────────────────────────────────────────────────────────────
# Ordinal ranking of education levels for gap calculation
EDUCATION_LEVELS: Dict[str, int] = {
    "high school": 1,
    "associate":   2,
    "bachelor":    3,
    "master":      4,
    "phd":         5,
    "doctorate":   5,
}

EDUCATION_KEYWORDS: Dict[str, List[str]] = {
    "high school": ["high school", "ged", "secondary"],
    "associate":   ["associate", "a.a.", "a.s."],
    "bachelor":    ["bachelor", "b.s.", "b.a.", "undergraduate", "b.eng", "b.tech"],
    "master":      ["master", "m.s.", "m.a.", "m.eng", "m.tech", "mba", "m.b.a."],
    "phd":         ["phd", "ph.d.", "doctorate", "doctoral"],
}

# ── Skill Aliases ─────────────────────────────────────────────────────────────
# Maps raw text variants to a canonical skill name.
# All keys and values should be lowercase.
SKILL_ALIASES: Dict[str, str] = {
    # Languages
    "js":                      "javascript",
    "ts":                      "typescript",
    "py":                      "python",
    "golang":                  "go",
    "c sharp":                 "c#",
    "cplusplus":               "c++",
    "c plus plus":             "c++",
    # Frontend
    "reactjs":                 "react",
    "react.js":                "react",
    "vuejs":                   "vue",
    "vue.js":                  "vue",
    "angularjs":               "angular",
    "nextjs":                  "next.js",
    "nuxtjs":                  "nuxt.js",
    # Backend
    "nodejs":                  "node.js",
    "node":                    "node.js",
    "expressjs":               "express",
    "express.js":              "express",
    "springboot":              "spring boot",
    "flask-api":               "flask",
    # Databases
    "postgres":                "postgresql",
    "mongo":                   "mongodb",
    "elastic":                 "elasticsearch",
    # Cloud
    "amazon web services":     "aws",
    "google cloud":            "gcp",
    "google cloud platform":   "gcp",
    "microsoft azure":         "azure",
    # ML / AI
    "ml":                      "machine learning",
    "dl":                      "deep learning",
    "nlp":                     "natural language processing",
    "cv":                      "computer vision",
    "tf":                      "tensorflow",
    "sklearn":                 "scikit-learn",
    # DevOps
    "k8s":                     "kubernetes",
    "ci/cd":                   "cicd",
    "ci cd":                   "cicd",
    "continuous integration":  "cicd",
    # General
    "oop":                     "object-oriented programming",
    "rest":                    "rest api",
    "restful":                 "rest api",
    "restful api":             "rest api",
    "tdd":                     "test-driven development",
    "bdd":                     "behavior-driven development",
}

# ── Known Tech Skills (for extraction) ───────────────────────────────────────
# Sorted longest-first so multi-word skills match before their substrings
# (e.g. "machine learning" matches before "machine").
KNOWN_TECH_SKILLS: List[str] = sorted(
    [
        "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#",
        "ruby", "scala", "kotlin", "swift", "php", "r", "matlab",
        "react", "angular", "vue", "html", "css", "sass", "svelte", "next.js",
        "django", "flask", "fastapi", "spring boot", "spring", "express", "node.js",
        "rails", "laravel", "asp.net",
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
        "dynamodb", "sqlite", "oracle", "sql server",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "machine learning", "deep learning", "natural language processing",
        "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
        "pandas", "numpy", "scipy", "matplotlib", "jupyter",
        "spark", "hadoop", "kafka", "airflow", "dbt", "tableau", "power bi",
        "git", "github", "gitlab", "bitbucket", "jenkins", "github actions",
        "linux", "bash", "shell scripting",
        "agile", "scrum", "kanban", "jira", "confluence",
        "rest api", "graphql", "grpc", "microservices",
        "rabbitmq", "celery", "nginx", "apache",
        "object-oriented programming", "functional programming",
        "test-driven development", "system design",
        "data structures", "algorithms", "cicd", "devops", "cloud computing",
    ],
    key=len,
    reverse=True,
)

# ── Skill Category Groups ─────────────────────────────────────────────────────
SKILL_CATEGORIES: Dict[str, List[str]] = {
    "languages":   ["python", "java", "javascript", "typescript", "go", "rust", "c++", "c#", "ruby", "scala"],
    "frontend":    ["react", "angular", "vue", "html", "css", "sass", "webpack", "vite", "next.js"],
    "backend":     ["django", "flask", "fastapi", "spring boot", "express", "node.js", "rails"],
    "databases":   ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb"],
    "cloud":       ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible"],
    "ml_ai":       ["machine learning", "deep learning", "natural language processing", "computer vision",
                    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy"],
    "devops":      ["cicd", "jenkins", "github actions", "gitlab ci", "linux", "bash", "git"],
    "data":        ["spark", "hadoop", "kafka", "airflow", "dbt", "tableau", "power bi"],
}

# ── Ranking ───────────────────────────────────────────────────────────────────
# Hard upper bound on candidates processed in a single ranking call
MAX_CANDIDATES_PER_RANKING: int = 200
# Candidates below this score are still returned but marked as low-match
MIN_RANKING_INCLUSION_SCORE: float = 0.0
