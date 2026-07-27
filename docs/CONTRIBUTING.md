# Contributing Guide

## Getting Started

```bash
git clone https://github.com/hamsini105/project.git
cd project
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
cp .env.example .env
```

## Branching Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-ready code.  Protected — no direct pushes. |
| `develop` | Integration branch for features. |
| `feat/<slug>` | New feature or enhancement. |
| `fix/<slug>` | Bug fix. |
| `chore/<slug>` | Tooling, CI, documentation changes. |

Example: `feat/pdf-export-improvements`

## Development Workflow

1. Branch from `develop`:
   ```bash
   git checkout develop && git pull
   git checkout -b feat/your-feature
   ```

2. Make focused, well-scoped commits.

3. Before pushing, run the full quality suite locally:
   ```bash
   black .
   ruff check .
   pytest tests/ -v
   ```

4. Push and open a Pull Request targeting `develop`.

## Coding Standards

**Python version**: 3.10+  
**Line length**: 100 (enforced by Black)  
**Import order**: enforced by Ruff (`isort` rules)

### Type hints

All public functions must have full type annotations:

```python
# Good
def score_resume(resume: Resume) -> tuple[float, dict[str, float]]:
    ...

# Bad — missing return type
def score_resume(resume):
    ...
```

### Docstrings

Module, class, and public function docstrings follow Google style:

```python
def normalize(self, skill: str) -> str:
    """
    Normalise a single skill string to its canonical form.

    Args:
        skill: Raw skill text, e.g. "ReactJS", "k8s".

    Returns:
        Canonical lowercase skill string.

    Raises:
        NormalizationException: If ``skill`` is not a string.
    """
```

### Module structure

Each module should follow this layout:

```python
"""Module docstring."""

from __future__ import annotations

# stdlib
import logging
from typing import ...

# third-party
import pandas as pd

# project-internal (alphabetical by package)
from ats.config import ...
from parser.models import ...

logger = logging.getLogger(__name__)

# Constants and type aliases

# Classes / functions
```

### Error handling

- Use the module-specific exception hierarchy rather than bare `Exception`.
- Wrap unexpected exceptions at boundary points and re-raise with context.
- Never swallow exceptions silently.

```python
# Good
try:
    result = external_call()
except SpecificError as exc:
    raise OurModuleException(f"External call failed: {exc}") from exc

# Bad
try:
    result = external_call()
except Exception:
    pass
```

### Logging

Use `logging.getLogger(__name__)` at module level, never `print()`:

```python
logger = logging.getLogger(__name__)

# Structured context
logger.info("Processing candidate %s", candidate_id)
logger.warning("No skills found in JD; scanning full text")
logger.error("Scoring failed for %s: %s", name, exc, exc_info=True)
```

## Writing Tests

- Place unit tests in `tests/unit/`, integration tests in `tests/integration/`.
- Name test files `test_<module_name>.py`.
- Use `pytest.mark.parametrize` for data-driven tests.
- Mock ML models with the `mock_embedding_engine` fixture from `conftest.py`.
- Target ≥ 80% coverage on new code.

```bash
pytest tests/unit/ -v              # fast — no ML deps
pytest tests/integration/ -v       # mocked embeddings
pytest tests/ --cov --cov-report=html
```

## Pull Request Checklist

- [ ] All tests pass locally: `pytest tests/ -v`
- [ ] Linting passes: `ruff check . && black --check .`
- [ ] New public functions have type hints and docstrings
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] PR description explains *what* changed and *why*
- [ ] No secrets or `.env` files committed

## Reporting Bugs

Open a GitHub Issue with:
1. Python version and OS
2. Minimal reproduction steps
3. Expected vs. actual behaviour
4. Relevant log output (redact any PII)
