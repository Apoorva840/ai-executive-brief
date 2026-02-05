import json
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_FILE = PROJECT_ROOT / "data" / "top_news.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "technical_summaries.json"

def clean_text(text, max_chars=350):
    if not text: return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]

def technical_summary(article):
    # Pass through data and provide initial technical context
    # enrich.py will perform the heavy logic later
    return {
        "title": article.get("title"),
        "url": article.get("url"),
        "source": article.get("source"),
        "score": article.get("score"),
        "what_happened": clean_text(article.get("summary", "")),
        "technical_takeaway": "Analyzing technical implications...", # Placeholder
        "primary_risk": None,
        "primary_opportunity": None,
        "who_should_care": ["AI Professionals"]
    }

def main():
    if not INPUT_FILE.exists():
        print(f"ERROR: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)

    summaries = [technical_summary(article) for article in articles]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    print(f"Technical summaries generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()