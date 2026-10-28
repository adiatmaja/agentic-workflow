#!/usr/bin/env python
"""PreToolUse/Bash guard: block git commits authored with PowerShell here-string
syntax (@'...'@) when run through the Bash tool.

Bash does not interpret @' / '@ as here-string delimiters, so the bare @ lines
leak into the commit message body. Seen leak into a real commit message once.

Emits a PreToolUse deny decision (exit 0 + JSON) only when a git commit command
contains the offending delimiters; otherwise stays silent and allows the call.
"""

import json
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # malformed input: don't block

    cmd = payload.get("tool_input", {}).get("command", "") or ""

    if "git commit" in cmd and ("@'" in cmd or "'@" in cmd):
        reason = (
            "Blocked: this git commit uses PowerShell here-string syntax "
            "(@quote ... quote@) but runs through the Bash tool, which does not "
            "interpret those delimiters. The bare @ lines will leak into the "
            "commit message. Use a bash heredoc instead: "
            "git commit -F - <<EOF / message / EOF, or repeated -m flags."
        )
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
