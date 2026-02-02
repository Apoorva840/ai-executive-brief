import json
from pathlib import Path

# ============================
# PATH CONFIGURATION (CI SAFE)
# ============================

# Get the directory where this script is located
#BASE_DIR = Path(__file__).resolve().parent

# Paths
#N8N_BASE = BASE_DIR / "n8n-files"
#INPUT_FILE = BASE_DIR / "data" / "technical_summaries.json"
#OUTPUT_FILE = N8N_BASE / "ai-input" / "enriched_summaries.json"

# Project root = directory of this file
PROJECT_ROOT = Path(__file__).resolve().parent

INPUT_FILE = PROJECT_ROOT / "data" / "technical_summaries.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "enriched_summaries.json"

# ============================
# ENRICHMENT LOGIC
# ============================

def enrich(article):
    title = article.get("title", "").strip()
    summary = article.get("what_happened", "").strip()

    # Correct f-string
    text = f"{title} {summary}".lower()

    # Defaults (never null)
    risk = (
        article.get("primary_risk")
        or "Execution and adoption risks remain manageable but present."
    )
    opportunity = (
        article.get("primary_opportunity")
        or "Incremental gains through applied AI adoption."
    )
    audience = article.get("who_should_care") or ["AI Professionals"]

    # Rule-based enrichment
    if "privacy" in text or "scraping" in text:
        risk = "Regulatory exposure and public trust risks if data governance is weak."
        opportunity = "Leadership in compliant, privacy-first AI system design."
        audience = ["AI Ethics Engineers", "Legal & Compliance Teams"]

    elif "energy" in text or "compute" in text:
        risk = "Escalating infrastructure costs and capacity bottlenecks."
        opportunity = "Operational efficiency through optimized AI infrastructure."
        audience = ["AI Infrastructure Engineers"]

    elif "model" in text or "llm" in text:
        risk = "Dependence on rapidly evolving model ecosystems."
        opportunity = "Accelerated development cycles using advanced AI tooling."
        audience = ["ML Engineers", "Product Leaders"]

    # Update article (in-place)
    article["primary_risk"] = risk
    article["primary_opportunity"] = opportunity
    article["who_should_care"] = audience

    return article

# ============================
# MAIN
# ============================

def main():
    print(f"Targeting input: {INPUT_FILE}")

    if not INPUT_FILE.exists():
        print(" ERROR: technical_summaries.json not found")
        print(
            " Available files:",
            [f.name for f in (PROJECT_ROOT / "data").glob("*")]
        )
        return

    # Load input
    with open(INPUT_FILE, "r", encoding="utf-8", errors="replace") as f:
        articles = json.load(f)

    enriched = [enrich(article) for article in articles]

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Save output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f" Enriched summaries created at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
