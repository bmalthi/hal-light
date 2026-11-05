#!/usr/bin/env python3
"""
Render inline SVG charts for analysis briefs from a compact JSON spec.

This does the coordinate math and SVG string emission for a closed set of five
chart forms — line, bar, hbar, waterfall, combo. The model still chooses the
form, which palette slots to use, which series/values to plot, and every title/
subtitle/annotation text; this script only lays out what it's told to.

Pick the chart form from the data's job first, per dataviz/references/
choosing-a-form.md — independent of what this script implements. Only after
that: if the chosen form happens to be one of the five below, use this script
for the mechanical part. If the right form is anything else — a dumbbell/
range, a slope chart, stacked-area, a timeline, a dot plot, or whatever else
choosing-a-form.md points to — hand-write bespoke SVG following the same
palette and mark specs instead. This script is a shortcut for five common
forms, never a menu to pick from.

By default each SVG carries both light and dark tokens and swaps on
`prefers-color-scheme`. When the chart will be inlined into a surface that
has only one scheme — e.g. the analyse skill's light-only brief template —
pass `--single-mode light` (or set `"single_mode": "light"` in a spec) to
emit just that mode's values with no media query.

Usage:
  uv run render.py specs.json --out-dir scratch/charts
  uv run render.py specs.json --out-dir scratch/charts --single-mode light
  uv run render.py spec.json --stdout

specs.json may contain: a single spec object, a list of spec objects, or an
id-keyed dict of specs (each value a spec; the key is used as `id` when the
spec omits one).

Importable: from render import render_chart, render_all
"""

import argparse
import html
import json
import math
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

# ---- fixed design-system tokens (dataviz/references/palette.md) — not a
# per-chart choice, so these are constants, not spec fields. ----
SURFACE = {"light": "#fcfcfb", "dark": "#1a1a19"}
TEXT_PRIMARY = {"light": "#0b0b0b", "dark": "#f0efec"}
TEXT_SECONDARY = {"light": "#52514e", "dark": "#c3c2b7"}
MUTED = "#898781"  # axis/tick ink — same both modes
GRID = {"light": "#e1e0d9", "dark": "#2c2c2a"}
BASELINE = {
    "light": "#c3c2b7",
    "dark": "#383835",
}  # axis line AND de-emphasis mark fill
FONT = "system-ui,-apple-system,'Segoe UI',sans-serif"

CATEGORICAL = {
    "blue": {"light": "#2a78d6", "dark": "#3987e5"},
    "aqua": {"light": "#1baf7a", "dark": "#199e70"},
    "yellow": {"light": "#eda100", "dark": "#c98500"},
    "green": {"light": "#008300", "dark": "#008300"},
    "violet": {"light": "#6250d6", "dark": "#9085e9"},
    "red": {"light": "#e34948", "dark": "#e66767"},
    "magenta": {"light": "#e87ba4", "dark": "#d55181"},
    "orange": {"light": "#eb6834", "dark": "#d95926"},
}
# the slot ORDER is the CVD-safety mechanism (palette.md) — keep it as given.
DEFAULT_SLOT_ORDER = [
    "blue",
    "orange",
    "aqua",
    "yellow",
    "magenta",
    "green",
    "violet",
    "red",
]

FORMS = {"line", "bar", "hbar", "waterfall", "combo"}
REQUIRED_FIELDS = {
    "line": ["x", "series"],
    "bar": ["categories", "series"],
    "hbar": ["rows"],
    "waterfall": ["start_label", "start_value", "steps", "end_label"],
    "combo": ["categories", "bar_series", "line_series"],
}


def esc(s):
    """Escape text and attribute values before embedding them in SVG."""
    return html.escape(str(s), quote=True)


def _slug(s):
    return re.sub(r"[^a-zA-Z0-9_-]", "-", str(s))


def fmt_value(v, value_format, unit=""):
    """Format a label and escape both the format output and its unit."""
    try:
        s = value_format.format(v)
    except (ValueError, KeyError, IndexError) as exc:
        raise ValueError(
            f"value_format {value_format!r} failed on {v!r}: {exc}"
        ) from exc
    return esc(f"{s}{unit}")


def _domain(values, explicit=None, include_zero=False, pad_frac=0.08):
    if explicit:
        return explicit[0], explicit[1]
    lo, hi = min(values), max(values)
    if include_zero:
        lo, hi = min(lo, 0), max(hi, 0)
    span = hi - lo
    if span == 0:
        span = abs(hi) or 1
    pad = span * pad_frac
    return lo - pad, hi + pad


