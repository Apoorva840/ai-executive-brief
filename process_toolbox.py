import os
import json
import time
import random
from pathlib import Path
from google import genai
from google.genai import types

# ============================
# CONFIGURATION & PATHS
# ============================
PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATA_INPUT = PROJECT_ROOT / "data" / "raw_github_trending.json"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "data" / "toolbox.json"

def call_gemini_with_retry(prompt, max_retries=3):
    """Handles 429 errors for Toolbox processing."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash", # Consistent with your other stable scripts
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json'
                )
            )
            return json.loads(response.text)
            
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.random()
                print(f"⚠️ Toolbox Quota Hit. Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            else:
                raise e

def process_tools_with_ai(raw_repos):
    """Categorizes and summarizes developer tools using structured prompt."""
    prompt = f"""
    Analyze these trending GitHub repositories and extract the top 3 most useful AI tools.
    For each tool, provide: Name, Category [Vision, NLP, Audio, Multimodal, DevTools, Infrastructure], 
    Description (1-sentence), Use Case, and URL.
    
    RAW DATA:
    {json.dumps(raw_repos[:15])} 
    """
    return call_gemini_with_retry(prompt)

def main():
    print("🛠️ [RUNNING] process_toolbox.py...")
    
    if not RAW_DATA_INPUT.exists():
        print(f"⚠️ No raw data found at {RAW_DATA_INPUT}. Skipping.")
        return

    with open(RAW_DATA_INPUT, "r", encoding="utf-8") as f:
        raw_repos = json.load(f)

    try:
        structured_data = process_tools_with_ai(raw_repos)
        
        final_output = {
            "last_updated": datetime.now().strftime('%B %d, %Y'),
            "tools": structured_data.get("tools", [])
        }

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=4)
            
        print(f"✅ Toolbox generated with {len(final_output['tools'])} tools.")

    except Exception as e:
        print(f"❌ Error processing toolbox: {e}")

if __name__ == "__main__":
    from datetime import datetime
    main()