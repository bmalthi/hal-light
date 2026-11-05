---
name: dataviz
description: >
  Design and render clear, accessible charts for analysis briefs. Use when a brief
  needs inline SVG charts, chart form selection, color palettes, chart anatomy,
  interaction affordances, or visual QA for a quantitative finding.
---

# dataviz

Use this skill before authoring charts in `brief.html` (see the `analyse` skill).
HAL briefs are static: use inline SVG, visible labels and an accompanying data
table. Read the interaction guidance only for requested interactive outputs;
a brief must not need JavaScript, hover or a browser session to reveal its values.

Adapted from Anthropic's bundled dataviz material; see the repository `NOTICE`.
The upstream material is excluded from HAL Light's Apache-2.0 license.

## What to read

- `references/choosing-a-form.md` — choose whether the finding needs a chart, table,
  stat tile, or another form.
- `references/palette.md` and `references/color-formula.md` — choose chart colors and
  validate them.
- `references/marks-and-anatomy.md` — use the expected mark, axis, label, and annotation
  rules.
- `references/anti-patterns.md` — check for common chart failures before shipping.
- `references/components.md` and `references/interaction.md` — use when the chart needs
  table-view, tooltip, legend, or interaction affordances.

## Validation

Run the palette validator when choosing or changing colors:

```bash
uv run .claude/skills/dataviz/scripts/validate_palette.py "#2a78d6,#eb6834,#1baf7a,#eda100,#e87ba4,#008300,#6250d6,#e34948" --mode light
```

Validate the colors actually used, in display order. Use `--pairs all` whenever
any two series can meet, including crossing lines, scatter plots, maps and small
multiples. The first three default slots pass all-pairs checks in both modes;
for more series, prefer facets or another form. Run each displayed scheme.
Warnings require visible labels, distinct marks or the accompanying table as
specified in the report; an exit code of zero alone does not finish the design.

For a lone status/text color (not a palette), check WCAG text contrast instead:

```bash
uv run .claude/skills/dataviz/scripts/validate_palette.py --contrast "#0b0b0b" "#fcfcfb"
```

For an additional text-legibility measure, use `--apca TEXT BACKGROUND`.
Interpret its signed Lc value with font size and weight; it does not replace
WCAG contrast checks when those criteria are required.

## Rendering the chart

Pick the form from `choosing-a-form.md` and the colors from `palette.md` first, as
above — before either has anything to do with `render.py`. Only once the form is
already decided: if it's one of **line, bar, hbar, waterfall, or combo**, hand the
coordinate math to `scripts/render.py` instead of hand-rolling the SVG path/viewBox
arithmetic yourself. If the data's job calls for something else — a dumbbell/range,
a slope chart, stacked-area, a timeline, a dot plot, or anything else the choosing
table points to — write bespoke inline SVG by hand, following the same mark specs
and palette roles. `render.py` is a shortcut for five recurring shapes, never a
reason to bend a chart into one of them.

`render.py` takes a compact JSON spec per chart (form, title/subtitle, series or
rows, palette slot names, and any annotations) and emits the inline SVG string —
title, gridlines, axis labels, direct end-labels, and the fixed chrome/ink tokens
are all handled for you; the CSS custom properties it emits swap light/dark on
`prefers-color-scheme` automatically. You still choose: the form, which palette
slot each series/bar gets (a name like `"blue"` or `"muted"`, or a literal
already-validated hex), which series to plot, and every title/subtitle/annotation
string.

```bash
uv run .claude/skills/dataviz/scripts/render.py <run>/scratch/chart_specs.json --out-dir <run>/scratch/charts
```

Charts default to dual-scheme (light/dark swap on `prefers-color-scheme`). When a
chart is bound for a one-scheme page — the analyse skill's brief template is
light-only — add `--single-mode light` so the SVG is pinned to that scheme and
can't flip dark on a white page. Hand-written bespoke SVG for such a page should
likewise skip the dark-mode block.

Write your specs to `<run>/scratch/chart_specs.json` (an id-keyed dict of specs is
easiest — one call renders every chart for the brief), then inline the resulting
`<run>/scratch/charts/<id>.svg` files into `brief.html`. A malformed spec — an
unknown `form`, a values array that doesn't match `x`/`categories` in length —
fails loudly naming the problem, rather than emitting a broken chart. See the
`REQUIRED_FIELDS` and the chart functions in `scripts/render.py` for each form's fields.

## Done when

The chart form matches the data's job, the palette passes validation, labels and
annotations state the takeaway directly, and the values are available in a table. Check the rendered layout when a preview
is available: look for clipped labels, collisions and unreadable small text.
If preview is unavailable, inspect the SVG and report that layout was not visually
reviewed; do not turn browser setup into a prerequisite for analysis.
