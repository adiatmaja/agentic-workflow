---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
  - "**/requirements*.txt"
  - "**/conftest.py"
---

# Python Hooks

## PostToolUse Hooks

Configure in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "ruff fmt \"$CLAUDE_TOOL_RESULT_FILE_PATH\" 2>/dev/null || true",
            "description": "Auto-format Python files with ruff fmt (replaces black)"
          },
          {
            "type": "command",
            "command": "ruff check --fix --silent \"$CLAUDE_TOOL_RESULT_FILE_PATH\" 2>/dev/null || true",
            "description": "Auto-fix lint issues and sort imports (replaces isort)"
          },
          {
            "type": "command",
            "command": "mypy \"$CLAUDE_TOOL_RESULT_FILE_PATH\" --ignore-missing-imports 2>&1 | grep -E 'error:|warning:' || true",
            "description": "Run mypy type checking after editing .py files"
          }
        ]
      }
    ]
  }
}
```

## Type Checking Strategy

- **IDE (VS Code)**: Pylance (powered by **Pyright**) — instant feedback, 3-5x faster than mypy
- **Hooks / CI**: **Mypy** — authoritative, strict mode enforcement

## Warnings

- Warn about `print()` statements in edited files (use `logging` module instead)
- Ruff replaces both `black` and `isort` — do not run them separately
