# agentic-workflow

> My workflow for AI coding harnesses, in which the main session works like an orchestrator: it
> doesn't write the code. It picks the right agent for each task, runs independent tasks in
> parallel, and merges what comes back.

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

Tell your coding agent:

```text
Install https://github.com/adiatmaja/agentic-workflow by following its INSTALL.md.
```

It clones the repo, works out which harness it's running in, and asks before touching any file of
yours.

## Project structure

```
agentic-workflow/
├── CLAUDE.md               # always-on rulings
├── rules/                  # workflow.md is the orchestrator; the rest are coding rules
├── agents/                 # the tiers: impl-*, review-*, planners, auditors
├── hooks/                  # the guardrails
├── settings.example.json   # permissions and hook wiring
├── INSTALL.md              # install steps your agent follows
└── tools/                  # export, verify, measure-footprint
```

The full rulings, with the measurements behind them, are in
[`rules/workflow.md`](rules/workflow.md).

## License

[MIT](LICENSE)
