import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key=os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env file.")
    exit()

print("Authenticating and fetching models...\n")

try:
    # Initialize the Gemini client
    client = genai.Client(api_key=api_key)

    # Fetch and list the models
    print("Available Gemini Models:")
    print("-" * 30)

    for model in client.models.list():
        # We filter for 'gemini' to skip older palm/bison models
        if "gemini" in model.name.lower():
            print(f"Model ID: {model.name}")

except Exception as e:
    print(f"Failed to fetch models: {e}")