class _Palette:
    """Collects only the CSS-var roles a given chart actually uses, per
    palette.md's 'define the slots you use' guidance, so the emitted <style>
    block stays chart-specific rather than declaring all eight slots always."""

    def __init__(self):
        self.used = {}

    def color(self, spec_color):
        if spec_color is None:
            return None
        if spec_color == "muted":
            var = "--mark-muted"
            self.used[var] = (BASELINE["light"], BASELINE["dark"])
            return f"var({var})"
        if spec_color in CATEGORICAL:
            var = f"--c-{spec_color}"
            self.used[var] = (
                CATEGORICAL[spec_color]["light"],
                CATEGORICAL[spec_color]["dark"],
            )
            return f"var({var})"
        if isinstance(spec_color, str) and re.fullmatch(
            r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", spec_color
        ):
            var = f"--c-hex-{_slug(spec_color)}"
            self.used[var] = (spec_color, spec_color)
            return f"var({var})"
        raise ValueError(
            f"unknown color {spec_color!r} — use a palette slot name "
            f"({sorted(CATEGORICAL)}), 'muted', or a literal #hex already run "
            "through validate_palette.py"
        )

    def style_block(self, class_name, single_mode=None):
        """single_mode of 'light' or 'dark' pins the chart to that scheme (no
        media query) — for inlining into a one-scheme page like the analyse
        brief template. Default emits both with a prefers-color-scheme swap."""
        light_extra = "\n".join(f"    {k}: {v[0]};" for k, v in self.used.items())
        dark_extra = "\n".join(f"      {k}: {v[1]};" for k, v in self.used.items())
        if single_mode is not None:
            if single_mode not in ("light", "dark"):
                raise ValueError(
                    f"single_mode must be 'light' or 'dark', got {single_mode!r}"
                )
            idx = 0 if single_mode == "light" else 1
            extra = "\n".join(f"    {k}: {v[idx]};" for k, v in self.used.items())
            return (
                f"<style>\n"
                f"  .{class_name} {{\n"
                f"    --surface: {SURFACE[single_mode]}; --ink-primary: {TEXT_PRIMARY[single_mode]};\n"
                f"    --ink-secondary: {TEXT_SECONDARY[single_mode]}; --ink-muted: {MUTED};\n"
                f"    --grid: {GRID[single_mode]}; --baseline: {BASELINE[single_mode]};\n"
                f"{extra}\n"
                f"  }}\n"
                f"  .{class_name} text {{ font-family: {FONT}; }}\n"
                f"</style>"
            )
        return (
            f"<style>\n"
            f"  .{class_name} {{\n"
            f"    --surface: {SURFACE['light']}; --ink-primary: {TEXT_PRIMARY['light']};\n"
            f"    --ink-secondary: {TEXT_SECONDARY['light']}; --ink-muted: {MUTED};\n"
            f"    --grid: {GRID['light']}; --baseline: {BASELINE['light']};\n"
            f"{light_extra}\n"
            f"  }}\n"
            f"  @media (prefers-color-scheme: dark) {{\n"
            f"    .{class_name} {{\n"
            f"      --surface: {SURFACE['dark']}; --ink-primary: {TEXT_PRIMARY['dark']};\n"
            f"      --ink-secondary: {TEXT_SECONDARY['dark']};\n"
            f"      --grid: {GRID['dark']}; --baseline: {BASELINE['dark']};\n"
            f"{dark_extra}\n"
            f"    }}\n"
            f"  }}\n"
            f"  .{class_name} text {{ font-family: {FONT}; }}\n"
            f"</style>"
        )


def _svg_wrap(class_name, width, height, title, body, style_block):
    return (
        f'<svg class="{class_name}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(title)}">'
        f"{style_block}"
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="var(--surface)"/>'
        f"{body}"
        f"</svg>"
    )


def _title_block(pad_l, title, subtitle):
    out = [
        f'<text x="{pad_l}" y="20" fill="var(--ink-primary)" font-size="14.5" font-weight="700">{esc(title)}</text>'
    ]
    if subtitle:
        out.append(
            f'<text x="{pad_l}" y="37" fill="var(--ink-secondary)" font-size="12">{esc(subtitle)}</text>'
        )
    return "".join(out)


def _rounded_bar_path(x, y_top, w, h, round_end, r=4):
    """Vertical bar: rounded corners at the data end only, square at the other
    end — marks-and-anatomy's bar/column spec. round_end is 'top' or 'bottom'."""
    if h <= 0 or w <= 0:
        return ""
    r = min(r, w / 2, h)
    if round_end == "top":
        return (
            f"M{x:.1f},{y_top + h:.1f} L{x:.1f},{y_top + r:.1f} "
            f"Q{x:.1f},{y_top:.1f} {x + r:.1f},{y_top:.1f} "
            f"L{x + w - r:.1f},{y_top:.1f} Q{x + w:.1f},{y_top:.1f} {x + w:.1f},{y_top + r:.1f} "
            f"L{x + w:.1f},{y_top + h:.1f} Z"
        )
    return (
        f"M{x:.1f},{y_top:.1f} L{x:.1f},{y_top + h - r:.1f} "
        f"Q{x:.1f},{y_top + h:.1f} {x + r:.1f},{y_top + h:.1f} "
        f"L{x + w - r:.1f},{y_top + h:.1f} Q{x + w:.1f},{y_top + h:.1f} {x + w:.1f},{y_top + h - r:.1f} "
        f"L{x + w:.1f},{y_top:.1f} Z"
    )


def _rounded_hbar_path(x_left, y, w, h, r=4):
    """Horizontal bar growing rightward from the baseline: rounded right (data)
    end, square left (baseline) end."""
    if w <= 0 or h <= 0:
        return ""
    r = min(r, w, h / 2)
    return (
        f"M{x_left:.1f},{y:.1f} L{x_left + w - r:.1f},{y:.1f} "
        f"Q{x_left + w:.1f},{y:.1f} {x_left + w:.1f},{y + r:.1f} "
        f"L{x_left + w:.1f},{y + h - r:.1f} Q{x_left + w:.1f},{y + h:.1f} {x_left + w - r:.1f},{y + h:.1f} "
        f"L{x_left:.1f},{y + h:.1f} Z"
    )


