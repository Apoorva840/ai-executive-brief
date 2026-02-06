import json
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_FILE = PROJECT_ROOT / "data" / "top_news.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "technical_summaries.json"

def clean_text(text, max_chars=350):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]

def neutral_fallback_summary(title, source):
    # Executive-safe, non-hallucinatory fallback
    return (
        f"{source} announced '{title}', highlighting new developments "
        f"relevant to AI researchers and practitioners."
    )

def technical_summary(article):
    title = article.get("title")
    source = article.get("source", "The publisher")
    raw_summary = clean_text(article.get("summary"))

    if not raw_summary:
        raw_summary = neutral_fallback_summary(title, source)

    return {
        "title": title,
        "url": article.get("url"),
        "source": source,
        "score": article.get("score"),
        "what_happened": raw_summary,
        "technical_takeaway": None,
        "primary_risk": None,
        "primary_opportunity": None,
        "who_should_care": None
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