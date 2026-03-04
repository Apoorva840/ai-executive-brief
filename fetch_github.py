import feedparser
import json
import os
from pathlib import Path

def fetch_github_trending():
    print("🌐 Fetching Trending GitHub Repositories (Python/AI)...")
    # Using a reliable RSS feed for trending Python projects
    URL = "https://github-rss.alexi.sh/trending/daily/python"
    
    try:
        feed = feedparser.parse(URL)
        repos = []
        
        # Take the top 15 trending entries
        for entry in feed.entries[:15]:
            repos.append({
                "title": entry.title,
                "url": entry.link,
                "summary": entry.description
            })
        
        # Ensure the 'data' directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Save to the exact path expected by process_toolbox.py
        output_path = data_dir / "raw_github_trending.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(repos, f, indent=4)
        
        print(f"✅ Saved {len(repos)} repos to {output_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to fetch GitHub data: {e}")
        return False

if __name__ == "__main__":
    fetch_github_trending()