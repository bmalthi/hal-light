"""Exercise offline chart output, input safety and brief validation."""

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDER = ROOT / ".claude/skills/dataviz/scripts/render.py"
VERIFY = ROOT / ".claude/skills/analyse/scripts/verify_brief.py"


def load_helper(name, path):
    """Load a standalone script without installing it as a package."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


renderer = load_helper("hal_render", RENDER)
palette = load_helper(
    "hal_palette", ROOT / ".claude/skills/dataviz/scripts/validate_palette.py"
)
SPECS = json.loads((ROOT / "tests/fixtures/charts.json").read_text())


class HelperTests(unittest.TestCase):
    """Check externally visible results with synthetic local fixtures."""

    def test_all_five_forms_are_svg(self):
        for spec in SPECS:
            with self.subTest(form=spec["form"]):
                tree = ET.fromstring(renderer.render_chart(spec))
                self.assertEqual(tree.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertEqual(tree.attrib["aria-label"], spec["title"])
                self.assertIn(spec["title"], "".join(tree.itertext()))

    def test_label_and_unit_markup_stays_text(self):
        for spec in copy.deepcopy(SPECS):
            payload = '<script>alert("synthetic")</script>'
            spec["title"] = payload
            for key in ("unit", "bar_unit", "line_unit"):
                spec[key] = payload
            for key in ("value_format", "bar_value_format", "line_value_format"):
                spec[key] = "{:.0f}" + payload
            svg = renderer.render_chart(spec)
            tree = ET.fromstring(svg)
            self.assertNotIn("<script>", svg)
            self.assertIn(payload, "".join(tree.itertext()))

    def test_hex_colors_include_alpha(self):
        for color in ("#abc", "#abcd", "#aabbcc", "#aabbccdd"):
            spec = copy.deepcopy(SPECS[0])
            spec["series"][0]["color"] = color
            svg = renderer.render_chart(spec)
            ET.fromstring(svg)
            self.assertIn(color, svg)

    def test_css_breakout_is_rejected(self):
        spec = copy.deepcopy(SPECS[0])
        spec["series"][0]["color"] = "#fff}</style><script>alert(1)</script>"
        with self.assertRaises(ValueError):
            renderer.render_chart(spec)

    def test_dimensions_cannot_inject_attributes(self):
        for example in SPECS:
            for field in ("height", "width"):
                for bad in (
                    '96" onload="alert(1)',
                    float("nan"),
                    float("inf"),
                    0,
                    -1,
                    True,
                ):
                    spec = {**example, field: bad}
                    with self.subTest(form=spec["form"], field=field, value=bad):
                        with self.assertRaises(ValueError):
                            renderer.render_chart(spec)

    def test_series_length_mismatch_fails(self):
        spec = copy.deepcopy(SPECS[0])
        spec["series"][0]["values"].pop()
        with self.assertRaises(ValueError):
            renderer.render_chart(spec)

    def test_output_names_and_symlinks_cannot_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            output = folder / "charts"
            output.mkdir()
            target = folder / "unrelated.txt"
            target.write_text("keep")
            (output / "weekly-tasks.svg").symlink_to(target)
            spec = copy.deepcopy(SPECS[0])
            other = {**spec, "id": "../../escape"}
            existing = output / "existing.svg"
            existing.write_text("old")
            existing.chmod(0o640)
            source = folder / "input.json"
            source.write_text(json.dumps([spec, other, {**spec, "id": "existing"}]))
            result = subprocess.run(
                [sys.executable, str(RENDER), str(source), "--out-dir", str(output)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(target.read_text(), "keep")
            self.assertFalse((output / "weekly-tasks.svg").is_symlink())
            self.assertEqual(len(list(output.glob("*.svg"))), 3)
            self.assertFalse((folder / "escape.svg").exists())
            creation_mask = os.umask(0)
            os.umask(creation_mask)
            self.assertEqual(
                (output / "weekly-tasks.svg").stat().st_mode & 0o777,
                0o666 & ~creation_mask,
            )
            self.assertEqual(existing.stat().st_mode & 0o777, 0o640)

    def check_document(self, body, *flags):
        """Run the checker on a private temporary document."""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "brief.html"
            path.write_text(f"<html><body><h1>Synthetic</h1>{body}</body></html>")
            return subprocess.run(
                [sys.executable, str(VERIFY), str(path), *flags],
                capture_output=True,
                text=True,
            )

    def test_external_resources_and_document_scripts_fail(self):
        bodies = [
            '<img src="https://example.invalid/image.png">',
            "<style>body{background:url(https://example.invalid/pixel)}</style>",
            "<style>@import 'https://example.invalid/font.css';</style>",
            "<script>alert(1)</script>",
        ]
        for body in bodies:
            with self.subTest(body=body):
                self.assertEqual(self.check_document(body).returncode, 1)

    def test_local_embedded_assets_and_deck_scripts_pass(self):
        bodies = [
            '<img src="chart.png" srcset="chart.png 1x, chart-large.png 2x">',
            '<img src="data:image/png;base64,AA==">',
            "<style>@font-face{font-family:demo;src:url(data:font/woff2;base64,AA==)}</style>",
            "<style>body{background:url(data:image/png;base64,AA==)}</style>",
            '<svg><defs><linearGradient id="fill"/></defs><rect style="fill:url(#fill)"/></svg>',
        ]
        for body in bodies:
            with self.subTest(body=body):
                self.assertEqual(self.check_document(body).returncode, 0)
        self.assertEqual(
            self.check_document("<script>void 0;</script>", "--deck").returncode, 0
        )

    def test_template_is_not_a_finished_brief(self):
        template = ROOT / ".claude/skills/analyse/assets/brief_template.html"
        result = subprocess.run(
            [sys.executable, str(VERIFY), str(template)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("unfilled template", result.stderr)

    def test_contrast_endpoints(self):
        self.assertAlmostEqual(palette.contrast("#000000", "#ffffff"), 21.0)
        self.assertAlmostEqual(palette.contrast("#123456", "#123456"), 1.0)

    def test_default_palette_in_both_modes(self):
        for mode, surface in renderer.SURFACE.items():
            colors = [
                renderer.CATEGORICAL[slot][mode] for slot in renderer.DEFAULT_SLOT_ORDER
            ]
            for selected, pairs in ((colors, "adjacent"), (colors[:3], "all")):
                with self.subTest(mode=mode, pairs=pairs):
                    report, ok = palette.validate(selected, mode, surface, pairs)
                    self.assertTrue(ok, report)
            # A fourth series introduces an ambiguous pair in this default set.
            self.assertFalse(palette.validate(colors[:4], mode, surface, "all")[1])

    def test_normal_vision_can_fail_even_when_cvd_passes(self):
        report, ok = palette.validate(["#e87ba4", "#eb6834"], "light", "#fcfcfb")
        states = {name: state for name, state, _ in report}
        self.assertIn(states["CVD separation"], ("pass", "floor"))
        self.assertEqual(states["Normal-vision floor"], "fail")
        self.assertFalse(ok)

    def test_palette_cli_rejects_empty_and_malformed_colors(self):
        cases = [[value] for value in ("", ",,,", "#2a78d6junk", "#gggggg", "#abc")]
        cases += [
            ["#2a78d6", "--surface", "#ffffffjunk"],
            ["--contrast", "#000000", "#fff"],
            ["--apca", "#000000junk", "#ffffff"],
        ]
        for args in cases:
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, palette.__file__, *args],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_apca_reference_extremes_and_polarity(self):
        self.assertAlmostEqual(palette.apca("#000000", "#ffffff"), 106.04, places=2)
        self.assertAlmostEqual(palette.apca("#ffffff", "#000000"), -107.88, places=2)
        self.assertEqual(palette.apca("#123456", "#123456"), 0)

    def test_ordinal_ramp_rejects_out_of_order_steps(self):
        ramp = ["#86b6ef", "#3987e5", "#1c5cab"]
        report, ok = palette.validate_ordinal(ramp, "light", "#fcfcfb")
        self.assertTrue(ok, report)
        report, ok = palette.validate_ordinal(
            [ramp[0], ramp[2], ramp[1]], "light", "#fcfcfb"
        )
        self.assertFalse(ok, report)


if __name__ == "__main__":
    unittest.main()
