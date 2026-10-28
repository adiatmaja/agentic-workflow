#!/usr/bin/env python
"""PreToolUse(Read): refuse an unbounded Read of a large text file, and hand back its outline.

Why a hook and not a rule: a markdown rule loses to habit.
Measured 2026-09-23 over 14 days: 99 % of big-file Reads were already ranged; this closes the rest,
and — more usefully — makes the refusal itself the pointer: the reason lists every section / symbol
with START-END lines (outline.py), so the next call is a precise Read(offset, limit).

Refused when the file is >= READ_GUARD_BYTES (default 40000) and the call has no `limit`, or a
`limit` above READ_GUARD_MAX_LINES (default 400). Images, PDFs, notebooks and binaries pass.
Any failure inside the hook allows the Read: a guard must never be the thing that breaks a session.
"""
import json
import os
import sys

MIN_BYTES = int(os.environ.get('READ_GUARD_BYTES', '40000'))
MAX_LINES = int(os.environ.get('READ_GUARD_MAX_LINES', '400'))
PASS_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.ico', '.pdf', '.ipynb',
            '.gz', '.zip', '.bin', '.db', '.sqlite', '.xlsx', '.docx', '.pptx', '.woff', '.woff2', '.ttf'}
MAX_REASON_ROWS = 120


def deny(reason):
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.exit(0)


def main():
    payload = json.load(sys.stdin)
    if payload.get('tool_name') != 'Read':
        return
    inp = payload.get('tool_input') or {}
    path = inp.get('file_path') or ''
    if not path or os.path.splitext(path)[1].lower() in PASS_EXT or not os.path.isfile(path):
        return
    size = os.path.getsize(path)
    if size < MIN_BYTES:
        return
    limit = inp.get('limit')
    try:
        limit = int(limit) if limit is not None else None
    except (TypeError, ValueError):
        limit = None
    if limit is not None and limit <= MAX_LINES:
        return

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import outline  # noqa: E402  (sibling module, imported only when a refusal is due)

    total, rows = outline.render(path, cap=MAX_REASON_ROWS)
    what = ('no limit' if limit is None else 'limit %d' % limit)
    head = [
        'READ REFUSED (read-guard): %s is %d KB / %d lines and this call has %s. '
        'Read only the range you need: Read(file_path, offset=START, limit=END-START+1), '
        'limit <= %d.' % (path, size // 1024, total, what, MAX_LINES),
    ]
    if rows:
        head.append('Outline (START-END, computed now):')
        body = rows
    else:
        body = ['  (no recognised structure)']
    tail = [
        'Find one symbol: python ~/.claude/hooks/outline.py "%s" <name>   |   '
        'or grep -n "<pattern>" "%s", then Read around the hit.' % (path, path),
    ]
    deny('\n'.join(head + body + tail))


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        pass  # fail open
    sys.exit(0)
