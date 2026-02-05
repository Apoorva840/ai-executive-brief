import json
from pathlib import Path

# ============================
# PATH CONFIGURATION
# ============================
PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_FILE = PROJECT_ROOT / "data" / "technical_summaries.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "enriched_summaries.json"

# ============================
# ENRICHMENT LOGIC
# ============================

def enrich(article):
    title = article.get("title", "").strip()
    summary = article.get("what_happened") or article.get("summary") or ""
    
    # Text for rule matching
    text = f"{title} {summary}".lower()

    # 1. Start with values from summarize.py if they exist
    risk = article.get("primary_risk")
    opportunity = article.get("primary_opportunity")
    takeaway = article.get("technical_takeaway")
    audience = article.get("who_should_care")

    # 2. Refined Rule-based Overrides (Deeper Granularity)
    if any(k in text for k in ["privacy", "scraping", "ethics", "legal"]):
        risk = "Regulatory exposure and public trust risks regarding data governance."
        opportunity = "Leadership in compliant, privacy-first AI system design."
        takeaway = "Highlights the technical shift toward 'verifiable' data pipelines and ethical scraping."
        audience = ["Legal & Compliance", "AI Ethics Engineers"]

    elif any(k in text for k in ["energy", "compute", "solar", "grid", "data center"]):
        risk = "Escalating infrastructure costs and power grid capacity bottlenecks."
        opportunity = "Operational efficiency through decentralized or renewable AI infrastructure."
        takeaway = "Infrastructure constraints are now a primary bottleneck for model scaling."
        audience = ["AI Infrastructure Engineers", "Sustainability Officers"]

    elif any(k in text for k in ["coding", "coder", "developer", "agent"]):
        risk = "Technical debt and quality variance from autonomous agentic workflows."
        opportunity = "Compression of software development lifecycles via AI agents."
        takeaway = "The shift from LLM-chatbots to autonomous 'agents' is the key current trend."
        audience = ["Engineering Leaders", "CTOs"]

    elif "apple" in text or "local" in text or "on-device" in text:
        risk = "Hardware-specific optimization silos (Apple vs. Rest)."
        opportunity = "Privacy-first, zero-latency inference on edge devices."
        takeaway = "Demonstrates the move toward hybrid local/remote model execution patterns."
        audience = ["Mobile Engineers", "Product Leaders"]

    # 3. Final Fallbacks (If everything is somehow missing)
    risk = risk or "Standard implementation and adoption risks apply."
    opportunity = opportunity or "Incremental gains through applied AI adoption."
    takeaway = takeaway or "Refines current understanding of AI implementation patterns."
    audience = audience or ["AI Professionals"]

    # 4. Map back to fields used by format_brief.py
    article["primary_risk"] = risk
    article["primary_opportunity"] = opportunity
    article["technical_angle"] = takeaway  # format_brief.py looks for this
    article["who_should_care"] = audience
    article["what_happened"] = summary

    return article

def main():
    print(f"Targeting input: {INPUT_FILE}")

    if not INPUT_FILE.exists():
        print(f" ERROR: {INPUT_FILE.name} not found")
        return

    with open(INPUT_FILE, "r", encoding="utf-8", errors="replace") as f:
        articles = json.load(f)

    enriched = [enrich(article) for article in articles]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f" Enriched summaries created at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()