# ---------------------------------------------------------------------------
# line — multi-series line/dot chart. direct end-labels, gridlines, optional
# dashed tail (censored/reverted/projected segments), band/vline/hline/point
# annotations.
# ---------------------------------------------------------------------------
def _render_line(spec):
    pal = _Palette()
    cid = f"viz-{_slug(spec['id'])}"
    W = spec.get("width", 680)
    H = spec.get("height", 330)
    x_labels = spec["x"]
    n = len(x_labels)
    series = spec["series"]
    many_series = len(series) > 4
    # end-labels ride past the plot's right edge — measure the longest one so it
    # never gets clipped by the viewBox (marks-and-anatomy: never overflow/clip text).
    end_labeled = (
        []
        if many_series
        else [s["name"] for s in series if s.get("label", "end") == "end"]
    )
    default_pad_r = max([108] + [24 + len(nm) * 6.2 for nm in end_labeled])
    PAD_L, PAD_R, PAD_T = 52, spec.get("pad_r", default_pad_r), 46
    PAD_B = 40 + (20 if many_series else 0)
    unit = spec.get("unit", "")
    vf = spec.get("value_format", "{:.1f}")
    y_ticks = spec.get("y_ticks", 4)
    annotations = spec.get("annotations", [])

    all_vals = [v for s in series for v in s["values"]]
    lo, hi = _domain(all_vals, spec.get("y_domain"))
    plot_w = W - PAD_L - PAD_R
    plot_h = H - PAD_T - PAD_B

    def X(i):
        return PAD_L + (plot_w * i / (n - 1) if n > 1 else 0)

    def Y(v):
        return PAD_T + plot_h * (1 - (v - lo) / (hi - lo))

    body = []
    for t in range(y_ticks + 1):
        val = lo + (hi - lo) * t / y_ticks
        y = Y(val)
        body.append(
            f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{PAD_L + plot_w}" y2="{y:.1f}" stroke="var(--grid)" stroke-width="1"/>'
        )
        body.append(
            f'<text x="{PAD_L - 8}" y="{y + 3.5:.1f}" fill="var(--ink-muted)" font-size="10.5" text-anchor="end">{fmt_value(val, vf, unit)}</text>'
        )

    tick_idxs = (
        range(n)
        if n <= 8
        else sorted(set([0, n - 1] + [round(n * f) for f in (0.25, 0.5, 0.75)]))
    )
    for i in tick_idxs:
        body.append(
            f'<text x="{X(i):.1f}" y="{H - PAD_B + 18:.1f}" fill="var(--ink-muted)" font-size="10.5" text-anchor="middle">{esc(x_labels[i])}</text>'
        )

    for a in annotations:
        kind = a["kind"]
        if kind == "band":
            x0, x1 = X(a["x0"]), X(a["x1"])
            body.append(
                f'<rect x="{x0:.1f}" y="{PAD_T}" width="{x1 - x0:.1f}" height="{plot_h:.1f}" fill="var(--ink-muted)" opacity="0.08"/>'
            )
            if a.get("label"):
                body.append(
                    f'<text x="{(x0 + x1) / 2:.1f}" y="{PAD_T + 12:.1f}" fill="var(--ink-secondary)" font-size="10.5" text-anchor="middle" font-weight="600">{esc(a["label"])}</text>'
                )
        elif kind == "vline":
            x = X(a["x"])
            body.append(
                f'<line x1="{x:.1f}" y1="{PAD_T}" x2="{x:.1f}" y2="{PAD_T + plot_h:.1f}" stroke="var(--baseline)" stroke-width="1" stroke-dasharray="3,3"/>'
            )
            if a.get("label"):
                body.append(
                    f'<text x="{x:.1f}" y="{PAD_T - 8:.1f}" fill="var(--ink-secondary)" font-size="10.5" text-anchor="middle">{esc(a["label"])}</text>'
                )
        elif kind == "hline":
            y = Y(a["y"])
            body.append(
                f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{PAD_L + plot_w}" y2="{y:.1f}" stroke="var(--baseline)" stroke-width="1" stroke-dasharray="3,3"/>'
            )
            if a.get("label"):
                body.append(
                    f'<text x="{PAD_L + plot_w:.1f}" y="{y - 6:.1f}" fill="var(--ink-secondary)" font-size="10.5" text-anchor="end">{esc(a["label"])}</text>'
                )
        elif kind != "point":
            raise ValueError(
                f"unknown annotation kind {kind!r} — use band/vline/hline/point"
            )

    resolved = []
    for si, s in enumerate(series):
        color_key = s.get("color") or DEFAULT_SLOT_ORDER[si % len(DEFAULT_SLOT_ORDER)]
        resolved.append(pal.color(color_key))

    for si, s in enumerate(series):
        color = resolved[si]
        vals = s["values"]
        pts_all = [(X(i), Y(v)) for i, v in enumerate(vals)]
        dash_from = s.get("dash_from")
        if dash_from is None:
            path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts_all)
            body.append(
                f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
            )
        else:
            solid = pts_all[: dash_from + 1]
            tail = pts_all[dash_from:]
            if len(solid) > 1:
                path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in solid)
                body.append(
                    f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
                )
            if len(tail) > 1:
                path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in tail)
                body.append(
                    f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="5,3" opacity="0.6"/>'
                )

        mark_all = n <= 12
        marker_idxs = set(range(n)) if mark_all else {0, n - 1}
        marker_idxs |= {
            a["x"]
            for a in annotations
            if a.get("kind") == "point" and a.get("series", s["name"]) == s["name"]
        }
        for i in sorted(marker_idxs):
            x, y = pts_all[i]
            body.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}" stroke="var(--surface)" stroke-width="2"/>'
            )

        label_mode = s.get("label", "end")
        dy = s.get("dy", 0)
        if label_mode == "end" and not many_series:
            lx, ly = pts_all[-1]
            body.append(
                f'<text x="{lx + 8:.1f}" y="{ly + 3.5 + dy:.1f}" fill="var(--ink-secondary)" font-size="11" font-weight="600">{esc(s["name"])}</text>'
            )
        elif label_mode == "points":
            for i, (x, y) in enumerate(pts_all):
                body.append(
                    f'<text x="{x:.1f}" y="{y - 10:.1f}" fill="var(--ink-primary)" font-size="10.5" font-weight="600" text-anchor="middle">{fmt_value(vals[i], vf, unit)}</text>'
                )
        elif label_mode not in ("end", "none"):
            raise ValueError(
                f"series {s.get('name')!r} has unknown label mode {label_mode!r} — use end/points/none"
            )

    for a in annotations:
        if a["kind"] == "point":
            sname = a.get("series", series[0]["name"])
            s = next(s for s in series if s["name"] == sname)
            i = a["x"]
            x, y = X(i), Y(s["values"][i])
            dy = a.get("dy", -10)
            body.append(
                f'<text x="{x:.1f}" y="{y + dy:.1f}" fill="var(--ink-secondary)" font-size="10.5" text-anchor="middle" font-weight="600">{esc(a["label"])}</text>'
            )

    if many_series:
        lx, ly = PAD_L, H - 6
        for s, color in zip(series, resolved):
            body.append(
                f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" rx="2" fill="{color}"/>'
            )
            body.append(
                f'<text x="{lx + 14}" y="{ly}" fill="var(--ink-secondary)" font-size="10.5">{esc(s["name"])}</text>'
            )
            lx += 20 + 6.2 * len(s["name"]) + 14

    title_block = _title_block(PAD_L, spec["title"], spec.get("subtitle"))
    return _svg_wrap(
        cid,
        W,
        H,
        spec["title"],
        title_block + "".join(body),
        pal.style_block(cid, spec.get("single_mode")),
    )


