import os
from dotenv import load_dotenv

# 1. Open the local .env "vault"
load_dotenv()

# 2. Grab ALL the secret keys from the vault
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# 3. Safety checks to warn you if something is misspelled in the .env file
if not GROQ_API_KEY:
    print("⚠️ WARNING: GROQ_API_KEY is missing!")
if not GMAIL_APP_PASSWORD:
    print("⚠️ WARNING: GMAIL_APP_PASSWORD is missing!")
if not GMAIL_ADDRESS:
    print("⚠️ WARNING: GMAIL_ADDRESS is missing!")
if not WEATHER_API_KEY:
    print("⚠️ WARNING: WEATHER_API_KEY is missing!")