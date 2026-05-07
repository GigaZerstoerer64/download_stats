import os
import requests
import json
from pathlib import Path
from datetime import datetime

STATS_GITHUB = os.getenv("STATS_GITHUB", "")
REPO_FILE = "repos_config.txt"
ARCHIVE_FILE = "github_stats_archive.json"
OUTPUT_FILE = "repos_stats.txt"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {STATS_GITHUB}"
}

API_BASE = "https://api.github.com"


def get_repo_info(repo):
    url = f"{API_BASE}/repos/{repo}"
    return requests.get(url, headers=HEADERS).json()


def get_traffic_views(repo):
    url = f"{API_BASE}/repos/{repo}/traffic/views"
    return requests.get(url, headers=HEADERS).json()


def get_traffic_clones(repo):
    url = f"{API_BASE}/repos/{repo}/traffic/clones"
    return requests.get(url, headers=HEADERS).json()


def get_traffic_popular_paths(repo):
    url = f"{API_BASE}/repos/{repo}/traffic/popular/paths"
    return requests.get(url, headers=HEADERS).json()


def get_traffic_popular_referrers(repo):
    url = f"{API_BASE}/repos/{repo}/traffic/popular/referrers"
    return requests.get(url, headers=HEADERS).json()


def get_releases(repo):
    url = f"{API_BASE}/repos/{repo}/releases"
    return requests.get(url, headers=HEADERS).json()


def summarize_release_downloads(releases):
    summary = []
    # Handle case where API returns an error or non-list response
    if not isinstance(releases, list):
        return summary
    
    for r in releases:
        if not isinstance(r, dict):
            continue
        total = sum(asset["download_count"] for asset in r.get("assets", []))
        summary.append({
            "name": r.get("name"),
            "tag": r.get("tag_name"),
            "total_downloads": total,
            "assets": [
                {
                    "name": a["name"],
                    "downloads": a["download_count"]
                }
                for a in r.get("assets", [])
            ]
        })
    return summary


def load_archive():
    """Load existing archive or create empty one"""
    if Path(ARCHIVE_FILE).exists():
        with open(ARCHIVE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_archive(archive):
    """Save archive to file"""
    with open(ARCHIVE_FILE, "w") as f:
        json.dump(archive, f, indent=2)


def format_stats_text(results):
    """Format results as comma-separated values"""
    lines = []

    # Header row
    lines.append(
        "repo,timestamp,description,stars,forks,watchers,open_issues,size_kb,"
        "license,topics,last_updated,views_14d,clones_14d"
    )

    for data in results:
        repo = data["repo"]
        meta = data["metadata"]
        traffic = data["traffic"]

        views_data = traffic.get("views", {})
        clones_data = traffic.get("clones", {})

        views_count = views_data.get("count", 0) if isinstance(views_data, dict) else 0
        clones_count = clones_data.get("count", 0) if isinstance(clones_data, dict) else 0

        topics = ";".join(meta.get("topics", [])) if meta.get("topics") else ""

        row = [
            repo,
            data["timestamp"],
            (meta.get("description") or "").replace(",", " "),
            str(meta.get("stars", 0)),
            str(meta.get("forks", 0)),
            str(meta.get("watchers", 0)),
            str(meta.get("open_issues", 0)),
            str(meta.get("size_kb", 0)),
            (meta.get("license") or ""),
            topics,
            meta.get("updated_at", ""),
            str(views_count),
            str(clones_count)
        ]

        lines.append(",".join(row))

    return "\n".join(lines)

def process_repo(repo):
    print(f"\n=== Processing {repo} ===")

    info = get_repo_info(repo)
    views = get_traffic_views(repo)
    clones = get_traffic_clones(repo)
    paths = get_traffic_popular_paths(repo)
    referrers = get_traffic_popular_referrers(repo)
    releases = get_releases(repo)

    return {
        "repo": repo,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metadata": {
            "description": info.get("description"),
            "stars": info.get("stargazers_count"),
            "forks": info.get("forks_count"),
            "watchers": info.get("subscribers_count"),
            "open_issues": info.get("open_issues_count"),
            "size_kb": info.get("size"),
            "topics": info.get("topics"),
            "license": info.get("license", {}).get("name") if info.get("license") else None,
            "updated_at": info.get("updated_at"),
        },
        "traffic": {
            "views": views,
            "clones": clones,
            "popular_paths": paths,
            "popular_referrers": referrers
        },
        "releases": summarize_release_downloads(releases)
    }


def main():
    repos = Path(REPO_FILE).read_text().strip().splitlines()
    results = []
    archive = load_archive()

    for repo in repos:
        repo = repo.strip()
        if repo:
            current_data = process_repo(repo)
            results.append(current_data)
            
            # Archive the data
            if repo not in archive:
                archive[repo] = []
            archive[repo].append(current_data)

    # Save current snapshot as text file
    with open(OUTPUT_FILE, "w") as f:
        f.write(format_stats_text(results))
    print(f"\nSaved current snapshot to {OUTPUT_FILE}")

    # Save to archive
    save_archive(archive)
    print(f"Saved historical data to {ARCHIVE_FILE}")


if __name__ == "__main__":
    main()
