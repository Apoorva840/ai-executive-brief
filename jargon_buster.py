import os
import json
import time
import random
import sys
from google import genai
from datetime import datetime

# --- CONFIGURATION ---
INPUT_FILE = "data/deduped_news.json"
OUTPUT_JSON = "docs/data/jargon_buster.json"

def call_gemini_with_retry(prompt, max_retries=3):
    """
    Helper function to handle 429 Resource Exhausted errors 
    using exponential backoff.
    """
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            # Clean the response text
            raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(raw_text)
            
        except Exception as e:
            error_msg = str(e)
            # If it's a quota error (429), wait and retry
            if "429" in error_msg and attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.random()
                print(f"⚠️ Quota Hit (429). Retrying in {sleep_time:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(sleep_time)
            else:
                print(f"❌ AI Error: {error_msg}")
                return None

def load_deduped_data():
    try:
        if not os.path.exists(INPUT_FILE):
            return None
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)
        
        combined_text = ""
        for art in articles[:20]:
            combined_text += f"Title: {art.get('title', '')}\nSummary: {art.get('summary', '')}\n\n"
        return combined_text
    except Exception as e:
        print(f"File Loading Error: {e}")
        return None

def process_jargon(text):
    if not text:
        return None
        
    current_date = datetime.now().strftime('%B %d, %Y')
    prompt = f"""
    You are an AI Expert Educator.
    Scan the following AI news:
    ---
    {text}
    ---
    Identify 3 technical AI terms.
    For each term provide a beginner-friendly definition and a car OR kitchen analogy.
    Return ONLY valid JSON:
    {{
      "last_updated": "{current_date}",
      "is_weekly_active": true,
      "terms": [
        {{ "term": "...", "definition": "...", "analogy": "..." }}
      ]
    }}
    """
    return call_gemini_with_retry(prompt)

def main():
    # 0=Mon, 5=Sat, 6=Sun
    now = datetime.now()
    is_saturday = now.weekday() == 5
    force_run = os.environ.get("SHOW_JARGON") == "true"

    if is_saturday or force_run:
        print("🚀 Saturday: Refreshing Weekly Jargon Library...")
        news_content = load_deduped_data()
        jargon_data = process_jargon(news_content)
        
        if jargon_data:
            os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(jargon_data, f, indent=4)
            print("✅ Jargon Library updated successfully.")
        else:
            print("⚠️ Critical: AI failed to generate jargon. Skipping update to preserve old data.")
            # We exit with 0 so the pipeline continues, but we don't break the JSON.
            sys.exit(0) 
            
    else:
        # Runs on Sunday-Friday to hide the section
        print(f"📅 Weekday/Sunday ({now.strftime('%A')}): Deactivating Jargon.")
        os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump({"is_weekly_active": False, "terms": []}, f, indent=4)

if __name__ == "__main__":
    main()