---
paths:
  - "**/*.html"
  - "**/*.css"
  - "**/*.scss"
  - "**/*.jsx"
  - "**/*.tsx"
  - "**/*.vue"
  - "**/*.svelte"
  - "**/slides*.js"
  - "**/mockup/**"
  - "**/deck/**"
  - "**/DESIGN.md"
---

# UI/UX engineering: no AI-looking design (user ruling 2026-10-17)

The user's exact words: "the design still looks very AI-generated … what I hate most is the usage of
card style." Sources with the full catalogue (67 tells, ranked by who notices):
`github.com/funboy322/avoid-ai-design/references/ai-tells-catalog.md`, Anthropic's `frontend-design`
skill cluster list, 925studios "AI slop tells" (2026-06-14), Krebs's left-border study.

## The one rule

**A pattern is a tell when it was reached for without a reason.** Before any box, badge, icon,
gradient or animation, name the information it carries. If it carries none, it is decoration a model
would have added for any product, and it does not ship.

## Design the family, never the single component (user ruling 2026-10-19)

The user's words: "when designing any ui ux work, you always only too focused on a single component,
not the family component." Real case: a custom date-range button was added next to native `<select>`s,
so one control row held three controls of different height, border, chevron and type.

- Before adding or restyling ANY control, list its siblings on the same screen and across the product
  (buttons, selects, inputs, triggers, popovers, tooltips, table headers, chart readouts). Change the
  family together, or match the existing family exactly.
- One family = one height, border, radius, padding, type size, chevron/icon, focus ring, hover,
  disabled and error state. Define it once (a shared class or token set), never per component.
- Same for patterns: every chart readout, every popover, every change figure behaves and looks alike.
- Briefs to implementers name the family and require a side-by-side screenshot of all its members;
  reviews check consistency across the family, not only the new piece.

## No layout shift on state change (user ruling 2026-10-21)

The user's words: "when doing ui ux, the shift issue is always happening". Real case: switching the
dashboard Periode from *Kemarin* to *7 hari terakhir* nudged every text and component a few pixels.

- Changing a filter, tab, toggle, period or data must move NOTHING except the content that changed.
  Design every slot for its widest/longest state up front: triggers get a stable width (text changes
  inside a fixed slot), figures use `tabular-nums`, legend/key/note lines are reserved even when empty,
  the chart's axis gutter is sized for the widest tick, a line count never depends on the value.
- Brief implementers with this rule; reviews check it.

## Cards: banned as a default (the user's hardest ruling)

- **No card grids.** No row of equal boxes with icon + title + line. No KPI tiles. No "feature cards".
  No bento. No card inside a card. No `1px` grey border around every block, no uniform radius +
  soft shadow kit, no coloured top or left stripe on a box ("colored left borders are as reliable a
  sign of AI design as em-dashes are for text").
- **Group with space, alignment, type and rules instead**: a hairline between rows, a column grid,
  a larger first element, a table when the reader compares, prose when the reader reads. Containers
  are for things that genuinely float (a dialog, a popover, a dragged item) or are physically
  separate (a device frame, a receipt).
- A single container that holds a real surface (one chart, one phone frame) is fine. Three of the
  same thing in a row is not.

## Also banned by default (P0/P1 in the catalogue)

| Tell | Instead |
|---|---|
| Inter / system stack as display; the "tasteful free font" set (Space Grotesk, Geist, Instrument Serif, Fraunces) | a face chosen from the subject, loaded for real, with a scale |
| Indigo-to-purple gradient, gradient headline text, neon glow shadows, glassmorphism by reflex | flat colour with a job; one accent that means something |
| The second-order escapes: cream + terracotta, near-black + one acid accent, broadsheet hairlines everywhere, all-caps tracked eyebrows, `A · B · C` meta strings, `→` glued to links and headings, mono for labels, one word coloured in a headline, decorative 01/02/03 | emphasis built into the type system; labels only when they carry information, sentence case |
| Centered hero + pill badge + three cards; stat strip of round numbers; numbered "how it works"; 4-column footer; stock section waterfall | order sections by what this reader must decide; open with the most characteristic real thing (a real screen, a true number, a table) |
| Icon in a tinted rounded square; the worn Lucide set; emoji as icons; status-chip soup | fewer icons, or none; a chip only for a real changing state |
| Fade-up on every section, per-element stagger everywhere, bounce easing, count-up numbers, hover on everything | one orchestrated moment per screen; interface motion eases out without overshoot; numbers are simply shown |
| Vague aspirational headlines, tricolon slogans, Title Case Everything, "Get started" | the sentence the reader needs, with the figure in it |

## Slides specifically (consulting standard)

- **Action titles**: the title states the conclusion in one sentence (≤ 15 words), not the topic.
  Test: reading only the titles tells the story.
- **One message per slide.** "and" in a title means two slides.
- The body proves the title: a table, a chart with the message in its title, a diagram, or three
  lines of prose. Never three icon boxes.
- Figures carry a source line. Figures from a meeting are quoted as said, with the timestamp.
- Two typefaces at most, one grid, titles that do not move between slides, margins left alone.

## Verification before "done" (user ruling 2026-10-18)

1. **Viewport matrix, viewed yourself**: render every touched screen at **1366×768, 1920×1080 and
   2560×1440** (plus any width the project's own contract names) and Read each PNG. Checking only
   the width a page was built for proves nothing. Wide-screen faults: content stuck in part of the
   screen, empty bands, lines over ~90 characters, charts that stop scaling. Dashboards and apps
   are fluid; only text pages get a max width (WFP design system, grids and layout).
2. **Independent review**: the builder never signs off its own UI. Dispatch `audit-visual` over the
   same matrix with the brief's goal, not the build reasoning. NNG: one evaluator misses problems,
   three to five should evaluate independently. **Always add Gemini as a reviewer** (user ruling
   2026-10-18): visual review of ANY UI/UX work, plus typography/copy review when the text is Bahasa
   Indonesia. `agy -p "<goal + rules + PNG paths>" --model gemini-3.8-flash-medium --add-dir <png dir>`
   (it reads the PNGs). **agy only reviews**: ask for structured findings (slide/screen, element,
   defect, severity 0-4, suggested fix); Claude writes every fix. Never let agy edit files.
2b. **Shift test, measured** (no eye check): in Playwright record `getBoundingClientRect` of every
   visible element, switch each control through its values, diff. Anything outside the changed content
   that moves or resizes by ≥ 1 px is a defect (severity 3).
3. **Severity 0–4** (NNG: frequency, impact, persistence) on every finding. Nothing rated 3 or 4
   stays open when reporting done; 1–2 are listed as known.
4. **Silhouette test**: shrink the screenshot to ~200 px wide, black blocks on white. If it could be
   any product's page, the structure is the problem; recolouring will not fix it.
5. **Scan**: `node ~/.claude/skills/avoid-ai-design/scripts/detect.mjs <dir>` if installed, else
   grep for `card|panel|chip|badge|rounded-2xl|backdrop-blur|bg-clip-text|count` and justify each hit.
6. Dashboards and charts follow `visualisation.md` (one chart per question, no gauges).

The brief wins over this file: when the user asks for a card, a gradient or a centered hero, build
that well. Minimal and restrained is not timid; it is a decision.
