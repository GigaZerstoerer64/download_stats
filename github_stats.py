import requests
import json
from pathlib import Path

GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"
REPO_FILE = "repos.txt"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}"
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
    for r in releases:
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
        "metadata": {
            "description": info.get("description"),
            "stars": info.get("stargazers_count"),
            "forks": info.get("forks_count"),
            "watchers": info.get("subscribers_count"),
            "open_issues": info.get("open_issues_count"),
            "size_kb": info.get("size"),
            "topics": info.get("topics"),
            "license": info.get("license", {}).get("name"),
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

    for repo in repos:
        repo = repo.strip()
        if repo:
            results.append(process_repo(repo))

    with open("github_stats_output.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nSaved results to github_stats_output.json")


if __name__ == "__main__":
    main()
