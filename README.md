# Resume Parser System - Frontend Foundation

Production-ready Streamlit frontend scaffold for a recruiter dashboard. This repository intentionally contains only UI foundation and design system architecture.

## Scope

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
