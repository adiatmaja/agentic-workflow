#!/usr/bin/env python
"""Inject the owner's plan-dispatch ruling whenever a planning/executing skill loads.

The ruling was first written into the superpowers skill files, but those live in the
plugin CACHE and a plugin update overwrites them. This hook carries it instead, on both
paths a skill can load by:

  PostToolUse (matcher: Skill)  - Claude called the Skill tool
  UserPromptExpansion           - the user typed /<skill> (bypasses the Skill tool)

Edit the prose in plan-dispatch-ruling.md - not this file.
"""

import json
import os
import sys

SKILLS = ("writing-plans", "subagent-driven-development", "executing-plans", "dispatching-parallel-agents", "using-git-worktrees")
BLOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan-dispatch-ruling.md")

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

event = payload.get("hook_event_name", "")
if event == "PostToolUse":
    name = str((payload.get("tool_input") or {}).get("skill", ""))
elif event == "UserPromptExpansion":
    name = str(payload.get("command_name", ""))
else:
    sys.exit(0)

# Plugin skills arrive as "superpowers:writing-plans"; match the last segment.
if name.split(":")[-1].strip().lstrip("/") not in SKILLS:
    sys.exit(0)

try:
    with open(BLOCK, encoding="utf-8") as fh:
        context = fh.read().strip()
except OSError:
    # Never break a skill load because a doc file moved.
    sys.exit(0)

# ensure_ascii=True keeps the payload safe on a cp1252 Windows console.
json.dump(
    {
        "hookSpecificOutput": {"hookEventName": event, "additionalContext": context},
        "suppressOutput": True,
    },
    sys.stdout,
)
