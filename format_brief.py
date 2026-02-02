import json
from pathlib import Path
from datetime import datetime

# ============================
# PATH CONFIGURATION (CI SAFE)
# ============================

PROJECT_ROOT = Path(__file__).resolve().parent

TOP_NEWS_FILE = PROJECT_ROOT / "data" / "top_news.json"
ENRICHED_FILE = PROJECT_ROOT / "data" / "enriched_summaries.json"

# n8n email output
#N8N_BASE = Path("C:/Users/HP/.n8n-files")
#EMAIL_OUTPUT = N8N_BASE / "ai-output" / "ai_professional_brief.txt"

# Microsite/Data output
SITE_DATA_DIR = PROJECT_ROOT / "site" / "data"
SITE_JSON_OUTPUT = SITE_DATA_DIR / "daily_brief.json"

# ============================
# HELPERS
# ============================

def safe(value, fallback):
    """Guarantee non-null, non-empty output"""
    if value is None:
        return fallback
    if isinstance(value, str) and value.strip() == "":
        return fallback
    return value

# ============================
# MAIN LOGIC
# ============================

def main():
    # Ensure output directory exists
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not TOP_NEWS_FILE.exists() or not ENRICHED_FILE.exists():
        print(" ERROR: Missing input files (top_news.json or enriched_summaries.json)")
        return

    # Load data
    with open(TOP_NEWS_FILE, "r", encoding="utf-8") as f:
        top_news = json.load(f)

    with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
        enriched = json.load(f)

    # Index enriched articles by title for fast lookup
    enriched_map = {
        a.get("title", "").strip(): a
        for a in enriched
    }

    final_articles = []

    for i, story in enumerate(top_news, start=1):
        title = story.get("title", "").strip()
        enriched_story = enriched_map.get(title, {})

        # Merge original news with enriched technical insights
        final_article = {
            "rank": i,
            "title": title,
            "summary": story.get("summary", ""),
            "technical_takeaway": safe(
                enriched_story.get("technical_angle"),
                "This development has direct technical implications for how AI systems are built, deployed, or governed."
            ),
            "primary_risk": safe(
                enriched_story.get("primary_risk"),
                "Execution and adoption risks remain manageable but present."
            ),
            "primary_opportunity": safe(
                enriched_story.get("primary_opportunity"),
                "Incremental gains through applied AI adoption."
            ),
            "source": story.get("source", "Unknown"),
            "url": story.get("url", "#")
        }

        final_articles.append(final_article)

    # ----------------------------
    # CREATE FINAL JSON PAYLOAD
    # ----------------------------
    site_payload = {
        "date": datetime.now().strftime("%B %d, %Y"),
        "timestamp": datetime.now().isoformat(),
        "total_stories": len(final_articles),
        "top_stories": final_articles
    }

    with open(SITE_JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(site_payload, f, indent=2, ensure_ascii=False)

    print(f" Success: Daily brief JSON created at {SITE_JSON_OUTPUT}")
    print(f" Processed {len(final_articles)} stories.")

if __name__ == "__main__":
    main()