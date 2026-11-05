#!/usr/bin/env python3
"""Static checks for a HAL HTML brief.

Errors (exit 1) enforce the analyse skill's hard rules: no placeholders or
leftover template markers, html/body structure, self-contained (no external
scripts/styles/images/fonts), and no JS in a document brief. Warnings flag
things worth a look (no chart, no table, very short text); --strict promotes
them to failures. For the Marp deck variant pass --deck: it allows the
<script> tags Marp emits, while the placeholder and external-asset checks
still apply.

This is document lint, not a sanitizer for untrusted HTML.

Usage:
  uv run verify_brief.py <run>/brief.html
  uv run verify_brief.py <run>/brief.html --deck    # Marp deck variant
  uv run verify_brief.py <run>/brief.html --strict  # warnings fail too
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

PLACEHOLDERS = re.compile(r"\b(TODO|FIXME|lorem ipsum|placeholder)\b|{{|}}", re.I)
COMMENT = re.compile(r"<!--(.*?)-->", re.S)
# external CSS pulls: url(http...), url(//...), @import — data: URIs are fine
CSS_EXTERNAL = re.compile(r"url\(\s*['\"]?\s*(?:https?:)?//|@import\b", re.I)
TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "brief_template.html"


def _norm(comment_text: str) -> str:
    return " ".join(comment_text.split())


def template_markers() -> set[str]:
    """Every comment in the brief template is a fill-me marker; any of them
    surviving verbatim in a shipped brief means a section was never filled."""
    if not TEMPLATE.exists():
        return set()
    return {
        _norm(m)
        for m in COMMENT.findall(TEMPLATE.read_text(encoding="utf-8"))
        if _norm(m)
    }


class BriefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: set[str] = set()
        self.text_parts: list[str] = []
        self.asset_refs: list[str] = []  # src/srcset anywhere, href on <link>
        self.anchor_links: list[str] = []  # href on <a>
        self.style_chunks: list[str] = []
        self._in_style = False
        self._in_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.tags.add(tag)
        if tag == "style":
            self._in_style = True
        if tag == "script":
            self._in_script = True
        attr_map = {key.lower(): value or "" for key, value in attrs}
        for attr in ("src", "srcset"):
            if attr in attr_map:
                self.asset_refs.append(attr_map[attr])
        if "href" in attr_map:
            (self.anchor_links if tag == "a" else self.asset_refs).append(
                attr_map["href"]
            )
        if "style" in attr_map:
            self.style_chunks.append(attr_map["style"])

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "style":
            self._in_style = False
        if tag.lower() == "script":
            self._in_script = False

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.style_chunks.append(data)
            return
        if self._in_script:
            return  # JS internals are not reader-facing content
        cleaned = data.strip()
        if cleaned:
            self.text_parts.append(cleaned)


def is_external(url: str) -> bool:
    return url.startswith(("http://", "https://", "//"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path, help="path to brief.html")
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as failures"
    )
    parser.add_argument(
        "--deck",
        action="store_true",
        help="Marp deck variant: allow the <script> tags Marp emits",
    )
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    brief = args.brief
    if not brief.exists():
        errors.append(f"brief does not exist: {brief}")
    elif brief.stat().st_size == 0:
        errors.append(f"brief is empty: {brief}")

    text = brief.read_text(encoding="utf-8") if brief.exists() else ""

    if text:
        markers = template_markers()
        comments = COMMENT.findall(text)
        leftover = sorted({_norm(m) for m in comments} & markers)
        if leftover:
            shown = "; ".join(
                f"<!-- {m[:60]}{'…' if len(m) > 60 else ''} -->" for m in leftover[:4]
            )
            errors.append(
                f"{len(leftover)} unfilled template marker(s) left in the brief: {shown}"
            )

        parser_state = BriefParser()
        parser_state.feed(text)
        plain_text = " ".join(parser_state.text_parts)
        # reader-facing text and comments only — style/script internals (e.g. a
        # ::placeholder CSS rule, Marp's runtime JS) are not shipped placeholders
        if PLACEHOLDERS.search(plain_text) or any(
            PLACEHOLDERS.search(c) for c in comments
        ):
            errors.append("brief contains placeholder-like text")
        if "html" not in parser_state.tags or "body" not in parser_state.tags:
            errors.append("brief is missing html/body structure")
        if "script" in parser_state.tags and not args.deck:
            errors.append(
                "brief contains <script> — a document brief is static HTML, "
                "no JS (pass --deck only for the Marp deck variant)"
            )

        external_assets = [u for u in parser_state.asset_refs if is_external(u)]
        if external_assets:
            errors.append(
                "brief loads external assets (must be self-contained): "
                + ", ".join(external_assets[:5])
            )
        css = "\n".join(parser_state.style_chunks)
        if CSS_EXTERNAL.search(css):
            errors.append(
                "brief CSS pulls external resources (url(http…)/url(//…)/@import) "
                "— inline fonts/images as data: URIs or drop them"
            )

        external_links = [u for u in parser_state.anchor_links if is_external(u)]
        if external_links:
            warnings.append(
                "brief has external <a> links (fine for citations, verify intended): "
                + ", ".join(external_links[:5])
            )
        if not ({"h1", "h2"} & parser_state.tags):
            warnings.append("brief has no h1/h2 heading")
        if len(plain_text) < 300:
            warnings.append(f"brief text is short ({len(plain_text)} characters)")
        if "svg" not in parser_state.tags:
            warnings.append("brief has no inline SVG chart")
        if "table" not in parser_state.tags:
            warnings.append("brief has no table")
        if not re.search(r"watch|caveat|method", plain_text, re.I):
            warnings.append(
                "brief text does not mention watch-items, caveats, or methodology"
            )

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)

    if errors or (args.strict and warnings):
        return 1
    print(f"ok: verified brief {brief}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
