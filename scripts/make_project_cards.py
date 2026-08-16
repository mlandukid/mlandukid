"""
make_project_cards.py

Hand-authors styled SVG cards for featured projects, matching the
terminal aesthetic of the rest of the profile. Each card shows a
project name, one-line description, and small tech badges. Cards
fade/slide in on a stagger, same treatment as the info card.

Usage:
    python scripts/make_project_cards.py
    STATIC=1 python scripts/make_project_cards.py

Output:
    project-cards.svg
    project-cards-light.svg
"""

import os
from pathlib import Path

STATIC = os.environ.get("STATIC") == "1"

CARD_WIDTH = 270
CARD_HEIGHT = 130
GAP = 20
PADDING = 16
FONT_FAMILY = '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace'

THEMES = {
    "dark": {
        "output": "project-cards.svg",
        "bg": "#0d1117",
        "card_bg": "#161b22",
        "border": "#30363d",
        "title": "#39d353",
        "desc": "#c9d1d9",
        "badge_bg": "#21262d",
        "badge_text": "#8b949e",
    },
    "light": {
        "output": "project-cards-light.svg",
        "bg": "#ffffff",
        "card_bg": "#f6f8fa",
        "border": "#d0d7de",
        "title": "#1a7f37",
        "desc": "#24292f",
        "badge_bg": "#eaeef2",
        "badge_text": "#57606a",
    },
}

PROJECTS = [
    {
        "name": "AmanziWatch",
        "desc": "Gauteng water & air quality tracker, mobile-first",
        "tags": ["React", "API"],
    },
    {
        "name": "EATS",
        "desc": "South African restaurant discovery platform",
        "tags": ["React", "Node"],
    },
    {
        "name": "LeadRadar",
        "desc": "Reddit/Twitter lead-gen SaaS (in progress)",
        "tags": ["SaaS", "Building"],
    },
]

STAGGER = 0.15
SLIDE_DUR = 0.4
SLIDE_DISTANCE = 14


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(theme: dict) -> str:
    total_width = len(PROJECTS) * CARD_WIDTH + (len(PROJECTS) - 1) * GAP
    height = CARD_HEIGHT

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {total_width} {height}" width="{total_width}" height="{height}">'
    )
    parts.append(
        f'<style>'
        f'text {{ font-family: {FONT_FAMILY}; }}'
        f'.title {{ font-size: 14px; font-weight: 600; fill: {theme["title"]}; }}'
        f'.desc {{ font-size: 11px; fill: {theme["desc"]}; }}'
        f'.badge-text {{ font-size: 9px; fill: {theme["badge_text"]}; }}'
        f'</style>'
    )
    parts.append(f'<rect width="100%" height="100%" fill="{theme["bg"]}" />')

    for i, project in enumerate(PROJECTS):
        x = i * (CARD_WIDTH + GAP)
        start_time = i * STAGGER

        group_open = ""
        group_close = ""
        if not STATIC:
            group_open = (
                f'<g opacity="0" transform="translate({x},{SLIDE_DISTANCE})">'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{start_time:.3f}s" dur="{SLIDE_DUR}s" fill="freeze" />'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="{x},{SLIDE_DISTANCE}" to="{x},0" '
                f'begin="{start_time:.3f}s" dur="{SLIDE_DUR}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1" />'
            )
            group_close = "</g>"
        else:
            group_open = f'<g transform="translate({x},0)">'
            group_close = "</g>"

        parts.append(group_open)

        # card background
        parts.append(
            f'<rect x="0" y="0" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" '
            f'rx="8" fill="{theme["card_bg"]}" stroke="{theme["border"]}" '
            f'stroke-width="1" />'
        )

        # title
        parts.append(
            f'<text x="{PADDING}" y="{PADDING + 14}" class="title">'
            f'{escape_xml(project["name"])}</text>'
        )

        # description, simple word-wrap at ~34 chars
        desc = project["desc"]
        words = desc.split(" ")
        lines = []
        current = ""
        for word in words:
            candidate = (current + " " + word).strip()
            if len(candidate) > 34:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)

        for li, line in enumerate(lines[:3]):
            y = PADDING + 38 + li * 15
            parts.append(
                f'<text x="{PADDING}" y="{y}" class="desc">{escape_xml(line)}</text>'
            )

        # tag badges along the bottom
        badge_y = CARD_HEIGHT - 28
        bx = PADDING
        for tag in project["tags"]:
            badge_w = len(tag) * 6 + 16
            parts.append(
                f'<rect x="{bx}" y="{badge_y}" width="{badge_w}" height="18" '
                f'rx="9" fill="{theme["badge_bg"]}" />'
            )
            parts.append(
                f'<text x="{bx + badge_w / 2}" y="{badge_y + 12}" '
                f'class="badge-text" text-anchor="middle">{escape_xml(tag)}</text>'
            )
            bx += badge_w + 8

        parts.append(group_close)

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
