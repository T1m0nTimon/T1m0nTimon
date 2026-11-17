import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "T1m0nTimon"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT = Path("assets/github-stats.svg")
API = "https://api.github.com"


def api_get(path):
    request = urllib.request.Request(
        API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}" if TOKEN else "",
            "User-Agent": "T1m0nTimon-profile-stats",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_repositories():
    repositories = []
    page = 1
    while True:
        batch = api_get(
            f"/users/{USERNAME}/repos?type=owner&sort=updated&per_page=100&page={page}"
        )
        if not batch:
            break
        repositories.extend(repo for repo in batch if not repo.get("private", False))
        if len(batch) < 100:
            break
        page += 1
    return repositories


def text(x, y, value, size=16, color="#F2F2F5", weight="normal"):
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,sans-serif" '
        f'font-size="{size}" font-weight="{weight}">{escape(str(value))}</text>'
    )


def make_svg(repositories, stars, forks, languages):
    total_repos = len(repositories)
    total_bytes = sum(languages.values()) or 1
    top_languages = languages.most_common(5)
    language_rows = []
    colors = ["#F2F2F5", "#C8C8D0", "#A0A0AA", "#777780", "#55555F"]
    for index, (name, amount) in enumerate(top_languages):
        y = 108 + index * 23
        percent = amount / total_bytes * 100
        language_rows.append(text(555, y, name, 13, "#F2F2F5"))
        language_rows.append(
            f'<rect x="690" y="{y-12}" width="210" height="8" rx="4" fill="#25252C"/>'
        )
        language_rows.append(
            f'<rect x="690" y="{y-12}" width="{210 * percent / 100:.1f}" '
            f'height="8" rx="4" fill="{colors[index]}"/>'
        )
        language_rows.append(text(920, y, f"{percent:.1f}%", 12, "#BFC0C8"))
    if not language_rows:
        language_rows.append(text(555, 108, "No public language data yet", 13, "#BFC0C8"))

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="250" viewBox="0 0 1000 250" role="img" aria-label="Public GitHub repository statistics">',
        '<rect width="1000" height="250" rx="18" fill="#08080B" stroke="#38383F"/>',
        text(36, 42, "PUBLIC GITHUB OVERVIEW", 15, "#BFC0C8", "bold"),
        text(36, 94, total_repos, 30, "#F2F2F5", "bold"),
        text(36, 119, "PUBLIC REPOSITORIES", 11, "#777780", "bold"),
        text(205, 94, stars, 30, "#F2F2F5", "bold"),
        text(205, 119, "TOTAL STARS", 11, "#777780", "bold"),
        text(365, 94, forks, 30, "#F2F2F5", "bold"),
        text(365, 119, "TOTAL FORKS", 11, "#777780", "bold"),
        text(555, 42, "LANGUAGES BY CODE SIZE", 15, "#BFC0C8", "bold"),
        *language_rows,
        text(36, 220, "Generated from GitHub's public API · Updated automatically", 11, "#777780"),
        "</svg>",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(parts), encoding="utf-8")


def main():
    repositories = get_repositories()
    stars = sum(repo.get("stargazers_count", 0) for repo in repositories)
    forks = sum(repo.get("forks_count", 0) for repo in repositories)
    language_totals = Counter()
    for repo in repositories:
        if repo.get("size", 0) == 0:
            continue
        try:
            language_totals.update(api_get(f"/repos/{USERNAME}/{urllib.parse.quote(repo['name'])}/languages"))
            time.sleep(0.05)
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            print(f"Skipping language data for {repo['name']}: {error}")
    make_svg(repositories, stars, forks, language_totals)
    print(f"Updated stats for {len(repositories)} public repositories.")


if __name__ == "__main__":
    main()
