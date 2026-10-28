---
paths:
  - "**/*.{js,mjs,cjs}"
  - "**/*.php"
  - "**/*.{html,css}"
---

# Web code and its tests — the rules that bite (2026-10-17, sources: Google eng-practices and testing blog, Beck's Test Desiderata, Fowler's Practical Test Pyramid)

## Writing the code

- **Fail loud, never default a required input** (`siteEnergy()` throws without `tempDaytimeMonthlyC`). A
  default is a wrong answer that looks right.
- **`===` always; no duplicate object keys; no redeclared `var`; no bare `toFixed`** — the first three are
  lint errors (`npm run lint`, pre-push), the last is `fmt.*`. Lint is green BEFORE the commit.
- **A swallowed exception names WHY in ≤ 2 lines**, else it is a bug with a comment.
- **A new behaviour is an own-global module with `create(deps)`**; a function past ~60 lines or a file past
  its cap is split, not grown. Names carry the unit (`_M`, `_DEG`, `_PT`, `_KWH`).
- **Comments say WHY only** (`code-comments.md`); the WHAT is the name; the history is the commit body.
- **No `console.log`, no `TODO` in shipped code** — a TODO is an open-item entry.

## When a test is OWED, and when it is NOT (user rulings 2026-10-02/05 restated)

| Change | Evidence owed |
|---|---|
| Calculation, money, data/registry, auth, API, a load-bearing invariant | a NEW test on the lowest rung that can see it |
| Layout, copy, restyle, spacing, colour | screenshots at the `ui-ux.md` viewport matrix (1366×768, 1920×1080, 2560×1440), viewed, plus an independent `audit-visual` pass. **No spec** |
| A fix to behaviour an existing test covers | the existing test, run alone, red → green |
| A docs-only change | nothing |

- **Never assert exact display text**; never a test that restates the implementation line by line
  (Beck: *behavioural* and *structure-insensitive* — a refactor must not turn it red).
- **Never a test for coverage's sake.** Each test states one behaviour in its name and one expected
  value in its message; a failure must localise without a debugger (Beck: *specific*).

## Which rung

Google's first guess is 70 / 20 / 10 (unit / integration / end-to-end); one client project's suite is the inverted
cone Google warns of (1.704 Playwright tests, 25,6 min, 68 standing reds) — so every NEW test goes DOWN:

1. **`verify/` node:test on the exported function** — pure input → output. The default.
2. **A source-text guard** only when there is no function boundary, and then it asserts WHAT THE SLICE
   FOUND, never only an absence (testing-guide § "Writing a source-text guard").
3. **A Playwright spec** only for what rendering or navigation alone can show, named for the surface,
   added to the per-surface map, and NEVER as the first evidence for a calculation.

- **Deterministic**: no live clock, no network (Open-Meteo is metered), no order dependence.
- **A flaky test is quarantined with an open-item entry the same day**, never re-run until green.
- **Run only what reads the touched files** (`node scripts/affected-tests.mjs <base> --run-verify`);
  an empty file list runs everything, and a non-zero SKIP is a regression.
