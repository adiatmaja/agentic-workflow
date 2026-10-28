---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
  - "**/requirements*.txt"
  - "**/conftest.py"
---

# Python Testing

## Framework

Use **pytest** as the testing framework.

## Coverage

Minimum 80% coverage — enforce in CI:

```bash
pytest --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=80
```

## Test Organization

Use `pytest.mark` for categorization:

```python
import pytest

@pytest.mark.unit
def test_calculate_total():
    ...

@pytest.mark.integration
def test_database_connection():
    ...

@pytest.mark.slow
def test_full_pipeline():
    ...
```

Register markers in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: fast, isolated unit tests",
    "integration: tests that touch external systems",
    "slow: tests that take more than a few seconds",
]
addopts = "-v --tb=short"
```

## conftest.py — Shared Fixtures

Use `conftest.py` for fixtures shared across test files:

```python
# tests/conftest.py
import pytest
from pathlib import Path


@pytest.fixture
def sample_data() -> list[dict]:
    return [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Provide a clean temporary directory for file output tests."""
    output = tmp_path / "output"
    output.mkdir()
    return output


@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set test environment variables."""
    monkeypatch.setenv("APP_API_KEY", "test-key")
    monkeypatch.setenv("APP_DEBUG", "true")
```

## Mocking

Use `pytest-mock` for clean mock syntax:

```python
def test_api_call_retries_on_timeout(mocker):
    mock_get = mocker.patch("httpx.get", side_effect=TimeoutError)

    with pytest.raises(TimeoutError):
        call_external_api("http://example.com")

    assert mock_get.call_count == 3  # verify retry count
```

For `unittest.mock` when pytest-mock is not available:

```python
from unittest.mock import MagicMock, patch

def test_sends_notification():
    with patch("src.notifications.send_email") as mock_send:
        process_order(order_id="123")
        mock_send.assert_called_once_with(to="user@example.com")
```

## Parametrize — Data-Driven Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("hello world", 2),
    ("one", 1),
    ("", 0),
    ("  spaces  ", 1),
])
def test_word_count(input: str, expected: int):
    assert count_words(input) == expected
```

## File System Tests

Use the built-in `tmp_path` fixture for file operations:

```python
def test_saves_output_file(tmp_path):
    output_file = tmp_path / "result.json"
    save_results([{"id": 1}], output_file)

    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert len(data) == 1
```

## Reference

See skill: `python-testing` for detailed pytest patterns and fixtures.
