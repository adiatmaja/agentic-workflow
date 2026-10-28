#!/usr/bin/env python
"""Line-range outline of a large text file: every section / symbol with its START-END lines.

Two callers:
  - read-guard.py puts this outline into the refusal of an unbounded Read, so the model's next
    call is a precise Read(offset, limit) instead of the whole file.
  - The model itself, from Bash, to jump straight to one symbol:
        python ~/.claude/hooks/outline.py <file>            # the full outline
        python ~/.claude/hooks/outline.py <file> <query>    # only entries whose name contains query

Computed from the file at call time, so it cannot go stale the way a committed index can.
Ranges are heuristic (indent-matched closing brace, else the next entry's start - 1): read the
range, and widen it by a few lines if the tail looks cut.
"""
import os
import re
import sys

MAX_ENTRIES = 120

JS_EXT = {'.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx'}
MD_EXT = {'.md', '.markdown'}

BANNER = re.compile(r'^\s*/\*+\s*[═=─#*-]{2,}\s*(.+?)\s*[═=─#*-]{2,}\s*\*+/\s*$')
JS_PATTERNS = [
    ('fn', re.compile(r'^(\s*)(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*\(')),
    ('const', re.compile(r'^(\s*)(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>|\{\s*$|\[\s*$)')),
    ('class', re.compile(r'^(\s*)(?:export\s+)?class\s+([A-Za-z_$][\w$]*)')),
    ('test', re.compile(r'''^(\s*)((?:test|it|describe)(?:\.\w+)?\(\s*(['"`])(.{1,90}?)\3)''')),
    ('method', re.compile(r'^(\s*)([A-Za-z_$][\w$]*)\s*[:=]\s*(?:async\s+)?function\b')),
]
PHP_FN = re.compile(r'^(\s*)(?:(?:public|private|protected|static|final|abstract)\s+)*function\s+&?([A-Za-z_]\w*)\s*\(')
MD_HEAD = re.compile(r'^(#{1,4})\s+(.+?)\s*#*\s*$')
HTML_TAG = re.compile(r'^\s*<(section|main|nav|aside|header|footer|dialog|template|script|style|h1|h2|h3)\b([^>]*)>', re.I)
HTML_ID = re.compile(r'\b(?:id|class|src)\s*=\s*["\']([^"\']{1,60})')
CSS_MEDIA = re.compile(r'^(\s*)(@media[^{]*|@container[^{]*|@layer[^{]*)\{')
JSON_KEY = re.compile(r'^(\s{2}|\t)"([^"]{1,80})"\s*:')


def _close_by_indent(lines, start, indent):
    """First line after start that sits at the same indent and opens with a closer."""
    pad = ' ' * indent
    for j in range(start + 1, len(lines)):
        ln = lines[j]
        if ln.startswith(pad) and ln[indent:indent + 1] in ('}', ']', ')') and (indent == 0 or not ln[indent - 1:indent].strip() and not ln[:indent].strip()):
            return j
    return None


def _fill_ends(entries, total):
    """Entries with no end get the next entry's start - 1 (or EOF)."""
    starts = sorted(e[0] for e in entries)
    banners = sorted(e[0] for e in entries if e[2].startswith('== '))
    out = []
    for s, e, label, depth in entries:
        if e is None:
            # A banner spans its whole area, up to the next banner; anything else to the next entry.
            pool = banners if label.startswith('== ') else starts
            nxt = next((x for x in pool if x > s), total + 1)
            e = nxt - 1
        out.append((s, max(e, s), label, depth))
    return out


def outline_md(lines):
    ents = []
    fence = False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith('```'):
            fence = not fence
            continue
        if fence:
            continue
        m = MD_HEAD.match(ln)
        if m:
            ents.append([i + 1, None, '#' * len(m.group(1)) + ' ' + m.group(2)[:100], len(m.group(1))])
    # end = line before the next heading of the same or higher level
    for k, e in enumerate(ents):
        for f in ents[k + 1:]:
            if f[3] <= e[3]:
                e[1] = f[0] - 1
                break
        else:
            e[1] = len(lines)
    return [tuple(e) for e in ents]


