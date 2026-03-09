import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("List of models that support text generation:")
for m in client.models.list():
    if 'generateContent' in m.supported_actions:
        print(f"-> {m.name}")