# ---------------------------------------------------------------------------
# bar — vertical bars, single or multi-series, grouped or stacked, zero-
# baseline (so signed values render as diverging bars for free).
# ---------------------------------------------------------------------------
def _render_bar(spec):
    pal = _Palette()
    cid = f"viz-{_slug(spec['id'])}"
    categories = spec["categories"]
    series = spec["series"]
    n_cat = len(categories)
    n_ser = len(series)
    stacking = spec.get("stacking", "grouped")
    vf = spec.get("value_format", "{:.1f}")
    unit = spec.get("unit", "")
    value_labels = spec.get("value_labels", True)
    legend = n_ser > 1
    W = spec.get("width", 640)
    PAD_L, PAD_R, PAD_T = 48, 20, 46
    PAD_B = 40 + (24 if legend else 0)
    H = spec.get("height", 300 + (24 if legend else 0))
    plot_w = W - PAD_L - PAD_R
    plot_h = H - PAD_T - PAD_B

    if stacking not in ("grouped", "stacked"):
        raise ValueError(f"stacking must be 'grouped' or 'stacked', got {stacking!r}")
    if stacking == "stacked":
        for s in series:
            if any(v < 0 for v in s["values"]):
                raise ValueError(
                    "stacking='stacked' requires non-negative values — use 'grouped' "
                    "for signed/diverging data, or the waterfall form for a running total"
                )
        all_vals = [sum(s["values"][i] for s in series) for i in range(n_cat)]
    else:
        all_vals = [v for s in series for v in s["values"]]

    lo, hi = _domain(all_vals, spec.get("y_domain"), include_zero=True)

    def Y(v):
        return PAD_T + plot_h * (1 - (v - lo) / (hi - lo))

    zero_y = Y(0)
    body = []
    for t in range(5):
        val = lo + (hi - lo) * t / 4
        y = Y(val)
        body.append(
            f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{PAD_L + plot_w}" y2="{y:.1f}" stroke="var(--grid)" stroke-width="1"/>'
        )
        body.append(
            f'<text x="{PAD_L - 6}" y="{y + 3.5:.1f}" fill="var(--ink-muted)" font-size="10" text-anchor="end">{fmt_value(val, vf, unit)}</text>'
        )
    body.append(
        f'<line x1="{PAD_L}" y1="{zero_y:.1f}" x2="{PAD_L + plot_w}" y2="{zero_y:.1f}" stroke="var(--baseline)" stroke-width="1.5"/>'
    )

    ref = spec.get("reference_line")
    if ref:
        ry = Y(ref["value"])
        body.append(
            f'<line x1="{PAD_L}" y1="{ry:.1f}" x2="{PAD_L + plot_w}" y2="{ry:.1f}" stroke="var(--baseline)" stroke-width="1" stroke-dasharray="3,3"/>'
        )
        if ref.get("label"):
            body.append(
                f'<text x="{PAD_L + plot_w:.1f}" y="{ry - 6:.1f}" fill="var(--ink-secondary)" font-size="10.5" text-anchor="end">{esc(ref["label"])}</text>'
            )

    group_w = plot_w / n_cat
    resolved = [
        pal.color(s.get("color") or DEFAULT_SLOT_ORDER[i % len(DEFAULT_SLOT_ORDER)])
        for i, s in enumerate(series)
    ]

    if stacking == "grouped":
        bw = min(24, (group_w * 0.8) / n_ser)
        gap = 3
        total_w = bw * n_ser + gap * (n_ser - 1)
        for ci, cat in enumerate(categories):
            gx0 = PAD_L + ci * group_w + (group_w - total_w) / 2
            for si, s in enumerate(series):
                v = s["values"][ci]
                per_bar = s.get("colors")
                color = pal.color(per_bar[ci]) if per_bar else resolved[si]
                x = gx0 + si * (bw + gap)
                y_top = min(Y(v), zero_y)
                h = abs(Y(v) - zero_y)
                round_end = "top" if v >= 0 else "bottom"
                body.append(
                    f'<path d="{_rounded_bar_path(x, y_top, bw, h, round_end)}" fill="{color}"/>'
                )
                if value_labels:
                    ly = y_top - 4 if v >= 0 else y_top + h + 11
                    body.append(
                        f'<text x="{x + bw / 2:.1f}" y="{ly:.1f}" fill="var(--ink-primary)" font-size="10" font-weight="700" text-anchor="middle">{fmt_value(v, vf, unit)}</text>'
                    )
            body.append(
                f'<text x="{PAD_L + ci * group_w + group_w / 2:.1f}" y="{PAD_T + plot_h + 16:.1f}" fill="var(--ink-muted)" font-size="10.5" text-anchor="middle">{esc(cat)}</text>'
            )
    else:
        bw = min(24, group_w * 0.6)
        for ci, cat in enumerate(categories):
            cx = PAD_L + ci * group_w + group_w / 2
            cum = 0
            for si, s in enumerate(series):
                v = s["values"][ci]
                y_bottom = Y(cum)
                y_top = Y(cum + v)
                h = y_bottom - y_top
                is_last = si == n_ser - 1
                path = (
                    _rounded_bar_path(cx - bw / 2, y_top, bw, h, "top")
                    if is_last
                    else f"M{cx - bw / 2:.1f},{y_top:.1f} h{bw:.1f} v{h:.1f} h{-bw:.1f} Z"
                )
                stroke = ' stroke="var(--surface)" stroke-width="2"' if si > 0 else ""
                body.append(f'<path d="{path}" fill="{resolved[si]}"{stroke}/>')
                cum += v
            if value_labels:
                body.append(
                    f'<text x="{cx:.1f}" y="{Y(cum) - 6:.1f}" fill="var(--ink-primary)" font-size="10" font-weight="700" text-anchor="middle">{fmt_value(cum, vf, unit)}</text>'
                )
            body.append(
                f'<text x="{cx:.1f}" y="{PAD_T + plot_h + 16:.1f}" fill="var(--ink-muted)" font-size="10.5" text-anchor="middle">{esc(cat)}</text>'
            )

    if legend:
        lx, ly = PAD_L, H - 10
        for s, color in zip(series, resolved):
            body.append(
                f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" rx="2" fill="{color}"/>'
            )
            body.append(
                f'<text x="{lx + 14}" y="{ly}" fill="var(--ink-secondary)" font-size="10.5">{esc(s["name"])}</text>'
            )
            lx += 20 + 6.2 * len(s["name"]) + 14

    title_block = _title_block(PAD_L, spec["title"], spec.get("subtitle"))
    return _svg_wrap(
        cid,
        W,
        H,
        spec["title"],
        title_block + "".join(body),
        pal.style_block(cid, spec.get("single_mode")),
    )


