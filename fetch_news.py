import feedparser
import json
import os
import re
import socket
import requests
from datetime import date, datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

# ============================
# BASE DIRECTORY (CI SAFE)
# ============================
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RAW_NEWS_FILE = DATA_DIR / "raw_news.json"
SENT_FILE = DATA_DIR / "sent_urls.json"
FAILED_FEEDS_FILE = DATA_DIR / "failed_feeds.json"

TODAY = date.today().isoformat()  # YYYY-MM-DD

# ============================
# SOURCES (HIGH SIGNAL)
# ============================
SOURCES = [
    {"name": "TechCrunch AI", "rss": "https://techcrunch.com/tag/artificial-intelligence/feed/"},
    {"name": "MIT Technology Review AI", "rss": "https://www.technologyreview.com/topic/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI", "rss": "https://venturebeat.com/category/ai/feed/"},
    {"name": "Wired AI", "rss": "https://www.wired.com/feed/tag/ai/latest/rss"},
    {"name": "Arxiv AI", "rss": "http://export.arxiv.org/rss/cs.AI"},
    {"name": "Microsoft Research", "rss": "https://www.microsoft.com/en-us/research/feed/"},
    {"name": "Hugging Face Blog", "rss": "https://huggingface.co/blog/feed.xml"}
]

# ============================
# HELPERS
# ============================
def clean_summary(text, max_chars=350):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text.replace("\n", " ").strip())
    return text[:max_chars]

# ============================
# LOAD SENT HISTORY
# ============================
if SENT_FILE.exists():
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        try:
            sent_log = json.load(f)
            if not isinstance(sent_log, dict):
                sent_log = {}
        except json.JSONDecodeError:
            sent_log = {}
else:
    sent_log = {}

# Skip URLs already seen today
sent_today = set(sent_log.get(TODAY, []))
print(f"Loaded {len(sent_today)} URLs already used today")

articles = []
skipped = 0
failed_feeds = []

# ============================
# FETCH FEEDS
# ============================
for source in SOURCES:
    try:
        socket.setdefaulttimeout(10)
        feed = feedparser.parse(
            source["rss"],
            request_headers={"User-Agent": "AI-Executive-Brief/1.0"}
        )

        # Fallback for feedparser failures (e.g., VentureBeat encoding)
        if feed.bozo:
            print(f"[WARN] feedparser failed for {source['name']}, attempting fallback...")
            try:
                resp = requests.get(source["rss"], headers={"User-Agent": "AI-Executive-Brief/1.0"}, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.content, "xml")
                entries = soup.find_all("item") or soup.find_all("entry")
                
                for entry in entries:
                    link_tag = entry.find("link")
                    title_tag = entry.find("title")
                    summary_tag = entry.find("summary") or entry.find("description")

                    link = link_tag.text.strip() if link_tag else None
                    title = title_tag.text.strip() if title_tag else None
                    summary = summary_tag.text.strip() if summary_tag else ""

                    # GUARD CLAUSE: Ignore broken entries
                    if not link or not title:
                        continue
                    if link in sent_today:
                        skipped += 1
                        continue

                    articles.append({
                        "title": title,
                        "summary": clean_summary(summary),
                        "url": link,
                        "source": source["name"]
                    })
                    sent_today.add(link)
                continue 
            except Exception as e:
                print(f"[ERROR] Fallback failed for {source['name']}: {e}")
                failed_feeds.append({"name": source["name"], "error": str(e)})
                continue

        # Normal processing
        print(f"{source['name']} entries: {len(feed.entries)}")
        for entry in feed.entries:
            link = entry.get("link")
            title = entry.get("title")
            summary = entry.get("summary", "")

            # GUARD CLAUSE: Skip if link or title is missing
            #if not link or not title:
            #    continue

            if link in sent_today:
                skipped += 1
                continue

            articles.append({
                "title": title.strip(),
                "summary": clean_summary(summary),
                "url": link,
                "source": source["name"]
            })
            sent_today.add(link)

    except Exception as e:
        print(f"[ERROR] Could not fetch {source['name']}: {e}")
        failed_feeds.append({"name": source["name"], "error": str(e)})

# ============================
# DEDUPLICATION
# ============================
seen_titles = set()
final_articles = []
for article in articles:
    key = " ".join(article["title"].lower().split()[:6])
    if key not in seen_titles:
        seen_titles.add(key)
        final_articles.append(article)

# ============================
# SAVE & 15-DAY RETENTION
# ============================
sent_log[TODAY] = list(sent_today)

# Delete entries older than 15 days
cutoff_date = (datetime.now() - timedelta(days=15)).date().isoformat()
cleaned_sent_log = {d: u for d, u in sent_log.items() if d >= cutoff_date}
days_removed = len(sent_log) - len(cleaned_sent_log)

with open(SENT_FILE, "w", encoding="utf-8") as f:
    json.dump(cleaned_sent_log, f, indent=2)

with open(RAW_NEWS_FILE, "w", encoding="utf-8") as f:
    json.dump(final_articles, f, indent=2, ensure_ascii=False)

with open(FAILED_FEEDS_FILE, "w", encoding="utf-8") as f:
    json.dump(failed_feeds, f, indent=2)

print("===================================")
print(f"New articles found: {len(final_articles)}")
print(f"Skipped (Today's duplicates): {skipped}")
print(f"Retention: Removed {days_removed} days of old data.")
print("Fetch stage completed successfully.")