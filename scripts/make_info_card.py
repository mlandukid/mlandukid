"""
make_info_card.py

Hand-authors a small SVG that looks like the output of the `neofetch`
command: a title bar, then colored key/value rows.

Each line fades and slides in on a short stagger so the panel looks
like it's printing next to the ASCII portrait. Prints once and freezes
(no looping).

A STATIC=1 env var emits a frozen frame (no animation) for local
Quick Look previews.

Usage:
    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py

Output:
    info-card.svg
"""

import os
from pathlib import Path

STATIC = os.environ.get("STATIC") == "1"

WIDTH = 490
TITLE_BAR_H = 34
ROW_H = 30
PADDING_X = 20
FONT_FAMILY = '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace'

THEMES = {
    "dark": {
        "output": "info-card.svg",
        "bg": "#0d1117",
        "title_bar": "#161b22",
        "border": "#30363d",
        "key": "#39d353",
        "value": "#c9d1d9",
        "title_text": "#8b949e",
    },
    "light": {
        "output": "info-card-light.svg",
        "bg": "#ffffff",
        "title_bar": "#f6f8fa",
        "border": "#d0d7de",
        "key": "#1a7f37",
        "value": "#24292f",
        "title_text": "#57606a",
    },
}

ROWS = [
    ("Now", "Full-stack Developer / AI Engineer"),
    ("Prev", "Financial institution, telecom & fintech clients"),
    ("Stack", "Full stack (JS/TS + Java)"),
    ("Learning", "Robotics & Intelligent Systems (Eduvos)"),
    ("Highlights", "BSc Computer Science"),
]

STAGGER = 0.15   # seconds between each row's animation start
SLIDE_DUR = 0.4  # seconds for a row to fade/slide into place
SLIDE_DISTANCE = 14  # px each row slides in from


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(theme: dict) -> str:
    height = TITLE_BAR_H + ROW_H * len(ROWS) + 20

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}">'
    )
    parts.append(
        f'<style>'
        f'text {{ font-family: {FONT_FAMILY}; }}'
        f'.key {{ font-size: 13px; fill: {theme["key"]}; font-weight: 600; }}'
        f'.value {{ font-size: 13px; fill: {theme["value"]}; }}'
        f'.title {{ font-size: 12px; fill: {theme["title_text"]}; }}'
        f'</style>'
    )

    # outer card with rounded border
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" '
        f'rx="8" fill="{theme["bg"]}" stroke="{theme["border"]}" stroke-width="1" />'
    )

    # title bar
    parts.append(
        f'<path d="M0.5,8 a8,8 0 0 1 8,-7.5 L{WIDTH - 8.5},0.5 '
        f'a8,8 0 0 1 8,8 L{WIDTH - 0.5},{TITLE_BAR_H} L0.5,{TITLE_BAR_H} Z" '
        f'fill="{theme["title_bar"]}" />'
    )
    parts.append(
        f'<line x1="0.5" y1="{TITLE_BAR_H}" x2="{WIDTH - 0.5}" y2="{TITLE_BAR_H}" '
        f'stroke="{theme["border"]}" stroke-width="1" />'
    )
    # traffic-light dots
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        cx = PADDING_X + i * 18
        parts.append(f'<circle cx="{cx}" cy="{TITLE_BAR_H / 2}" r="5" fill="{color}" />')
    parts.append(
        f'<text x="{WIDTH / 2}" y="{TITLE_BAR_H / 2 + 4}" class="title" '
        f'text-anchor="middle">whoami.sh</text>'
    )

    # key/value rows
    key_x = PADDING_X
    value_x = PADDING_X + 100

    for i, (key, value) in enumerate(ROWS):
        y = TITLE_BAR_H + 26 + i * ROW_H
        safe_key = escape_xml(key)
        safe_value = escape_xml(value)
        start_time = i * STAGGER

        if STATIC:
            parts.append(f'<text x="{key_x}" y="{y}" class="key">{safe_key}</text>')
            parts.append(f'<text x="{value_x}" y="{y}" class="value">{safe_value}</text>')
        else:
            parts.append(
                f'<g opacity="0" transform="translate({SLIDE_DISTANCE},0)">'
            )
            parts.append(f'  <text x="{key_x}" y="{y}" class="key">{safe_key}</text>')
            parts.append(f'  <text x="{value_x}" y="{y}" class="value">{safe_value}</text>')
            parts.append(
                f'  <animate attributeName="opacity" from="0" to="1" '
                f'begin="{start_time:.3f}s" dur="{SLIDE_DUR}s" fill="freeze" />'
            )
            parts.append(
                f'  <animateTransform attributeName="transform" type="translate" '
                f'from="{SLIDE_DISTANCE},0" to="0,0" '
                f'begin="{start_time:.3f}s" dur="{SLIDE_DUR}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1" />'
            )
            parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    mode = "static frame" if STATIC else "animated"
    for name, theme in THEMES.items():
        svg = build_svg(theme)
        Path(theme["output"]).write_text(svg, encoding="utf-8")
        print(f"Done. Wrote {theme['output']} ({mode})")


if __name__ == "__main__":
    main()