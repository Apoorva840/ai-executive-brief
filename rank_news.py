import json
from datetime import date
from pathlib import Path

# ============================
# Configuration
# ============================

TOP_K = 5
MAX_PER_SOURCE = 2        # diversity cap
MAX_ARXIV = 1             # hard limit for arXiv
TODAY = date.today().isoformat()

# Pathing (CI Safe)
PROJECT_ROOT = Path(__file__).resolve().parent
RAW_NEWS_FILE = PROJECT_ROOT / "data" / "raw_news.json"
TOP_NEWS_FILE = PROJECT_ROOT / "data" / "top_news.json"
BACKUP_QUEUE_FILE = PROJECT_ROOT / "data" / "backup_queue.json"

# ============================
# Source authority (rebalanced)
# ============================

SOURCE_SCORES = {
    "OpenAI Blog": 6,
    "Google AI Blog": 6,
    "Meta AI": 6,
    "Hugging Face Blog": 6,
    "TechCrunch AI": 5,
    "VentureBeat AI": 5,
    "Wired AI": 4,
    "Microsoft Research": 4,
    "Arxiv AI": 3
}

# ============================
# Keyword signals
# ============================

TECH_KEYWORDS = [
    "model", "llm", "transformer", "architecture",
    "training", "fine-tuning", "pretraining",
    "benchmark", "evaluation", "open-source",
    "weights", "checkpoint", "multimodal",
    "api", "sdk", "library", "framework"
]

TOOL_KEYWORDS = [
    "release", "launched", "update", "tool",
    "plugin", "integration"
]

NON_TECH_KEYWORDS = [
    "funding", "valuation", "revenue",
    "stock", "shares", "lawsuit",
    "ceo said", "executive"
]

# ============================
# Article scoring
# ============================

def score_article(article):
    score = 0
    source = article.get("source", "")

    # 1. Source authority
    score += SOURCE_SCORES.get(source, 1)

    text = (
        article.get("title", "") + " " +
        article.get("summary", "")
    ).lower()

    # 2. Technical depth
    for word in TECH_KEYWORDS:
        if word in text:
            score += 1

    # 3. Tool / release bonus
    for word in TOOL_KEYWORDS:
        if word in text:
            score += 1

    # 4. Penalize business noise
    for word in NON_TECH_KEYWORDS:
        if word in text:
            score -= 2

    # 5. Prefer readable titles
    if len(article.get("title", "")) < 110:
        score += 1

    # 6. Penalize arXiv abstract length
    if source == "Arxiv AI" and len(text.split()) > 250:
        score -= 3

    # 7. Hugging Face boost
    if source == "Hugging Face Blog":
        score += 3

    return score

# ============================
# Load articles
# ============================

if not RAW_NEWS_FILE.exists():
    print(f"ERROR: {RAW_NEWS_FILE} not found.")
    exit(1)

with open(RAW_NEWS_FILE, "r", encoding="utf-8") as f:
    articles = json.load(f)

# ============================
# Score & rank
# ============================

for article in articles:
    article["score"] = score_article(article)

# Sort all articles by score descending
ranked = sorted(articles, key=lambda x: x["score"], reverse=True)

# ============================
# Enforce diversity & Build Backup
# ============================

selected = []      # The Top 5 for today
backup_pool = []   # The "Next Best" for slow news days
source_counter = {}
arxiv_count = 0

for article in ranked:
    src = article.get("source", "Unknown")
    source_counter[src] = source_counter.get(src, 0)

    # Apply arXiv limit
    if src == "Arxiv AI" and arxiv_count >= MAX_ARXIV:
        continue

    # Apply Source Diversity
    if source_counter[src] < MAX_PER_SOURCE:
        if len(selected) < TOP_K:
            selected.append(article)
            source_counter[src] += 1
            if src == "Arxiv AI":
                arxiv_count += 1
        else:
            # Once Top 5 is full, fill the backup pool with high-quality leftovers
            backup_pool.append(article)

# ============================
# Save outputs
# ============================

# 1. Save main selection
with open(TOP_NEWS_FILE, "w", encoding="utf-8") as f:
    json.dump(selected, f, indent=2, ensure_ascii=False)

# 2. Save backup queue (next best 15 articles)
with open(BACKUP_QUEUE_FILE, "w", encoding="utf-8") as f:
    json.dump(backup_pool[:15], f, indent=2, ensure_ascii=False)

print(f" Success: Selected {len(selected)} stories for today.")
print(f" Archive: {len(backup_pool[:15])} stories saved to backup_queue.json.")

print("\nTop 5 AI-professional articles selected:\n")
for a in selected:
    print(f"- ({a['score']}) [{a.get('source')}] {a['title']}")