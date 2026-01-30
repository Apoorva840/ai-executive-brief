import json
from datetime import date

# ============================
# Configuration
# ============================

TOP_K = 5
MAX_PER_SOURCE = 2        # diversity cap
MAX_ARXIV = 1             # hard limit for arXiv
TODAY = date.today().isoformat()

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

with open("data/raw_news.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

# ============================
# Score & rank
# ============================

for article in articles:
    article["score"] = score_article(article)

ranked = sorted(articles, key=lambda x: x["score"], reverse=True)

# ============================
# Enforce diversity
# ============================

selected = []
source_counter = {}
arxiv_count = 0

for article in ranked:
    src = article.get("source", "Unknown")
    source_counter[src] = source_counter.get(src, 0)

    if src == "Arxiv AI" and arxiv_count >= MAX_ARXIV:
        continue

    if source_counter[src] < MAX_PER_SOURCE:
        selected.append(article)
        source_counter[src] += 1

        if src == "Arxiv AI":
            arxiv_count += 1

    if len(selected) == TOP_K:
        break

# ============================
# Save output
# ============================

with open("data/top_news.json", "w", encoding="utf-8") as f:
    json.dump(selected, f, indent=2)

print("Top 5 AI-professional articles selected:\n")
for a in selected:
    print(f"- ({a['score']}) [{a.get('source')}] {a['title']}")
