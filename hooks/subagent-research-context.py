#!/usr/bin/env python
"""SubagentStart hook: inject the mandatory research method into every subagent.

Subagents do not inherit ~/.claude/CLAUDE.md reliably, so a subagent asked to look
something up reaches for WebFetch (denied) or answers from training data. This hook
pushes the rule into every subagent at spawn time, including agents added later.

Edit the prose in research-block.md — not this file.
Reads the hook payload on stdin (unused, but drained so the writer never blocks).
"""

import json
import os
import sys

BLOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research-block.md")

try:
    sys.stdin.read()
except Exception:
    pass

try:
    with open(BLOCK, encoding="utf-8") as fh:
        context = fh.read().strip()
except OSError:
    # Never break subagent spawning because a doc file moved.
    sys.exit(0)

# ensure_ascii=True keeps the payload safe on a cp1252 Windows console.
json.dump(
    {
        "hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": context,
        },
        "suppressOutput": True,
    },
    sys.stdout,
)