# ---------------------------------------------------------------------------
# hbar — ranked horizontal bars, one value per row, optional reference line.
# ---------------------------------------------------------------------------
def _render_hbar(spec):
    pal = _Palette()
    cid = f"viz-{_slug(spec['id'])}"
    rows = spec["rows"]
    n = len(rows)
    vf = spec.get("value_format", "{:.0f}")
    unit = spec.get("unit", "")
    W = spec.get("width", 680)
    PAD_L = spec.get("pad_l", 150)
    PAD_R, PAD_T, PAD_B = 60, 46, 20
    rowh = 30
    H = spec.get("height", PAD_T + PAD_B + rowh * n)
    plot_w = W - PAD_L - PAD_R
    values = [r["value"] for r in rows]
    ref = spec.get("reference_line")
    x_domain = spec.get("x_domain")
    xmax = (
        x_domain[1]
        if x_domain
        else max(values + ([ref["value"]] if ref else [0])) * 1.15
    )
    xmin = x_domain[0] if x_domain else 0

    def X(v):
        return PAD_L + plot_w * (v - xmin) / (xmax - xmin)

    body = []
    default_slot = DEFAULT_SLOT_ORDER[0]
    for i, row in enumerate(rows):
        y = PAD_T + i * rowh + 4
        bh = 16
        color_key = row.get("color") or ("muted" if row.get("muted") else default_slot)
        color = pal.color(color_key)
        w = max(X(row["value"]) - PAD_L, 0)
        body.append(f'<path d="{_rounded_hbar_path(PAD_L, y, w, bh)}" fill="{color}"/>')
        body.append(
            f'<text x="{PAD_L - 8}" y="{y + bh - 3:.1f}" fill="var(--ink-secondary)" font-size="11" text-anchor="end">{esc(row["label"])}</text>'
        )
        body.append(
            f'<text x="{PAD_L + w + 6:.1f}" y="{y + bh - 3:.1f}" fill="var(--ink-primary)" font-size="11" font-weight="600" text-anchor="start">{fmt_value(row["value"], vf, unit)}</text>'
        )
    if ref:
        rx = X(ref["value"])
        body.append(
            f'<line x1="{rx:.1f}" y1="{PAD_T - 4}" x2="{rx:.1f}" y2="{H - PAD_B}" stroke="var(--baseline)" stroke-width="1" stroke-dasharray="3,3"/>'
        )
        if ref.get("label"):
            body.append(
                f'<text x="{rx:.1f}" y="{H - PAD_B + 14:.1f}" fill="var(--ink-muted)" font-size="10" text-anchor="middle">{esc(ref["label"])}</text>'
            )

    title_block = _title_block(16, spec["title"], spec.get("subtitle"))
    return _svg_wrap(
        cid,
        W,
        H,
        spec["title"],
        title_block + "".join(body),
        pal.style_block(cid, spec.get("single_mode")),
    )


