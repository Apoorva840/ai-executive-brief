import feedparser
import json
import os
import re
import socket
from datetime import date
from bs4 import BeautifulSoup
import requests

# ============================
# BASE DIRECTORY (portable)
# ============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

RAW_NEWS_FILE = os.path.join(DATA_DIR, "raw_news.json")
SENT_FILE = os.path.join(DATA_DIR, "sent_urls.json")
FAILED_FEEDS_FILE = os.path.join(DATA_DIR, "failed_feeds.json")

os.makedirs(DATA_DIR, exist_ok=True)

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
# LOAD TODAY'S SENT URLS
# ============================

if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        try:
            sent_log = json.load(f)
            if not isinstance(sent_log, dict):
                sent_log = {}
        except json.JSONDecodeError:
            sent_log = {}
else:
    sent_log = {}

# Only today's URLs are skipped
sent_today = set(sent_log.get(TODAY, []))
print(f"Loaded {len(sent_today)} URLs already used today")

articles = []
skipped = 0
failed_feeds = []

# ============================
# FETCH FEEDS WITH TIMEOUT & FALLBACK
# ============================

for source in SOURCES:
    try:
        socket.setdefaulttimeout(10)

        feed = feedparser.parse(
            source["rss"],
            request_headers={"User-Agent": "AI-Executive-Brief/1.0"}
        )

        # feedparser error handling + fallback parser
        if feed.bozo:
            print(f"[WARN] feedparser failed for {source['name']}: {feed.bozo_exception}")
            try:
                resp = requests.get(source["rss"], headers={"User-Agent": "AI-Executive-Brief/1.0"}, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.content, "xml")
                entries = soup.find_all("item") or soup.find_all("entry")
                if not entries:
                    raise ValueError("No entries found in fallback parser")

                print(f"[INFO] {source['name']} fallback parser found {len(entries)} entries")

                for entry in entries:
                    link_tag = entry.find("link")
                    title_tag = entry.find("title")
                    summary_tag = entry.find("summary") or entry.find("description")

                    link = link_tag.text.strip() if link_tag else None
                    title = title_tag.text.strip() if title_tag else None
                    summary = summary_tag.text.strip() if summary_tag else ""

                    if not link or not title:
                        continue
                    if link in sent_today:
                        skipped += 1
                        continue

                    article = {
                        "title": title,
                        "summary": clean_summary(summary),
                        "url": link,
                        "source": source["name"]
                    }
                    articles.append(article)
                    sent_today.add(link)

                continue  # Skip normal feedparser processing

            except Exception as e:
                print(f"[ERROR] Fallback parser also failed for {source['name']}: {e}")
                failed_feeds.append({"name": source["name"], "rss": source["rss"], "error": str(e)})
                continue

        # Normal feedparser processing
        print(f"{source['name']} entries: {len(feed.entries)}")
        for entry in feed.entries:
            link = entry.get("link")
            title = entry.get("title")
            summary = entry.get("summary", "")

            #if not link or not title:
            #    continue
            if link in sent_today:
                skipped += 1
                continue

            article = {
                "title": title.strip(),
                "summary": clean_summary(summary),
                "url": link,
                "source": source["name"]
            }
            articles.append(article)
            sent_today.add(link)

    except Exception as e:
        print(f"[ERROR] Could not fetch {source['name']}: {e}")
        failed_feeds.append({"name": source["name"], "rss": source["rss"], "error": str(e)})
        continue

# ============================
# TITLE-BASED DEDUPLICATION
# ============================

seen_titles = set()
final_articles = []

for article in articles:
    key = " ".join(article["title"].lower().split()[:6])
    if key not in seen_titles:
        seen_titles.add(key)
        final_articles.append(article)

# ============================
# SAVE OUTPUTS
# ============================

with open(RAW_NEWS_FILE, "w", encoding="utf-8") as f:
    json.dump(final_articles, f, indent=2, ensure_ascii=False)

sent_log[TODAY] = list(sent_today)
with open(SENT_FILE, "w", encoding="utf-8") as f:
    json.dump(sent_log, f, indent=2)

with open(FAILED_FEEDS_FILE, "w", encoding="utf-8") as f:
    json.dump(failed_feeds, f, indent=2)

print("===================================")
print(f"New articles added today: {len(final_articles)}")
print(f"Skipped duplicates today: {skipped}")
print(f"Final articles written: {len(final_articles)}")
print(f"Failed feeds logged: {len(failed_feeds)}")
print("Fetch stage completed successfully")
