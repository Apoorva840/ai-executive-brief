import json
from pathlib import Path
from datetime import datetime

# ============================
# PATH CONFIGURATION
# ============================
PROJECT_ROOT = Path(__file__).resolve().parent
TOP_NEWS_FILE = PROJECT_ROOT / "data" / "top_news.json"
ENRICHED_FILE = PROJECT_ROOT / "data" / "enriched_summaries.json"
SITE_DATA_DIR = PROJECT_ROOT / "docs" / "data"
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
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not TOP_NEWS_FILE.exists():
        print(" ERROR: Missing critical input file (top_news.json)")
        return

    with open(TOP_NEWS_FILE, "r", encoding="utf-8") as f:
        top_news = json.load(f)

    enriched = []
    if ENRICHED_FILE.exists():
        with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
            try:
                enriched = json.load(f)
            except json.JSONDecodeError:
                enriched = []

    # Map enriched articles by title
    enriched_map = {a.get("title", "").strip(): a for a in enriched}
    final_articles = []

    for i, story in enumerate(top_news, start=1):
        original_title = story.get("title", "").strip()
        enriched_story = enriched_map.get(original_title)
        
        # If enriched_story exists, we use its data; otherwise, it's a backup/archive item
        is_backup = enriched_story is None
        display_title = f"[Archive] {original_title}" if is_backup else original_title

        # Merging with fallback logic
        # NOTE: We look for 'technical_angle' to match enrich.py output
        final_article = {
            "rank": i,
            "title": display_title,
            "summary": story.get("summary") or (enriched_story.get("what_happened") if enriched_story else ""),
            "technical_takeaway": safe(
                enriched_story.get("technical_angle") if enriched_story else None,
                "Key technical reference from our recent archive. (Historical Analysis)"
            ),
            "primary_risk": safe(
                enriched_story.get("primary_risk") if enriched_story else None,
                "Standard implementation and adoption risks apply."
            ),
            "primary_opportunity": safe(
                enriched_story.get("primary_opportunity") if enriched_story else None,
                "Leveraging existing frameworks for incremental gains."
            ),
            "source": story.get("source", "Unknown"),
            "url": story.get("url", "#")
        }
        final_articles.append(final_article)

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
    print(f" Processed {len(final_articles)} stories.")

if __name__ == "__main__":
    main()