# ---------------------------------------------------------------------------
# waterfall — a start anchor, a sequence of signed contributions, an end
# anchor. Pairs with report's bridge-table convention.
# ---------------------------------------------------------------------------
def _render_waterfall(spec):
    pal = _Palette()
    cid = f"viz-{_slug(spec['id'])}"
    vf = spec.get("value_format", "{:.1f}")
    unit = spec.get("unit", "")
    steps = spec["steps"]
    start_label, start_value = spec["start_label"], spec["start_value"]
    end_label = spec["end_label"]
    end_value = spec.get("end_value", start_value + sum(s["delta"] for s in steps))
    pos_color = pal.color(spec.get("positive_color", "blue"))
    neg_color = pal.color(spec.get("negative_color", "red"))
    total_color = pal.color(spec.get("total_color", "muted"))

    bars = [
        {
            "label": start_label,
            "from": 0.0,
            "to": start_value,
            "kind": "total",
            "show": start_value,
        }
    ]
    cum = start_value
    for s in steps:
        nxt = cum + s["delta"]
        bars.append(
            {
                "label": s["label"],
                "from": cum,
                "to": nxt,
                "kind": "pos" if s["delta"] >= 0 else "neg",
                "show": s["delta"],
            }
        )
        cum = nxt
    bars.append(
        {
            "label": end_label,
            "from": 0.0,
            "to": end_value,
            "kind": "total",
            "show": end_value,
        }
    )

    n = len(bars)
    W = spec.get("width", max(680, 90 * n))
    H = spec.get("height", 360)
    PAD_L, PAD_R, PAD_T, PAD_B = 48, 20, 46, 46
    plot_w = W - PAD_L - PAD_R
    plot_h = H - PAD_T - PAD_B
    all_edges = [b["from"] for b in bars] + [b["to"] for b in bars]
    lo, hi = _domain(all_edges, include_zero=True)

    def Y(v):
        return PAD_T + plot_h * (1 - (v - lo) / (hi - lo))

    zero_y = Y(0)
    group_w = plot_w / n
    bw = min(48, group_w * 0.55)

    body = []
    for t in range(5):
        val = lo + (hi - lo) * t / 4
        y = Y(val)
        body.append(
            f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{PAD_L + plot_w}" y2="{y:.1f}" stroke="var(--grid)" stroke-width="1"/>'
        )
        body.append(
            f'<text x="{PAD_L - 6}" y="{y + 3.5:.1f}" fill="var(--ink-muted)" font-size="10" text-anchor="end">{fmt_value(val, vf, unit)}</text>'
        )
    body.append(
        f'<line x1="{PAD_L}" y1="{zero_y:.1f}" x2="{PAD_L + plot_w}" y2="{zero_y:.1f}" stroke="var(--baseline)" stroke-width="1.5"/>'
    )

    for i, b in enumerate(bars):
        cx = PAD_L + group_w * (i + 0.5)
        x = cx - bw / 2
        y_top = Y(max(b["from"], b["to"]))
        y_bot = Y(min(b["from"], b["to"]))
        h = y_bot - y_top
        color = (
            total_color
            if b["kind"] == "total"
            else (pos_color if b["kind"] == "pos" else neg_color)
        )
        round_end = "top" if b["to"] >= b["from"] else "bottom"
        body.append(
            f'<path d="{_rounded_bar_path(x, y_top, bw, h, round_end)}" fill="{color}"/>'
        )
        if b["kind"] == "total":
            label_text = fmt_value(b["show"], vf, unit)
        else:
            sign = "+" if b["show"] > 0 else ""
            label_text = sign + fmt_value(b["show"], vf, unit)
        label_y = y_top - 6 if b["to"] >= b["from"] else y_bot + 14
        body.append(
            f'<text x="{cx:.1f}" y="{label_y:.1f}" fill="var(--ink-primary)" font-size="10.5" font-weight="700" text-anchor="middle">{label_text}</text>'
        )
        body.append(
            f'<text x="{cx:.1f}" y="{PAD_T + plot_h + 18:.1f}" fill="var(--ink-muted)" font-size="10.5" text-anchor="middle">{esc(b["label"])}</text>'
        )
        if i < n - 1:
            nxt_cx = PAD_L + group_w * (i + 1.5)
            connector_y = Y(b["to"])
            body.append(
                f'<line x1="{cx + bw / 2:.1f}" y1="{connector_y:.1f}" x2="{nxt_cx - bw / 2:.1f}" y2="{connector_y:.1f}" stroke="var(--baseline)" stroke-width="1" stroke-dasharray="2,2"/>'
            )

    title_block = _title_block(PAD_L, spec["title"], spec.get("subtitle"))
    return _svg_wrap(
        cid,
        W,
        H,
        spec["title"],
        title_block + "".join(body),
        pal.style_block(cid, spec.get("single_mode")),
    )


