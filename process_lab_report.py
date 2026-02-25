import json
import os
from pathlib import Path
from google import genai
from google.genai import types # This is part of google-genai

# --- CONFIG ---
INPUT_FILE = "data/deduped_news.json"
OUTPUT_FILE = "docs/data/lab_report.json"

def filter_research_papers():
    if not os.path.exists(INPUT_FILE):
        return []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        all_articles = json.load(f)

    research_sources = ["Arxiv AI", "Hugging Face Blog", "Microsoft Research"]
    papers = [a for a in all_articles if a.get("source") in research_sources]
    
    return papers

def analyze_papers_with_gemini(papers):
    if not papers:
        return None

    sample_text = ""
    for p in papers[:10]:
        sample_text += f"Title: {p['title']}\nAbstract: {p.get('summary', 'No abstract')}\nURL: {p['url']}\n---\n"

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = f"""
    You are a Senior AI Research Scientist. Review these papers:
    {sample_text}

    Select the 3 most important papers for an AI Engineer.
    Return ONLY valid JSON:
    {{
      "last_updated": "Today's Date",
      "papers": [
        {{
          "title": "...",
          "innovation": "...",
          "benchmarks": "...",
          "use_case": "...",
          "url": "..."
        }}
      ]
    }}
    """

    # Using your confirmed working model version
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type='application/json'
        )
    )
    return json.loads(response.text)

def main():
    print("🔬 Filtering Research Papers for Lab Report...")
    papers = filter_research_papers()
    
    if not papers:
        print("⚠️ No research papers found today.")
        return

    report = analyze_papers_with_gemini(papers)
    
    if report:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(report, f, indent=4)
        print(f"✅ Lab Report generated with {len(report['papers'])} papers.")

if __name__ == "__main__":
    main()