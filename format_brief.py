import json
from pathlib import Path
from datetime import datetime

# ============================
# PATH CONFIGURATION (CI SAFE)
# ============================

PROJECT_ROOT = Path(__file__).resolve().parent

TOP_NEWS_FILE = PROJECT_ROOT / "data" / "top_news.json"
ENRICHED_FILE = PROJECT_ROOT / "data" / "enriched_summaries.json"

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

    if not TOP_NEWS_FILE.exists():
        print(" ERROR: Missing critical input file (top_news.json)")
        return

    # Load top news data
    with open(TOP_NEWS_FILE, "r", encoding="utf-8") as f:
        top_news = json.load(f)

    # Load enriched data (Handle case where file might be empty/missing in backup mode)
    enriched = []
    if ENRICHED_FILE.exists():
        with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
            try:
                enriched = json.load(f)
            except json.JSONDecodeError:
                enriched = []

    # Index enriched articles by title for fast lookup
    enriched_map = {
        a.get("title", "").strip(): a
        for a in enriched
    }

    final_articles = []

    for i, story in enumerate(top_news, start=1):
        original_title = story.get("title", "").strip()
        enriched_story = enriched_map.get(original_title)

        # CHECK: Is this from the backup archive? 
        # (If it's not in the enriched_map, it didn't run through the AI today)
        is_backup = enriched_story is None
        
        display_title = f"[Archive] {original_title}" if is_backup else original_title

        # Merge original news with enriched technical insights
        final_article = {
            "rank": i,
            "title": display_title,
            "summary": story.get("summary", ""),
            "technical_takeaway": safe(
                enriched_story.get("technical_angle") if not is_backup else None,
                "Trending highly in our 24h archive. This development remains a key technical reference for current AI implementations."
            ),
            "primary_risk": safe(
                enriched_story.get("primary_risk") if not is_backup else None,
                "Standard implementation and adoption risks apply."
            ),
            "primary_opportunity": safe(
                enriched_story.get("primary_opportunity") if not is_backup else None,
                "Leveraging existing frameworks for incremental gains."
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
        "is_archive_run": any("[Archive]" in a["title"] for a in final_articles),
        "total_stories": len(final_articles),
        "top_stories": final_articles
    }

    with open(SITE_JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(site_payload, f, indent=2, ensure_ascii=False)

    print(f" Success: Daily brief JSON created at {SITE_JSON_OUTPUT}")
    if site_payload["is_archive_run"]:
        print(" NOTE: This run used articles from the backup queue.")
    print(f" Processed {len(final_articles)} stories.")

if __name__ == "__main__":
    main()