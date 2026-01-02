import os
from dotenv import load_dotenv
import cohere

load_dotenv()

api_key = os.getenv("COHERE_API_KEY")
print("API Key from env:", api_key)

if not api_key:
    print("❌ No API key found")
else:
    co = cohere.Client(api_key)

    try:
        resp = co.chat(
            model="command-r-plus-08-2024",  # ✅ new stable model
            message="Say hello in one sentence!"
        )
        print("✅ Response:", resp.text)
    except Exception as e:
        print("Error:", e)
