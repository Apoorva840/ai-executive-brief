import json
from pathlib import Path

# ============================
# DYNAMIC PATH CONFIGURATION
# ============================

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent

# Paths
N8N_BASE = BASE_DIR / "n8n-files"
INPUT_FILE = BASE_DIR / "data" / "technical_summaries.json"
OUTPUT_FILE = N8N_BASE / "ai-input" / "enriched_summaries.json"

# ============================
# ENRICHMENT LOGIC
# ============================

def enrich(article):
    title = article.get("title", "")
    summary = article.get("what_happened", "")

    #  CORRECT f-string (this was the crash cause earlier)
    text = f"{title} {summary}".lower()

    # Defaults (never null)
    risk = article.get("primary_risk") or (
        "Execution and adoption risks remain manageable but present."
    )
    opportunity = article.get("primary_opportunity") or (
        "Incremental gains through applied AI adoption."
    )
    audience = article.get("who_should_care") or ["AI Professionals"]

    # Rule-based enrichment
    if "privacy" in text or "scraping" in text:
        risk = "Regulatory exposure and public trust risks if data governance is weak."
        opportunity = "Leadership in compliant, privacy-first AI system design."
        audience = ["AI Ethics Engineers", "Legal & Compliance Teams"]

    if "energy" in text or "compute" in text:
        risk = "Escalating infrastructure costs and capacity bottlenecks."
        opportunity = "Operational efficiency through optimized AI infrastructure."
        audience = ["AI Infrastructure Engineers"]

    if "model" in text or "llm" in text:
        risk = "Dependence on rapidly evolving model ecosystems."
        opportunity = "Accelerated development cycles using advanced AI tooling."
        audience = ["ML Engineers", "Product Leaders"]

    # Update article
    article["primary_risk"] = risk
    article["primary_opportunity"] = opportunity
    article["who_should_care"] = audience

    return article

# ============================
# MAIN EXECUTION
# ============================

def main():
    print(f"Targeting Input: {INPUT_FILE}")

    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        print(
            "Available files in data directory:",
            [f.name for f in (BASE_DIR / "data").glob("*")]
        )
        return

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load input
    with open(INPUT_FILE, "r", encoding="utf-8", errors="replace") as f:
        try:
            articles = json.load(f)
        except json.JSONDecodeError:
            print(f"ERROR: Could not decode JSON from {INPUT_FILE}")
            return

    # Enrich
    enriched = [enrich(article) for article in articles]

    # Save output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f" Success! Enriched AI summaries created at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
