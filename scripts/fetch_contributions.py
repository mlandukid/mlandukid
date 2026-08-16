"""
fetch_contributions.py

Fetches your public GitHub contribution calendar without any token or
the GraphQL API. GitHub serves the calendar as a public HTML fragment
at https://github.com/users/<username>/contributions -- the same
fragment the profile page itself uses.

Parses the day cells with BeautifulSoup and writes data/contributions.json
with the raw days plus derived stats (current streak, longest streak,
best day, monthly totals).

Usage:
    python scripts/fetch_contributions.py

Output:
    data/contributions.json
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

GITHUB_USERNAME = "mlandukid"
CONTRIB_URL = f"https://github.com/users/{GITHUB_USERNAME}/contributions"
OUTPUT_PATH = "data/contributions.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def fetch_contribution_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub renders each day as a <td> with data-date and a title/tooltip
    # containing the contribution count. Structure has shifted over the
    # years, so we handle both the older td[data-date] layout and newer
    # tool-tip based rendering.
    cells = soup.select("td[data-date]")
    for cell in cells:
        date_str = cell.get("data-date")
        level = cell.get("data-level")
        tooltip_id = cell.get("id")

        count = 0
        if tooltip_id:
            tooltip = soup.select_one(f'tool-tip[for="{tooltip_id}"]')
            if tooltip:
                text = tooltip.get_text(strip=True)
                digits = "".join(ch for ch in text.split(" ")[0] if ch.isdigit())
                count = int(digits) if digits else 0

        days.append(
            {
                "date": date_str,
                "count": count,
                "level": int(level) if level is not None else 0,
            }
        )

    return days


def compute_stats(days: list[dict]) -> dict:
    if not days:
        return {}

    sorted_days = sorted(days, key=lambda d: d["date"])

    total = sum(d["count"] for d in sorted_days)

    # streaks
    longest_streak = 0
    current_run = 0
    for d in sorted_days:
        if d["count"] > 0:
            current_run += 1
            longest_streak = max(longest_streak, current_run)
        else:
            current_run = 0

    # current streak = trailing run ending at the most recent day with data
    current_streak = 0
    for d in reversed(sorted_days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    best_day = max(sorted_days, key=lambda d: d["count"])

    monthly = defaultdict(int)
    for d in sorted_days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] += d["count"]

    return {
        "total_last_year": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "monthly_totals": dict(sorted(monthly.items())),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def main() -> None:
    print(f"Fetching contribution calendar for {GITHUB_USERNAME}...")
    html = fetch_contribution_html(GITHUB_USERNAME)

    print("Parsing day cells...")
    days = parse_days(html)

    if not days:
        raise RuntimeError(
            "No contribution cells found. GitHub may have changed the "
            "page structure, or the username may be wrong."
        )

    print(f"Parsed {len(days)} days. Computing stats...")
    stats = compute_stats(days)

    output = {"days": days, "stats": stats}

    Path("data").mkdir(exist_ok=True)
    Path(OUTPUT_PATH).write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"Done. Wrote {OUTPUT_PATH}")
    print(f"  Total (last year): {stats['total_last_year']}")
    print(f"  Current streak: {stats['current_streak']} days")
    print(f"  Longest streak: {stats['longest_streak']} days")


if __name__ == "__main__":
    main()