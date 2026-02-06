import json
from pathlib import Path
from datetime import datetime

# ============================
# PATH CONFIGURATION
# ============================
PROJECT_ROOT = Path(__file__).resolve().parent
TOP_NEWS_FILE = PROJECT_ROOT / "data" / "top_news.json"
ENRICHED_FILE = PROJECT_ROOT / "data" / "enriched_summaries.json"
SENT_URLS_FILE = PROJECT_ROOT / "data" / "sent_urls.json"
SITE_DATA_DIR = PROJECT_ROOT / "docs" / "data"
SITE_JSON_OUTPUT = SITE_DATA_DIR / "daily_brief.json"

def safe(value, fallback):
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return fallback
    return value

def main():
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not TOP_NEWS_FILE.exists():
        print(" ERROR: Missing top_news.json")
        return

    with open(TOP_NEWS_FILE, "r", encoding="utf-8") as f:
        top_news = json.load(f)

    enriched_map = {}
    if ENRICHED_FILE.exists():
        with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
            try:
                enriched_data = json.load(f)
                enriched_map = {a.get("title", "").strip(): a for a in enriched_data}
            except:
                enriched_map = {}

    final_articles = []
    newly_sent_urls = []

    for i, story in enumerate(top_news, start=1):
        original_title = story.get("title", "").strip()
        enriched_story = enriched_map.get(original_title)
        is_backup = enriched_story is None
        
        # Summary Recovery Logic: Check AI text first, then RSS summary
        summary_text = safe(
            enriched_story.get("what_happened") if enriched_story else None,
            story.get("summary", "No summary available.")
        )

        final_article = {
            "rank": i,
            "title": f"[Archive] {original_title}" if is_backup else original_title,
            "summary": summary_text,
            "technical_takeaway": safe(
                enriched_story.get("technical_angle") if enriched_story else None,
                "Key technical reference from archive."
            ),
            "primary_risk": safe(
                enriched_story.get("primary_risk") if enriched_story else None,
                "Standard implementation risks apply."
            ),
            "primary_opportunity": safe(
                enriched_story.get("primary_opportunity") if enriched_story else None,
                "Incremental framework gains."
            ),
            "source": story.get("source", "Unknown"),
            "url": story.get("url", "#")
        }
        final_articles.append(final_article)
        newly_sent_urls.append(story.get("url"))

    # Memory update
    existing_sent = []
    if SENT_URLS_FILE.exists():
        with open(SENT_URLS_FILE, "r") as f:
            try: existing_sent = json.load(f)
            except: existing_sent = []
    
    updated_sent = list(set(existing_sent + newly_sent_urls))[-200:]
    with open(SENT_URLS_FILE, "w") as f:
        json.dump(updated_sent, f)

    site_payload = {
        "date": datetime.now().strftime("%B %d, %Y"),
        "timestamp": datetime.now().isoformat(),
        "is_archive_run": any("[Archive]" in a["title"] for a in final_articles),
        "total_stories": len(final_articles),
        "top_stories": final_articles
    }

    with open(SITE_JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(site_payload, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()