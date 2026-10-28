# Research method — mandatory

Use **`WebSearch`** only to *find* the right URL. Use **`curl` via the Bash tool** to *read* it —
`WebFetch` is denied at the permission layer and must not be attempted.

Verify against primary sources, never from memory. If a fact cannot be verified, report it as
**UNVERIFIED** rather than filling the gap.

**Guessing a URL from memory is still answering from training data.** A guess that 404s is harmless
— you find out. A guess that resolves to a stale page is a silent failure. Search for the current
location before curling a URL you are recalling rather than one you were given.

Most vendor docs are JS-heavy, so fetch then strip tags. On Windows, write the helper to a file —
inline heredocs and `-c` regexes get mangled by shell quoting; print non-ASCII with
`sys.stdout.reconfigure(encoding='utf-8')`, since `python -I` ignores `PYTHONIOENCODING`.

Prefer structured endpoints where they exist: `api.github.com`, `registry.npmjs.org`,
`data.jsdelivr.com`, `pypi.org/pypi/<pkg>/json`.

Never echo a secret — read keys into a shell variable, never print the value.

**If you have not been granted `WebSearch`**, you can still `curl` a URL you were given, and you must
still report unverifiable facts as **UNVERIFIED** rather than answering from training data.
