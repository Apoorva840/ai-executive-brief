import json
import os
from pathlib import Path

# ============================
# DYNAMIC PATH CONFIGURATION
# ============================

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent

# Set paths relative to the script location
N8N_BASE = BASE_DIR / "n8n-files"
# Adjusted to ensure it looks inside the 'data' folder relative to the script
INPUT_FILE = BASE_DIR / "data" / "technical_summaries.json"
OUTPUT_FILE = N8N_BASE / "ai-input" / "enriched_summaries.json"

# ============================
# ENRICHMENT LOGIC
# ============================

def enrich(article):
    # FIX: Removed the "beach" typo which caused the SyntaxError
    title = article.get('title', '')
    summary = article.get('what_happened', '')
    text = f("{title} {summary}").lower()

    # Defaults (never null)  
    risk = article.get("primary_risk") or "Execution and adoption risks remain manageable but present."
    opportunity = article.get("primary_opportunity") or "Incremental gains through applied AI adoption."
    audience = article.get("who_should_care") or ["AI Professionals"]

    # Rule-based enrichment based on keywords
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

    # Update article dictionary
    article["primary_risk"] = risk
    article["primary_opportunity"] = opportunity
    article["who_should_care"] = audience
    return article

# ============================
# MAIN EXECUTION
# ============================

def main():
    print(f"Targeting Input: {INPUT_FILE}")
    
    # Check if input file exists to avoid crash
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        # List files to help debug if it fails on GitHub
        print("Available files in data directory:", [f.name for f in (BASE_DIR / "data").glob("*")])
        return

    # Create output directories if they don't exist
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    with open(INPUT_FILE, "r", encoding="utf-8", errors="replace") as f:
        try:
            articles = json.load(f)
        except json.JSONDecodeError:
            print(f"ERROR: Could not decode JSON from {INPUT_FILE}")
            return

    # Process
    enriched = [enrich(article) for article in articles]

    # Save data
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"Success! Enriched AI summaries created at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()