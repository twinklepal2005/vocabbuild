import os
import requests
from dotenv import load_dotenv

# Load API key
dotenv_path = r"C:\Users\ASUS\AppData\Local\Programs\Python\Python312\resume scanner\.env"
load_dotenv(dotenv_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

word = "example"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

headers = {
    "Content-Type": "application/json"
}

# Correct payload for Gemini 2.5 Flash
data = {
    "contents": [
        {
            "parts": [
                {
                    "text": f"Explain the word '{word}' in very simple English with 2–3 short example sentences demonstrating how to use it. Do NOT include synonyms or antonyms."
                }
            ]
        }
    ]
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    resp_json = response.json()
    candidates = resp_json.get("candidates", [])
    if candidates:
        meaning = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        print("Meaning:\n", meaning)
    else:
        print("No candidates returned")
else:
    print("Failed:", response.status_code, response.text)
