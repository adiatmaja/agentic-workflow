"""WorktreeRemove hook for worktrees made by worktree-create.py.

Removes the worktree only when it is UNCHANGED: HEAD still equals the recorded base and
no tracked or untracked-but-not-ignored change exists. Anything else is kept on disk for
the session to merge, and the hook still exits 0 so the agent's finish is not an error.
Junctions and symlinks at the top level (node_modules) are unlinked FIRST: on Windows
`git worktree remove --force` deletes THROUGH a junction and has emptied the main
checkout's node_modules before.
"""
import json, os, subprocess, sys


def run(*args, cwd):
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)


def is_link(p):
    # os.path.isjunction exists only from Python 3.12; a junction is a reparse point.
    try:
        st = os.lstat(p)
    except OSError:
        return False
    return os.path.islink(p) or bool(getattr(st, 'st_file_attributes', 0) & 0x400)


def main():
    data = json.load(sys.stdin)
    path = os.path.normpath(data['worktree_path'])
    if not os.path.isdir(path):
        return
    name = os.path.basename(path)
    meta = os.path.join(os.path.dirname(path), '.meta', name + '.base')
    base = open(meta).read().strip() if os.path.isfile(meta) else None
    head = run('git', 'rev-parse', 'HEAD', cwd=path).stdout.strip()
    dirty = run('git', 'status', '--porcelain', cwd=path).stdout.strip()
    if not base or head != base or dirty:
        print(f'worktree kept: {path} (changed or unknown base)', file=sys.stderr)
        return

    for entry in os.listdir(path):
        p = os.path.join(path, entry)
        if is_link(p):
            try:
                os.rmdir(p)
            except OSError:
                os.unlink(p)
            if os.path.lexists(p):
                print(f'worktree kept: could not unlink {p}', file=sys.stderr)
                return
    common = run('git', 'rev-parse', '--path-format=absolute', '--git-common-dir', cwd=path).stdout.strip()
    main_root = os.path.dirname(os.path.normpath(common))
    run('git', 'worktree', 'remove', '--force', path, cwd=main_root)
    run('git', 'branch', '-D', 'worktree-' + name, cwd=main_root)
    if os.path.isfile(meta):
        os.remove(meta)


if __name__ == '__main__':
    main()
