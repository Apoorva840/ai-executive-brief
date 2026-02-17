import os
import json
from datetime import datetime
from openai import OpenAI

# --- CONFIGURATION ---
INPUT_FILE = "data/deduped_news.json"
OUTPUT_JSON = "docs/data/jargon_buster.json"

# Load OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


def load_deduped_data():
    try:
        if not os.path.exists(INPUT_FILE):
            return None

        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)

        combined_text = ""
        for art in articles[:20]:
            combined_text += (
                f"Title: {art.get('title', '')}\n"
                f"Summary: {art.get('summary', '')}\n\n"
            )

        return combined_text

    except Exception as e:
        print(f"File Loading Error: {e}")
        return None


def process_jargon(text):
    if not text:
        return None

    current_date = datetime.now().strftime('%B %d, %Y')

    prompt = f"""
    Scan the following AI news:
    ---
    {text}
    ---
    Identify 3 technical AI terms.
    For each term provide:
    - A clear beginner-friendly definition
    - A car OR kitchen analogy

    Return ONLY valid JSON in this structure:

    {{
      "last_updated": "{current_date}",
      "is_weekly_active": true,
      "terms": [
        {{
          "term": "Term Name",
          "definition": "...",
          "analogy": "..."
        }}
      ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an AI Expert Educator. Return strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"AI Error: {e}")
        return None


def main():
    is_saturday = datetime.now().weekday() == 5
    force_run = os.environ.get("SHOW_JARGON") == "true"

    if is_saturday or force_run:
        print("🚀 Refreshing Weekly Jargon Library...")
        news_content = load_deduped_data()
        jargon_data = process_jargon(news_content)

        if jargon_data:
            os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(jargon_data, f, indent=4)

    else:
        print("📅 Weekday: Clearing Jargon for Daily Brief view.")
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump({"is_weekly_active": False, "terms": []}, f)


if __name__ == "__main__":
    main()