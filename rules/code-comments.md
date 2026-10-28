---
paths:
  - "**/*.{js,mjs,cjs,ts,tsx,jsx}"
  - "**/*.{py,php,cs,java,go,rs,rb,sh,ps1,sql}"
  - "**/*.{html,htm,css,scss,vue,svelte}"
---

# Code comments: comment the WHY, briefly. History goes in git, rulings in docs

**User ruling, 2026-10-02.** This replaces the earlier stance "source keeps its comments, the build
strips them". Stripping at build time fixes what ships. It does not fix what developers and agents
have to read. A file that is 60 % comment is a defect even if no browser ever downloads the comments.

## What a comment may say

- **Why** the code exists or takes this shape, when the code cannot say it: a constraint, a
  non-obvious invariant, a workaround and what it works around.
- **The contract** of a module or exported function (inputs, outputs, throws), in a short header.
- **A pointer**: one issue or decision ID, or a doc path (`// O118`, `// see docs/x.md §3`).

## What a comment must NOT carry. Each has a proper home

| Content | Its home |
|---|---|
| Dates, commit SHAs, branch, round or session names, "Task 7c" | `git log` / commit message |
| What a bug was, how it was found, "before this fix…", "was X, now Y" | Commit message, or the issue entry |
| A ruling, its reasoning, user quotes, measurements, test counts | `docs/` (the comment points to it) |
| What the next line does | Nothing. Rename instead |
| Commented-out code | Delete it. Git keeps it |

## Size

- Inline comments: **at most 2 lines**. Header: **at most ~10 lines**. If it needs more, write it in
  `docs/` and leave a one-line pointer.
- A comment longer than the code it explains is a smell. Shorten the comment or simplify the code.

## Upkeep

- When code changes, **rewrite or delete its comment in the same edit**. A stale comment is a
  confident lie that survives review.
- When you touch a function, bring its comments within these limits. This is how a heavily commented
  codebase converges without a single big-bang rewrite.
- Never grow a comment to record the change you just made. That record is the commit message.

**Enforced by** `~/.claude/hooks/comment-guard.py` (PostToolUse on Edit/Write). It flags newly
added comment lines that carry dates or SHAs, and comment blocks longer than the limits above.
