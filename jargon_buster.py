import os
import json
from google import genai
from datetime import datetime

# --- CONFIGURATION ---
INPUT_FILE = "data/deduped_news.json"
OUTPUT_JSON = "docs/data/jargon_buster.json"

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
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.0-flash", # Use 2.0 or 1.5 for stability
            contents=prompt
        )
        raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw_text)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

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
    else:
        # IMPORTANT: This block runs on Sunday-Friday
        print(f"📅 Weekday/Sunday ({now.strftime('%A')}): Deactivating Jargon.")
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            # We set active to False so send_email.py ignores this file
            json.dump({"is_weekly_active": False, "terms": []}, f, indent=4)

if __name__ == "__main__":
    main()