# Resume Parser System

A production-grade platform for parsing resumes, scoring ATS compatibility, matching candidates to job descriptions with semantic embeddings, and surfacing insights through an interactive recruiter dashboard.

## Features

| Module | Description |
|---|---|
| **Parser** | Extracts structured data from PDF/DOCX into a typed Pydantic schema |
| **ATS Engine** | Scores resumes across 9 weighted categories with explainable recommendations |
| **Job Matching** | Semantic similarity matching using Sentence Transformers |
| **Recruiter Dashboard** | Interactive Streamlit UI with charts, filters, and CSV/PDF export |

## Quick Start

```bash
git clone https://github.com/hamsini105/project.git && cd project
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## Docker

```bash
# Development (live reload)
docker compose up app

# Production
docker compose --profile production up app-prod
```

## Project Structure

```
├── app.py                    # Streamlit entry point
├── core/                     # Deployment infrastructure
│   ├── settings.py           # Pydantic Settings (env var management)
│   └── logging_setup.py      # Structured logging (text + JSON)
├── parser/                   # Resume parsing engine
├── ats/                      # ATS analysis and scoring
├── job_matching/             # Semantic job matching
├── components/               # Reusable Streamlit UI components
├── pages/                    # Dashboard page modules
├── utils/                    # Shared utilities
├── tests/                    # pytest test suite (unit + integration)
├── docs/                     # Architecture and deployment docs
├── Dockerfile                # Multi-stage production image
├── docker-compose.yml        # Dev and production services
└── pyproject.toml            # Tool configuration (Black, Ruff, mypy, pytest)
```

## Environment Variables

Copy `.env.example` to `.env`.  All variables have safe defaults for local development.

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` / `staging` / `production` |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FORMAT` | `text` | `text` (human) or `json` (for log aggregators) |
| `MAX_UPLOAD_SIZE_MB` | `10` | Resume upload size limit |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence Transformers model |
| `SERVER_PORT` | `8501` | Streamlit server port |

See `.env.example` for the full list.

## Development

```bash
pip install -r requirements-dev.txt
pre-commit install
pytest tests/ -v
ruff check . && black .
```

## Testing

```bash
pytest tests/unit/        -v          # no ML deps required
pytest tests/integration/ -v          # embedding engine is mocked
pytest tests/ --cov --cov-report=html # with coverage
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## License

MIT

Included:
- Modular frontend architecture
- Reusable components (Sidebar, Navbar, Metric Cards, Section Header, Footer)
- Custom HTML and external CSS styling
- Responsive SaaS-style dashboard layout
- Logging, type hints, and docstrings

Excluded by design:
- Resume parsing logic
- AI models and ATS scoring
- Authentication
- Database or backend services

## Folder Structure

```text
resume-parser-system-frontend/
  app.py
  requirements.txt
  README.md
  .streamlit/
    config.toml
  assets/
    css/
      theme.css
      layout.css
      cards.css
      responsive.css
  components/
    __init__.py
    footer.py
    metric_cards.py
    navbar.py
    section_header.py
    sidebar.py
  pages/
    __init__.py
    dashboard.py
  utils/
    logger.py
```

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
streamlit run app.py
```

## Architecture Notes

- `app.py`: Entry point, global page setup, CSS loading, page render orchestration.
- `components/`: Small reusable UI units with isolated responsibilities.
- `pages/dashboard.py`: Feature composition layer for KPI cards, uploads, activity, analytics placeholders, and quick actions.
- `assets/css/`: External stylesheet system split by concern (theme, layout, cards, responsive).
- `utils/logger.py`: Shared logging utility for consistent diagnostics.

## Design Direction

- Inter typography
- Linear/Ashby/Greenhouse/Notion-inspired professional UI language
- Soft shadows, rounded surfaces, roomy spacing
- Subtle entrance and hover motion
- Mobile/tablet/desktop responsive behavior

## Next Frontend Steps

1. Add lightweight client-side state for filters and date ranges.
2. Introduce chart rendering layer (frontend-only placeholder replacement).
3. Add visual regression checks for key breakpoints.

