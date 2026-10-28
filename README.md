# agentic-workflow

> My main coding session doesn't write the code. It picks the right agent for each task, runs
> independent tasks in parallel, and merges what comes back.

## Overview

A coding agent working alone does one task at a time, and its context grows with every file it
touches. I run the main session as an **orchestrator** instead, whatever I ask it for. A one-line
"fix this bug" in a fresh session goes to an implementer agent at the right tier, in its own git
worktree. The session then merges the result. A larger feature gets a plan first, and its
independent tasks run side by side, so five of them take about as long as one.

This repo is the configuration that makes that work day to day: the rulings the orchestrator
follows, the agent tiers it dispatches to, and the hooks that stop it from drifting back to doing
everything itself.

## The workflow

```
   "fix this bug"                       "build this feature"
   one task, no plan                    plan first: tasks + dependencies
          │                                        │
  ┌───────▼────────────────────────────────────────▼───────────┐
  │  ORCHESTRATOR (main session)                               │
  │  trivial edit ─▶ does it inline                            │
  │  anything else ─▶ picks the tier, dispatches every         │
  │  unblocked task at once, then waits for nothing: the       │
  │  harness wakes it when an agent reports                    │
  └───────┬──────────────────┬──────────────────┬──────────────┘
          ▼                  ▼                  ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ agent  t1   │    │ agent  t2   │    │ agent  t3   │   one worktree each,
   │ sonnet      │    │ sonnet-low  │    │ opus        │   tier picked by
   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘   task complexity
          └───────── short report + diff ───────┘
                            │
  ┌─────────────────────────▼──────────────────────────────────┐
  │  INTEGRATE, one branch at a time                           │
  │  rebase ─▶ lint + affected tests on the MERGED tree        │
  │         ─▶ fast-forward main ─▶ remove the worktree        │
  └─────────────────────────┬──────────────────────────────────┘
                            ▼
          next wave (if any) starts from the new main ─▶ review
          ─▶ push when the merged gate is green
```

A plan only appears for multi-file features. A fix, a single edit or a question goes straight to
dispatch, because planning skills cost more requests than they save on small work.

There are three rules behind it:

- **The session orchestrates. It doesn't implement.** It writes code itself only for trivial
  edits. Everything else goes to an agent, even a single-file fix, which keeps the session's own
  context small however long the session runs.
- **Parallel by default.** Any task that doesn't need another task's output runs now, even two
  sections of the same file. Conflicts get resolved at integration, not during the work.
- **Each task gets the cheapest tier that can do it.** The tier depends on how complex the task
  is, never on how urgent it is. Model and effort live in the agent file, not in the dispatch.

| Task | Agent |
|---|---|
| Docs only | `impl-haiku-medium` |
| Mechanical, fully specified in the brief | `impl-sonnet-low` |
| Well-scoped code (the default) | `impl-sonnet-medium` |
| UI work, open-ended tasks, load-bearing invariants | `impl-opus-medium` / `-high` |
| Review the diff · re-check after fixes | `review-first` · `review-recheck` |

## Guardrails

Written rules alone didn't hold, so hooks enforce the ones that matter for the loop:

| Hook | Stops |
|---|---|
| `agent-dispatch-guard.py` | dispatching a built-in agent, overriding `model`, or running an implementer outside a worktree |
| `worktree-create.py` / `worktree-remove.py` | worktrees landing in the wrong place, or removal deleting through a `node_modules` junction |
| `plan-dispatch-ruling.py` | a planning skill forgetting the dispatch rulings |
| `read-guard.py` | the orchestrator reading a whole large file instead of a range |
| `peer-sessions-context.py` | two sessions in one checkout colliding on the index, stash or ports |

Every guard fails open. If a hook hits an internal error, it allows the call and says so.

## What it costs

Parallelism trades machine resources and tokens for wall-clock time. Measured on a 16 GB laptop:
each worktree takes about 1 GB of disk, which is reclaimed after the merge, and each session about
400 MB of RAM. Subagents add tokens, not processes. Disk runs out first, so worktrees get removed
as soon as they're merged.

## Quick start

```bash
git clone https://github.com/adiatmaja/agentic-workflow && cd agentic-workflow
cp CLAUDE.md ~/.claude/ && cp -r rules hooks agents ~/.claude/
# merge settings.example.json into ~/.claude/settings.json (keep your own keys), then:
bash tools/verify-setup.sh        # PASS / FAIL per check
```

Hooks need `python` and `bash` (Git Bash on Windows). `plan-dispatch-ruling` expects the
[superpowers](https://github.com/obra/superpowers) plugin and does nothing without it.

<details>
<summary>Or let your agent install it</summary>

```text
Install the agentic-workflow configuration from https://github.com/adiatmaja/agentic-workflow into my Claude Code setup.

1. Clone it into a temporary directory. Read its README.md first.
2. Back up ~/.claude/CLAUDE.md and ~/.claude/settings.json if they exist (append .bak-<date>).
3. Copy CLAUDE.md, rules/, hooks/ and agents/ into ~/.claude/. If a file with the same name already exists there, show me a diff and ask before overwriting.
4. Merge settings.example.json into ~/.claude/settings.json: add its permissions, hooks and enabledPlugins entries to mine without removing any key I already have. Never overwrite the file.
5. Run `bash tools/verify-setup.sh` and paste every PASS/FAIL line to me. Fix nothing silently: if a line fails, tell me why.
6. Remove the temporary clone. Do not touch any other path under ~/.claude.
```

</details>

**Other harnesses.** The rules are plain prose and port anywhere. `tools/export-config.sh --target
codex,gemini,agy` writes an installer for each target, and `--flat` produces one paste-able file.
Hooks and agents are Claude Code only.

## Project structure

```
agentic-workflow/
├── CLAUDE.md               # always-on rulings
├── rules/                  # workflow.md is the orchestrator; the rest are coding rules
├── agents/                 # the tiers: impl-*, review-*, planners, auditors
├── hooks/                  # the guardrails
├── settings.example.json   # permissions and hook wiring
└── tools/                  # export, verify, measure-footprint
```

The full rulings, with the measurements behind them, are in
[`rules/workflow.md`](rules/workflow.md).

## License

[MIT](LICENSE)
