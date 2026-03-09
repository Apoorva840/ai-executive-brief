import os
import json
import time
import random
import sys
import re
from google import genai
from datetime import datetime

# --- CONFIGURATION ---
INPUT_FILE = "data/deduped_news.json"
OUTPUT_JSON = "docs/data/jargon_buster.json"

def call_gemini_with_retry(prompt, max_retries=5):
    """
    Enhanced retry logic to specifically handle Gemini Free Tier 429 limits
    and robustly extract JSON from the response.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment.")
        return None

    client = genai.Client(api_key=api_key)
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )
            
            # Robust JSON extraction using regex
            raw_text = response.text.strip()
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            
            if json_match:
                clean_json = json_match.group(0)
                return json.loads(clean_json)
            else:
                print("⚠️ AI returned text but no valid JSON block found.")
                continue
            
        except Exception as e:
            error_msg = str(e)
            
            # 429 RESOURCE_EXHAUSTED handling
            if "429" in error_msg:
                sleep_time = (30 * (attempt + 1)) + random.uniform(2, 5)
                print(f"⚠️ Quota Hit (429). Waiting {sleep_time:.2f}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(sleep_time)
            else:
                print(f"❌ AI Error: {error_msg}")
                return None
    
    return None

def load_deduped_data():
    try:
        if not os.path.exists(INPUT_FILE):
            return "General AI advancements and LLMs."
            
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)
        
        if not articles:
            return "General AI advancements."

        combined_text = ""
        # Limiting to top 10 articles to avoid context window/token limits
        for art in articles[:10]:
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
    Identify 3 technical AI terms from the news below.
    For each term provide a beginner-friendly definition and a clever car OR kitchen analogy.
    
    Context:
    ---
    {text}
    ---
    
    Return ONLY valid JSON:
    {{
      "last_updated": "{current_date}",
      "is_weekly_active": true,
      "terms": [
        {{ "term": "...", "definition": "...", "analogy": "..." }},
        {{ "term": "...", "definition": "...", "analogy": "..." }},
        {{ "term": "...", "definition": "...", "analogy": "..." }}
      ]
    }}
    """
    return call_gemini_with_retry(prompt)

def main():
    print(f"🚀 Running Daily Jargon Update ({datetime.now().strftime('%A')})...")
    
    news_content = load_deduped_data()
    jargon_data = process_jargon(news_content)
    
    if jargon_data:
        os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(jargon_data, f, indent=4)
        print("✅ Jargon Library updated successfully.")
    else:
        if os.path.exists(OUTPUT_JSON):
            print("⚠️ AI failed. Keeping existing jargon data to prevent site breakage.")
        else:
            print("⚠️ Creating fallback jargon file.")
            fallback = {
                "last_updated": datetime.now().strftime('%B %d, %Y'),
                "is_weekly_active": True, 
                "terms": [{"term": "LLM", "definition": "Large Language Model", "analogy": "A giant digital library that can talk back."}]
            }
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(fallback, f, indent=4)

if __name__ == "__main__":
    main()