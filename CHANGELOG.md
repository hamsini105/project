# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.3.0] — 2026-07-27

### Added — Production Readiness
- `core/settings.py` — Pydantic Settings with full environment variable management
- `core/logging_setup.py` — Structured logging supporting `text` and `json` formats
- `pyproject.toml` — Unified tool configuration for Black, Ruff, mypy, and pytest
- `requirements-dev.txt` — Separate dev dependency manifest
- `Dockerfile` — Multi-stage build (`base`, `deps`, `development`, `production`)
- `docker-compose.yml` — Development and production service definitions
- `.pre-commit-config.yaml` — Black, Ruff, mypy, and file-hygiene hooks
- `.github/workflows/ci.yml` — CI pipeline: lint → test (matrix 3.10/3.11/3.12) → Docker build
- `.streamlit/config.toml` — Hardened server settings (XSRF, upload limits, telemetry off)
- `.env.example` — Documented environment variable template
- `tests/` — Full pytest suite: unit tests for formatters, normalizer, JD parser,
  data service, settings; integration tests for the ATS and job-matching pipelines

### Changed
- `README.md` — Complete rewrite with quick start, project structure, and links
- `app.py` — Initialises centralised logging at startup via `core.logging_setup`

---

## [1.2.0] — 2026-07-27

### Added — Recruiter Dashboard
- `utils/data_service.py` — `CandidateService` with deterministic mock data
- `utils/formatters.py` — Pure formatting helpers (scores, dates, skills)
- `utils/report_generator.py` — CSV and PDF export via `fpdf2`
- `components/charts.py` — 8 Plotly chart functions (funnel, donut, bar, histogram …)
- `components/candidate_table.py` — Paginated row-level candidate table
- `components/filters.py` — `FilterState` dataclass + full filter panel
- `components/status_badge.py` — HTML badge/pill/gauge utilities per status band
- `components/export.py` — CSV and PDF download button components
- `components/empty_state.py` — Empty state and loading placeholders
- `pages/candidates.py` — List ↔ profile drill-down routing
- `pages/analytics.py` — 8-chart analytics grid
- `pages/candidate_profile.py` — Score gauge, contact, skills, notes, status edit
- `pages/reports.py` — Scoped report generation
- `assets/css/recruiter.css` — Status badges, filter panel, and table styles

### Changed
- `app.py` — 4-tab shell (Overview / Candidates / Analytics / Reports)
- `components/sidebar.py` — Live Quick Stats expander
- `pages/dashboard.py` — Real Plotly charts replacing placeholders

---

## [1.1.0] — 2026-07-27

### Added — Semantic Job Matching
- `job_matching/` — Full semantic matching engine using Sentence Transformers
  - `jd_parser.py` — Pattern-based JD text parser
  - `normalizer.py` — Skill alias normalisation
  - `embeddings.py` — Lazy-loading model with LRU cache
  - `similarity.py` — Skills (40%) + Semantic (35%) + Experience (15%) + Education (10%)
  - `ranker.py` — Stable-sort candidate pool ranker
  - `explainer.py` — Human-readable match explanations and recommendations
  - `matcher.py` — `JobMatcher` orchestrator

---

## [1.0.0] — 2026-07-27

### Added — Core Modules
- `parser/` — Resume parsing engine (PDF/DOCX, 6 extractors)
- `ats/` — ATS analysis engine (9-category scorer, completeness, experience, recommendations)
- `components/` — Reusable Streamlit UI components (navbar, sidebar, metric cards)
- `pages/dashboard.py` — Initial recruiter dashboard
- `utils/logger.py` — Module-level logger utility
- `assets/css/` — Custom design system (Inter font, brand tokens)
