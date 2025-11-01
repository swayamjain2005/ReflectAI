import os
import requests
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateMessage"

SYSTEM_PROMPT = "You are a helpful assistant."

body = {
    "prompt": {
        "messages": [
            {"content": SYSTEM_PROMPT, "role": "system"},
            {"content": "Hello!", "role": "user"}
        ]
    },
    "temperature": 0.7,
    "maxOutputTokens": 100
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {GOOGLE_API_KEY}"
}

response = requests.post(GEMINI_API_URL, headers=headers, json=body)
print("Status code:", response.status_code)
print("Response body:", response.text)