# ---------------------------------------------------------------------------
# combo — bar series (left axis) with a line series overlaid (right axis).
# The recurring "volume bars + rate line" twin-axis pattern.
# ---------------------------------------------------------------------------
def _render_combo(spec):
    pal = _Palette()
    cid = f"viz-{_slug(spec['id'])}"
    categories = spec["categories"]
    n = len(categories)
    bar_series = (
        spec["bar_series"]
        if isinstance(spec["bar_series"], list)
        else [spec["bar_series"]]
    )
    line_series = spec["line_series"]
    bar_stacking = spec.get("bar_stacking", "stacked")
    if bar_stacking not in ("grouped", "stacked"):
        raise ValueError(
            f"bar_stacking must be 'grouped' or 'stacked', got {bar_stacking!r}"
        )
    W = spec.get("width", 720)
    H = spec.get("height", 340)
    PAD_L, PAD_R, PAD_T, PAD_B = 56, 56, 46, 44
    plot_w = W - PAD_L - PAD_R
    plot_h = H - PAD_T - PAD_B

    if bar_stacking == "stacked":
        bar_vals = [sum(s["values"][i] for s in bar_series) for i in range(n)]
    else:
        bar_vals = [v for s in bar_series for v in s["values"]]
    bar_lo, bar_hi = _domain(bar_vals, spec.get("bar_y_domain"), include_zero=True)

    def BY(v):
        return PAD_T + plot_h * (1 - (v - bar_lo) / (bar_hi - bar_lo))

    zero_y = BY(0)
    line_lo, line_hi = _domain(line_series["values"], spec.get("line_y_domain"))

    def LY(v):
        return PAD_T + plot_h * (1 - (v - line_lo) / (line_hi - line_lo))

    def X(i):
        return PAD_L + (plot_w * i / (n - 1) if n > 1 else 0)

    bar_vf = spec.get("bar_value_format", "{:.0f}")
    bar_unit = spec.get("bar_unit", "")
    line_vf = spec.get("line_value_format", "{:.0%}")
    line_unit = spec.get("line_unit", "")

    body = []
    for t in range(5):
        val = bar_lo + (bar_hi - bar_lo) * t / 4
        y = BY(val)
        body.append(
            f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{W - PAD_R}" y2="{y:.1f}" stroke="var(--grid)" stroke-width="1"/>'
        )
        body.append(
            f'<text x="{PAD_L - 6}" y="{y + 3.5:.1f}" fill="var(--ink-muted)" font-size="10" text-anchor="end">{fmt_value(val, bar_vf, bar_unit)}</text>'
        )
    for t in range(5):
        val = line_lo + (line_hi - line_lo) * t / 4
        y = PAD_T + plot_h * (1 - t / 4)
        body.append(
            f'<text x="{W - PAD_R + 6}" y="{y + 3.5:.1f}" fill="var(--ink-muted)" font-size="10" text-anchor="start">{fmt_value(val, line_vf, line_unit)}</text>'
        )
    body.append(
        f'<line x1="{PAD_L}" y1="{zero_y:.1f}" x2="{W - PAD_R}" y2="{zero_y:.1f}" stroke="var(--baseline)" stroke-width="1.5"/>'
    )

    group_w = plot_w / n
    bw = min(20, group_w * 0.55)
    bar_colors = [pal.color(s.get("color") or "muted") for s in bar_series]
    for ci in range(n):
        cx = PAD_L + group_w * (ci + 0.5)
        cum = 0
        for si, s in enumerate(bar_series):
            v = s["values"][ci]
            if bar_stacking == "stacked":
                y_top, y_bot = BY(cum + v), BY(cum)
            else:
                y_top, y_bot = min(BY(v), zero_y), zero_y
            h = y_bot - y_top
            x = cx - bw / 2
            is_last = si == len(bar_series) - 1
            path = (
                _rounded_bar_path(x, y_top, bw, h, "top")
                if (is_last or bar_stacking == "grouped")
                else f"M{x:.1f},{y_top:.1f} h{bw:.1f} v{h:.1f} h{-bw:.1f} Z"
            )
            stroke = (
                ' stroke="var(--surface)" stroke-width="2"'
                if (si > 0 and bar_stacking == "stacked")
                else ""
            )
            body.append(f'<path d="{path}" fill="{bar_colors[si]}"{stroke}/>')
            if bar_stacking == "stacked":
                cum += v

    tick_idxs = (
        range(n)
        if n <= 10
        else sorted(set([0, n - 1] + [round(n * f) for f in (0.25, 0.5, 0.75)]))
    )
    for i in tick_idxs:
        body.append(
            f'<text x="{X(i):.1f}" y="{PAD_T + plot_h + 16:.1f}" fill="var(--ink-muted)" font-size="9.5" text-anchor="middle">{esc(categories[i])}</text>'
        )

    line_color = pal.color(line_series.get("color", "red"))
    pts = [(X(i), LY(v)) for i, v in enumerate(line_series["values"])]
    path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    body.append(
        f'<path d="{path}" fill="none" stroke="{line_color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    mark_idxs = range(n) if n <= 12 else (0, n - 1)
    for i in mark_idxs:
        x, y = pts[i]
        body.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{line_color}" stroke="var(--surface)" stroke-width="2"/>'
        )

    legend_items = [(s["name"], bar_colors[i]) for i, s in enumerate(bar_series)] + [
        (line_series["name"], line_color)
    ]
    lx, ly = PAD_L, H - 6
    for name, color in legend_items:
        body.append(
            f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" rx="2" fill="{color}"/>'
        )
        body.append(
            f'<text x="{lx + 14}" y="{ly}" fill="var(--ink-secondary)" font-size="10.5">{esc(name)}</text>'
        )
        lx += 20 + 6.2 * len(name) + 14

    title_block = _title_block(PAD_L, spec["title"], spec.get("subtitle"))
    return _svg_wrap(
        cid,
        W,
        H,
        spec["title"],
        title_block + "".join(body),
        pal.style_block(cid, spec.get("single_mode")),
    )


_RENDERERS = {
    "line": _render_line,
    "bar": _render_bar,
    "hbar": _render_hbar,
    "waterfall": _render_waterfall,
    "combo": _render_combo,
}


