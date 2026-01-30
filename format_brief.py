import json
from pathlib import Path
from datetime import datetime

# ============================
# Paths
# ============================

PROJECT_ROOT = Path(__file__).parent

TOP_NEWS_FILE = PROJECT_ROOT / "data" / "top_news.json"
ENRICHED_FILE = PROJECT_ROOT / "data" / "enriched_summaries.json"

# n8n email output
N8N_BASE = Path("C:/Users/HP/.n8n-files")
EMAIL_OUTPUT = N8N_BASE / "ai-output" / "ai_professional_brief.txt"

# Microsite output
SITE_DATA_DIR = PROJECT_ROOT / "site" / "data"
SITE_JSON_OUTPUT = SITE_DATA_DIR / "daily_brief.json"

# ============================
# Helpers
# ============================

def safe(value, fallback):
    """Guarantee non-null, non-empty output"""
    if value is None:
        return fallback
    if isinstance(value, str) and value.strip() == "":
        return fallback
    return value

def format_email_article(article):
    return f"""
==============================
{article['title']}
==============================

Summary:
{article['summary']}

Technical takeaway:
{article['technical_takeaway']}

Primary risk:
{article['primary_risk']}

Primary opportunity:
{article['primary_opportunity']}

Source: {article['source']}
Link: {article['url']}
"""

# ============================
# Main
# ============================

def main():
    EMAIL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not TOP_NEWS_FILE.exists() or not ENRICHED_FILE.exists():
        print(" Missing input files")
        return

    with open(TOP_NEWS_FILE, "r", encoding="utf-8") as f:
        top_news = json.load(f)

    with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
        enriched = json.load(f)

    # Index enriched articles by title
    enriched_map = {
        a["title"].strip(): a
        for a in enriched
    }

    final_articles = []

    for i, story in enumerate(top_news, start=1):
        title = story["title"].strip()
        enriched_story = enriched_map.get(title, {})

        final_article = {
            "rank": i,
            "title": title,
            "summary": story["summary"],

            # 🔒 HARD GUARANTEES — NO NULLS
            "technical_takeaway": safe(
                enriched_story.get("technical_angle"),
                "This development has direct technical implications for how AI systems are built, deployed, or governed."
            ),

            "primary_risk": safe(
                enriched_story.get("primary_risk"),
                "Ignoring this trend may introduce operational, regulatory, or strategic risk."
            ),

            "primary_opportunity": safe(
                enriched_story.get("primary_opportunity"),
                "Early adopters can gain competitive advantage by acting on this shift."
            ),

            "source": story["source"],
            "url": story["url"]
        }

        final_articles.append(final_article)

    # ----------------------------
    # EMAIL OUTPUT
    # ----------------------------
    email_content = "\n\n".join(
        format_email_article(a) for a in final_articles
    )

    with open(EMAIL_OUTPUT, "w", encoding="utf-8") as f:
        f.write(email_content.strip() + "\n")

    print(f" Email brief created at {EMAIL_OUTPUT}")

    # ----------------------------
    # MICROSITE JSON OUTPUT
    # ----------------------------
    site_payload = {
        "date": datetime.now().strftime("%B %d, %Y"),
        "top_stories": final_articles
    }

    with open(SITE_JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(site_payload, f, indent=2, ensure_ascii=False)

    print(f" Microsite JSON created at {SITE_JSON_OUTPUT}")
    print(" Nulls are now structurally impossible.")

if __name__ == "__main__":
    main()
