# agentic-workflow

> A working configuration for agentic coding harnesses: the rules an agent reads, the hooks that
> enforce them when reading is not enough, and the agent tiers that keep the bill proportional.

## Overview

This is my working configuration for agentic coding, published as it runs day to day on my RAG,
LLM fine-tuning, forecasting and agent-tooling projects. Client and project names are removed, the
rulings and measurements are kept, and every hook is the one in use.

The prose parts (`CLAUDE.md`, `rules/`) are harness-agnostic and port to Codex, Gemini CLI and
Antigravity with `tools/export-config.sh`. The machinery (`hooks/`, `agents/`,
`settings.example.json`) uses Claude Code's hook and subagent protocol.

The design rests on one measured fact: **every turn re-reads the whole context, so the bill is
requests × context size.** Everything here either cuts requests, cuts context, or refuses the action
that a rule alone failed to stop.

## What loads when

```
  session start                     file opened                        tool call
  ─────────────                     ───────────                        ─────────
  CLAUDE.md ──────────────┐         rules/*.md with paths: ──┐         PreToolUse ─▶ hook ─▶ allow / deny / rewrite
  rules/workflow.md ──────┼─▶ ctx     *.py ──▶ coding-style, testing   │                      │
  rules/indonesian-copy.md┘           *.html ─▶ ui-ux, visualisation   │                      └─▶ reason returns to the model
  SessionStart hook ──────┘           CLAUDE.md ─▶ claude-md           PostToolUse ─▶ comment-guard, plan-dispatch-ruling
  (peer-sessions)
                                                                       SubagentStart ─▶ research-block, peer-sessions
  every turn re-reads ALL of it ──▶ bill = requests × context size
```

