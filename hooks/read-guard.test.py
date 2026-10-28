#!/usr/bin/env python
"""Self-test for read-guard.py + outline.py. Exit 0 = every case behaves; run by verify-token-setup.sh.

Uses fixture files it writes itself, so it runs from any project and cannot pass vacuously on a
machine where some repo file moved.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, 'read-guard.py')
sys.path.insert(0, HERE)
import outline  # noqa: E402

tmp = tempfile.mkdtemp()
big_js = os.path.join(tmp, 'big.js')
with open(big_js, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('(function () {\n')
    for i in range(700):
        fh.write('  /* ══ area %d ══ */\n' % i if i % 100 == 0 else '')
        fh.write('  // a long explanatory comment line that pads the file the way this repo does\n' * 2)
        fh.write('  function f%d(a) {\n    if (a) {\n      return %d;\n    }\n    return 0;\n  }\n' % (i, i))
        fh.write('  function one%d(x) { return x; }\n' % i)
    fh.write('})();\n')
small = os.path.join(tmp, 'small.md')
with open(small, 'w', encoding='utf-8') as fh:
    fh.write('# tiny\n')
png = os.path.join(tmp, 'shot.png')
with open(png, 'wb') as fh:
    fh.write(b'\x89PNG' + b'\0' * 60000)


def run(inp, tool='Read'):
    p = subprocess.run([sys.executable, GUARD], input=json.dumps({'tool_name': tool, 'tool_input': inp}),
                       capture_output=True, text=True, encoding='utf-8')
    if not p.stdout.strip():
        return 'ALLOW', p.returncode, ''
    o = json.loads(p.stdout)['hookSpecificOutput']
    return o['permissionDecision'].upper(), p.returncode, o['permissionDecisionReason']


cases = [
    ('big, no limit', 'DENY', {'file_path': big_js}),
    ('big, limit 100', 'ALLOW', {'file_path': big_js, 'offset': 40, 'limit': 100}),
    ('big, limit 2000', 'DENY', {'file_path': big_js, 'limit': 2000}),
    ('big, offset only', 'DENY', {'file_path': big_js, 'offset': 500}),
    ('big, forward-slash path', 'DENY', {'file_path': big_js.replace('\\', '/')}),
    ('big, garbage limit', 'DENY', {'file_path': big_js, 'limit': 'x'}),
    ('small file', 'ALLOW', {'file_path': small}),
    ('image', 'ALLOW', {'file_path': png}),
    ('missing file', 'ALLOW', {'file_path': os.path.join(tmp, 'nope.js')}),
]
bad = 0
for name, want, inp in cases:
    got, rc, _ = run(inp)
    ok = got == want and rc == 0
    bad += not ok
    print('ok  ' if ok else 'FAIL', name, '->', got)
got, _, _ = run({'command': 'ls'}, tool='Bash')
bad += got != 'ALLOW'
print('ok  ' if got == 'ALLOW' else 'FAIL', 'non-Read tool ->', got)

# The refusal must carry usable ranges, and every function range must end on its closing brace.
_, _, reason = run({'file_path': big_js})
has_ranges = 'L' in reason and '== area 0 ==' in reason
bad += not has_ranges
print('ok  ' if has_ranges else 'FAIL', 'refusal carries the outline (%d B)' % len(reason))
lines = open(big_js, encoding='utf-8').read().split('\n')
_, ents = outline.outline(big_js)
fns = [e for e in ents if e[2].startswith('function ')]
exact = sum(1 for s, e, _, _ in fns if (e == s and lines[s - 1].rstrip().endswith('}')) or lines[e - 1].strip() == '}')
ok = fns and exact == len(fns) and len(fns) == 1400
bad += not ok
print('ok  ' if ok else 'FAIL', 'function ranges exact: %d/%d' % (exact, len(fns)))
sys.exit(1 if bad else 0)
