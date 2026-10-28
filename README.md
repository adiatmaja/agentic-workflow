# agentic-workflow

> The rules an agent reads, the hooks that enforce them when reading is not enough, and the agent
> tiers that keep the bill proportional. A working configuration for agentic coding harnesses.

## Overview

This is my working configuration for agentic coding, published as it runs day to day on my RAG,
LLM fine-tuning, forecasting and agent-tooling projects. Client and project names are removed; the
rulings, measurements and hooks are the ones in use.

It rests on one measured fact: **every turn re-reads the whole context, so the bill is
requests × context size.** Everything here cuts requests, cuts context, or refuses the action a rule
alone failed to stop.

The prose (`CLAUDE.md`, `rules/`) is harness-agnostic and ports to Codex, Gemini CLI and Antigravity.
The machinery (`hooks/`, `agents/`, `settings.example.json`) uses Claude Code's hook and subagent
protocol.

## What loads when

```
  session start                  file opened                       tool call
  ─────────────                  ───────────                       ─────────
  CLAUDE.md ─────────────┐       rules with paths: ──┐             PreToolUse ──▶ hook ──▶ allow / deny / rewrite
  rules/workflow.md ─────┼─▶ ctx   *.py ───▶ python rules         PostToolUse ─▶ comment-guard, plan-dispatch-ruling
  rules/indonesian-copy.md        *.html ─▶ ui-ux, visualisation   SubagentStart ▶ research method, peer protocol
  SessionStart hook ─────┘       CLAUDE.md ▶ claude-md
                                                  every turn re-reads all of it ──▶ bill = requests × context
```

