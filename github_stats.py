import os
import requests
import json
from pathlib import Path
from datetime import datetime

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN")
REPO_FILE = "repos.txt"
ARCHIVE_FILE = "github_stats_archive.json"
OUTPUT_FILE = "repos_stats.txt"

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
    """Format results as readable text"""
    lines = []
    lines.append("=" * 80)
    lines.append(f"GitHub Repository Statistics - {datetime.utcnow().isoformat()}Z")
    lines.append("=" * 80)
    lines.append("")
    
    for data in results:
        repo = data["repo"]
        meta = data["metadata"]
        traffic = data["traffic"]
        releases = data["releases"]
        
        lines.append(f"Repository: {repo}")
        lines.append(f"Timestamp: {data['timestamp']}")
        lines.append("-" * 80)
        
        # Metadata
        lines.append("Metadata:")
        lines.append(f"  Description: {meta.get('description', 'N/A')}")
        lines.append(f"  Stars: {meta.get('stars', 0)}")
        lines.append(f"  Forks: {meta.get('forks', 0)}")
        lines.append(f"  Watchers: {meta.get('watchers', 0)}")
        lines.append(f"  Open Issues: {meta.get('open_issues', 0)}")
        lines.append(f"  Size (KB): {meta.get('size_kb', 0)}")
        lines.append(f"  License: {meta.get('license', 'N/A')}")
        lines.append(f"  Topics: {', '.join(meta.get('topics', [])) if meta.get('topics') else 'N/A'}")
        lines.append(f"  Last Updated: {meta.get('updated_at', 'N/A')}")
        
        # Traffic
        lines.append("Traffic:")
        views_data = traffic.get("views", {})
        if isinstance(views_data, dict) and views_data.get('count'):
            lines.append(f"  Views (14d): {views_data['count']}")
        clones_data = traffic.get("clones", {})
        if isinstance(clones_data, dict) and clones_data.get('count'):
            lines.append(f"  Clones (14d): {clones_data['count']}")
        
        # Popular Paths
        paths_data = traffic.get("popular_paths", [])
        if isinstance(paths_data, list) and paths_data:
            lines.append("  Top Paths:")
            for i, path in enumerate(paths_data[:5], 1):
                lines.append(f"    {i}. {path.get('path', 'N/A')} - {path.get('count', 0)} views")
        
        # Popular Referrers
        referrers_data = traffic.get("popular_referrers", [])
        if isinstance(referrers_data, list) and referrers_data:
            lines.append("  Top Referrers:")
            for i, ref in enumerate(referrers_data[:5], 1):
                lines.append(f"    {i}. {ref.get('referrer', 'N/A')} - {ref.get('count', 0)} views")
        
        # Releases
        if releases:
            lines.append("Latest Releases:")
            for rel in releases[:5]:
                lines.append(f"  {rel.get('name', rel.get('tag', 'N/A'))}")
                lines.append(f"    Total Downloads: {rel.get('total_downloads', 0)}")
                for asset in rel.get('assets', [])[:3]:
                    lines.append(f"      - {asset['name']}: {asset['downloads']} downloads")
        
        lines.append("")
    
    lines.append("=" * 80)
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
