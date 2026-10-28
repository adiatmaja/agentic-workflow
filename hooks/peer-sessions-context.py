#!/usr/bin/env python
"""SessionStart + SubagentStart hook: make every session and every subagent aware that
other Claude sessions may share this machine and this checkout, and that ListAgents /
SendMessage exist to coordinate with them.

A rule file is not enough: subagents do not reliably inherit ~/.claude rules, and a rule
loses to habit. Edit the prose in peer-sessions-session.md / peer-sessions-subagent.md -
not this file.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCKS = {
    "SessionStart": "peer-sessions-session.md",
    "SubagentStart": "peer-sessions-subagent.md",
}

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

event = payload.get("hook_event_name", "")
if event not in BLOCKS:
    sys.exit(0)

try:
    with open(os.path.join(HERE, BLOCKS[event]), encoding="utf-8") as fh:
        context = fh.read().strip()
except OSError:
    # Never break a session or a spawn because a doc file moved.
    sys.exit(0)

# ensure_ascii=True keeps the payload safe on a cp1252 Windows console.
json.dump(
    {
        "hookSpecificOutput": {"hookEventName": event, "additionalContext": context},
        "suppressOutput": True,
    },
    sys.stdout,
)
