"""
render_language_bar.py

Renders data/languages.json as a slim horizontal stacked bar showing
top language usage by bytes across your public repos, with a legend
row underneath. Reveals once with each segment growing in left to
right, staggered, then freezes.

Usage:
    python scripts/render_language_bar.py

Input:
    data/languages.json

Output:
    language-bar.svg
    language-bar-light.svg
"""

import json
from pathlib import Path

INPUT_PATH = "data/languages.json"

WIDTH = 860
BAR_HEIGHT = 14
TOP_MARGIN = 10
LEGEND_ROW_H = 20
MAX_LANGS = 6  # top N shown individually; rest grouped as "Other"

THEMES = {
    "dark": {
        "output": "language-bar.svg",
        "bg": "#0d1117",
        "text": "#8b949e",
        "track": "#161b22",
    },
    "light": {
        "output": "language-bar-light.svg",
        "bg": "#ffffff",
        "text": "#57606a",
        "track": "#ebedf0",
    },
}

# GitHub-linguist-ish colors for common languages; falls back to a
# generated gray-blue for anything not listed.
LANGUAGE_COLORS = {
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#3572A5",
    "Java": "#b07219",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Clojure": "#db5855",
    "Shell": "#89e051",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Dockerfile": "#384d54",
    "Vue": "#41b883",
    "Other": "#6e7681",
}

FALLBACK_COLOR = "#6e7681"


def load_data() -> dict:
    path = Path(INPUT_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_PATH}. Run fetch_languages.py first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def collapse_languages(languages: list[dict]) -> list[dict]:
    if len(languages) <= MAX_LANGS:
        return languages

    top = languages[:MAX_LANGS]
    rest = languages[MAX_LANGS:]
    other_bytes = sum(r["bytes"] for r in rest)
    other_percent = round(sum(r["percent"] for r in rest), 1)
    if other_bytes > 0:
        top.append({"language": "Other", "bytes": other_bytes, "percent": other_percent})
    return top


def color_for(language: str) -> str:
    return LANGUAGE_COLORS.get(language, FALLBACK_COLOR)


def build_svg(data: dict, theme: dict) -> str:
    languages = collapse_languages(data.get("languages", []))
    total_percent = sum(lang["percent"] for lang in languages) or 1

    parts = []
    legend_rows = (len(languages) + 2) // 3  # wrap legend at ~3 per row
    height = TOP_MARGIN + BAR_HEIGHT + 14 + legend_rows * LEGEND_ROW_H

    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}">'
    )
    parts.append(
        '<style>'
        f'text {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", '
        f'Menlo, monospace; font-size: 11px; fill: {theme["text"]}; }}'
        '.seg { animation: grow 0.5s ease-out both; transform-origin: left; }'
        '@keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }'
        '</style>'
    )
    parts.append(f'<rect width="100%" height="100%" fill="{theme["bg"]}" />')

    # track background
    parts.append(
        f'<rect x="0" y="{TOP_MARGIN}" width="{WIDTH}" height="{BAR_HEIGHT}" '
        f'rx="7" fill="{theme["track"]}" />'
    )

    # stacked segments
    x_cursor = 0.0
    for i, lang in enumerate(languages):
        seg_width = (lang["percent"] / total_percent) * WIDTH
        color = color_for(lang["language"])
        delay = i * 0.08
        parts.append(
            f'<g class="seg" style="animation-delay: {delay:.2f}s" '
            f'transform="translate({x_cursor:.1f},0)">'
        )
        parts.append(
            f'<rect x="0" y="{TOP_MARGIN}" width="{seg_width:.1f}" height="{BAR_HEIGHT}" '
            f'fill="{color}">'
        )
        parts.append(f'<title>{lang["language"]} — {lang["percent"]}%</title>')
        parts.append("</rect>")
        parts.append("</g>")
        x_cursor += seg_width

    # rounded mask over the whole bar so segment edges don't poke out
    parts.append(
        f'<rect x="0" y="{TOP_MARGIN}" width="{WIDTH}" height="{BAR_HEIGHT}" '
        f'rx="7" fill="none" stroke="{theme["bg"]}" stroke-width="0" />'
    )

    # legend, wrapped ~3 per row
    legend_y_start = TOP_MARGIN + BAR_HEIGHT + 22
    col_width = WIDTH // 3
    for i, lang in enumerate(languages):
        row = i // 3
        col = i % 3
        lx = col * col_width
        ly = legend_y_start + row * LEGEND_ROW_H
        color = color_for(lang["language"])
        parts.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}" />'
        )
        parts.append(
            f'<text x="{lx + 16}" y="{ly}">{lang["language"]} {lang["percent"]}%</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    print(f"Reading {INPUT_PATH}...")
    data = load_data()

    for name, theme in THEMES.items():
        print(f"Rendering {name} language bar SVG...")
        svg = build_svg(data, theme)
        Path(theme["output"]).write_text(svg, encoding="utf-8")
        print(f"Done. Wrote {theme['output']}")


if __name__ == "__main__":
    main()
