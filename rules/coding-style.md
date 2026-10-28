---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
  - "**/requirements*.txt"
  - "**/conftest.py"
---

# Python Coding Style

## Standards

- Follow **PEP 8** conventions
- Target **Python 3.10+**
- Use **type annotations** on all function signatures
- Max line length: **88 characters** (ruff/black default)

## Type Annotations

Use PEP 604 union syntax (Python 3.10+):

```python
# Good
def get_user(id: str) -> dict | None: ...
def process(value: int | str) -> str: ...

# Avoid
from typing import Optional, Union
def get_user(id: str) -> Optional[dict]: ...
def process(value: Union[int, str]) -> str: ...
```

Use built-in generics (Python 3.9+):

```python
# Good
def items() -> list[str]: ...
def mapping() -> dict[str, int]: ...

# Avoid
from typing import List, Dict
def items() -> List[str]: ...
```

## Immutability

Prefer immutable data structures:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    name: str
    email: str

from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float
```

## Formatting — Ruff Only

Use **ruff** as the single tool for formatting, import sorting, and linting.
Do NOT use black or isort separately — ruff replaces both.

```bash
ruff fmt .           # format code (replaces black)
ruff check --fix .   # lint + fix imports (replaces isort + flake8)
```

Recommended `pyproject.toml` ruff config:

```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "DTZ", "EM", "ISC", "PIE", "PT", "Q", "RET", "SIM", "TID", "ARG"]
ignore = ["E501", "B008", "ARG001", "ARG002"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.format]
quote-style = "double"

[tool.ruff.lint.isort]
lines-after-imports = 2
```

## Type Checking

Use a **hybrid approach**:
- **Pyright** in the IDE (VS Code Pylance) — instant feedback, 3-5x faster
- **Mypy** in CI — authoritative gate with strict settings

```toml
[tool.mypy]
python_version = "3.10"
disallow_untyped_defs = true
disallow_incomplete_defs = true
warn_return_any = true
warn_redundant_casts = true
warn_unused_ignores = true
strict_equality = true
no_implicit_optional = true
```

## Logging

Never use `print()` in production code. Always use the `logging` module:

```python
import logging

logger = logging.getLogger(__name__)

# Good
logger.info("Processing %d records", count)
logger.error("Failed to connect: %s", err)

# Bad
print(f"Processing {count} records")
```

## Docstrings

Use **Google-style** docstrings:

```python
def load_data(path: str, limit: int | None = None) -> list[dict]:
    """Load records from a file.

    Args:
        path: Path to the input file.
        limit: Maximum number of records to load. None means no limit.

    Returns:
        List of parsed record dicts.

    Raises:
        FileNotFoundError: If the path does not exist.
    """
```

## Exception Handling

Always catch specific exceptions, never bare `except`:

```python
# Good
try:
    result = api_call()
except httpx.TimeoutException as e:
    logger.warning("Request timed out: %s", e)
except httpx.HTTPStatusError as e:
    logger.error("HTTP error %d: %s", e.response.status_code, e)

# Bad
try:
    result = api_call()
except:
    pass
```

Use `raise ... from` to preserve exception chains:

```python
try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON in response: {raw[:100]}") from e
```

## Reference

See skill: `python-patterns` for comprehensive Python idioms and patterns.
