# Installing agentic-workflow

These steps are for the coding agent doing the install. Read `README.md` and `rules/workflow.md`
first.

## Every harness

1. Work from a temporary clone of <https://github.com/adiatmaja/agentic-workflow>.
2. Tell the user which harness you are (Claude Code, Codex, Gemini CLI, Antigravity or other) and
   where its global instruction file and config live. Back up each file you will change (append
   `.bak-<date>`).
3. Never overwrite a file of the user's. Where a file with the same name exists, show the user the
   diff and ask first. Never remove a key or rule the user already has.

## If you are Claude Code

4. Copy `CLAUDE.md`, `rules/`, `hooks/` and `agents/` into `~/.claude/`, and
   `tools/verify-setup.sh` to `~/.claude/verify-setup.sh`.
5. Merge `settings.example.json` into `~/.claude/settings.json`: add its `permissions`, `hooks`
   and `enabledPlugins` entries to theirs.
6. Check that `python` and `bash` are on `PATH` (Git Bash on Windows); the hooks need both. Tell
   the user if the superpowers plugin is missing: `plan-dispatch-ruling` does nothing without it.
7. Run `bash ~/.claude/verify-setup.sh` and show the user every PASS/FAIL line. Fix nothing
   silently.

## If you are another harness

4. Append `CLAUDE.md` and every rule without a `paths:` header to your global instruction file.
   Turn each rule that has `paths:` into an on-demand skill or include in your own format.
   `tools/flatten.awk` documents the transforms another harness needs.
5. Read `agents/*.md` and `hooks/*.py`. Map each agent to a subagent or profile of yours, picking
   your own small, mid and large models for the tiers. Where you support tool-call hooks, rewire
   the same checks; list every check you cannot enforce.
6. Show the user what you installed and where, file by file.

## Finally

Delete the temporary clone and touch nothing else.
