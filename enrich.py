import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_FILE = PROJECT_ROOT / "data" / "technical_summaries.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "enriched_summaries.json"

# ----------------------------
# Diversified fallback pools
# ----------------------------
GENERIC_TAKEAWAYS = [
    "Signals incremental evolution rather than a paradigm shift in current AI systems.",
    "Reinforces known techniques with modest refinements to existing methods.",
    "Adds empirical validation to approaches already used in production AI stacks."
]

GENERIC_RISKS = [
    "Marginal performance gains may not justify integration effort.",
    "Unclear production readiness despite promising early results.",
    "Risk of overfitting conclusions to narrow benchmarks."
]

GENERIC_OPPORTUNITIES = [
    "Practical improvements when layered onto existing AI workflows.",
    "Selective adoption in niche use cases with clear ROI.",
    "Foundation for future optimization rather than immediate disruption."
]

SOURCE_AUDIENCE_MAP = {
    "Arxiv": ["Research Scientists", "ML Engineers"],
    "Hugging Face": ["ML Engineers", "Open-Source Contributors"],
    "Microsoft": ["Applied Researchers", "Enterprise ML Teams"],
    "Wired": ["Policy Leaders", "Tech Strategists"],
    "TechCrunch": ["Startup Founders", "Product Leaders"]
}

def enrich(article):
    title = (article.get("title") or "").strip()
    summary = article.get("what_happened") or "No summary available."
    source = article.get("source", "")

    text = f"{title} {summary}".lower()

    risk = article.get("primary_risk")
    opportunity = article.get("primary_opportunity")
    takeaway = article.get("technical_takeaway")
    audience = article.get("who_should_care")

    # ----------------------------
    # High-signal rule overrides
    # ----------------------------
    if any(k in text for k in ["privacy", "scraping", "ethics", "legal", "surveillance"]):
        risk = "Regulatory exposure and erosion of public trust due to opaque data practices."
        opportunity = "Differentiation through auditable, privacy-preserving AI pipelines."
        takeaway = "Trust, not model size, is becoming a core technical constraint in AI systems."
        audience = ["AI Ethics Engineers", "Legal & Compliance"]

    elif any(k in text for k in ["energy", "compute", "data center", "grid", "power"]):
        risk = "Compute scaling limited by physical and energy infrastructure."
        opportunity = "Efficiency-driven architectures and workload-aware scheduling."
        takeaway = "Hardware and energy constraints now shape model design decisions."
        audience = ["AI Infrastructure Engineers", "Sustainability Leaders"]

    elif any(k in text for k in ["agent", "multi-agent", "autonomous", "coding"]):
        risk = "Debugging complexity and cascading failures in agentic systems."
        opportunity = "End-to-end automation of complex cognitive workflows."
        takeaway = "Agent orchestration is emerging as a new software abstraction layer."
        audience = ["CTOs", "Engineering Leaders"]

    elif any(k in text for k in ["on-device", "edge", "local", "apple"]):
        risk = "Fragmentation across hardware-specific inference stacks."
        opportunity = "Low-latency, privacy-preserving user experiences."
        takeaway = "Hybrid local-cloud inference is becoming the dominant deployment model."
        audience = ["Mobile Engineers", "Product Managers"]

    # ----------------------------
    # Intelligent fallbacks
    # ----------------------------
    if not takeaway:
        takeaway = GENERIC_TAKEAWAYS[hash(title) % len(GENERIC_TAKEAWAYS)]

    if not risk:
        risk = GENERIC_RISKS[hash(title + "risk") % len(GENERIC_RISKS)]

    if not opportunity:
        opportunity = GENERIC_OPPORTUNITIES[hash(title + "opp") % len(GENERIC_OPPORTUNITIES)]

    if not audience:
        audience = SOURCE_AUDIENCE_MAP.get(
            next((k for k in SOURCE_AUDIENCE_MAP if k.lower() in source.lower()), ""),
            ["AI Professionals"]
        )

    # ----------------------------
    # Final mapping
    # ----------------------------
    article["primary_risk"] = risk
    article["primary_opportunity"] = opportunity
    article["technical_angle"] = takeaway
    article["who_should_care"] = audience
    article["what_happened"] = summary

    return article

def main():
    if not INPUT_FILE.exists():
        print(f"ERROR: {INPUT_FILE.name} not found")
        return

    with open(INPUT_FILE, "r", encoding="utf-8", errors="replace") as f:
        articles = json.load(f)

    enriched = [enrich(article) for article in articles]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"Enriched summaries created at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()