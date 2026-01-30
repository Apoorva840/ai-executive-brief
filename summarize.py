import json
from pathlib import Path
import re

INPUT_FILE = Path("data/top_news.json")
OUTPUT_FILE = Path("data/technical_summaries.json")

TECH_KEYWORDS = {
    "ethics": ["scraping", "privacy", "consent", "ethics"],
    "infrastructure": ["data center", "grid", "energy", "compute", "gpu"],
    "models": ["llm", "language model", "model", "training", "prompt"],
    "vision": ["camera", "vision", "glasses", "facial"],
    "deployment": ["deployment", "scaling", "inference", "production"]
}

def clean_text(text, max_chars=350):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]

def infer_technical_takeaway(text):
    if any(k in text for k in TECH_KEYWORDS["ethics"]):
        return "Highlights growing technical and regulatory pressure to design AI systems with compliant data pipelines and privacy safeguards."
    if any(k in text for k in TECH_KEYWORDS["infrastructure"]):
        return "Reinforces infrastructure constraints around compute, energy efficiency, and large-scale model deployment."
    if any(k in text for k in TECH_KEYWORDS["models"]):
        return "Demonstrates rapid evolution of model capabilities and the importance of tooling that accelerates development workflows."
    if any(k in text for k in TECH_KEYWORDS["vision"]):
        return "Signals continued advancement in computer vision systems with implications for privacy-sensitive environments."
    return "Reflects incremental but meaningful progress in applied AI capabilities and tooling."

def infer_risk(text):
    if "privacy" in text or "scraping" in text:
        return "Potential regulatory scrutiny and reputational risk related to data usage and consent."
    if "energy" in text or "compute" in text:
        return "Rising infrastructure costs and scalability limitations."
    if "model" in text:
        return "Risk of vendor lock-in or over-reliance on rapidly changing AI platforms."
    return "Execution risk as adoption outpaces organizational readiness."

def infer_opportunity(text):
    if "privacy" in text or "scraping" in text:
        return "Opportunity to differentiate through compliant and transparent AI data practices."
    if "energy" in text or "compute" in text:
        return "Competitive advantage through optimized, cost-efficient AI infrastructure."
    if "model" in text:
        return "Productivity gains by integrating advanced AI models into workflows."
    return "Early-mover advantage for teams that operationalize AI effectively."

def detect_role(text):
    if "ethics" in text or "privacy" in text:
        return ["AI Ethics Engineers", "Policy Teams"]
    if "infrastructure" in text or "energy" in text:
        return ["AI Infrastructure Engineers"]
    if "model" in text or "llm" in text:
        return ["ML Engineers", "Product Leaders"]
    return ["AI Professionals"]

def technical_summary(article):
    combined_text = f"{article['title']} {article['summary']}".lower()

    return {
        "title": article["title"],
        "url": article["url"],
        "source": article["source"],
        "score": article["score"],
        "what_happened": clean_text(article["summary"]),
        "technical_takeaway": infer_technical_takeaway(combined_text),
        "primary_risk": infer_risk(combined_text),
        "primary_opportunity": infer_opportunity(combined_text),
        "who_should_care": detect_role(combined_text)
    }

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)

    summaries = [technical_summary(article) for article in articles]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    print(f"Technical summaries generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
