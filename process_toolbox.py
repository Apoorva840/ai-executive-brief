import os
import json
import time
import random
from pathlib import Path
from google import genai
from google.genai import types
from datetime import datetime

# ============================
# CONFIGURATION & PATHS
# ============================
PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATA_INPUT = PROJECT_ROOT / "data" / "raw_github_trending.json"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "data" / "toolbox.json"

def call_gemini_with_retry(prompt, max_retries=3):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json'
                )
            )
            # Parse the response text as JSON
            return json.loads(response.text)
            
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                sleep_time = (5 * (attempt + 1)) + random.random()
                print(f"⚠️ Quota Hit. Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            else:
                print(f"❌ AI Error: {e}")
                return None

def process_tools_with_ai(raw_repos):
    # Use fallback context if repos are missing
    context = json.dumps(raw_repos[:15]) if raw_repos else "No new repos today. Suggest 3 trending AI tools."
    
    prompt = f"""
    Analyze these repositories and extract the top 3 most useful AI tools.
    Return a JSON object with a 'tools' key containing a list of objects.
    
    Format:
    {{
      "tools": [
        {{ "Name": "..", "Category": "..", "Description": "..", "Use_Case": "..", "URL": ".." }}
      ]
    }}

    RAW DATA: {context}
    """
    return call_gemini_with_retry(prompt)

def main():
    print("🛠️ [RUNNING] process_toolbox.py...")
    
    if not RAW_DATA_INPUT.exists():
        print(f"⚠️ No data found at {RAW_DATA_INPUT}. Creating empty toolbox.")
        raw_repos = []
    else:
        with open(RAW_DATA_INPUT, "r", encoding="utf-8") as f:
            raw_repos = json.load(f)

    try:
        structured_data = process_tools_with_ai(raw_repos)
        
        if not structured_data:
            return

        # --- FIX: TYPE CHECKING ---
        # If AI returns a list directly, use it. If it's a dict, use .get()
        if isinstance(structured_data, list):
            tools_list = structured_data
        else:
            tools_list = structured_data.get("tools", [])

        final_output = {
            "last_updated": datetime.now().strftime('%B %d, %Y'),
            "tools": tools_list
        }

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=4)
            
        print(f"✅ Toolbox generated with {len(final_output['tools'])} tools.")

    except Exception as e:
        print(f"❌ Error processing toolbox: {e}")

if __name__ == "__main__":
    main()