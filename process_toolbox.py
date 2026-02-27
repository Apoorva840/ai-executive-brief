import os
import json
from pathlib import Path
import google.generativeai as genai

# ============================
# CONFIGURATION & PATHS
# ============================
PROJECT_ROOT = Path(__file__).resolve().parent
# This assumes your Ingest script saves raw repo data here
RAW_DATA_INPUT = PROJECT_ROOT / "data" / "raw_github_trending.json"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "data" / "toolbox.json"

# Configure Gemini
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

def process_tools_with_ai(raw_repos):
    """
    Uses Gemini 2.5 Flash to categorize and summarize developer tools.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Constructing the system prompt for structured JSON output
    prompt = f"""
    You are an expert AI Developer Advocate. 
    Analyze the following list of trending GitHub repositories and extract the top 3 most useful AI tools.
    
    For each tool, you MUST provide:
    1. Name: Repository name.
    2. Category: Strictly one of [Vision, NLP, Audio, Multimodal, DevTools, Infrastructure].
    3. Description: A 1-sentence summary of what it does.
    4. Use Case: How a developer would use this in a real project.
    5. URL: The GitHub link.

    Return the result as a VALID JSON object with the key "tools".
    
    RAW DATA:
    {json.dumps(raw_repos)}
    """

    response = model.generate_content(prompt)
    
    # Clean the response to ensure it's pure JSON
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)

def main():
    print("🛠️ [RUNNING] process_toolbox.py...")
    
    if not RAW_DATA_INPUT.exists():
        print(f"⚠️ No raw data found at {RAW_DATA_INPUT}. Skipping.")
        return

    with open(RAW_DATA_INPUT, "r") as f:
        raw_repos = json.load(f)

    try:
        # Process data with Gemini 2.5 Flash
        structured_data = process_tools_with_ai(raw_repos)
        
        # Add metadata
        final_output = {
            "last_updated": os.getenv("CURRENT_DATE", "2026-02-26"),
            "tools": structured_data["tools"]
        }

        # Save to the "Face" directory for the microsite
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(final_output, f, indent=4)
            
        print(f"✅ Toolbox generated with {len(final_output['tools'])} tools.")

    except Exception as e:
        print(f"❌ Error processing toolbox: {e}")

if __name__ == "__main__":
    main()