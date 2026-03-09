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

def call_gemini_with_retry(prompt, max_retries=3):
    """
    Enhanced failover logic: Tries multiple models to bypass individual model quotas.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found.")
        return None

    client = genai.Client(api_key=api_key)
    
    # Model Pool to distribute load and bypass 'Daily Quota' blocks
    model_pool = [
        "gemini-3-flash-preview", 
        "gemini-1.5-flash", 
        "gemini-2.0-flash"
    ]
    
    for model_name in model_pool:
        print(f"🤖 Attempting Jargon generation with: {model_name}")
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                
                raw_text = response.text.strip()
                json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                
                if json_match:
                    return json.loads(json_match.group(0))
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    sleep_time = (20 * (attempt + 1)) + random.uniform(2, 5)
                    print(f"⚠️ {model_name} Quota Hit. Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                else:
                    print(f"❌ {model_name} Error: {error_msg}")
                    break # Skip to next model in pool
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
        # Send a concentrated slice of news to keep prompt high-quality
        for art in articles[:12]:
            combined_text += f"Title: {art.get('title', '')}\nSummary: {art.get('summary', '')}\n\n"
        return combined_text
    except Exception as e:
        print(f"File Loading Error: {e}")
        return None

def process_jargon(text):
    if not text:
        return None
        
    current_date = datetime.now().strftime('%B %d, %Y')
    
    # NEW PROFESSIONAL PROMPT: Longer definitions, Business Value, and Analogies
    prompt = f"""
    You are an AI Expert Educator for a high-end technical executive brief. 
    Identify 3 complex technical AI terms or trends from the news below. 
    
    For each term, provide:
    1. A 'Deep Dive' definition (2-3 sentences) that explains the mechanics.
    2. A clever Car OR Kitchen analogy to make it relatable.
    3. A 'Business Value' or 'CEO Insight' explaining why this matters for the bottom line.

    Context:
    ---
    {text}
    ---
    
    Return ONLY valid JSON:
    {{
      "last_updated": "{current_date}",
      "is_weekly_active": true,
      "terms": [
        {{ 
          "term": "...", 
          "definition": "...", 
          "analogy": "...", 
          "business_value": "..." 
        }}
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
        print("⚠️ AI failed. Keeping existing data.")

if __name__ == "__main__":
    main()