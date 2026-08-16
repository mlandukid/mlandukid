"""
render_heatmap_svg.py

Renders data/contributions.json as the classic 53-week x 7-day
calendar of rounded, colored boxes using a GitHub-ish green ramp.

Reveals once with a diagonal, line-after-line slide-down (CSS
keyframes that play on load, then freeze -- no looping "glow"), plus
a Less->More legend and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py

Input:
    data/contributions.json

Output:
    contrib-heatmap.svg
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

INPUT_PATH = "data/contributions.json"

THEMES = {
    "dark": {
        "output": "contrib-heatmap.svg",
        "bg": "#0d1117",
        "text": "#8b949e",
        # none -> brightest (level 5 is a neon top end)
        "palette": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"],
    },
    "light": {
        "output": "contrib-heatmap-light.svg",
        "bg": "#ffffff",
        "text": "#57606a",
        "palette": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39", "#0d4429"],
    },
}

CELL = 11
GAP = 3
LEFT_MARGIN = 30
TOP_MARGIN = 20
BOTTOM_MARGIN = 40
WEEKS = 53
DAYS_PER_WEEK = 7

MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def load_data() -> dict:
    path = Path(INPUT_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_PATH}. Run fetch_contributions.py first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def level_to_color(level: int, palette: list[str]) -> str:
    idx = max(0, min(len(palette) - 1, level))
    return palette[idx]


def build_week_grid(days):
    """Arrange days into columns (weeks) of 7 rows (Sun-Sat), most recent last."""
    by_date = {d["date"]: d for d in days if d.get("date")}
    if not by_date:
        return []

    dates_sorted = sorted(by_date.keys())
    last_date = datetime.strptime(dates_sorted[-1], "%Y-%m-%d")

    # find the Saturday ending the final week and the Sunday starting 53 weeks back
    end = last_date
    end_dow = (end.weekday() + 1) % 7  # convert Mon=0 -> Sun=0 indexing
    end = end + timedelta(days=(6 - end_dow))
    start = end - timedelta(weeks=WEEKS - 1) - timedelta(days=6)

    weeks = []
    cursor = start
    for _ in range(WEEKS):
        week = []
        for _ in range(DAYS_PER_WEEK):
            key = cursor.strftime("%Y-%m-%d")
            week.append(by_date.get(key))
            cursor += timedelta(days=1)
        weeks.append(week)

    return weeks


def build_svg(data: dict, theme: dict) -> str:
    days = data.get("days", [])
    stats = data.get("stats", {})
    palette = theme["palette"]

    weeks = build_week_grid(days)
    grid_width = LEFT_MARGIN + WEEKS * (CELL + GAP)
    grid_height = TOP_MARGIN + DAYS_PER_WEEK * (CELL + GAP) + BOTTOM_MARGIN

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {grid_width} {grid_height}" '
        f'width="{grid_width}" height="{grid_height}">'
    )
    parts.append(
        '<style>'
        f'text {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", '
        f'Menlo, monospace; fill: {theme["text"]}; }}'
        '.cell { animation: reveal 0.4s ease-out both; }'
        '@keyframes reveal { from { opacity: 0; transform: scale(0.4); } '
        'to { opacity: 1; transform: scale(1); } }'
        '</style>'
    )
    parts.append(f'<rect width="100%" height="100%" fill="{theme["bg"]}" />')

    # month labels along the top
    seen_months = set()
    for week_idx, week in enumerate(weeks):
        first_real_day = next((d for d in week if d), None)
        if not first_real_day:
            continue
        month = first_real_day["date"][:7]
        month_num = int(first_real_day["date"][5:7])
        if month not in seen_months:
            seen_months.add(month)
            x = LEFT_MARGIN + week_idx * (CELL + GAP)
            parts.append(
                f'<text x="{x}" y="{TOP_MARGIN - 6}" font-size="10">'
                f'{MONTH_LABELS[month_num - 1]}</text>'
            )

    # day-of-week labels (Mon, Wed, Fri)
    dow_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for dow, label in dow_labels.items():
        y = TOP_MARGIN + dow * (CELL + GAP) + CELL - 1
        parts.append(f'<text x="0" y="{y}" font-size="9">{label}</text>')

    # cells, diagonal stagger: delay based on (week + day) so it reveals
    # top-left to bottom-right in a diagonal sweep, line after line
    for week_idx, week in enumerate(weeks):
        for day_idx, day in enumerate(week):
            x = LEFT_MARGIN + week_idx * (CELL + GAP)
            y = TOP_MARGIN + day_idx * (CELL + GAP)
            level = day["level"] if day else 0
            color = level_to_color(level, palette)
            delay = (week_idx + day_idx) * 0.006
            title = ""
            if day:
                title = f'{day["count"]} contributions on {day["date"]}'

            parts.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2" fill="{color}" style="animation-delay: {delay:.3f}s">'
            )
            if title:
                parts.append(f'<title>{title}</title>')
            parts.append("</rect>")

    # legend: Less -> More
    legend_y = TOP_MARGIN + DAYS_PER_WEEK * (CELL + GAP) + 18
    legend_x = LEFT_MARGIN
    parts.append(f'<text x="{legend_x}" y="{legend_y + 8}" font-size="10">Less</text>')
    lx = legend_x + 32
    for color in palette:
        parts.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{color}" />'
        )
        lx += CELL + GAP
    parts.append(f'<text x="{lx + 4}" y="{legend_y + 8}" font-size="10">More</text>')

    # stats footer
    total = stats.get("total_last_year", 0)
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer = f"{total} contributions in the last year  \u00b7  current streak {streak}  \u00b7  longest {longest}"
    parts.append(
        f'<text x="{grid_width - LEFT_MARGIN}" y="{legend_y + 8}" '
        f'font-size="10" text-anchor="end">{footer}</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    print(f"Reading {INPUT_PATH}...")
    data = load_data()

    for name, theme in THEMES.items():
        print(f"Rendering {name} heatmap SVG...")
        svg = build_svg(data, theme)
        Path(theme["output"]).write_text(svg, encoding="utf-8")
        print(f"Done. Wrote {theme['output']}")


if __name__ == "__main__":
    main()