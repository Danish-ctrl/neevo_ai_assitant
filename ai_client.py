import requests
from config import GROQ_API_KEY

def get_ai_response(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        return f"AI Error: {response.text}"

    data = response.json()
    return data["choices"][0]["message"]["content"]