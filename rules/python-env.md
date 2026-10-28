---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
  - "**/requirements*.txt"
  - "**/conftest.py"
---

# Python Environment

## Package Manager — uv

Use **uv** as the standard package manager. It replaces pip, venv, pip-tools, and pyenv:

```bash
# Install uv (once)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtualenv and install deps
uv venv
uv pip install -r requirements.txt

# Add a dependency
uv add httpx

# Run a script in the venv
uv run python scripts/run_generation.py

# Sync dependencies from pyproject.toml
uv sync
```

## Python Version

- Minimum: **Python 3.10** (required for `X | Y` union syntax, `match` statements)
- Pin version with `.python-version` file in the project root:

```
3.11
```

## pyproject.toml — Single Source of Truth

All project config lives in `pyproject.toml`. Do not use `setup.py`, `setup.cfg`, or `tox.ini`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-mock>=3.0",
    "ruff>=0.4",
    "mypy>=1.0",
]

[tool.setuptools.packages.find]
where = ["src"]
```

## requirements.txt — For Docker and CI

Keep a flat `requirements.txt` for Docker images and CI environments where uv is not available:

```bash
# Generate from pyproject.toml
uv pip compile pyproject.toml -o requirements.txt

# Or for dev dependencies
uv pip compile pyproject.toml --extra dev -o requirements-dev.txt
```

## Project Structure

```
project/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       └── ...
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── scripts/          # one-off utility scripts
├── config/           # YAML config files
├── docker/           # Dockerfiles
├── .python-version   # pin Python version
├── pyproject.toml    # single source of truth
├── requirements.txt  # generated, for Docker/CI
└── .env.example      # template, never commit .env
```

## Environment Variables

- Store secrets in `.env` (never commit)
- Provide `.env.example` as a template
- Use `python-dotenv` to load in development
- Use `os.environ["KEY"]` (not `.get()`) so missing vars fail loudly

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["API_KEY"]       # raises KeyError if missing — good
db_url = os.environ.get("DB_URL", "sqlite:///dev.db")  # optional with default
```

## Docker Considerations

- Training/GPU workloads run inside Docker — keep host requirements minimal
- Do not install GPU/CUDA packages on the host (`torch`, `unsloth`, `transformers`)
- Pin the Docker base image tag for reproducibility
- Use multi-stage builds to keep final images small
