#!/usr/bin/env python
"""PostToolUse(Edit|Write|MultiEdit): flag newly ADDED code comments that break the comment rule.

Rule: ~/.claude/rules/code-comments.md. A markdown rule loses to habit, so this hook enforces it.
Only lines the edit adds are checked. Lines carried over from old_string were already there.
Flags: a date or SHA inside a comment, or one comment block longer than MAX_BLOCK lines.
It never undoes the edit. The reason goes back to the model, which rewrites the comment.
Any failure inside the hook stays silent: a guard must never break a session.
Off switch: COMMENT_GUARD=off.
"""
import json
import os
import re
import sys
from collections import Counter

MAX_BLOCK = int(os.environ.get('COMMENT_GUARD_MAX_BLOCK', '10'))
SLASH_EXT = {'.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.php', '.cs', '.java', '.go', '.rs',
             '.css', '.scss', '.html', '.htm', '.vue', '.svelte'}
HASH_EXT = {'.py', '.sh', '.rb', '.ps1', '.php'}
SQL_EXT = {'.sql'}

DATE_RE = re.compile(r'\b20\d\d-[01]\d-[0-3]\d\b')
SHA_RE = re.compile(r'(?<![#\w])(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b')
TRAILING_SLASH_RE = re.compile(r'(?<![:\'"\\\w/])//\s.*$')


def comment_text(line, ext, in_block):
    """Return (comment text or None, still inside a /* */ or <!-- --> block)."""
    s = line.strip()
    if in_block:
        closed = '*/' in s or '-->' in s
        return s, not closed
    if ext in SLASH_EXT:
        if s.startswith('/*') or s.startswith('<!--'):
            closed = ('*/' in s[2:]) or ('-->' in s[4:])
            return s, not closed
        if s.startswith('//') or s.startswith('* ') or s == '*' or s.startswith('*/'):
            return s, False
        m = TRAILING_SLASH_RE.search(line)
        if m:
            return m.group(0), False
    if ext in HASH_EXT and s.startswith('#') and not s.startswith('#!'):
        return s, False
    if ext in SQL_EXT and s.startswith('--'):
        return s, False
    return None, False


def added_lines(old, new):
    """Lines of `new` not already present in `old`, as a multiset difference, in order."""
    have = Counter(l.strip() for l in old.splitlines())
    out = []
    for l in new.splitlines():
        k = l.strip()
        if have[k] > 0:
            have[k] -= 1
            out.append(None)
        else:
            out.append(l)
    return out


def check(lines, ext):
    problems = []
    run = 0
    run_start = None
    in_block = False
    for i, l in enumerate(lines):
        if l is None:
            run, run_start = 0, None
            continue
        text, in_block = comment_text(l, ext, in_block)
        if text is None:
            run, run_start = 0, None
            continue
        run += 1
        run_start = run_start if run_start is not None else i
        if DATE_RE.search(text):
            problems.append(f'date in a comment: "{text[:90]}"')
        elif SHA_RE.search(text):
            problems.append(f'commit SHA in a comment: "{text[:90]}"')
        if run == MAX_BLOCK + 1:
            problems.append(f'comment block over {MAX_BLOCK} lines (starting "{lines[run_start].strip()[:70]}")')
    return problems


def main():
    if os.environ.get('COMMENT_GUARD', '').lower() == 'off':
        return
    payload = json.load(sys.stdin)
    tool = payload.get('tool_name')
    ti = payload.get('tool_input') or {}
    path = ti.get('file_path') or ''
    ext = os.path.splitext(path)[1].lower()
    if ext not in SLASH_EXT | HASH_EXT | SQL_EXT:
        return
    if tool == 'Write':
        pairs = [('', ti.get('content') or '')]
    elif tool == 'Edit':
        pairs = [(ti.get('old_string') or '', ti.get('new_string') or '')]
    elif tool == 'MultiEdit':
        pairs = [(e.get('old_string') or '', e.get('new_string') or '') for e in ti.get('edits') or []]
    else:
        return
    problems = []
    for old, new in pairs:
        problems += check(added_lines(old, new), ext)
    if not problems:
        return
    shown = problems[:8]
    more = f'\n  (+{len(problems) - 8} more)' if len(problems) > 8 else ''
    reason = (
        f'comment-guard: the edit to {os.path.basename(path)} added comments that break '
        '~/.claude/rules/code-comments.md:\n  - ' + '\n  - '.join(shown) + more +
        '\nFix it now: move history (dates, SHAs, what-was-fixed) to the commit message, move '
        'rulings and reasoning to docs/ with a one-line pointer, and cut blocks to <= 2 lines '
        f'inline or <= {MAX_BLOCK} lines for a header.'
    )
    json.dump({'decision': 'block', 'reason': reason}, sys.stdout)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