A rule without `paths:` loads at launch; a scoped rule loads when a matching file is read or edited
([docs](https://code.claude.com/docs/en/memory)). Hooks run on tool events and return a decision or
extra context ([docs](https://code.claude.com/docs/en/hooks)).

Measured on this setup (157k requests, deduplicated, see `rules/workflow.md`):

| | |
|---|---|
| Request volume once dispatch went parallel | 2,4k/day → 10,6k/day; implementers 69–72 % of spend |
| Start context an agent pays on every turn | ~60k tokens |
| Agent resume vs fresh dispatch | a resume re-writes ~243k of 260k tokens |
| `node --test` output reaching the model | 80.936 B → 62 B with `node-test-compact` |

## One plan, executed

```
  plan ── every task carries: Agent · Worktree · Review · Parallel
    │
    ▼
  SESSION ── wave 1: every unblocked task, one message ──┐
    │                                                     ▼
    │    ┌─ impl-sonnet-medium  .worktree/<project>/t1 ─┐    agent-dispatch-guard checks:
    │    ├─ impl-sonnet-low     .worktree/<project>/t2 ─┤    configured name · no `model` override
    │    └─ impl-opus-medium    .worktree/<project>/t3 ─┘    impl-* in its own worktree
    │                 │ ≤ 200-word report + git diff --stat
    ▼                 ▼
  integrate one branch at a time:
    rebase ─▶ lint + affected tests on the MERGED tree ─▶ fast-forward main ─▶ remove worktree
    │                                                       (worktree-remove-guard: unlink node_modules first)
    ▼ wave 2 starts from the new main
  review-first over the whole diff ─▶ exactly located: fix inline · else fix 1 = same agent, fix 2 = one tier up
    ▼
  push origin main on a green merged-tree gate · deploy only on explicit order
```

The session dispatches, merges and reclaims worktrees; it implements only the trivial. Independent
tasks run at once, each in its own worktree. Nobody waits for an agent: no polling, no sleeping; the
harness re-invokes the session when a child reports.

### Agent tiers

Model and effort live in the agent file, never in the dispatch. Go up a tier for the task's
complexity, never its priority.

| Task | Agent |
|---|---|
| Docs only | `impl-haiku-medium` |
| Mechanical code, complete in the brief | `impl-sonnet-low` |
| Well-scoped code (the default) | `impl-sonnet-medium` |
| UI/UX work; too open to scope fully; a load-bearing invariant | `impl-opus-medium` |
| The one task whose silent error invalidates everything after it | `impl-opus-high` |
| Review the plan's diff · adversarial second pass · re-check | `review-first` · `review-adversarial` · `review-recheck` |
| Read-only code review · rendered-geometry audit | `code-reviewer` · `audit-visual` |
| Plan · architecture · one large plan end to end | `planner`, `planner-fable` · `architect` · `plan-orchestrator` |

Reviewers start without `CLAUDE.md`; the brief pastes the rules that bite.

## Hooks: the enforcement layer

Each hook exists because a rule was written first and did not hold.

```
  Read   big file, no limit ──▶ read-guard ────────────▶ DENY + outline with line ranges
  Agent  built-in / `model` ──▶ agent-dispatch-guard ──▶ DENY, lists the configured agents
  Agent  impl-* w/o worktree ─▶ agent-dispatch-guard ──▶ DENY
  Bash   node --test ─────────▶ node-test-compact ─────▶ REWRITE: log to file, print the summary
  Bash   git commit @'…'@ ────▶ block-ps-heredoc ──────▶ DENY
  Bash   git worktree remove ─▶ worktree-remove-guard ─▶ DENY while a junction remains
  Edit   comment with date/SHA ▶ comment-guard ─────────▶ BLOCK, reason back to the model
  Skill  writing-plans etc. ──▶ plan-dispatch-ruling ──▶ INJECT the dispatch rulings
  SubagentStart ──────────────▶ research + peer blocks ─▶ INJECT
  WorktreeCreate / Remove ────▶ worktree-create/-remove ▶ place, copy .env, unlink links first
```

| Hook | Why it exists |
|---|---|
| `read-guard.py` + `outline.py` | An unbounded Read of a 40 KB file is refused and the refusal carries the file's outline, so the next call is a precise ranged Read |
| `agent-dispatch-guard.py` | A built-in agent or a `model` override silently bypasses the tiering; an implementer outside a worktree blocks parallel work |
| `node-test-compact.py` | 80.936 B of test output per run entered the context; the summary and failures are enough, the full log stays on disk |
| `block-ps-heredoc-commit.py` | PowerShell `@'…'@` through the Bash tool leaked bare `@` lines into a commit message |
| `worktree-remove-guard.py` | On Windows `git worktree remove` deletes through a junction; the main `node_modules` was emptied four times |
| `comment-guard.py` | Dates, SHAs and long blocks in comments belong in git; `rules/code-comments.md` alone did not hold |
| `plan-dispatch-ruling.py` | The rulings were first edited into a plugin's skill files, which every plugin update overwrites |
| `subagent-research-context.py`, `peer-sessions-context.py` | Subagents do not inherit `CLAUDE.md`; sessions sharing one checkout collide on the index, stash and ports |
| `worktree-create.py`, `worktree-remove.py` | Worktrees go to `<workspace>/.worktree/<project>/<name>`, branch from the main HEAD, carry `.env`; removal unlinks first and keeps a changed tree |

Every guard fails open: an internal error allows the call and says so. A guard must never be the
thing that breaks a session.

## Rules

| File | Scope | Subject |
|---|---|---|
| `workflow.md` | always | tokens, dispatch tiers, worktrees, commits, update in place |
| `indonesian-copy.md` | always | Bahasa Indonesia copy that sells; EYD V mechanics |
| `claude-md.md` | instruction files | what belongs in a `CLAUDE.md` and what does not |
| `code-comments.md` | code | comment the WHY, briefly |
| `coding-style`, `patterns`, `python-env`, `security`, `testing`, `hooks`, `python/fastapi` | Python | uv, ruff, pytest, pydantic at the boundary, FastAPI |
| `web-code-and-tests.md` | js, php, html, css | fail loud; which test rung; when a test is owed |
| `ui-ux.md` | html, css, jsx, tsx, vue, decks | no AI-looking design; family over component; no layout shift |
| `visualisation.md` | charts, dashboards | when to draw a chart, how many, how |
| `documentation.md` | `README.md` | ASCII diagrams; this file's structure |

`CLAUDE.md` holds the two always-on rulings: do not over-engineer, and web research is mandatory for
any real-world fact (search to find the page, `curl` to read it, record the source).

## Quick start

```bash
git clone https://github.com/adiatmaja/agentic-workflow && cd agentic-workflow
cp CLAUDE.md ~/.claude/ && cp -r rules hooks agents ~/.claude/
# settings.example.json holds permissions, hook wiring and plugins: merge it into
# ~/.claude/settings.json (do not overwrite your own keys), then verify:
bash tools/verify-setup.sh        # each line prints PASS or FAIL with the measured value
```

Copy rather than symlink: rules in `~/.claude/rules/` load without an approval dialog, a symlink
that resolves outside a project does not ([docs](https://code.claude.com/docs/en/memory)). Hooks
need `python` on `PATH` and run through `bash` (Git Bash on Windows). `plan-dispatch-ruling`
assumes the [superpowers](https://github.com/obra/superpowers) plugin and is inert without it.

### Or let your agent install it

Paste this into Claude Code (or any harness with shell access) from any directory:

```text
Install the agentic-workflow configuration from https://github.com/adiatmaja/agentic-workflow into my Claude Code setup.

1. Clone it into a temporary directory. Read its README.md first.
2. Back up ~/.claude/CLAUDE.md and ~/.claude/settings.json if they exist (append .bak-<date>).
3. Copy CLAUDE.md, rules/, hooks/ and agents/ into ~/.claude/. If a file with the same name already exists there, show me a diff and ask before overwriting.
4. Merge settings.example.json into ~/.claude/settings.json: add its permissions, hooks and enabledPlugins entries to mine without removing any key I already have. Never overwrite the file.
5. Run `bash tools/verify-setup.sh` and paste every PASS/FAIL line to me. Fix nothing silently: if a line fails, tell me why.
6. Remove the temporary clone. Do not touch any other path under ~/.claude.
```

For Codex, Gemini CLI or Antigravity, paste instead: *"Clone https://github.com/adiatmaja/agentic-workflow,
run `tools/export-config.sh --target <codex|gemini|agy>`, then run the generated `install.sh`
for that target and show me its verification line."*

## One source, four harnesses

```
                    ┌──────────────────────────┐
                    │  CLAUDE.md + rules/       │  prose: harness-agnostic
                    │  hooks/ + agents/         │  machinery: Claude Code
                    └────────────┬─────────────┘
                                 │ tools/export-config.sh
          ┌──────────────┬───────┴────────┬──────────────────┐
          ▼              ▼                ▼                  ▼
   Claude Code      Codex             Gemini CLI        Antigravity
   copy into        AGENTS.md +       GEMINI.md block   config/AGENTS.md
   ~/.claude        skills/           + skills/         + skills/
```

```bash
tools/export-config.sh --target codex,gemini,agy   # one install.sh per target, idempotent
tools/export-config.sh --flat                      # PORTABLE.md: one paste-able file for any harness
```

A rule without `paths:` goes into the target's global instruction file; a scoped rule becomes a
skill loaded on demand. The script carries the measured caveats per harness (Codex's 32 KB
project-doc cap, Gemini's `context.fileName` replacing the default, Antigravity's separate skills
tree).

## Project structure

```
agentic-workflow/
├── CLAUDE.md               # always-on rulings
├── rules/                  # 15 rules, 13 of them path-scoped
├── hooks/                  # 11 hooks, 4 injected prose blocks, outline.py, read-guard.test.py
├── agents/                 # 15 configured agents: impl-* tiers, review-*, planners, auditors
├── settings.example.json   # permissions, hook wiring, plugins
└── tools/                  # export-config.sh, flatten.awk, verify-setup.sh
```

Related: [`finish-session`](https://github.com/adiatmaja/skills), the skill that ends a session
with nothing running, uncommitted or unrecorded.

## License

[MIT](LICENSE)
