import json
import os
import time  # For backoff
from google import genai
from google.genai import types, errors  # Added errors for specific catching

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

    # Configure Client with built-in Retries for 503/429 errors
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=3, 
                http_status_codes=[429, 500, 502, 503, 504]
            )
        )
    )
    
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

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        return json.loads(response.text)
    except errors.ServerError as e:
        print(f"⚠️ Gemini Server Error (503): {e}. High demand detected. Skipping Lab Report.")
        return None
    except Exception as e:
        print(f"❌ Unexpected Error in Gemini Call: {e}")
        return None

def main():
    print("🔬 Filtering Research Papers for Lab Report...")
    papers = filter_research_papers()
    
    if not papers:
        print("⚠️ No research papers found today.")
        return

    # Call the AI analyzer
    report = analyze_papers_with_gemini(papers)
    
    # --- GRACEFUL FALLBACK ---
    if not report:
        print("💡 Falling back: Creating a placeholder report to keep the pipeline moving.")
        report = {
            "last_updated": time.strftime("%Y-%m-%d"),
            "papers": [],
            "status": "AI service temporarily unavailable"
        }
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=4)
    
    if report.get("papers"):
        print(f"✅ Lab Report generated with {len(report['papers'])} papers.")
    else:
        print("✅ Pipeline continued with a placeholder report.")

if __name__ == "__main__":
    main()