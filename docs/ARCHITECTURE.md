# Architecture

## Overview

The Resume Parser System is a modular Python platform built around three independent domain engines that share a common data model layer.  A Streamlit dashboard surfaces the results.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Streamlit UI (app.py)                        │
│  Overview │ Candidates │ Analytics │ Reports                         │
└───────────────────────────┬─────────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐
   │   Parser    │  │  ATS Engine  │  │  Job Matching     │
   │  (parser/)  │  │   (ats/)     │  │ (job_matching/)   │
   └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘
          │                │                    │
          └────────────────┼────────────────────┘
                           ▼
                   parser.models.Resume
                   (shared Pydantic schema)
```

## Module Responsibilities

### `parser/`
Converts raw resume files (PDF, DOCX) into `parser.models.Resume`.

| Component | Role |
|---|---|
| `ResumeParser` | Orchestrator: file validation → read → preprocess → extract |
| `readers/` | PDF (PyMuPDF) and DOCX text extraction |
| `preprocessors/` | Section boundary detection and text normalisation |
| `extractors/` | Contact, Skills, Experience, Education, Projects, Certifications |

### `ats/`
Scores a `Resume` against 9 weighted categories and generates actionable recommendations.

**Scoring weights (configurable in `ats/config.py`):**

| Category | Weight |
|---|---|
| Work Experience | 25% |
| Skills | 15% |
| Education | 12% |
| Contact Details | 10% |
| Projects | 10% |
| Professional Summary | 8% |
| Certifications | 8% |
| Formatting | 7% |
| Keywords | 5% |

**Pipeline:** `ResumeValidator` → `ATSScorer` → `CompletenessAnalyzer` → `ExperienceCalculator` → `MatchExplainer` → `RecommendationGenerator` → `ATSReport`

### `job_matching/`
Computes semantic similarity between a resume and a job description and ranks candidate pools.

**Similarity dimensions:**

| Dimension | Weight | Method |
|---|---|---|
| Skills Match | 40% | Exact + alias + cosine similarity per skill |
| Semantic Similarity | 35% | Cosine similarity of full-text embeddings |
| Experience Match | 15% | Rule-based gap scoring |
| Education Match | 10% | Ordinal qualification comparison |

**Pipeline:** `JDParser` → `SkillNormalizer` → `EmbeddingEngine` → `SimilarityCalculator` → `MatchExplainer` → `CandidateRanker` → `MatchResult` / `RankingResult`

### `core/`
Deployment infrastructure shared across all modules.

| Component | Role |
|---|---|
| `settings.py` | Pydantic Settings — reads all config from env vars or `.env` |
| `logging_setup.py` | Root-logger configuration, text + JSON format, rotating file handler |

## Data Flow

```
PDF/DOCX file
     │
     ▼
ResumeParser.parse()
     │
     ▼
parser.models.Resume  ──────────────────────────────────────┐
     │                                                       │
     ├──► ATSAnalyzer.analyze()                             │
     │         │                                             │
     │         ▼                                             │
     │    ATSReport (score, strengths, recommendations)      │
     │                                                       │
     └──► JobMatcher.match(resume, jd_text=...)    ◄────────┘
               │
               ▼
          MatchResult (score, matched skills, missing skills)
```

## Dependency Graph (no circular imports)

```
core.settings          (no internal deps)
core.logging_setup     (no internal deps)

parser.models          (no internal deps)
parser.readers         → parser.models
parser.extractors      → parser.models
parser.parser          → parser.models, readers, extractors

ats.config             (no internal deps)
ats.exceptions         (no internal deps)
ats.models             → pydantic
ats.validators         → parser.models, ats.config, ats.exceptions
ats.completeness       → parser.models, ats.config
ats.experience_calc    → parser.models, ats.config
ats.scorer             → parser.models, ats.config, ats.completeness, ats.experience_calc
ats.recommendations    → parser.models, ats.config, ats.models, ats.completeness
ats.analyzer           → all ats.*, parser.models

job_matching.config    (no internal deps)
job_matching.exceptions (no internal deps)
job_matching.models    → pydantic
job_matching.normalizer → job_matching.config, job_matching.exceptions
job_matching.embeddings → job_matching.config, job_matching.exceptions
job_matching.jd_parser  → job_matching.config, job_matching.exceptions, job_matching.models
job_matching.similarity → parser.models, job_matching.config, job_matching.embeddings, job_matching.models
job_matching.explainer  → parser.models, job_matching.config, job_matching.models, job_matching.similarity
job_matching.ranker     → parser.models, job_matching.config, job_matching.exceptions, job_matching.models
job_matching.matcher    → all job_matching.*

utils.formatters       (no internal deps)
utils.data_service     → utils.logger
utils.report_generator → utils.formatters

components.*           → utils.*, components.*
pages.*                → components.*, utils.*, ats.*, job_matching.*
app.py                 → core.*, pages.*
```

## Design Principles

1. **No circular imports** — dependency graph is a DAG.
2. **Configurable over hardcoded** — all weights and thresholds live in `config.py` files; `core/settings.py` manages deployment parameters.
3. **Fail fast** — Pydantic validates all inputs at construction time; misconfigured deployments raise immediately.
4. **Testability** — every module is independently testable.  ML models are injected as dependencies so tests can mock them.
5. **Separation of concerns** — scoring, validation, completeness, experience, and recommendations are separate classes.
