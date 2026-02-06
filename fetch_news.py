import feedparser
import json
import re
import socket
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from bs4 import BeautifulSoup

# ============================
# PATHS
# ============================
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

RAW_NEWS_FILE = DATA_DIR / "raw_news.json"
SENT_URLS_FILE = DATA_DIR / "sent_urls.json"
FAILED_FEEDS_FILE = DATA_DIR / "failed_feeds.json"

# ============================
# TIME WINDOW
# ============================
NOW_UTC = datetime.now(timezone.utc)
CUTOFF_UTC = NOW_UTC - timedelta(hours=24)

# ============================
# SOURCES
# ============================
SOURCES = [
    {"name": "TechCrunch AI", "rss": "https://techcrunch.com/tag/artificial-intelligence/feed/"},
    {"name": "MIT Technology Review AI", "rss": "https://www.technologyreview.com/topic/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI", "rss": "https://venturebeat.com/category/ai/feed/"},
    {"name": "Wired AI", "rss": "https://www.wired.com/feed/tag/ai/latest/rss"},
    {"name": "Arxiv AI", "rss": "http://export.arxiv.org/rss/cs.AI"},
    {"name": "Microsoft Research", "rss": "https://www.microsoft.com/en-us/research/feed/"},
    {"name": "Hugging Face Blog", "rss": "https://huggingface.co/blog/feed.xml"},
]

# ============================
# HELPERS
# ============================
def clean_summary(text, max_chars=350):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]

def extract_datetime(entry):
    ts = entry.get("published_parsed") or entry.get("updated_parsed")
    if not ts:
        return None
    return datetime(*ts[:6], tzinfo=timezone.utc)

# ============================
# LOAD ARCHIVED URLS (LIST)
# ============================
archived_urls = []

if SENT_URLS_FILE.exists():
    try:
        data = json.loads(SENT_URLS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            archived_urls = data
    except:
        archived_urls = []

archived_set = set(archived_urls)

# ============================
# FETCH
# ============================
articles = []
failed_feeds = []
too_old = no_date = 0

for source in SOURCES:
    try:
        socket.setdefaulttimeout(10)
        feed = feedparser.parse(source["rss"])

        if feed.bozo:
            print(f"[WARN] feedparser failed for {source['name']} — fallback")
            resp = requests.get(source["rss"], timeout=10)
            soup = BeautifulSoup(resp.content, "xml")
            entries = soup.find_all("item")

            for e in entries:
                title = e.title.text.strip() if e.title else None
                link = e.link.text.strip() if e.link else None
                pub = e.pubDate.text if e.pubDate else None
                summary = e.description.text if e.description else ""

                if not title or not link or not pub:
                    no_date += 1
                    continue

                try:
                    published = datetime.strptime(
                        pub, "%a, %d %b %Y %H:%M:%S %z"
                    ).astimezone(timezone.utc)
                except:
                    no_date += 1
                    continue

                if published < CUTOFF_UTC:
                    too_old += 1
                    continue

                articles.append({
                    "title": title,
                    "summary": clean_summary(summary),
                    "url": link,
                    "source": source["name"],
                    "published_at": published.isoformat()
                })

        else:
            print(f"{source['name']} entries: {len(feed.entries)}")
            for e in feed.entries:
                title = e.get("title")
                link = e.get("link")
                summary = e.get("summary", "")

                if not title or not link:
                    continue

                published = extract_datetime(e)
                if not published:
                    no_date += 1
                    continue

                if published < CUTOFF_UTC:
                    too_old += 1
                    continue

                articles.append({
                    "title": title.strip(),
                    "summary": clean_summary(summary),
                    "url": link,
                    "source": source["name"],
                    "published_at": published.isoformat()
                })

    except Exception as ex:
        failed_feeds.append({"source": source["name"], "error": str(ex)})

# ============================
# SAVE RAW DATA
# ============================
RAW_NEWS_FILE.write_text(json.dumps(articles, indent=2), encoding="utf-8")
FAILED_FEEDS_FILE.write_text(json.dumps(failed_feeds, indent=2), encoding="utf-8")

# ============================
# UPDATE ARCHIVE (LIST)
# ============================
new_urls = 0
for a in articles:
    if a["url"] not in archived_set:
        archived_set.add(a["url"])
        archived_urls.append(a["url"])
        new_urls += 1

# keep last 500 URLs max
archived_urls = archived_urls[-500:]

SENT_URLS_FILE.write_text(
    json.dumps(archived_urls, indent=2),
    encoding="utf-8"
)

# ============================
# REPORT
# ============================
print("===================================")
print(f"Fresh articles fetched: {len(articles)}")
print(f"New URLs archived: {new_urls}")
print(f"Dropped (too old): {too_old}")
print(f"Dropped (no date): {no_date}")
print("Fetch stage completed successfully.")