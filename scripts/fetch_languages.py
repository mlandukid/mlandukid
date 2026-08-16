"""
fetch_languages.py

Fetches your public repos from the GitHub REST API (no token needed
for public data) and aggregates language usage by bytes of code
across all repos, using the /languages endpoint per repo for accuracy
(a repo's primary "language" field alone undercounts secondary
languages).

Usage:
    python scripts/fetch_languages.py

Output:
    data/languages.json
"""

import json
import time
from pathlib import Path

import requests

GITHUB_USERNAME = "mlandukid"
OUTPUT_PATH = "data/languages.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/vnd.github+json",
}

# Skip forks by default -- they inflate your language stats with code
# you didn't write.
INCLUDE_FORKS = False


def fetch_repos(username: str) -> list[dict]:
    repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{username}/repos"
            f"?per_page=100&page={page}&type=owner"
        )
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def fetch_languages_for_repo(username: str, repo_name: str) -> dict:
    url = f"https://api.github.com/repos/{username}/{repo_name}/languages"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code == 404:
        return {}
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    print(f"Fetching public repos for {GITHUB_USERNAME}...")
    repos = fetch_repos(GITHUB_USERNAME)

    if not INCLUDE_FORKS:
        repos = [r for r in repos if not r.get("fork")]

    print(f"Found {len(repos)} repos. Fetching language breakdown for each...")

    totals: dict[str, int] = {}
    for repo in repos:
        name = repo["name"]
        langs = fetch_languages_for_repo(GITHUB_USERNAME, name)
        for lang, byte_count in langs.items():
            totals[lang] = totals.get(lang, 0) + byte_count
        # be polite to the unauthenticated rate limit
        time.sleep(0.2)

    total_bytes = sum(totals.values()) or 1
    breakdown = sorted(
        (
            {
                "language": lang,
                "bytes": count,
                "percent": round(count / total_bytes * 100, 1),
            }
            for lang, count in totals.items()
        ),
        key=lambda x: x["bytes"],
        reverse=True,
    )

    output = {
        "repo_count": len(repos),
        "languages": breakdown,
    }

    Path("data").mkdir(exist_ok=True)
    Path(OUTPUT_PATH).write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"Done. Wrote {OUTPUT_PATH}")
    for entry in breakdown[:5]:
        print(f"  {entry['language']}: {entry['percent']}%")


if __name__ == "__main__":
    main()
