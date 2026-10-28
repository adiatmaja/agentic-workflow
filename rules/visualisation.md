---
paths:
  - "**/*.html"
  - "**/*.jsx"
  - "**/*.tsx"
  - "**/*.vue"
  - "**/*.svelte"
  - "**/*chart*"
  - "**/*viz*"
  - "**/*graph*"
  - "**/*dashboard*"
---

# Charts: when to draw one, how many, and how

**User ruling, 2026-10-02.** Too many charts is a real cost, not a neutral extra. Sources with exact
quotes: a project research note (2026-10-02, not included here).

## Pick the form from the reader's question

| The reader needs | Use | Why |
|---|---|---|
| One value | The number, in a sentence | A chart of one value is decoration (Nussbaumer, storytelling with data) |
| A few exact values to act on | A table | Precise lookup beats a picture (UK Analysis Function, Datawrapper, IBM Carbon) |
| A pattern, trend, comparison of many items, spread or place | A chart | That is what charts are faster at (Analysis Function) |

Write the chart's message in one sentence first. If you cannot, do not draw it (Analysis Function).

## How many

- **One chart per question the user actually brings. One primary chart visible per view**; the rest
  go behind a disclosure, never deleted (NN/g, progressive disclosure).
- People hold about four items in mind at once (Cowan 2001). Every chart that answers nothing spends
  one of them and competes with the one that does (Few, Wilke).
- **Never the same data twice on one view, and never two different measures of the same thing side
  by side**: the reader has to decide which one to believe (Wilke on repetitive panels; Analysis
  Function on dual axes).
- "One per view" is an inference from these sources, not a number any of them states.

## How

- Position and length before angle, area or colour (Cleveland & McGill 1984). **No gauges or dials**:
  they take space and read worse than a bar (NN/g; Few's bullet graph replaces them).
- Colour carries state or category, never decoration. Status never by colour alone: add a word.
- Zero-based axes for magnitudes. One shared scale when items are compared.
- Label directly; keep axes and units, since data-ink is "within reason" (Wilke on Tufte).
- Text built at host width; never a fixed viewBox stretched to 100 %.
- **Every chart answers on hover AND focus, with more detail than it draws** (user ruling
  2026-10-02): the readout shows the value AT THE POINTER and follows it (hairline at the cursor,
  nearest point or interpolated value, unit, comparison), never one fixed caption per chart. That is
  what lets the screen carry fewer words. Keyboard reaches each mark; a tap pins the readout; print is exempt.

## Limits, so the rule is not over-applied

- Repeating a chart TYPE is fine; repeating DATA is not (Few, Pitfall 6).
- Never split one question's evidence across screens to save charts (Few, Pitfall 1).
- Decoration does not reduce accuracy and can help recall (Bateman 2010): the case against it is
  speed and clutter, so cut it in tools, not necessarily in storytelling.
- A project's own visualisation-decisions document overrides this file where they differ.
