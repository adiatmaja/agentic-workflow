---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
  - "**/requirements*.txt"
  - "**/conftest.py"
---

# Python Patterns

## Protocol (Duck Typing)

```python
from typing import Protocol

class Repository(Protocol):
    def find_by_id(self, id: str) -> dict | None: ...
    def save(self, entity: dict) -> dict: ...
```

## Pydantic vs Dataclasses

Use both tools strategically — they serve different roles:

| Use case | Tool |
|----------|------|
| API input / external data validation | **Pydantic** |
| Config from env vars / files | **Pydantic Settings** |
| Internal domain models (core logic) | **Dataclasses** |
| Typed DTOs passed between functions | **Dataclasses** |

```python
# Pydantic at the boundary (API input, env config)
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings

class CreateUserRequest(BaseModel):
    name: str
    email: str
    age: int | None = None

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email")
        return v.lower()

class AppSettings(BaseSettings):
    api_key: str
    db_url: str
    debug: bool = False

    model_config = {"env_prefix": "APP_"}

# Dataclass in core logic (fast, no overhead)
from dataclasses import dataclass

@dataclass
class UserRecord:
    name: str
    email: str
    age: int | None = None
```

## Config: YAML + Environment Overrides

Use YAML for defaults, environment variables for runtime overrides:

```python
import os
import yaml
from dataclasses import dataclass, field


@dataclass
class ServerConfig:
    host: str = "localhost"
    port: int = 8080


def load_config(path: str, env_prefix: str = "APP_") -> dict:
    with open(path) as f:
        config = yaml.safe_load(f)

    # Environment variables override YAML values
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            config_key = key[len(env_prefix):].lower()
            config[config_key] = value

    return config
```

## Retry with Tenacity

Use `tenacity` for production retry logic — not manual loops:

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def call_external_api(url: str) -> dict:
    """Call external API with automatic retry on transient failures."""
    response = httpx.get(url, timeout=30)
    response.raise_for_status()
    return response.json()
```

## Logger Setup

Centralize logging configuration:

```python
import logging
import sys


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: str | None = None,
) -> logging.Logger:
    """Create a configured logger with console and optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    return logger
```

## Dataclasses as DTOs

```python
from dataclasses import dataclass


@dataclass
class CreateUserRequest:
    name: str
    email: str
    age: int | None = None
```

## Context Managers & Generators

- Use context managers (`with` statement) for resource management
- Use generators for lazy evaluation and memory-efficient iteration

```python
from contextlib import contextmanager
from typing import Generator


@contextmanager
def managed_connection(url: str) -> Generator[Connection, None, None]:
    conn = connect(url)
    try:
        yield conn
    finally:
        conn.close()


def stream_records(path: str) -> Generator[dict, None, None]:
    """Yield records one at a time without loading all into memory."""
    with open(path) as f:
        for line in f:
            yield json.loads(line)
```

## Custom Exception Hierarchy

Define a clear exception hierarchy per module or domain:

```python
class AppError(Exception):
    """Base exception for this application."""


class ValidationError(AppError):
    """Raised when input data fails validation."""


class ExternalServiceError(AppError):
    """Raised when an external API or service fails."""


class ConfigurationError(AppError):
    """Raised when required configuration is missing or invalid."""
```

## Reference

See skill: `python-patterns` for comprehensive patterns including decorators, concurrency, and package organization.