Rules without a `paths:` field load at launch; the rest load only when a matching file is read,
written or edited ([memory docs](https://code.claude.com/docs/en/memory)). Hooks run on tool
events and return a decision or extra context ([hooks reference](https://code.claude.com/docs/en/hooks)).

Measured on this setup (from `rules/workflow.md`, 157k requests, deduplicated):

| What | Measured |
|---|---|
| Per-request cost | flat since 2026-09-20 (~2,2 units) |
| Request volume, before vs after parallel dispatch | 2,4k/day vs 10,6k/day |
| Subagent runs per main session | 59 |
| Implementers' share of spend | 69–72 % |
| Start context an agent pays on every turn | ~60k tokens |
| `node --test` output reaching the model, before/after `node-test-compact` | 80.936 B → 62 B |
| Agent resume vs fresh dispatch | a resume re-writes ~243k of 260k tokens |

## One plan, executed

```
  plan (superpowers:writing-plans + plan-dispatch-ruling hook)
    │  every task carries: Agent · Worktree · Review · Parallel
    ▼
  SESSION ──dispatch wave 1: every unblocked task, one message──┐
    │                                                           ▼
    │     ┌─ impl-sonnet-medium  .worktree/<project>/t1 ─┐   agent-dispatch-guard:
    │     ├─ impl-sonnet-low     .worktree/<project>/t2 ─┤     configured agent name?  no `model` override?
    │     └─ impl-opus-medium    .worktree/<project>/t3 ─┘     impl-* dispatched with isolation: "worktree"?
    │                    │  ≤ 200-word report + git diff --stat
    ▼                    ▼
  integrate ONE branch at a time
    rebase ─▶ lint + affected tests on the MERGED tree ─▶ fast-forward main ─▶ remove worktree
                                                                                  │ worktree-remove-guard:
                                                                                  │ unlink node_modules first
    │ wave 2 starts from the new main
    ▼
  review-first over the whole plan diff ─▶ findings ─▶ exactly located: fix inline
                                                      otherwise: fix 1 = same agent (fresh), fix 2 = one tier up
    ▼
  review-recheck ─▶ push origin main (green merged-tree gate only; deploy on explicit order)
```

The session dispatches, merges and reclaims worktrees; it implements only the trivial. Each
implementer gets its own worktree (`hooks/worktree-create.py` places it at
`<workspace>/.worktree/<project>/<name>`), so independent tasks run at once. Parallel runs multiply
spend; the saving comes from tier and effort per run, never from run count. Nobody waits for an
agent: no polling, no sleeping, the harness re-invokes the session when a child reports.

### Agent tiers

Model and effort live in the agent definition, not in the dispatch. `agent-dispatch-guard.py`
refuses a built-in agent type or a `model` override, so the tiering cannot be bypassed quietly.

| Task | Agent | Model / effort |
|---|---|---|
| Docs only: index, close-out, handoff text | `impl-haiku-medium` | haiku / medium |
| Mechanical code, complete in the brief | `impl-sonnet-low` | sonnet / low |
| Well-scoped, not-too-complex code (the default) | `impl-sonnet-medium` | sonnet / medium |
| Any UI/UX work; too open to scope fully in the brief; a load-bearing invariant | `impl-opus-medium` | opus / medium |
| The one task whose silent error invalidates everything downstream | `impl-opus-high` | opus / high |
| First-pass review of a plan's diff | `review-first` | sonnet / high |
| Adversarial second pass, only after a critical/high finding | `review-adversarial` | opus / high |
| Re-check after fixes | `review-recheck` | sonnet / low |
| Read-only code review / rendered-geometry audit | `code-reviewer` / `audit-visual` | sonnet |
| Plan a feature / architecture | `planner`, `planner-fable` / `architect` | opus, fable / high, medium |
| Own one large plan (8+ tasks remaining) | `plan-orchestrator` | opus / medium |

Reviewers start without `CLAUDE.md` (`omitClaudeMd: true`): the brief pastes the rules that bite.
Go up a tier for a reason about the task's complexity, never its priority.

## Hooks: the enforcement layer

A markdown rule loses to habit. Each hook exists because a rule was written first and did not hold.

```
  Read   big file, no limit ─────▶ read-guard ───────────▶ DENY + outline (L12-L80 fn …)   99 % of big reads were ranged; this closes the rest
  Agent  built-in / `model` ─────▶ agent-dispatch-guard ─▶ DENY, lists configured agents   tiering bypassed silently
  Agent  impl-* w/o worktree ────▶ agent-dispatch-guard ─▶ DENY                            one worktree per independent task
  Bash   node --test ────────────▶ node-test-compact ────▶ REWRITE: log to file, grep summary   80.936 B → 62 B
  Bash   git commit @'…'@ ───────▶ block-ps-heredoc ─────▶ DENY                            bare @ lines leaked into a commit
  Bash   git worktree remove ────▶ worktree-remove-guard ▶ DENY while a junction remains   main node_modules emptied 4 times
  Edit   comment with date/SHA ──▶ comment-guard ────────▶ BLOCK, reason to the model      history belongs in git, not comments
  Skill  writing-plans etc. ─────▶ plan-dispatch-ruling ─▶ INJECT the owner's rulings      plugin updates overwrite edited skills
  SubagentStart ─────────────────▶ research-context, peer-sessions ▶ INJECT              subagents do not inherit rules
  WorktreeCreate / Remove ───────▶ worktree-create / -remove ▶ place, copy .env, unlink links first
```

| Hook | Event | What it does | Why it exists |
|---|---|---|---|
| `read-guard.py` | PreToolUse · Read | Refuses an unbounded Read of a file ≥ 40 KB (or `limit` > 400) and returns the file's outline with line ranges, computed by `outline.py` | Makes the refusal itself the pointer: the next call is a precise ranged Read |
| `outline.py` | (library + CLI) | Section/symbol outline with START-END lines for md, js/ts, php, html, css, json | Used by `read-guard` and by the model from Bash to jump to one symbol |
| `agent-dispatch-guard.py` | PreToolUse · Agent | Denies a non-configured agent, a `model` override, or an `impl-*` agent without `isolation: "worktree"`; lists the live names | Model and effort live in the definition; a built-in bypasses the tiering |
| `node-test-compact.py` | PreToolUse · Bash | Rewrites `node --test …` to log to a file and print only the summary lines plus failures, preserving the exit status through compound commands | 80.936 B of test output per run was entering the context |
| `block-ps-heredoc-commit.py` | PreToolUse · Bash | Denies `git commit` that uses PowerShell `@'…'@` through the Bash tool | Bash does not parse the delimiters; the `@` lines leaked into a commit message |
| `worktree-remove-guard.py` | PreToolUse · Bash, PowerShell | Denies `git worktree remove` while the target holds a directory junction or symlink, or untracked review artefacts the main checkout lacks | On Windows the removal deletes through the junction; main `node_modules` was emptied four times |
| `comment-guard.py` | PostToolUse · Edit, Write | Flags newly added comments that carry a date or SHA, or a block over 10 lines; never undoes the edit | `rules/code-comments.md` alone did not hold |
| `plan-dispatch-ruling.py` + `.md` | PostToolUse · Skill, UserPromptExpansion | Injects the dispatch rulings whenever a planning or executing skill loads | The rulings were first edited into the plugin's skill files, which a plugin update overwrites |
| `subagent-research-context.py` + `research-block.md` | SubagentStart | Injects the research method (search to find, curl to read, UNVERIFIED over guessing) | Subagents do not inherit `CLAUDE.md` reliably |
| `peer-sessions-context.py` + two `.md` | SessionStart, SubagentStart | Injects the protocol for other sessions sharing the checkout | Several sessions in one working tree collide on the index, stash and ports |
| `worktree-create.py` | WorktreeCreate | Places the worktree at `<workspace>/.worktree/<project>/<name>`, branches from the main checkout's HEAD, copies `.env`/`var` (or `.worktreeinclude`), junctions `node_modules` | Default placement littered the project; default base was sometimes stale |
| `worktree-remove.py` | WorktreeRemove | Removes only an unchanged worktree, after unlinking top-level junctions | A changed worktree is kept for the session to merge |

Every guard fails open: an internal error allows the call and says so on stderr. A guard must never
be the thing that breaks a session.

## Rules

| File | Scope (`paths:`) | Subject |
|---|---|---|
| `workflow.md` | always | tokens, dispatch tiers, worktrees, commits, update-in-place |
| `indonesian-copy.md` | always | Bahasa Indonesia copy that sells, EYD V mechanics |
| `claude-md.md` | `CLAUDE.md`, `AGENTS.md`, `MEMORY.md` | what belongs in an instruction file and what does not |
| `code-comments.md` | code files | comment the WHY, briefly; enforced by `comment-guard` |
| `coding-style.md`, `patterns.md`, `python-env.md`, `security.md`, `testing.md`, `hooks.md` | `*.py`, `pyproject.toml` | Python stack: uv, ruff, pytest, pydantic at the boundary |
| `python/fastapi.md` | `api/`, `app/`, `routers/`, `main.py` | FastAPI structure, async, schemas |
| `web-code-and-tests.md` | `*.js`, `*.php`, `*.html`, `*.css` | fail loud, which test rung, when a test is owed |
| `ui-ux.md` | html, css, jsx, tsx, vue, svelte, decks | no AI-looking design; family over component; no layout shift; verification matrix |
| `visualisation.md` | html, charts, dashboards | when to draw a chart, how many, how |
| `documentation.md` | `README.md` | ASCII diagrams, README structure (this file follows it) |

`CLAUDE.md` holds the two always-on rulings: do not over-engineer, and research on the internet is
mandatory for real-world facts (search to find the page, `curl` to read it, record the source).

## Quick start

Copy, do not symlink. Claude Code loads `~/.claude/rules/` without an approval dialog; a symlinked
rule that resolves outside a project's working directory needs one-time approval per project
([memory docs](https://code.claude.com/docs/en/memory)).

```bash
git clone https://github.com/<you>/agentic-workflow
cd agentic-workflow
cp CLAUDE.md ~/.claude/CLAUDE.md
cp -r rules hooks agents ~/.claude/
# settings: MERGE, never overwrite. settings.example.json holds only permissions, hooks and plugins.
python - <<'EOF'
import json, os
p = os.path.expanduser("~/.claude/settings.json")
cur = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
new = json.load(open("settings.example.json", encoding="utf-8"))
for k, v in new.items():
    cur[k] = {**cur.get(k, {}), **v} if isinstance(v, dict) else v
json.dump(cur, open(p, "w", encoding="utf-8"), indent=2)
EOF
bash tools/verify-setup.sh        # every line prints PASS or FAIL with the measured value
```

The hooks need Python 3 on `PATH` as `python` and run through `bash` (Git Bash on Windows).
`plan-dispatch-ruling` assumes the `superpowers` plugin; without it the hook simply never fires.

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
   ~/.claude        skills/ (scoped   + skills/         + skills/
                    rules → skills)
```

```bash
tools/export-config.sh --target codex            # ~/claude-config-export/claude-config-<date>/codex/
tools/export-config.sh --target gemini,agy       # one install.sh per target, each idempotent
tools/export-config.sh --flat                    # PORTABLE.md: one paste-able file for any harness
```

The split is by the rule's own frontmatter: a rule without `paths:` goes into the global
instruction file, a rule with `paths:` becomes a skill loaded on demand. `tools/flatten.awk` does
the rendering. The script carries the measured caveats per harness (Codex's 32 KB project-doc cap,
Gemini's `context.fileName` replacing the default, Antigravity's separate skills tree).

## Project structure

```
agentic-workflow/
├── CLAUDE.md               # always-on rulings: no over-engineering, mandatory web research
├── rules/                  # 15 rules; paths: frontmatter scopes 13 of them
│   └── python/fastapi.md
├── hooks/                  # 11 hooks + 4 injected prose blocks + outline.py + read-guard.test.py
├── agents/                 # 15 configured agents: impl-* tiers, review-*, planners, auditors
├── settings.example.json   # permissions, hook wiring, plugins — merge into your settings.json
└── tools/
    ├── export-config.sh    # port to Codex / Gemini CLI / Antigravity, or a flat paste file
    ├── flatten.awk         # frontmatter-aware renderer used by export-config.sh
    └── verify-setup.sh     # PASS/FAIL check that the installed setup is intact
```

## Related

- [`finish-session`](https://github.com/adiatmaja/skills) skill: ends a session with nothing of
  yours running, uncommitted or unrecorded. Lives in its own repo so it does not drift.
- [`superpowers`](https://github.com/obra/superpowers): the process skills (`writing-plans`,
  `subagent-driven-development`) that `plan-dispatch-ruling` amends.

## License

[MIT](LICENSE)
