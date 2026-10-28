#!/usr/bin/env python3
"""PreToolUse(Bash): make `node --test` cheap without losing the count.

Measured 2026-09-19 on a client project's UI test gate (917 tests):
    node --test <glob>                 80.936 B   keeps 'pass N'
    node --test --test-reporter=dot       963 B   dots only, NO count
    redirect to file + grep summary        62 B   keeps the count   <- this

Full output stays on disk, so a failure is still diagnosable; only the summary
plus any failure lines enter the model's context. No pipe is used, so the exit
status is the test runner's own (repo rule: "Never pipe a test command").
"""
import json, re, sys

SKIP = ("--test-reporter", ">", "|")
RE_NODE_TEST = re.compile(r"^\s*node\s+(?:--\S+\s+)*--test\b")


def split_first(cmd: str):
    """Split at the first UNQUOTED `;`, `&&` or newline -> (node_part, sep, rest).

    The redirect must bind to the node run alone: appended to a whole compound
    line (`node --test x; echo $?`) it binds only to the LAST command, and the
    full test output reaches the model uncompacted (seen 2026-09-19, 79 KB).
    """
    q = None
    i = 0
    while i < len(cmd):
        ch = cmd[i]
        if q:
            if ch == "\\" and q == '"':
                i += 2
                continue
            if ch == q:
                q = None
        elif ch == "\\":
            i += 2
            continue
        elif ch in "'\"":
            q = ch
        elif ch in ";\n":
            return cmd[:i], ch, cmd[i + 1:]
        elif cmd.startswith("&&", i):
            return cmd[:i], "&&", cmd[i + 2:]
        i += 1
    return cmd, "", ""


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    ti = data.get("tool_input") or {}
    cmd = ti.get("command")
    if not isinstance(cmd, str) or not RE_NODE_TEST.match(cmd):
        return 0
    head, sep, rest = split_first(cmd)
    if any(tok in head for tok in SKIP):
        return 0

    log = "/tmp/claude-node-test-$$.log"
    new = (
        f'{{ {head.strip()}; }} > "{log}" 2>&1; __rc=$?; '
        f'grep -E "^. (tests|pass|fail|skipped|todo) [0-9]+$" "{log}"; '
        f'if [ $__rc -ne 0 ]; then echo "--- failures (full log: {log}) ---"; '
        f'grep -nE "^not ok |AssertionError|^  Error" "{log}" | head -40; fi; '
        # `(exit $__rc)` restores the runner's status for whatever follows, so a
        # trailing `echo $?` or `&& next` sees the test result, not grep's.
        f'(exit $__rc)'
    )
    if sep:
        new += (" && " if sep == "&&" else "; ") + rest
    ti = dict(ti)
    ti["command"] = new
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecisionReason": "node --test compacted (summary + failures only; full log on disk)",
        "updatedInput": ti,
    }}, sys.stdout)
    return 0

if __name__ == "__main__":
    sys.exit(main())
