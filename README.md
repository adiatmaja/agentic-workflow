# agentic-workflow

> An orchestrator workflow for AI coding harnesses: the main session doesn't write the code. It
> picks the right agent for each task, runs independent tasks in parallel, and merges what comes
> back.

## Overview

A coding agent working alone does one task at a time, and its context grows with every file it
touches. I run the main session as an **orchestrator** instead, whatever I ask it for. A one-line
"fix this bug" in a fresh session goes to an implementer agent at the right tier, in its own git
worktree. The session then merges the result. A larger feature gets a plan first, and its
independent tasks run side by side, so five of them take about as long as one.

The orchestrator's context stays clean, too. Each agent does its reading, test runs and failed
attempts in its own context and hands back only a short report and the diff. A long session of
fixes stays sharp instead of filling up with files it read three tasks ago.

The pattern isn't tied to one tool. It fits any agentic coding harness that can run subagents,
work in git worktrees and hook into tool calls. This repo holds the rulings the orchestrator
follows, the agent tiers it dispatches to, and the hooks that stop it from drifting back to doing
everything itself. I run it on Claude Code, so the hooks and agent files are written for that
harness, and the rules export to Codex, Gemini CLI and Antigravity.

## The workflow

```
   "fix this bug"                       "build this feature"
   one task, no plan                    plan first: tasks + dependencies
          │                                        │
  ┌───────▼────────────────────────────────────────▼───────────┐
  │  ORCHESTRATOR (main session)                               │
  │  trivial edit -> does it inline                            │
  │  anything else -> picks the tier, dispatches every         │
  │  unblocked task at once, then waits for nothing: the       │
  │  harness wakes it when an agent reports                    │
  └───────┬──────────────────┬──────────────────┬──────────────┘
          ▼                  ▼                  ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ agent  t1   │    │ agent  t2   │    │ agent  t3   │   one worktree each,
   │ sonnet      │    │ sonnet-low  │    │ opus        │   tier picked by
   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘   task complexity
          └─────── only a report + diff ────────┘
                            │
  ┌─────────────────────────▼──────────────────────────────────┐
  │  INTEGRATE, one branch at a time                           │
  │  rebase -> lint + affected tests on the MERGED tree        │
  │         -> fast-forward main -> remove the worktree        │
  └─────────────────────────┬──────────────────────────────────┘
                            ▼
          next wave (if any) starts from the new main ─▶ review
          ─▶ push when the merged gate is green
```

A plan only appears for multi-file features. A fix, a single edit or a question goes straight to
dispatch, because planning skills cost more requests than they save on small work.

There are three rules behind it:

- **The session orchestrates. It doesn't implement.** It writes code itself only for trivial
  edits. Everything else goes to an agent, even a single-file fix. The agent's working context
  stays with the agent; the session keeps only the results.
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

The tier names carry the models I use. In another harness, map them to its own small, mid and
large models.

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

Paste this into your coding agent. It works out which harness it is running in and installs
accordingly.

```text
Install the agentic-workflow configuration from https://github.com/adiatmaja/agentic-workflow into this harness's global setup.

1. Clone the repo into a temporary directory and read its README.md and rules/workflow.md first.
2. Tell me which harness you are (Claude Code, Codex, Gemini CLI, Antigravity or other) and where its global instruction file and config live. Back up each file you will change (append .bak-<date>).
3. Never overwrite a file of mine. Where a file with the same name exists, show me the diff and ask first. Never remove a key or rule I already have.

If you are Claude Code:
4. Copy CLAUDE.md, rules/, hooks/ and agents/ into ~/.claude/, and tools/verify-setup.sh to ~/.claude/verify-setup.sh.
5. Merge settings.example.json into ~/.claude/settings.json: add its permissions, hooks and enabledPlugins entries to mine.
6. Check that `python` and `bash` are on PATH (Git Bash on Windows); the hooks need both. Tell me if the superpowers plugin is missing: plan-dispatch-ruling does nothing without it.
7. Run `bash ~/.claude/verify-setup.sh` and show me every PASS/FAIL line. Fix nothing silently.

If you are another harness:
4. Append CLAUDE.md and every rule without a `paths:` header to your global instruction file. Turn each rule that has `paths:` into an on-demand skill or include in your own format. tools/flatten.awk documents the transforms another harness needs.
5. Read agents/*.md and hooks/*.py. Map each agent to a subagent or profile of yours, picking your own small, mid and large models for the tiers. Where you support tool-call hooks, rewire the same checks; list every check you cannot enforce.
6. Show me what you installed and where, file by file.

Finally, delete the temporary clone and touch nothing else.
```

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
