"""
make_ascii_svg.py

Converts source-prepped.png into a monochrome, self-typing ASCII SVG.

Design choices:
  - Monochrome: one light-gray fill. Per-character rainbow coloring is
    exactly what makes most ASCII portraits look like static.
  - High contrast: a busy/white background washes out to the space
    glyph, so only the subject prints.
  - Animation: each row is wrapped in a horizontal clip that wipes
    left-to-right (a small block "cursor" rides the wipe edge),
    staggered top to bottom. Prints once and freezes (no looping).
    Pure SMIL inside the SVG -- GitHub renders it fine, no JS needed.

Usage:
    python scripts/make_ascii_svg.py

Input:
    source-prepped.png  (grayscale, from prep_photo.py)

Output:
    ascii-portrait.svg
"""

from pathlib import Path

from PIL import Image

INPUT_PATH = "source-prepped.png"

GRID_COLS = 100
GRID_ROWS = 53

# bright (sparse) -> dark (dense). Leading space clears background to nothing.
RAMP = " .`:-=+*cs#%@"

CHAR_W = 6.0
CHAR_H = 11.0
FONT_SIZE = 11

THEMES = {
    "dark": {
        "output": "ascii-portrait.svg",
        "bg": "#0d1117",
        "fill": "#c9d1d9",
    },
    "light": {
        "output": "ascii-portrait-light.svg",
        "bg": "#ffffff",
        "fill": "#24292f",
    },
}

ROW_STAGGER = 0.035   # seconds between each row starting its wipe
WIPE_DURATION = 0.5   # seconds for a single row to fully reveal


def brightness_to_char(value: int) -> str:
    """Map a 0-255 grayscale value to a ramp character (dark end wins)."""
    idx = int((255 - value) / 255 * (len(RAMP) - 1))
    idx = max(0, min(len(RAMP) - 1, idx))
    return RAMP[idx]


def build_ascii_grid(image_path: str) -> list[str]:
    img = Image.open(image_path).convert("L")
    small = img.resize((GRID_COLS, GRID_ROWS), Image.LANCZOS)
    pixels = small.load()

    rows = []
    for y in range(GRID_ROWS):
        row_chars = []
        for x in range(GRID_COLS):
            row_chars.append(brightness_to_char(pixels[x, y]))
        rows.append("".join(row_chars))
    return rows


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(rows: list[str], theme: dict) -> str:
    width = GRID_COLS * CHAR_W
    height = GRID_ROWS * CHAR_H
    fill_color = theme["fill"]

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}">'
    )
    parts.append(
        f'<rect width="100%" height="100%" fill="{theme["bg"]}" />'
    )
    parts.append(
        f'<style>text {{ font-family: "SFMono-Regular", Consolas, '
        f'"Liberation Mono", Menlo, monospace; font-size: {FONT_SIZE}px; '
        f'fill: {fill_color}; white-space: pre; }}</style>'
    )

    for row_idx, row_text in enumerate(rows):
        y = (row_idx + 1) * CHAR_H
        start_time = row_idx * ROW_STAGGER
        row_width = len(row_text) * CHAR_W
        clip_id = f"clip{row_idx}"
        safe_text = escape_xml(row_text)

        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(f'  <rect x="0" y="{y - CHAR_H:.1f}" width="0" height="{CHAR_H:.1f}">')
        parts.append(
            f'    <animate attributeName="width" from="0" to="{row_width:.1f}" '
            f'begin="{start_time:.3f}s" dur="{WIPE_DURATION}s" '
            f'fill="freeze" calcMode="linear" />'
        )
        parts.append("  </rect>")
        parts.append("</clipPath>")

        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(
            f'  <text x="0" y="{y:.1f}">{safe_text}</text>'
        )
        parts.append("</g>")

        # small cursor block riding the wipe edge
        cursor_id = f"cursor{row_idx}"
        parts.append(
            f'<rect x="0" y="{y - CHAR_H:.1f}" width="{CHAR_W:.1f}" height="{CHAR_H:.1f}" '
            f'fill="{fill_color}" opacity="0.85">'
        )
        parts.append(
            f'  <animate attributeName="x" from="0" to="{row_width:.1f}" '
            f'begin="{start_time:.3f}s" dur="{WIPE_DURATION}s" '
            f'fill="freeze" calcMode="linear" />'
        )
        parts.append(
            f'  <animate attributeName="opacity" from="0.85" to="0" '
            f'begin="{start_time + WIPE_DURATION:.3f}s" dur="0.15s" fill="freeze" />'
        )
        parts.append(f'  <set attributeName="width" to="{CHAR_W:.1f}" begin="0s" />')
        parts.append("</rect>")

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    if not Path(INPUT_PATH).exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_PATH}. Run prep_photo.py first."
        )

    print(f"Reading {INPUT_PATH}...")
    rows = build_ascii_grid(INPUT_PATH)

    for name, theme in THEMES.items():
        print(f"Building {name} {GRID_COLS}x{GRID_ROWS} SVG with staggered wipe animation...")
        svg = build_svg(rows, theme)
        Path(theme["output"]).write_text(svg, encoding="utf-8")
        print(f"Done. Wrote {theme['output']}")


if __name__ == "__main__":
    main()