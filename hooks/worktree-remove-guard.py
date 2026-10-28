"""PreToolUse guard (Bash|PowerShell): refuse `git worktree remove` while a target worktree
still has a top-level junction or symlink (node_modules).

On Windows `git worktree remove --force` deletes THROUGH a junction; it has emptied the main
checkout's node_modules four times (2026-09-14, 10-04, 10-13, 10-14), each time after an unlink
step failed silently. A rule in memory did not hold, so this refuses the removal itself.
A target the hook cannot resolve (a shell variable, a loop) is checked against EVERY linked
worktree of the repository, so a loop cannot slip past.

It also refuses while a target holds untracked review artefacts (screenshots, PDFs, videos) that
the main checkout lacks at the same path: removing the worktree deletes them, and an agent's
evidence stills were lost that way on 2026-10-20.
"""
import json, os, re, shlex, subprocess, sys


def is_link(p):
    # os.path.isjunction exists only from Python 3.12; a junction is a reparse point.
    try:
        st = os.lstat(p)
    except OSError:
        return False
    return os.path.islink(p) or bool(getattr(st, 'st_file_attributes', 0) & 0x400)


def links_in(wt):
    # Only a link to a DIRECTORY is deleted through; a file link (the tracked AGENTS.md -> CLAUDE.md) is not.
    try:
        return [os.path.join(wt, e) for e in os.listdir(wt)
                if is_link(os.path.join(wt, e)) and os.path.isdir(os.path.join(wt, e))]
    except OSError:
        return []


ARTEFACT = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.pdf', '.mp4', '.webm')


def unsaved_artefacts(wt, main_root):
    # Untracked, not ignored: ignored files are by definition disposable, and listing them would walk node_modules.
    out = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], cwd=wt,
                         capture_output=True, text=True).stdout
    return [os.path.join(wt, f) for f in out.splitlines()
            if f.lower().endswith(ARTEFACT) and not os.path.exists(os.path.join(main_root, f))]


def main_checkout(cwd):
    out = subprocess.run(['git', 'worktree', 'list', '--porcelain'], cwd=cwd,
                         capture_output=True, text=True).stdout
    first = next((l for l in out.splitlines() if l.startswith('worktree ')), '')
    return first[len('worktree '):]


def all_worktrees(cwd):
    out = subprocess.run(['git', 'worktree', 'list', '--porcelain'], cwd=cwd,
                         capture_output=True, text=True).stdout
    paths = [l[len('worktree '):] for l in out.splitlines() if l.startswith('worktree ')]
    return paths[1:]  # the first entry is the main checkout


def targets(cmd):
    """Path arguments after each `worktree remove`; None marks one the hook cannot resolve."""
    found = []
    for m in re.finditer(r'worktree\s+remove\b(.*?)(?:&&|\|\||;|\||\n|$)', cmd):
        try:
            toks = shlex.split(m.group(1), posix=True)
        except ValueError:
            found.append(None)
            continue
        paths = [t for t in toks if not t.startswith('-')]
        if not paths:
            found.append(None)
        for t in paths:
            found.append(None if re.search(r'[$`%*?]', t) else t)
    return found


def main():
    data = json.load(sys.stdin)
    cmd = (data.get('tool_input') or {}).get('command') or ''
    if not re.search(r'worktree\s+remove', cmd):
        return
    cwd = data.get('cwd') or os.getcwd()
    offenders, unsaved = [], []
    main_root = main_checkout(cwd)
    for t in targets(cmd):
        if t is not None and re.match(r'^/[a-zA-Z]/', t):
            t = t[1] + ':' + t[2:]  # Git Bash /c/... -> C:/...; Windows Python cannot resolve the POSIX form
        wts = all_worktrees(cwd) if t is None else [os.path.normpath(t if os.path.isabs(t) else os.path.join(cwd, t))]
        for wt in wts:
            offenders += links_in(wt)
            if main_root and os.path.isdir(wt):
                unsaved += unsaved_artefacts(wt, main_root)
    offenders, unsaved = sorted(set(offenders)), sorted(set(unsaved))
    if not offenders and not unsaved:
        return
    parts = []
    if offenders:
        parts.append('`git worktree remove` would delete THROUGH these links and empty their '
                     'targets (main node_modules was emptied 4 times):\n  ' + '\n  '.join(offenders) +
                     '\nUnlink each first and confirm it is gone: '
                     'python -c "import os,sys; os.rmdir(sys.argv[1])" <path>')
    if unsaved:
        shown = unsaved[:15] + ([f'... and {len(unsaved) - 15} more'] if len(unsaved) > 15 else [])
        parts.append('these untracked artefacts exist only in the worktree and would be deleted with it:\n  ' +
                     '\n  '.join(shown) + '\nCopy the ones you need into the main checkout (`cp -r <wt>/<dir>/. '
                     '<main>/<dir>/`) or delete them on purpose, then retry.')
    reason = 'Refused: ' + '\n\n'.join(parts)
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',
                                             'permissionDecision': 'deny',
                                             'permissionDecisionReason': reason}}))


if __name__ == '__main__':
    main()
