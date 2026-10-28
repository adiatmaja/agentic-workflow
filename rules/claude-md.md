---
paths:
  - "**/CLAUDE.md"
  - "**/CLAUDE.local.md"
  - "**/AGENTS.md"
  - "**/GEMINI.md"
  - "**/memory/MEMORY.md"
---

# Writing and modifying a CLAUDE.md

`CLAUDE.md` is loaded into **every session, before any work**. Every byte is rent paid
on every task forever. It is not a log, a changelog, a status report or a place to be
thorough. **It is an operating manual for the next task.**

This rule is itself path-scoped: it costs zero tokens until someone opens one of these files.

## The one test, applied per paragraph

> **Would a competent agent, starting cold on an ARBITRARY task in this repo, do something
> DIFFERENT because it read this paragraph?**

- **Yes** → it belongs. It is a rule, a trap, an invariant, a convention, or a pointer.
- **No** → it is a record. It goes in `docs/`, a commit message, or a memory file.

"Someone might want to know" is not a yes. "It was expensive to learn" is not a yes either —
that argues for writing it down *somewhere*, not for putting it in front of every session.

## Never in a CLAUDE.md — move these out on sight

| Shape | Where it goes |
|---|---|
| **Status paragraphs** — "as of DATE, branch X is at SHA, unmerged" | `docs/ROADMAP.md`; the honest form is a command to re-run |
| **Round / session history** — what happened, in what order, with commit ranges | `docs/state-history.md`, `docs/ROADMAP.md` |
| **Commit ledgers and per-round tables** | the git log; a ledger doc |
| **Struck-through text** (`~~superseded~~`) | **delete it.** Kept-but-struck text costs full price to say nothing |
| **Test counts, percentages, file counts, line numbers** | the command that measures them, written inline instead |
| **Narrative of how a defect was found** | the commit message or `docs/` |
| **Anything a `grep` answers in one line** | the grep, quoted in place of the number |

A status paragraph is a measurement with a timestamp. It is **stale the moment it is written**
and it reads as authoritative forever. Replace it with the command that re-derives it.

## The ratchet — how a modification is allowed to happen

**The general law is `~/.claude/rules/workflow.md` § "Update in place — never append", and it is
always loaded. It is not repeated here.** What is specific to this file:

1. **Measure first.** `wc -c CLAUDE.md` before touching it. State the number.
2. **A pointer beats a copy.** One line — *"Before touching X, read `docs/y.md`"* — is worth thirty
   lines of summarised content, and cannot drift from its source.
3. **Compaction that moves text VERBATIM and strikes the old copy in place shrinks nothing.** It is
   why a file gets compacted four times and grows back four times. Rewrite each surviving paragraph
   to its current-state form, and move the pre-compaction text OUT before editing, not after.
4. **Verify nothing was lost, mechanically.** Extract every backtick-quoted token from the
   pre-edit file and confirm each one survives, either in the new file or in the doc it moved to.
   Report kept / moved / not-found; anything in the not-found list that is a real identifier, path
   or command goes back. A worked example of this check is in a client project's session that took
   its CLAUDE.md from 100 KB to 47 KB with zero loss.

## Budget

| | |
|---|---|
| **Target** | ≤ 20 KB (~5.000 tokens) |
| **Warn** | > 40 KB — the file is now a document, not an index; schedule a compaction |
| **Hard** | > 80 KB — compaction is the next task, ahead of feature work |

```bash
wc -c CLAUDE.md                                    # the number that matters
awk '/^## /{print prev_b, prev_t; prev_t=$0; prev_b=0} {prev_b+=length($0)+1} \
     END{print prev_b, prev_t}' CLAUDE.md | sort -rn | head   # the fattest sections
```

**Compaction that moves text VERBATIM and strikes the old copy in place does not shrink
anything** — it is the reason a file gets compacted four times and grows back four times.
Rewrite each surviving paragraph to its current-state form, and move the pre-compaction
text OUT before editing, not after.

## What a good CLAUDE.md contains

- **Rules whose violation happens by default, silently** — the ones a careful agent breaks
  precisely because nothing warns it.
- **Invariants and conventions** the code cannot express itself.
- **Traps**, named, with the mechanical test that detects each.
- **Pointers** to the deep docs, one line each, with the condition that triggers reading them.
- **Commands to measure**, never the measurements.

## What a good MEMORY.md contains

The same test, one line per memory, plus: **convert relative dates to absolute**, and never
put memory content in the index — the index is pointers only.
