import json
from datetime import datetime, timedelta
from pathlib import Path

# ============================
# Configuration
# ============================
TOP_K = 5
MAX_PER_SOURCE = 2
MAX_ARXIV = 1
# Define the "Freshness" window (24 hours)
FRESH_THRESHOLD = datetime.now() - timedelta(hours=24)

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_NEWS_FILE = PROJECT_ROOT / "data" / "raw_news.json"
TOP_NEWS_FILE = PROJECT_ROOT / "data" / "top_news.json"
BACKUP_QUEUE_FILE = PROJECT_ROOT / "data" / "backup_queue.json"
SENT_URLS_FILE = PROJECT_ROOT / "data" / "sent_urls.json"

SOURCE_SCORES = {
    "OpenAI Blog": 6, "Google AI Blog": 6, "Meta AI": 6, "Hugging Face Blog": 6,
    "TechCrunch AI": 5, "VentureBeat AI": 5, "Wired AI": 4, "Microsoft Research": 4, "Arxiv AI": 3
}

TECH_KEYWORDS = ["model", "llm", "transformer", "architecture", "weights", "multimodal", "framework"]

def score_article(article):
    score = 0
    source = article.get("source", "")
    score += SOURCE_SCORES.get(source, 1)
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    for word in TECH_KEYWORDS:
        if word in text: score += 1
    if len(article.get("title", "")) < 110: score += 1
    if source == "Hugging Face Blog": score += 3
    return score

# ============================
# Load & Filter Logic
# ============================
if not RAW_NEWS_FILE.exists():
    print("ERROR: raw_news.json not found")
    exit(1)

with open(RAW_NEWS_FILE, "r", encoding="utf-8") as f:
    articles = json.load(f)

sent_urls = set()
if SENT_URLS_FILE.exists():
    with open(SENT_URLS_FILE, "r", encoding="utf-8") as f:
        try:
            sent_urls = set(json.load(f))
        except:
            sent_urls = set()

fresh_articles = []
for a in articles:
    # 1. Skip if already sent
    if a.get("url") in sent_urls:
        continue
    
    # 2. Freshness Check
    try:
        # Handling potential 'Z' or offset in isoformat
        date_str = a.get("date", "").replace("Z", "+00:00")
        pub_date = datetime.fromisoformat(date_str)
        
        # If the date is naive (no timezone), make it aware to compare with datetime.now()
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=None) # Ensure comparison is same-type
            
        if pub_date >= (datetime.now() - timedelta(hours=24)):
            a["score"] = score_article(a)
            fresh_articles.append(a)
    except Exception as e:
        continue

ranked = sorted(fresh_articles, key=lambda x: x["score"], reverse=True)

# ============================
# Selection
# ============================
selected, backup_pool = [], []
source_counter, arxiv_count = {}, 0

for article in ranked:
    src = article.get("source", "Unknown")
    source_counter[src] = source_counter.get(src, 0)
    
    if src == "Arxiv AI" and arxiv_count >= MAX_ARXIV:
        continue

    if source_counter[src] < MAX_PER_SOURCE and len(selected) < TOP_K:
        selected.append(article)
        source_counter[src] += 1
        if src == "Arxiv AI": arxiv_count += 1
    else:
        backup_pool.append(article)

with open(TOP_NEWS_FILE, "w", encoding="utf-8") as f:
    json.dump(selected, f, indent=2, ensure_ascii=False)

with open(BACKUP_QUEUE_FILE, "w", encoding="utf-8") as f:
    json.dump(backup_pool[:15], f, indent=2, ensure_ascii=False)

print(f" Success: Selected {len(selected)} stories from last 24h.")