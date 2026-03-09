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

def call_gemini_with_retry(prompt, max_retries=5):
    """
    Enhanced retry logic to specifically handle Gemini Free Tier 429 limits.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment.")
        return None

    client = genai.Client(api_key=api_key)
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            # Clean the response text from potential Markdown wrappers
            raw_text = response.text.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
            return json.loads(raw_text)
            
        except Exception as e:
            error_msg = str(e)
            
            # If it's a quota error (429), we need a significant wait
            if "429" in error_msg:
                # Exponential backoff: 30s, 60s, 90s...
                sleep_time = (30 * (attempt + 1)) + random.uniform(1, 5)
                print(f"⚠️ Quota Hit (429). Gemini Free Tier busy. Waiting {sleep_time:.2f}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(sleep_time)
            else:
                print(f"❌ AI Error: {error_msg}")
                return None
    
    print("❌ Failed after maximum retries due to Quota limits.")
    return None

def load_deduped_data():
    try:
        if not os.path.exists(INPUT_FILE):
            print(f"⚠️ {INPUT_FILE} not found. Using generic prompt.")
            return "General AI advancements and Large Language Models."
            
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)
        
        if not articles:
            return "General AI advancements."

        combined_text = ""
        # Take a sample of news to stay within token limits
        for art in articles[:15]:
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
    Identify 3 technical AI terms from the news below or general trending AI topics.
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
        print("✅ Jargon Library updated successfully and is now VISIBLE.")
    else:
        # If AI fails, we try to keep the existing file so the website doesn't break
        if os.path.exists(OUTPUT_JSON):
            print("⚠️ Keeping existing jargon data due to AI failure.")
        else:
            print("⚠️ Creating empty fallback jargon file.")
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump({"is_weekly_active": True, "terms": [{"term": "Neural Networks", "definition": "Computer systems modeled on the human brain.", "analogy": "Like a series of filters in a coffee machine."}]}, f)

if __name__ == "__main__":
    main()