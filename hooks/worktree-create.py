"""WorktreeCreate hook: put every worktree at <workspace>/.worktree/<project>/<name>.

User ruling 2026-10-04: worktrees must not litter the project tree or the workspace root.
<workspace> is the main checkout's parent, <project> its folder name. The worktree branches
from the main checkout's HEAD (the default isolation sometimes started from a stale base).
Copies the gitignored files a checkout cannot run without (.worktreeinclude: one literal
relative path per line; default .env and var/) and junctions node_modules to the main one.
The last stdout line is the path Claude Code enters; everything else goes to stderr.
"""
import json, os, shutil, subprocess, sys


def git(*args, cwd):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def main():
    data = json.load(sys.stdin)
    name = data['name']
    cwd = data.get('cwd') or os.getcwd()
    common = git('rev-parse', '--path-format=absolute', '--git-common-dir', cwd=cwd)
    main_root = os.path.dirname(os.path.normpath(common))
    project = os.path.basename(main_root)
    base_dir = os.path.join(os.path.dirname(main_root), '.worktree', project)
    path = os.path.normpath(os.path.join(base_dir, name))
    os.makedirs(base_dir, exist_ok=True)
    head = git('rev-parse', 'HEAD', cwd=main_root)
    subprocess.run(['git', 'worktree', 'add', '-b', 'worktree-' + name, path, head],
                   cwd=main_root, check=True, stdout=sys.stderr, stderr=sys.stderr)

    meta = os.path.join(base_dir, '.meta')
    os.makedirs(meta, exist_ok=True)
    with open(os.path.join(meta, name + '.base'), 'w') as f:
        f.write(head)

    include = ['.env', 'var']
    inc_file = os.path.join(main_root, '.worktreeinclude')
    if os.path.isfile(inc_file):
        include = [l.strip().rstrip('/\\') for l in open(inc_file, encoding='utf-8')
                   if l.strip() and not l.lstrip().startswith('#')]
    for rel in include:
        src, dst = os.path.join(main_root, rel), os.path.join(path, rel)
        if os.path.isdir(src) and not os.path.exists(dst):
            shutil.copytree(src, dst)
        elif os.path.isfile(src) and not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

    nm = os.path.join(main_root, 'node_modules')
    if os.path.isdir(nm) and not os.path.exists(os.path.join(path, 'node_modules')):
        if os.name == 'nt':
            subprocess.run(['cmd', '/c', 'mklink', '/J', os.path.join(path, 'node_modules'), nm],
                           stdout=sys.stderr, stderr=sys.stderr)
        else:
            os.symlink(nm, os.path.join(path, 'node_modules'))

    print(path.replace('\\', '/'))


if __name__ == '__main__':
    main()
