import json
from pathlib import Path

N8N_BASE = Path("C:/Users/HP/.n8n-files")
INPUT_FILE = Path("data/technical_summaries.json")
OUTPUT_FILE = N8N_BASE / "ai-input" / "enriched_summaries.json"

def enrich(article):
    text = f"{article.get('title','')} {article.get('what_happened','')}".lower()

    # Defaults (never null)
    risk = article.get("primary_risk") or "Execution and adoption risks remain manageable but present."
    opportunity = article.get("primary_opportunity") or "Incremental gains through applied AI adoption."
    audience = article.get("who_should_care") or ["AI Professionals"]

    # Strengthen if keywords exist
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

    article["primary_risk"] = risk
    article["primary_opportunity"] = opportunity
    article["who_should_care"] = audience
    return article

def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8", errors="replace") as f:
        articles = json.load(f)

    enriched = [enrich(article) for article in articles]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"Enriched AI summaries created: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