def validate_spec(spec):
    """Check required chart fields and series lengths before rendering."""
    # Dimensions can reach SVG attributes without arithmetic (notably hbar height).
    # Validate their type here so spec text cannot create markup or event handlers.
    for field in ("width", "height"):
        if field in spec:
            value = spec[field]
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or value <= 0
            ):
                raise ValueError(f"{field} must be a finite positive number")
    for field in ("id", "form", "title"):
        if field not in spec:
            raise ValueError(f"spec missing required field {field!r}")
    form = spec["form"]
    if form not in FORMS:
        raise ValueError(
            f"form {form!r} is not one of {sorted(FORMS)} — if that's genuinely the "
            "right chart for this data, hand-write bespoke SVG per the dataviz mark/"
            "palette specs instead of forcing it into one of these five forms"
        )
    for field in REQUIRED_FIELDS[form]:
        if field not in spec:
            raise ValueError(f"form {form!r} spec missing required field {field!r}")
    if spec.get("single_mode") not in (None, "light", "dark"):
        raise ValueError(
            f"single_mode must be 'light' or 'dark', got {spec['single_mode']!r}"
        )

    if form == "line":
        n = len(spec["x"])
        for s in spec["series"]:
            if len(s["values"]) != n:
                raise ValueError(
                    f"series {s.get('name')!r} has {len(s['values'])} values, expected {n} (len(x))"
                )
    elif form == "bar":
        n = len(spec["categories"])
        for s in spec["series"]:
            if len(s["values"]) != n:
                raise ValueError(
                    f"series {s.get('name')!r} has {len(s['values'])} values, expected {n} (len(categories))"
                )
    elif form == "combo":
        n = len(spec["categories"])
        bar_series = (
            spec["bar_series"]
            if isinstance(spec["bar_series"], list)
            else [spec["bar_series"]]
        )
        for s in bar_series:
            if len(s["values"]) != n:
                raise ValueError(
                    f"bar series {s.get('name')!r} has {len(s['values'])} values, expected {n} (len(categories))"
                )
        if len(spec["line_series"]["values"]) != n:
            raise ValueError("line_series values length does not match len(categories)")


def render_chart(spec):
    """One spec dict in, one SVG string out."""
    validate_spec(spec)
    return _RENDERERS[spec["form"]](spec)


def _normalize_specs(raw):
    if isinstance(raw, dict) and "form" in raw:
        return [raw]
    if isinstance(raw, dict):
        out = []
        for key, val in raw.items():
            val = dict(val)
            val.setdefault("id", key)
            out.append(val)
        return out
    if isinstance(raw, list):
        return raw
    raise ValueError(
        "specs must be a spec object, a list of specs, or an id-keyed dict of specs"
    )


def render_all(raw_specs, single_mode=None):
    """dict of {id: svg} for a spec object / list of specs / id-keyed dict of specs.
    single_mode ('light'/'dark') pins every chart to one scheme unless a spec
    sets its own single_mode."""
    specs = _normalize_specs(raw_specs)
    if single_mode is not None:
        for s in specs:
            s.setdefault("single_mode", single_mode)
    return {s["id"]: render_chart(s) for s in specs}


def main():
    """Render local JSON specs to SVG files or standard output."""
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "specs",
        help="path to a JSON file: a spec object, a list of specs, or an id-keyed dict of specs",
    )
    ap.add_argument(
        "--out-dir",
        default=None,
        help="directory to write <id>.svg files (default: alongside the specs file)",
    )
    ap.add_argument(
        "--stdout",
        action="store_true",
        help="print SVG to stdout instead of writing a file (only valid for exactly one spec)",
    )
    ap.add_argument(
        "--single-mode",
        choices=["light", "dark"],
        default=None,
        help="pin every chart to one color scheme, no prefers-color-scheme "
        "media query — use 'light' for charts inlined into the analyse "
        "skill's light-only brief template",
    )
    args = ap.parse_args()

    specs_path = Path(args.specs)
    raw = json.loads(specs_path.read_text())
    try:
        specs = _normalize_specs(raw)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.single_mode:
        for spec in specs:
            spec.setdefault("single_mode", args.single_mode)

    if args.stdout:
        if len(specs) != 1:
            print("error: --stdout only works with exactly one spec", file=sys.stderr)
            return 1
        try:
            print(render_chart(specs[0]))
        except ValueError as exc:
            print(f"error rendering spec: {exc}", file=sys.stderr)
            return 1
        return 0

    out_dir = Path(args.out_dir) if args.out_dir else specs_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_dir = out_dir.resolve()
    creation_mask = os.umask(0)
    os.umask(creation_mask)
    written = []
    for spec in specs:
        try:
            svg = render_chart(spec)
        except ValueError as exc:
            print(
                f"error rendering {spec.get('id', '<no id>')!r}: {exc}", file=sys.stderr
            )
            return 1
        out_path = out_dir / f"{_slug(spec['id'])}.svg"
        # Replace the entry without following symlinks or modifying hard-link
        # targets. Preserve regular-file permissions; new files use the umask.
        output_mode = 0o666 & ~creation_mask
        try:
            existing = out_path.lstat()
        except FileNotFoundError:
            pass
        else:
            if stat.S_ISREG(existing.st_mode):
                output_mode = stat.S_IMODE(existing.st_mode)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=out_dir, delete=False
        ) as temporary:
            temporary.write(svg)
        temporary_path = Path(temporary.name)
        try:
            temporary_path.chmod(output_mode)
            os.replace(temporary_path, out_path)
        finally:
            temporary_path.unlink(missing_ok=True)
        written.append((spec["id"], out_path, len(svg)))

    for cid, path, size in written:
        print(f"wrote {cid} -> {path} ({size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
