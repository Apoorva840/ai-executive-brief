import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ============================
# CONFIG
# ============================
TOP_K = 5
ARCHIVE_ADD_DAILY = 15
ARCHIVE_MAX = 300
MAX_PER_SOURCE = 2
MAX_ARXIV = 1

NOW_UTC = datetime.now(timezone.utc)
FRESH_THRESHOLD = NOW_UTC - timedelta(hours=24)

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

RAW_NEWS_FILE = DATA_DIR / "raw_news.json"
TOP_NEWS_FILE = DATA_DIR / "top_news.json"
ARCHIVE_FILE = DATA_DIR / "archive_news.json"
BACKUP_QUEUE_FILE = DATA_DIR / "backup_queue.json"

# ============================
# SOURCE WEIGHTS (Updated with New Sources)
# ============================
SOURCE_SCORES = {
    "Hugging Face Blog": 6,
    "The Decoder": 5,          # High rank for weekend/analytical coverage
    "TechCrunch AI": 5,
    "VentureBeat AI": 5,
    "AI News": 4,              # Reliable weekend daily updates
    "Wired AI": 4,
    "Microsoft Research": 4,
    "Arxiv AI": 3
}

TECH_KEYWORDS = [
    "model", "llm", "transformer",
    "architecture", "multimodal",
    "weights", "framework"
]

# ============================
# SCORING
# ============================
def score_article(a):
    score = SOURCE_SCORES.get(a.get("source"), 2)
    text = (a.get("title", "") + " " + a.get("summary", "")).lower()

    for kw in TECH_KEYWORDS:
        if kw in text:
            score += 1

    if len(a.get("title", "")) < 110:
        score += 1

    return score

# ============================
# LOAD RAW ARTICLES
# ============================
if not RAW_NEWS_FILE.exists():
    print("ERROR: raw_news.json missing")
    exit(1)

articles = json.loads(RAW_NEWS_FILE.read_text(encoding="utf-8"))

# ============================
# FILTER FRESH (24H)
# ============================
fresh = []
for a in articles:
    try:
        published = datetime.fromisoformat(a["published_at"])
    except:
        continue

    if published >= FRESH_THRESHOLD:
        a["score"] = score_article(a)
        fresh.append(a)

# Sort by score descending
fresh = sorted(fresh, key=lambda x: x["score"], reverse=True)

# ============================
# SELECT TOP STORIES
# ============================
selected = []
overflow = []

source_counter = {}
arxiv_count = 0

for a in fresh:
    src = a.get("source", "Unknown")
    source_counter[src] = source_counter.get(src, 0)

    # Arxiv constraint
    if src == "Arxiv AI" and arxiv_count >= MAX_ARXIV:
        overflow.append(a)
        continue

    # Diversity constraint
    if source_counter[src] < MAX_PER_SOURCE and len(selected) < TOP_K:
        selected.append(a)
        source_counter[src] += 1
        if src == "Arxiv AI":
            arxiv_count += 1
    else:
        overflow.append(a)

# ============================
# LOAD ARCHIVE
# ============================
if ARCHIVE_FILE.exists():
    try:
        archive = json.loads(ARCHIVE_FILE.read_text(encoding="utf-8"))
    except:
        archive = []
else:
    archive = []

# ============================
# FILL FROM ARCHIVE IF NEEDED
# ============================
if len(selected) < TOP_K:
    needed = TOP_K - len(selected)
    print(f"[ARCHIVE] Filling {needed} slots from archive")

    for a in archive:
        if len(selected) >= TOP_K:
            break
        # Optional: Add check to avoid duplicates if they exist in both
        if a["url"] not in [s["url"] for s in selected]:
            selected.append(a)

# ============================
# UPDATE ARCHIVE
# ============================
today_archive = overflow[:ARCHIVE_ADD_DAILY]
timestamp = NOW_UTC.isoformat()

for a in today_archive:
    a["archived_at"] = timestamp

archive = today_archive + archive
archive = archive[:ARCHIVE_MAX]

# ============================
# SAVE FILES
# ============================
TOP_NEWS_FILE.write_text(
    json.dumps(selected, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

ARCHIVE_FILE.write_text(
    json.dumps(archive, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

BACKUP_QUEUE_FILE.write_text(
    json.dumps(overflow[:15], indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# ============================
# LOGS
# ============================
print(f"Success: Selected {len(selected)} stories for today.")
print(f"Archive: {len(today_archive)} stories added.")
print(f"Archive size: {len(archive)}")