def outline_js(lines):
    ents = []
    for i, ln in enumerate(lines):
        b = BANNER.match(ln)
        if b:
            ents.append((i + 1, None, '== ' + b.group(1)[:90] + ' ==', 0))
            continue
        for kind, rx in JS_PATTERNS:
            m = rx.match(ln)
            if not m:
                continue
            indent = len(m.group(1).expandtabs(2))
            name = m.group(4) if kind == 'test' else m.group(2)
            label = {'fn': 'function ', 'const': '', 'class': 'class ', 'test': m.group(2).split('(')[0] + ' ', 'method': ''}[kind] + name
            end = None
            opens, closes = ln.count('{'), ln.count('}')
            if (opens and opens == closes) or (not opens and ln.rstrip().endswith(';')):  # one-line body
                end = i + 1
            else:
                j = _close_by_indent(lines, i, indent)
                if j is not None:
                    end = j + 1
            ents.append((i + 1, end, label, indent))
            break
    return ents


def outline_php(lines):
    ents = []
    for i, ln in enumerate(lines):
        m = PHP_FN.match(ln)
        if m:
            indent = len(m.group(1))
            j = _close_by_indent(lines, i, indent)
            ents.append((i + 1, j + 1 if j is not None else None, 'function ' + m.group(2), indent))
    return ents


def outline_html(lines):
    ents = []
    for i, ln in enumerate(lines):
        m = HTML_TAG.match(ln)
        if not m:
            continue
        tag = m.group(1).lower()
        ident = HTML_ID.search(m.group(2) or '')
        label = '<' + tag + ('#' + ident.group(1) if ident else '') + '>'
        end = None
        closer = '</' + tag
        for j in range(i, len(lines)):
            if closer in lines[j].lower():
                end = j + 1
                break
        ents.append((i + 1, end, label, 0 if tag in ('script', 'style', 'main', 'section') else 2))
    return ents


def outline_css(lines):
    ents = []
    for i, ln in enumerate(lines):
        b = BANNER.match(ln)
        if b:
            ents.append((i + 1, None, '== ' + b.group(1)[:90] + ' ==', 0))
            continue
        m = CSS_MEDIA.match(ln)
        if m:
            j = _close_by_indent(lines, i, len(m.group(1)))
            ents.append((i + 1, j + 1 if j is not None else None, m.group(2).strip()[:90], 2))
    return ents


def outline_json(lines):
    ents = [(i + 1, None, '"' + m.group(2) + '"', 0) for i, ln in enumerate(lines) for m in [JSON_KEY.match(ln)] if m]
    return ents


def outline(path):
    """(total_lines, [(start, end, label, depth)]) — empty list when no structure is recognised."""
    ext = os.path.splitext(path)[1].lower()
    with open(path, encoding='utf-8', errors='replace') as fh:
        lines = fh.read().split('\n')
    if ext in MD_EXT:
        ents = outline_md(lines)
    elif ext in JS_EXT:
        ents = outline_js(lines)
    elif ext == '.php':
        ents = outline_php(lines)
    elif ext in ('.html', '.htm'):
        ents = outline_html(lines)
    elif ext == '.css':
        ents = outline_css(lines)
    elif ext == '.json':
        ents = outline_json(lines)
    else:
        ents = []
    return len(lines), _fill_ends(ents, len(lines))


def render(path, query=None, cap=MAX_ENTRIES):
    total, ents = outline(path)
    hidden = 0
    if query:
        q = query.lower()
        ents = [e for e in ents if q in e[2].lower()]
    elif len(ents) > cap:
        # Too many to show: keep the deepest indent level whose entries still fit, else truncate.
        shown = ents[:cap]
        for d in sorted({e[3] for e in ents}):
            keep = [e for e in ents if e[3] <= d]
            if len(keep) > cap:
                break
            shown = keep
        hidden = len(ents) - len(shown)
        ents = shown
    rows = ['  L%d-L%d%s%s' % (s, e, ' ' * max(1, 14 - len('L%d-L%d' % (s, e))), ('  ' * min(d // 2, 3)) + label)
            for s, e, label, d in ents]
    if query is None and hidden > 0:
        rows.append('  ... %d deeper entries (functions, tests) hidden - pass a name to list them' % hidden)
    return total, rows


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    query = argv[2] if len(argv) > 2 else None
    total, rows = render(path, query, cap=10 ** 6 if query else MAX_ENTRIES)
    print('%s — %d lines, %d KB' % (path, total, os.path.getsize(path) // 1024))
    print('\n'.join(rows) if rows else '  (no recognised structure — use grep -n "<pattern>" then Read with offset/limit)')
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv))
